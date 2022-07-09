"""Register info websocket commands."""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from custom_components.hacs.utils import regex

from ..const import DOMAIN
from ..enums import HacsDispatchEvent

if TYPE_CHECKING:
    from ..base import HacsBase


@websocket_api.websocket_command(
    {
        vol.Required("type"): "hacs/repositories/list",
        vol.Optional("categories"): [str],
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def hacs_repositories_list(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
):
    """List repositories."""
    hacs: HacsBase = hass.data.get(DOMAIN)
    connection.send_message(
        websocket_api.result_message(
            msg["id"],
            [
                {
                    "authors": repo.data.authors,
                    "available_version": repo.display_available_version,
                    "installed_version": repo.display_installed_version,
                    "config_flow": repo.data.config_flow,
                    "can_download": repo.can_download,
                    "category": repo.data.category,
                    "country": repo.repository_manifest.country,
                    "custom": not hacs.repositories.is_default(str(repo.data.id)),
                    "description": repo.data.description,
                    "domain": repo.data.domain,
                    "downloads": repo.data.downloads,
                    "file_name": repo.data.file_name,
                    "full_name": repo.data.full_name,
                    "hide": repo.data.hide,
                    "homeassistant": repo.repository_manifest.homeassistant,
                    "id": repo.data.id,
                    "installed": repo.data.installed,
                    "last_updated": repo.data.last_updated,
                    "local_path": repo.content.path.local,
                    "name": repo.display_name,
                    "new": repo.data.new,
                    "pending_upgrade": repo.pending_update,
                    "stars": repo.data.stargazers_count,
                    "state": repo.state,
                    "status": repo.display_status,
                    "topics": repo.data.topics,
                }
                for repo in hacs.repositories.list_all
                if repo.data.category in (msg.get("categories") or hacs.common.categories)
                and not repo.ignored_by_country_configuration
            ],
        )
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "hacs/repositories/clear_new",
        vol.Optional("categories"): cv.ensure_list,
        vol.Optional("repository"): cv.string,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def hacs_repositories_clear_new(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Clear new repositories for spesific categories."""
    hacs: HacsBase = hass.data.get(DOMAIN)

    if repo := msg.get("repository"):
        repository = hacs.repositories.get_by_id(repo)
        repository.data.new = False

    else:
        for repo in hacs.repositories.list_all:
            if repo.data.new and repo.data.category in msg.get("categories", []):
                hacs.log.debug(
                    "Clearing new flag from '%s'",
                    repo.data.full_name,
                )
                repo.data.new = False
    hacs.async_dispatch(HacsDispatchEvent.REPOSITORY, {})
    await hacs.data.async_write()
    connection.send_message(websocket_api.result_message(msg["id"]))


@websocket_api.websocket_command(
    {
        vol.Required("type"): "hacs/repositories/removed",
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def hacs_repositories_removed(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
):
    """Get information about removed repositories."""
    hacs: HacsBase = hass.data.get(DOMAIN)
    content = []
    for repo in hacs.repositories.list_removed:
        if repo.repository not in hacs.common.ignored_repositories:
            content.append(repo.to_json())
    connection.send_message(websocket_api.result_message(msg["id"], content))


@websocket_api.websocket_command(
    {
        vol.Required("type"): "hacs/repositories/add",
        vol.Required("repository"): cv.string,
        vol.Required("category"): vol.Lower,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def hacs_repositories_add(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
):
    """Add custom repositoriy."""
    hacs: HacsBase = hass.data.get(DOMAIN)
    repository = regex.extract_repository_from_url(msg["repository"])
    category = msg["category"]

    if repository is None:
        return

    if repository in hacs.common.skip:
        hacs.common.skip.remove(repository)

    if renamed := hacs.common.renamed_repositories.get(repository):
        repository = renamed

    if not hacs.repositories.get_by_full_name(repository):
        try:
            await hacs.async_register_repository(
                repository_full_name=repository,
                category=category,
            )

        except BaseException as exception:  # lgtm [py/catch-base-exception] pylint: disable=broad-except
            hacs.async_dispatch(
                HacsDispatchEvent.ERROR,
                {
                    "action": "add_repository",
                    "exception": str(sys.exc_info()[0].__name__),
                    "message": str(exception),
                },
            )

    else:

        hacs.async_dispatch(
            HacsDispatchEvent.ERROR,
            {
                "action": "add_repository",
                "message": f"Repository '{repository}' exists in the store.",
            },
        )

    connection.send_message(websocket_api.result_message(msg["id"], {}))


@websocket_api.websocket_command(
    {
        vol.Required("type"): "hacs/repositories/remove",
        vol.Required("repository"): cv.string,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def hacs_repositories_remove(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
):
    """Remove custom repositoriy."""
    hacs: HacsBase = hass.data.get(DOMAIN)
    hacs.log.warning(connection.context)
    hacs.log.warning(msg)
    repository = hacs.repositories.get_by_id(msg["repository"])

    repository.remove()
    await hacs.data.async_write()

    connection.send_message(websocket_api.result_message(msg["id"], {}))
