from __future__ import annotations
from enum import Enum
from functools import lru_cache


class BaseStates(Enum):
    @lru_cache
    def __str__(self):
        return self.name.lower().replace("_", " ").replace("and", "&").title()


class LockStates(BaseStates):
    UNCALIBRATED = 0
    LOCKED = 1
    UNLOCKING = 2
    UNLOCKED = 3
    LOCKING = 4
    UNLATCHED = 5
    LOCK_N_GO = 6
    UNLATCHING = 7
    MOTOR_BLOCKED = 254
    UNDEFINED = 255


class DoorSensorStates(BaseStates):
    UNAVAILABLE = 0
    DEACTIVATED = 1
    DOOR_CLOSED = 2
    DOOR_OPENED = 3
    DOOR_UNKNOWN = 4
    CALIBRATING = 5
    UNCALIBRATED = 16
    REMOVED = 240
    UNKNOWN = 255


class DoorSecurityStates(BaseStates):
    CLOSED_AND_LOCKED = 1
    CLOSED_AND_UNLOCKED = 2
    OPEN = 3


class LockModes(BaseStates):
    DOOR_MODE = 2
    CONTINUOUS_MODE = 3
