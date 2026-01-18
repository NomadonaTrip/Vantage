"""Rate limiting middleware for voice endpoints."""

import logging
import time
from collections import defaultdict
from threading import Lock
from typing import Callable

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter using sliding window algorithm.

    Thread-safe implementation suitable for single-process deployments.
    For distributed deployments, consider Redis-based rate limiting.
    """

    def __init__(
        self,
        requests_per_minute: int = 10,
        window_seconds: int = 60,
    ):
        """Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests allowed per window
            window_seconds: Window size in seconds
        """
        self.max_requests = requests_per_minute
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def _clean_old_requests(self, user_id: str, current_time: float) -> None:
        """Remove requests outside the current window."""
        cutoff = current_time - self.window_seconds
        self._requests[user_id] = [
            t for t in self._requests[user_id] if t > cutoff
        ]

    def check_rate_limit(self, user_id: str) -> tuple[bool, int]:
        """Check if request is allowed and record it.

        Args:
            user_id: User identifier for rate limiting

        Returns:
            Tuple of (allowed, remaining_requests)
        """
        current_time = time.time()

        with self._lock:
            self._clean_old_requests(user_id, current_time)
            current_count = len(self._requests[user_id])

            if current_count >= self.max_requests:
                remaining = 0
                return False, remaining

            self._requests[user_id].append(current_time)
            remaining = self.max_requests - current_count - 1
            return True, remaining

    def get_retry_after(self, user_id: str) -> int:
        """Get seconds until next request is allowed.

        Args:
            user_id: User identifier

        Returns:
            Seconds until rate limit resets
        """
        if not self._requests.get(user_id):
            return 0

        oldest_request = min(self._requests[user_id])
        current_time = time.time()
        retry_after = self.window_seconds - (current_time - oldest_request)
        return max(1, int(retry_after))


# Voice-specific rate limiter (10 requests per minute)
voice_rate_limiter = RateLimiter(requests_per_minute=10, window_seconds=60)


def rate_limit_voice(user_id: str) -> None:
    """Check voice endpoint rate limit.

    Args:
        user_id: User ID to check

    Raises:
        HTTPException: If rate limit exceeded
    """
    allowed, remaining = voice_rate_limiter.check_rate_limit(user_id)

    if not allowed:
        retry_after = voice_rate_limiter.get_retry_after(user_id)
        logger.warning(
            f"Rate limit exceeded for user {user_id}, retry after {retry_after}s"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(voice_rate_limiter.max_requests),
                "X-RateLimit-Remaining": "0",
            },
        )
