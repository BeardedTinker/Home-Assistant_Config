"""Initialize repositories."""
from __future__ import annotations

from ..enums import HacsCategory
from .appdaemon import HacsAppdaemonRepository
from .base import HacsRepository
from .integration import HacsIntegrationRepository
from .netdaemon import HacsNetdaemonRepository
from .plugin import HacsPluginRepository
from .python_script import HacsPythonScriptRepository
from .template import HacsTemplateRepository
from .theme import HacsThemeRepository

RERPOSITORY_CLASSES: dict[HacsCategory, HacsRepository] = {
    HacsCategory.THEME: HacsThemeRepository,
    HacsCategory.INTEGRATION: HacsIntegrationRepository,
    HacsCategory.PYTHON_SCRIPT: HacsPythonScriptRepository,
    HacsCategory.APPDAEMON: HacsAppdaemonRepository,
    HacsCategory.NETDAEMON: HacsNetdaemonRepository,
    HacsCategory.PLUGIN: HacsPluginRepository,
    HacsCategory.TEMPLATE: HacsTemplateRepository,
}
