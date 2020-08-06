"""Initialize the HACS base."""
# pylint: disable=unused-argument, bad-continuation
import json
import uuid
from datetime import timedelta

from queueman import QueueManager
from aiogithubapi import AIOGitHubAPIException
from homeassistant.helpers.event import async_track_time_interval

from custom_components.hacs.helpers import HacsHelpers
from custom_components.hacs.helpers.functions.get_list_from_default import (
    async_get_list_from_default,
)
from custom_components.hacs.helpers.functions.logger import getLogger
from custom_components.hacs.helpers.functions.register_repository import (
    register_repository,
)
from custom_components.hacs.helpers.functions.remaining_github_calls import (
    get_fetch_updates_for,
)
from custom_components.hacs.helpers.functions.store import (
    async_load_from_store,
    async_save_to_store,
)
from custom_components.hacs.operational.setup_actions.categories import (
    async_setup_extra_stores,
)
from custom_components.hacs.share import (
    get_factory,
    get_queue,
    get_removed,
    is_removed,
    list_removed_repositories,
)


class HacsStatus:
    """HacsStatus."""

    startup = True
    new = False
    background_task = False
    reloading_data = False
    upgrading_all = False


class HacsFrontend:
    """HacsFrontend."""

    version_running = None
    version_available = None
    version_expected = None
    update_pending = False


class HacsCommon:
    """Common for HACS."""

    categories = []
    default = []
    installed = []
    skip = []


class System:
    """System info."""

    status = HacsStatus()
    config_path = None
    ha_version = None
    disabled = False
    running = False
    lovelace_mode = "storage"


class Hacs(HacsHelpers):
    """The base class of HACS, nested throughout the project."""

    token = f"{str(uuid.uuid4())}-{str(uuid.uuid4())}"
    action = False
    hacsweb = f"/hacsweb/{token}"
    hacsapi = f"/hacsapi/{token}"
    repositories = []
    frontend = HacsFrontend()
    repo = None
    data_repo = None
    data = None
    configuration = None
    logger = getLogger()
    github = None
    hass = None
    version = None
    session = None
    factory = get_factory()
    queue = get_queue()
    system = System()
    recuring_tasks = []

    common = HacsCommon()

    def get_by_id(self, repository_id):
        """Get repository by ID."""
        try:
            for repository in self.repositories:
                if str(repository.data.id) == str(repository_id):
                    return repository
        except (Exception, BaseException):  # pylint: disable=broad-except
            pass
        return None

    def get_by_name(self, repository_full_name):
        """Get repository by full_name."""
        try:
            repository_full_name_lower = repository_full_name.lower()
            for repository in self.repositories:
                if repository.data.full_name_lower == repository_full_name_lower:
                    return repository
        except (Exception, BaseException):  # pylint: disable=broad-except
            pass
        return None

    def is_known(self, repository_id):
        """Return a bool if the repository is known."""
        return str(repository_id) in [str(x.data.id) for x in self.repositories]

    @property
    def sorted_by_name(self):
        """Return a sorted(by name) list of repository objects."""
        return sorted(self.repositories, key=lambda x: x.display_name)

    @property
    def sorted_by_repository_name(self):
        """Return a sorted(by repository_name) list of repository objects."""
        return sorted(self.repositories, key=lambda x: x.data.full_name)

    async def register_repository(self, full_name, category, check=True):
        """Register a repository."""
        await register_repository(full_name, category, check=True)

    async def startup_tasks(self):
        """Tasks that are started after startup."""
        self.system.status.background_task = True
        await async_setup_extra_stores()
        self.hass.bus.async_fire("hacs/status", {})

        await self.handle_critical_repositories_startup()
        await self.handle_critical_repositories()
        await self.async_load_default_repositories()
        await self.clear_out_removed_repositories()

        self.recuring_tasks.append(
            async_track_time_interval(
                self.hass, self.recurring_tasks_installed, timedelta(minutes=30)
            )
        )
        self.recuring_tasks.append(
            async_track_time_interval(
                self.hass, self.recurring_tasks_all, timedelta(minutes=800)
            )
        )
        self.recuring_tasks.append(
            async_track_time_interval(
                self.hass, self.prosess_queue, timedelta(minutes=10)
            )
        )

        self.hass.bus.async_fire("hacs/reload", {"force": True})
        await self.recurring_tasks_installed()

        await self.prosess_queue()

        self.system.status.startup = False
        self.system.status.background_task = False
        self.hass.bus.async_fire("hacs/status", {})
        await self.data.async_write()

    async def handle_critical_repositories_startup(self):
        """Handled critical repositories during startup."""
        alert = False
        critical = await async_load_from_store(self.hass, "critical")
        if not critical:
            return
        for repo in critical:
            if not repo["acknowledged"]:
                alert = True
        if alert:
            self.logger.critical("URGENT!: Check the HACS panel!")
            self.hass.components.persistent_notification.create(
                title="URGENT!", message="**Check the HACS panel!**"
            )

    async def handle_critical_repositories(self):
        """Handled critical repositories during runtime."""
        # Get critical repositories
        critical_queue = QueueManager()
        instored = []
        critical = []
        was_installed = False

        try:
            critical = await self.data_repo.get_contents("critical")
            critical = json.loads(critical.content)
        except AIOGitHubAPIException:
            pass

        if not critical:
            self.logger.debug("No critical repositories")
            return

        stored_critical = await async_load_from_store(self.hass, "critical")

        for stored in stored_critical or []:
            instored.append(stored["repository"])

        stored_critical = []

        for repository in critical:
            removed_repo = get_removed(repository["repository"])
            removed_repo.removal_type = "critical"
            repo = self.get_by_name(repository["repository"])

            stored = {
                "repository": repository["repository"],
                "reason": repository["reason"],
                "link": repository["link"],
                "acknowledged": True,
            }
            if repository["repository"] not in instored:
                if repo is not None and repo.installed:
                    self.logger.critical(
                        f"Removing repository {repository['repository']}, it is marked as critical"
                    )
                    was_installed = True
                    stored["acknowledged"] = False
                    # Remove from HACS
                    critical_queue.add(repository.uninstall())
                    repo.remove()

            stored_critical.append(stored)
            removed_repo.update_data(stored)

        # Uninstall
        await critical_queue.execute()

        # Save to FS
        await async_save_to_store(self.hass, "critical", stored_critical)

        # Restart HASS
        if was_installed:
            self.logger.critical("Resarting Home Assistant")
            self.hass.async_create_task(self.hass.async_stop(100))

    async def prosess_queue(self, notarealarg=None):
        """Recurring tasks for installed repositories."""
        if not self.queue.has_pending_tasks:
            self.logger.debug("Nothing in the queue")
            return
        if self.queue.running:
            self.logger.debug("Queue is already running")
            return

        can_update = await get_fetch_updates_for(self.github)
        if can_update == 0:
            self.logger.info(
                "HACS is ratelimited, repository updates will resume later."
            )
        else:
            self.system.status.background_task = True
            self.hass.bus.async_fire("hacs/status", {})
            await self.queue.execute(can_update)
            self.system.status.background_task = False
            self.hass.bus.async_fire("hacs/status", {})

    async def recurring_tasks_installed(self, notarealarg=None):
        """Recurring tasks for installed repositories."""
        self.logger.debug(
            "Starting recurring background task for installed repositories"
        )
        self.system.status.background_task = True
        self.hass.bus.async_fire("hacs/status", {})

        for repository in self.repositories:
            if (
                repository.data.installed
                and repository.data.category in self.common.categories
            ):
                self.queue.add(self.factory.safe_update(repository))

        await self.handle_critical_repositories()
        self.system.status.background_task = False
        self.hass.bus.async_fire("hacs/status", {})
        await self.data.async_write()
        self.logger.debug("Recurring background task for installed repositories done")

    async def recurring_tasks_all(self, notarealarg=None):
        """Recurring tasks for all repositories."""
        self.logger.debug("Starting recurring background task for all repositories")
        await async_setup_extra_stores()
        self.system.status.background_task = True
        self.hass.bus.async_fire("hacs/status", {})

        for repository in self.repositories:
            if repository.data.category in self.common.categories:
                self.queue.add(self.factory.safe_common_update(repository))

        await self.async_load_default_repositories()
        await self.clear_out_removed_repositories()
        self.system.status.background_task = False
        await self.data.async_write()
        self.hass.bus.async_fire("hacs/status", {})
        self.hass.bus.async_fire("hacs/repository", {"action": "reload"})
        self.logger.debug("Recurring background task for all repositories done")

    async def clear_out_removed_repositories(self):
        """Clear out blaclisted repositories."""
        need_to_save = False
        for removed in list_removed_repositories():
            repository = self.get_by_name(removed.repository)
            if repository is not None:
                if repository.data.installed and removed.removal_type != "critical":
                    self.logger.warning(
                        f"You have {repository.data.full_name} installed with HACS "
                        + f"this repository has been removed, please consider removing it. "
                        + f"Removal reason ({removed.removal_type})"
                    )
                else:
                    need_to_save = True
                    repository.remove()

        if need_to_save:
            await self.data.async_write()

    async def async_load_default_repositories(self):
        """Load known repositories."""
        self.logger.info("Loading known repositories")

        for item in await async_get_list_from_default("removed"):
            removed = get_removed(item["repository"])
            removed.reason = item.get("reason")
            removed.link = item.get("link")
            removed.removal_type = item.get("removal_type")

        for category in self.common.categories or []:
            self.queue.add(self.async_get_category_repositories(category))

        await self.queue.execute()

    async def async_get_category_repositories(self, category):
        repositories = await async_get_list_from_default(category)
        for repo in repositories:
            if is_removed(repo):
                continue
            repository = self.get_by_name(repo)
            if repository is not None:
                if str(repository.data.id) not in self.common.default:
                    self.common.default.append(str(repository.data.id))
                else:
                    continue
                continue
            self.queue.add(self.factory.safe_register(repo, category))
