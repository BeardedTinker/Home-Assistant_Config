from __future__ import annotations

from ..enums import RepositoryFile
from ..repositories.base import HacsRepository
from .base import ActionValidationBase, ValidationException


async def async_setup_validator(repository: HacsRepository) -> Validator:
    """Set up this validator."""
    return Validator(repository=repository)


class Validator(ActionValidationBase):
    def validate(self):
        if RepositoryFile.HACS_JSON not in [x.filename for x in self.repository.tree]:
            raise ValidationException(f"The repository has no '{RepositoryFile.HACS_JSON}' file")
