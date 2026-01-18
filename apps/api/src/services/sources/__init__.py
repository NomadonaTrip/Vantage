"""Source adapter framework for lead generation."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Type

from src.schemas.lead import LeadSource
from src.services.sources.base import (
    AdapterResult,
    BaseSourceAdapter,
    RateLimitStatus,
    RawLead,
    SearchQuery,
    SourceStatus,
)
from src.services.sources.mock_adapter import MockSourceAdapter
from src.services.sources.rate_limiter import (
    RateLimitConfig,
    RateLimiterRegistry,
    TokenBucketRateLimiter,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)

__all__ = [
    # Base types
    "BaseSourceAdapter",
    "AdapterResult",
    "RawLead",
    "SearchQuery",
    "SourceStatus",
    "RateLimitStatus",
    # Rate limiting
    "RateLimitConfig",
    "RateLimiterRegistry",
    "TokenBucketRateLimiter",
    # Adapters
    "MockSourceAdapter",
    # Registry
    "SourceRegistry",
    "AdapterHealth",
]


@dataclass
class AdapterHealth:
    """Health status for a source adapter."""

    source: LeadSource
    is_available: bool
    is_rate_limited: bool
    last_success: datetime | None = None
    last_failure: datetime | None = None
    consecutive_failures: int = 0
    total_requests: int = 0
    total_leads_found: int = 0
    average_response_time_ms: float = 0.0


class SourceRegistry:
    """
    Central registry for source adapters.

    Manages adapter lifecycle, health tracking, and provides
    unified interface for searching across sources.
    """

    # Maximum consecutive failures before marking adapter unavailable
    MAX_CONSECUTIVE_FAILURES = 3

    def __init__(
        self,
        rate_limiter_registry: RateLimiterRegistry | None = None,
        use_mock: bool = False,
    ) -> None:
        """
        Initialize source registry.

        Args:
            rate_limiter_registry: Optional custom rate limiter registry.
            use_mock: If True, register mock adapters for all sources.
        """
        self._adapters: dict[LeadSource, BaseSourceAdapter] = {}
        self._health: dict[LeadSource, AdapterHealth] = {}
        self._rate_limiters = rate_limiter_registry or RateLimiterRegistry()
        self._use_mock = use_mock

        if use_mock:
            self._register_mock_adapters()

    def _register_mock_adapters(self) -> None:
        """Register mock adapters for all source types."""
        for source in LeadSource:
            if source != LeadSource.MANUAL:
                adapter = MockSourceAdapter(source=source)
                self.register(adapter)

    def register(self, adapter: BaseSourceAdapter) -> None:
        """
        Register a source adapter.

        Args:
            adapter: Adapter instance to register.
        """
        source = adapter.source_type
        self._adapters[source] = adapter
        self._health[source] = AdapterHealth(
            source=source,
            is_available=adapter.is_available,
            is_rate_limited=False,
        )
        logger.info(
            "adapter_registered",
            source=source.value,
            name=adapter.name,
        )

    def unregister(self, source: LeadSource) -> None:
        """
        Unregister a source adapter.

        Args:
            source: Source type to unregister.
        """
        if source in self._adapters:
            del self._adapters[source]
            del self._health[source]
            logger.info("adapter_unregistered", source=source.value)

    def get_adapter(self, source: LeadSource) -> BaseSourceAdapter | None:
        """
        Get adapter for a source.

        Args:
            source: Source type.

        Returns:
            Adapter instance or None if not registered.
        """
        return self._adapters.get(source)

    def get_available_sources(self) -> list[LeadSource]:
        """
        Get list of available sources.

        Returns:
            List of sources that are registered and available.
        """
        available = []
        for source, adapter in self._adapters.items():
            health = self._health[source]
            if adapter.is_available and not health.is_rate_limited:
                available.append(source)
        return available

    def get_all_sources(self) -> list[LeadSource]:
        """Get all registered sources regardless of availability."""
        return list(self._adapters.keys())

    def get_health(self, source: LeadSource) -> AdapterHealth | None:
        """
        Get health status for a source.

        Args:
            source: Source type.

        Returns:
            AdapterHealth or None if not registered.
        """
        return self._health.get(source)

    def get_all_health(self) -> dict[LeadSource, AdapterHealth]:
        """Get health status for all sources."""
        return dict(self._health)

    async def search(
        self,
        source: LeadSource,
        query: SearchQuery,
        timeout: float = 30.0,
    ) -> AdapterResult:
        """
        Execute search on a single source.

        Args:
            source: Source to search.
            query: Search parameters.
            timeout: Rate limit acquisition timeout.

        Returns:
            AdapterResult with leads and status.
        """
        adapter = self._adapters.get(source)
        if not adapter:
            return AdapterResult(
                source=source,
                status=SourceStatus.UNAVAILABLE,
                error_message=f"No adapter registered for {source.value}",
            )

        health = self._health[source]

        # Check availability
        if not adapter.is_available:
            return AdapterResult(
                source=source,
                status=SourceStatus.UNAVAILABLE,
                error_message="Adapter marked as unavailable",
            )

        # Acquire rate limit
        if not await self._rate_limiters.acquire(source, timeout):
            health.is_rate_limited = True
            return AdapterResult(
                source=source,
                status=SourceStatus.RATE_LIMITED,
                error_message="Rate limit exceeded",
                rate_limit_status=self._rate_limiters.get_status(source),
            )

        # Execute search
        try:
            result = await adapter.search(query)
            self._update_health(source, result)
            return result

        except Exception as e:
            logger.exception("adapter_search_error", source=source.value, error=str(e))
            error_result = AdapterResult(
                source=source,
                status=SourceStatus.FAILED,
                error_message=str(e),
            )
            self._update_health(source, error_result)
            return error_result

    async def search_multiple(
        self,
        sources: list[LeadSource],
        query: SearchQuery,
        timeout: float = 30.0,
    ) -> dict[LeadSource, AdapterResult]:
        """
        Execute search across multiple sources concurrently.

        Args:
            sources: List of sources to search.
            query: Search parameters.
            timeout: Timeout per source.

        Returns:
            Dict mapping sources to their results.
        """
        import asyncio

        tasks = {
            source: asyncio.create_task(self.search(source, query, timeout))
            for source in sources
        }

        results = {}
        for source, task in tasks.items():
            try:
                results[source] = await task
            except Exception as e:
                logger.exception("search_task_error", source=source.value, error=str(e))
                results[source] = AdapterResult(
                    source=source,
                    status=SourceStatus.FAILED,
                    error_message=str(e),
                )

        return results

    def _update_health(self, source: LeadSource, result: AdapterResult) -> None:
        """Update health metrics after a search."""
        health = self._health[source]
        health.total_requests += 1

        if result.is_success:
            health.last_success = datetime.now(timezone.utc)
            health.consecutive_failures = 0
            health.total_leads_found += result.lead_count
            health.is_rate_limited = False

            # Update average response time
            if health.total_requests > 1:
                health.average_response_time_ms = (
                    health.average_response_time_ms * (health.total_requests - 1)
                    + result.execution_time_ms
                ) / health.total_requests
            else:
                health.average_response_time_ms = result.execution_time_ms

        else:
            health.last_failure = datetime.now(timezone.utc)
            health.consecutive_failures += 1

            if result.status == SourceStatus.RATE_LIMITED:
                health.is_rate_limited = True
                self._rate_limiters.trigger_cooldown(source)

            # Mark unavailable after too many failures
            if health.consecutive_failures >= self.MAX_CONSECUTIVE_FAILURES:
                adapter = self._adapters.get(source)
                if adapter:
                    adapter.mark_unavailable(f"Too many consecutive failures: {health.consecutive_failures}")
                health.is_available = False
                logger.warning(
                    "adapter_marked_unavailable",
                    source=source.value,
                    consecutive_failures=health.consecutive_failures,
                )

    def reset_adapter(self, source: LeadSource) -> None:
        """Reset adapter availability and health metrics."""
        adapter = self._adapters.get(source)
        if adapter:
            adapter.mark_available()

        if source in self._health:
            health = self._health[source]
            health.is_available = True
            health.is_rate_limited = False
            health.consecutive_failures = 0

        logger.info("adapter_reset", source=source.value)
