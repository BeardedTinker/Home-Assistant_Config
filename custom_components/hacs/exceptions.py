"""Custom Exceptions for HACS."""


class HacsException(Exception):
    """Super basic."""


class HacsRepositoryArchivedException(HacsException):
    """For repositories that are archived."""


class HacsNotModifiedException(HacsException):
    """For responses that are not modified."""


class HacsExpectedException(HacsException):
    """For stuff that are expected."""


class HacsRepositoryExistException(HacsException):
    """For repositories that are already exist."""


class HacsExecutionStillInProgress(HacsException):
    """Exception to raise if execution is still in progress."""


class AddonRepositoryException(HacsException):
    """Exception to raise when user tries to add add-on repository."""

    exception_message = (
        "The repository does not seem to be a integration, "
        "but an add-on repository. HACS does not manage add-ons."
    )

    def __init__(self) -> None:
        super().__init__(self.exception_message)


class HomeAssistantCoreRepositoryException(HacsException):
    """Exception to raise when user tries to add the home-assistant/core repository."""

    exception_message = (
        "You can not add homeassistant/core, to use core integrations "
        "check the Home Assistant documentation for how to add them."
    )

    def __init__(self) -> None:
        super().__init__(self.exception_message)
