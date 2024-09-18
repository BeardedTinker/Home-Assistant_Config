from __future__ import annotations

from typing import TYPE_CHECKING

from .base import ActionValidationBase, ValidationException

if TYPE_CHECKING:
    from ..repositories.base import HacsRepository


async def async_setup_validator(repository: HacsRepository) -> Validator:
    """Set up this validator."""
    return Validator(repository=repository)


class Validator(ActionValidationBase):
    """Validate the repository."""

    more_info = "https://hacs.xyz/docs/publish/include#check-archived"
    allow_fork = False

    async def async_validate(self) -> None:
        """Validate the repository."""
        if self.repository.data.archived:
            raise ValidationException("The repository is archived")
