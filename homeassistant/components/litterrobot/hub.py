"""A wrapper 'hub' for the Litter-Robot API."""
from __future__ import annotations

from collections.abc import Generator, Mapping
from datetime import timedelta
import logging
from typing import Any

from pylitterbot import Account, LitterRobot
from pylitterbot.exceptions import LitterRobotException, LitterRobotLoginException

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL_SECONDS = 20


class LitterRobotHub:
    """A Litter-Robot hub wrapper class."""

    def __init__(self, hass: HomeAssistant, data: Mapping[str, Any]) -> None:
        """Initialize the Litter-Robot hub."""
        self._data = data
        self.account = Account(websession=async_get_clientsession(hass))

        async def _async_update_data() -> bool:
            """Update all device states from the Litter-Robot API."""
            await self.account.refresh_robots()
            return True

        self.coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_method=_async_update_data,
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
        )

    async def login(self, load_robots: bool = False) -> None:
        """Login to Litter-Robot."""
        try:
            await self.account.connect(
                username=self._data[CONF_USERNAME],
                password=self._data[CONF_PASSWORD],
                load_robots=load_robots,
            )
            return
        except LitterRobotLoginException as ex:
            _LOGGER.error("Invalid credentials")
            raise ex
        except LitterRobotException as ex:
            _LOGGER.error("Unable to connect to Litter-Robot API")
            raise ex

    def litter_robots(self) -> Generator[LitterRobot, Any, Any]:
        """Get Litter-Robots from the account."""
        return (
            robot for robot in self.account.robots if isinstance(robot, LitterRobot)
        )
