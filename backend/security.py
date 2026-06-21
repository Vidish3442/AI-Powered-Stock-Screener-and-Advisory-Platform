"""Small, process-local security helpers for API endpoints."""

from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request, status


class RateLimiter:
    """Fixed-window-like limiter backed by timestamp queues.

    This protects the current single-process deployment. A shared Redis-backed
    limiter should replace it if the API is later run with multiple workers.
    """

    def __init__(self):
        self._events = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str, limit: int, window_seconds: int) -> None:
        now = monotonic()
        cutoff = now - window_seconds

        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()

            if len(events) >= limit:
                retry_after = max(1, int(events[0] + window_seconds - now) + 1)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please try again later.",
                    headers={"Retry-After": str(retry_after)},
                )

            events.append(now)

            if not events:
                self._events.pop(key, None)


rate_limiter = RateLimiter()


def client_ip(request: Request) -> str:
    """Return the socket peer address without trusting spoofable headers."""
    return request.client.host if request.client else "unknown"
