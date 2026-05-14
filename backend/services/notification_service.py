"""DEPRECATED - Notifications have been removed per feedback.

This stub remains only so legacy imports do not break in case something is
still referenced externally. All methods are no-ops returning True.
"""
import logging

log = logging.getLogger(__name__)


class _NoopNotifier:
    """No-op notifier. Kept to preserve backward-compatibility of imports."""

    enabled = False

    def send_email(self, *args, **kwargs) -> bool:
        return True

    def notify_large_withdrawal(self, *args, **kwargs) -> bool:
        return True

    def notify_account_opened(self, *args, **kwargs) -> bool:
        return True

    def notify_suspicious_activity(self, *args, **kwargs) -> bool:
        return True


# Legacy singleton name.
notifier = _NoopNotifier()