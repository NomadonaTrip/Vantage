"""Rate limiting for source adapters."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.schemas.lead import LeadSource
from src.services.sources.base import RateLimitStatus
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for a rate limiter."""

    requests_per_second: float = 1.0
    burst_size: int = 5
    cooldown_seconds: float = 60.0  # Cooldown after hitting limit


# Default rate limits per source
DEFAULT_RATE_LIMITS: dict[LeadSource, RateLimitConfig] = {
    LeadSource.UPWORK: RateLimitConfig(requests_per_second=0.5, burst_size=3, cooldown_seconds=120.0),
    LeadSource.REDDIT: RateLimitConfig(requests_per_second=1.0, burst_size=10, cooldown_seconds=60.0),
    LeadSource.APOLLO: RateLimitConfig(requests_per_second=0.5, burst_size=5, cooldown_seconds=60.0),
    LeadSource.CLUTCH: RateLimitConfig(requests_per_second=0.2, burst_size=2, cooldown_seconds=180.0),
    LeadSource.BING: RateLimitConfig(requests_per_second=3.0, burst_size=10, cooldown_seconds=30.0),
    LeadSource.GOOGLE: RateLimitConfig(requests_per_second=1.0, burst_size=10, cooldown_seconds=60.0),
    LeadSource.MANUAL: RateLimitConfig(requests_per_second=100.0, burst_size=100, cooldown_seconds=0.0),
}


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter implementation.

    Allows bursting up to burst_size requests, then limits to
    requests_per_second sustained rate.
    """

    def __init__(self, config: RateLimitConfig) -> None:
        """
        Initialize rate limiter.

        Args:
            config: Rate limit configuration.
        """
        self.config = config
        self.tokens = float(config.burst_size)
        self.last_update = datetime.now(timezone.utc)
        self.cooldown_until: datetime | None = None
        self._lock = asyncio.Lock()

    async def acquire(self, timeout: float = 30.0) -> bool:
        """
        Acquire a token, waiting if necessary.

        Args:
            timeout: Maximum time to wait in seconds.

        Returns:
            True if token acquired, False if timeout or limited.
        """
        start_time = datetime.now(timezone.utc)

        while True:
            async with self._lock:
                # Check if in cooldown
                if self.cooldown_until:
                    if datetime.now(timezone.utc) < self.cooldown_until:
                        remaining = (self.cooldown_until - datetime.now(timezone.utc)).total_seconds()
                        logger.warning(
                            "rate_limiter_in_cooldown",
                            cooldown_remaining=remaining,
                        )
                        return False
                    else:
                        # Cooldown expired
                        self.cooldown_until = None
                        self.tokens = float(self.config.burst_size)

                # Refill tokens based on time elapsed
                now = datetime.now(timezone.utc)
                elapsed = (now - self.last_update).total_seconds()
                self.tokens = min(
                    float(self.config.burst_size),
                    self.tokens + elapsed * self.config.requests_per_second,
                )
                self.last_update = now

                # Check if we have a token
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return True

            # Check timeout
            elapsed_total = (datetime.now(timezone.utc) - start_time).total_seconds()
            if elapsed_total >= timeout:
                return False

            # Wait for token refill
            wait_time = (1.0 - self.tokens) / self.config.requests_per_second
            wait_time = min(wait_time, timeout - elapsed_total, 1.0)
            await asyncio.sleep(wait_time)

    def trigger_cooldown(self) -> None:
        """Trigger cooldown period after hitting external rate limit."""
        self.cooldown_until = datetime.now(timezone.utc)
        if self.config.cooldown_seconds > 0:
            from datetime import timedelta

            self.cooldown_until += timedelta(seconds=self.config.cooldown_seconds)
        logger.info(
            "rate_limiter_cooldown_triggered",
            cooldown_until=self.cooldown_until.isoformat() if self.cooldown_until else None,
        )

    def get_status(self) -> RateLimitStatus:
        """Get current rate limit status."""
        is_limited = False
        reset_at = None

        if self.cooldown_until:
            if datetime.now(timezone.utc) < self.cooldown_until:
                is_limited = True
                reset_at = self.cooldown_until

        return RateLimitStatus(
            remaining_requests=int(self.tokens),
            reset_at=reset_at,
            is_limited=is_limited,
        )


class RateLimiterRegistry:
    """
    Registry of rate limiters for all sources.

    Provides centralized management of rate limiting across adapters.
    """

    def __init__(self, custom_configs: dict[LeadSource, RateLimitConfig] | None = None) -> None:
        """
        Initialize registry with rate limiters.

        Args:
            custom_configs: Optional custom rate limit configurations.
        """
        self._limiters: dict[LeadSource, TokenBucketRateLimiter] = {}
        self._configs = {**DEFAULT_RATE_LIMITS}

        if custom_configs:
            self._configs.update(custom_configs)

        # Initialize limiters for all sources
        for source, config in self._configs.items():
            self._limiters[source] = TokenBucketRateLimiter(config)

    def get_limiter(self, source: LeadSource) -> TokenBucketRateLimiter:
        """
        Get rate limiter for a source.

        Args:
            source: Lead source.

        Returns:
            Rate limiter instance.
        """
        if source not in self._limiters:
            # Use default config for unknown sources
            config = self._configs.get(source, RateLimitConfig())
            self._limiters[source] = TokenBucketRateLimiter(config)

        return self._limiters[source]

    async def acquire(self, source: LeadSource, timeout: float = 30.0) -> bool:
        """
        Acquire rate limit token for a source.

        Args:
            source: Lead source.
            timeout: Maximum wait time.

        Returns:
            True if acquired, False otherwise.
        """
        limiter = self.get_limiter(source)
        return await limiter.acquire(timeout)

    def trigger_cooldown(self, source: LeadSource) -> None:
        """Trigger cooldown for a source after external rate limit."""
        limiter = self.get_limiter(source)
        limiter.trigger_cooldown()

    def get_status(self, source: LeadSource) -> RateLimitStatus:
        """Get rate limit status for a source."""
        limiter = self.get_limiter(source)
        return limiter.get_status()

    def get_all_statuses(self) -> dict[LeadSource, RateLimitStatus]:
        """Get rate limit status for all sources."""
        return {source: limiter.get_status() for source, limiter in self._limiters.items()}
