from __future__ import annotations


class IdempotencyGuard:
    """Makes side effects fire at most once.

    Retries and reflector re-runs are expected, so an external action (sending an
    email) is keyed; replaying the same key is skipped instead of repeated.
    """

    def __init__(self) -> None:
        self._done: set[str] = set()

    def seen(self, key: str) -> bool:
        return key in self._done

    def mark(self, key: str) -> None:
        self._done.add(key)

    def run_once(self, key: str) -> bool:
        """Return True if the caller may proceed; False if already done."""
        if key in self._done:
            return False
        self._done.add(key)
        return True
