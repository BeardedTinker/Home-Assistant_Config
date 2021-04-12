"""Mikrotik API for Mikrotik Router."""

import logging
import ssl
from time import time
from threading import Lock

from voluptuous import Optional

from .const import (
    DEFAULT_LOGIN_METHOD,
    DEFAULT_ENCODING,
)

import librouteros
from socket import error as socket_error, timeout as socket_timeout

_LOGGER = logging.getLogger(__name__)


# ---------------------------
#   MikrotikAPI
# ---------------------------
class MikrotikAPI:
    """Handle all communication with the Mikrotik API."""

    def __init__(
        self,
        host,
        username,
        password,
        port=0,
        use_ssl=True,
        login_method=DEFAULT_LOGIN_METHOD,
        encoding=DEFAULT_ENCODING,
    ):
        """Initialize the Mikrotik Client."""
        self._host = host
        self._use_ssl = use_ssl
        self._port = port
        self._username = username
        self._password = password
        self._login_method = login_method
        self._encoding = encoding
        self._ssl_wrapper = None
        self.lock = Lock()

        self._connection = None
        self._connected = False
        self._reconnected = False
        self._connection_epoch = 0
        self._connection_retry_sec = 58
        self.error = None
        self.connection_error_reported = False
        self.accounting_last_run = None

        # Default ports
        if not self._port:
            self._port = 8729 if self._use_ssl else 8728

    # ---------------------------
    #   has_reconnected
    # ---------------------------
    def has_reconnected(self) -> bool:
        """Check if mikrotik has reconnected"""
        if self._reconnected:
            self._reconnected = False
            return True

        return False

    # ---------------------------
    #   connection_check
    # ---------------------------
    def connection_check(self) -> bool:
        """Check if mikrotik is connected"""
        if not self._connected or not self._connection:
            if self._connection_epoch > time() - self._connection_retry_sec:
                return False

            if not self.connect():
                return False

        return True

    # ---------------------------
    #   disconnect
    # ---------------------------
    def disconnect(self, location="unknown", error=None):
        """Disconnect from Mikrotik device."""
        if not error:
            error = "unknown"

        if not self.connection_error_reported:
            if location == "unknown":
                _LOGGER.error("Mikrotik %s connection closed", self._host)
            else:
                _LOGGER.error(
                    "Mikrotik %s error while %s : %s", self._host, location, error
                )

            self.connection_error_reported = True

        self._reconnected = False
        self._connected = False
        self._connection = None
        self._connection_epoch = 0

    # ---------------------------
    #   connect
    # ---------------------------
    def connect(self) -> bool:
        """Connect to Mikrotik device."""
        self.error = ""
        self._connected = False
        self._connection_epoch = time()

        kwargs = {
            "encoding": self._encoding,
            "login_methods": self._login_method,
            "port": self._port,
        }

        if self._use_ssl:
            if self._ssl_wrapper is None:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                self._ssl_wrapper = ssl_context.wrap_socket
            kwargs["ssl_wrapper"] = self._ssl_wrapper
        self.lock.acquire()
        try:
            self._connection = librouteros.connect(
                self._host, self._username, self._password, **kwargs
            )
        except (
            librouteros.exceptions.TrapError,
            librouteros.exceptions.MultiTrapError,
            librouteros.exceptions.ConnectionClosed,
            librouteros.exceptions.ProtocolError,
            librouteros.exceptions.FatalError,
            socket_timeout,
            socket_error,
            ssl.SSLError,
            BrokenPipeError,
            OSError,
        ) as api_error:
            if not self.connection_error_reported:
                _LOGGER.error(
                    "Mikrotik %s error while connecting: %s", self._host, api_error
                )
                self.connection_error_reported = True

            self.error_to_strings("%s" % api_error)
            self._connection = None
            self.lock.release()
            return False
        except:
            if not self.connection_error_reported:
                _LOGGER.error(
                    "Mikrotik %s error while connecting: %s", self._host, "Unknown"
                )
                self.connection_error_reported = True

            self._connection = None
            self.lock.release()
            return False
        else:
            if self.connection_error_reported:
                _LOGGER.warning("Mikrotik Reconnected to %s", self._host)
                self.connection_error_reported = False
            else:
                _LOGGER.debug("Mikrotik Connected to %s", self._host)

            self._connected = True
            self._reconnected = True
            self.lock.release()

        return self._connected

    # ---------------------------
    #   error_to_strings
    # ---------------------------
    def error_to_strings(self, error):
        """Translate error output to error string."""
        self.error = "cannot_connect"
        if error == "invalid user name or password (6)":
            self.error = "wrong_login"

        if "ALERT_HANDSHAKE_FAILURE" in error:
            self.error = "ssl_handshake_failure"

    # ---------------------------
    #   connected
    # ---------------------------
    def connected(self) -> bool:
        """Return connected boolean."""
        return self._connected

    # ---------------------------
    #   path
    # ---------------------------
    def path(self, path, return_list=True) -> Optional(list):
        """Retrieve data from Mikrotik API."""
        """Returns generator object, unless return_list passed as True"""

        if not self.connection_check():
            return None

        self.lock.acquire()
        try:
            _LOGGER.debug("API query: %s", path)
            response = self._connection.path(path)
        except librouteros.exceptions.ConnectionClosed:
            self.disconnect()
            self.lock.release()
            return None
        except (
            librouteros.exceptions.TrapError,
            librouteros.exceptions.MultiTrapError,
            librouteros.exceptions.ProtocolError,
            librouteros.exceptions.FatalError,
            socket_timeout,
            socket_error,
            ssl.SSLError,
            BrokenPipeError,
            OSError,
            ValueError,
        ) as api_error:
            self.disconnect("path", api_error)
            self.lock.release()
            return None
        except:
            self.disconnect("path")
            self.lock.release()
            return None

        if return_list:
            try:
                response = list(response)
            except librouteros.exceptions.ConnectionClosed as api_error:
                self.disconnect("building list for path", api_error)
                self.lock.release()
                return None
            except:
                self.disconnect("building list for path")
                self.lock.release()
                return None

        self.lock.release()
        return response if response else None

    # ---------------------------
    #   update
    # ---------------------------
    def update(self, path, param, value, mod_param, mod_value) -> bool:
        """Modify a parameter"""
        entry_found = None

        if not self.connection_check():
            return False

        response = self.path(path, return_list=False)
        if response is None:
            return False

        for tmp in response:
            if param not in tmp:
                continue

            if tmp[param] != value:
                continue

            entry_found = tmp[".id"]

        if not entry_found:
            _LOGGER.error(
                "Mikrotik %s Update parameter %s with value %s not found",
                self._host,
                param,
                value,
            )
            return True

        params = {".id": entry_found, mod_param: mod_value}
        self.lock.acquire()
        try:
            response.update(**params)
        except librouteros.exceptions.ConnectionClosed:
            self.disconnect()
            self.lock.release()
            return False
        except (
            librouteros.exceptions.TrapError,
            librouteros.exceptions.MultiTrapError,
            librouteros.exceptions.ProtocolError,
            librouteros.exceptions.FatalError,
            socket_timeout,
            socket_error,
            ssl.SSLError,
            BrokenPipeError,
            OSError,
            ValueError,
        ) as api_error:
            self.disconnect("update", api_error)
            self.lock.release()
            return False
        except:
            self.disconnect("update")
            self.lock.release()
            return False

        self.lock.release()
        return True

    # ---------------------------
    #   execute
    # ---------------------------
    def execute(self, path, command, param, value) -> bool:
        """Execute a command"""
        entry_found = None

        if not self.connection_check():
            return False

        response = self.path(path, return_list=False)
        if response is None:
            return False

        for tmp in response:
            if param not in tmp:
                continue

            if tmp[param] != value:
                continue

            entry_found = tmp[".id"]

        if not entry_found:
            _LOGGER.error(
                "Mikrotik %s Execute %s parameter %s with value %s not found",
                self._host,
                command,
                param,
                value,
            )
            return True

        params = {".id": entry_found}
        self.lock.acquire()
        try:
            tuple(response(command, **params))
        except librouteros.exceptions.ConnectionClosed:
            self.disconnect()
            self.lock.release()
            return False
        except (
            librouteros.exceptions.TrapError,
            librouteros.exceptions.MultiTrapError,
            librouteros.exceptions.ProtocolError,
            librouteros.exceptions.FatalError,
            socket_timeout,
            socket_error,
            ssl.SSLError,
            BrokenPipeError,
            OSError,
            ValueError,
        ) as api_error:
            self.disconnect("execute", api_error)
            self.lock.release()
            return False
        except:
            self.disconnect("execute")
            self.lock.release()
            return False

        self.lock.release()
        return True

    # ---------------------------
    #   run_script
    # ---------------------------
    def run_script(self, name) -> bool:
        """Run script"""
        entry_found = None
        if not self.connection_check():
            return False

        response = self.path("/system/script", return_list=False)
        if response is None:
            return False

        self.lock.acquire()
        for tmp in response:
            if "name" not in tmp:
                continue

            if tmp["name"] != name:
                continue

            entry_found = tmp[".id"]

        if not entry_found:
            _LOGGER.error("Mikrotik %s Script %s not found", self._host, name)
            return True

        try:
            run = response("run", **{".id": entry_found})
            tuple(run)
        except librouteros.exceptions.ConnectionClosed:
            self.disconnect()
            self.lock.release()
            return False
        except (
            librouteros.exceptions.TrapError,
            librouteros.exceptions.MultiTrapError,
            librouteros.exceptions.ProtocolError,
            librouteros.exceptions.FatalError,
            socket_timeout,
            socket_error,
            ssl.SSLError,
            BrokenPipeError,
            OSError,
            ValueError,
        ) as api_error:
            self.disconnect("run_script", api_error)
            self.lock.release()
            return False
        except:
            self.disconnect("run_script")
            self.lock.release()
            return False

        self.lock.release()
        return True

    # ---------------------------
    #   get_traffic
    # ---------------------------
    def get_traffic(self, interfaces) -> Optional(list):
        """Get traffic stats"""
        if not self.connection_check():
            return None

        response = self.path("/interface", return_list=False)
        if response is None:
            return None

        args = {"interface": interfaces, "once": True}
        self.lock.acquire()
        try:
            _LOGGER.debug("API query: %s", "/interface/monitor-traffic")
            traffic = response("monitor-traffic", **args)
        except librouteros.exceptions.ConnectionClosed:
            self.disconnect()
            self.lock.release()
            return None
        except (
            librouteros.exceptions.TrapError,
            librouteros.exceptions.MultiTrapError,
            librouteros.exceptions.ProtocolError,
            librouteros.exceptions.FatalError,
            ssl.SSLError,
            socket_timeout,
            socket_error,
            BrokenPipeError,
            OSError,
            ValueError,
        ) as api_error:
            self.disconnect("get_traffic", api_error)
            self.lock.release()
            return None
        except:
            self.disconnect("get_traffic")
            self.lock.release()
            return None

        try:
            traffic = list(traffic)
        except librouteros.exceptions.ConnectionClosed as api_error:
            self.disconnect("get_traffic", api_error)
            self.lock.release()
            return None
        except:
            self.disconnect("get_traffic")
            self.lock.release()
            return None

        self.lock.release()
        return traffic if traffic else None

    # ---------------------------
    #   get_sfp
    # ---------------------------
    def get_sfp(self, interfaces) -> Optional(list):
        """Get sfp info"""
        if not self.connection_check():
            return None

        response = self.path("/interface/ethernet", return_list=False)
        if response is None:
            return None

        args = {".id": interfaces, "once": True}
        self.lock.acquire()
        try:
            _LOGGER.debug("API query: %s %s", "/interface/ethernet/monitor", interfaces)
            sfpinfo = response("monitor", **args)
        except librouteros.exceptions.ConnectionClosed:
            self.disconnect()
            self.lock.release()
            return None
        except (
            librouteros.exceptions.TrapError,
            librouteros.exceptions.MultiTrapError,
            librouteros.exceptions.ProtocolError,
            librouteros.exceptions.FatalError,
            ssl.SSLError,
            socket_timeout,
            socket_error,
            BrokenPipeError,
            OSError,
            ValueError,
        ) as api_error:
            self.disconnect("get_sfp", api_error)
            self.lock.release()
            return None
        except:
            self.disconnect("get_sfp")
            self.lock.release()
            return None

        try:
            sfpinfo = list(sfpinfo)
        except librouteros.exceptions.ConnectionClosed as api_error:
            self.disconnect("get_sfp", api_error)
            self.lock.release()
            return None
        except:
            self.disconnect("get_sfp")
            self.lock.release()
            return None

        self.lock.release()
        return sfpinfo if sfpinfo else None

    # ---------------------------
    #   arp_ping
    # ---------------------------
    def arp_ping(self, address, interface) -> bool:
        """Check arp ping response traffic stats"""
        if not self.connection_check():
            return False

        response = self.path("/ping", return_list=False)
        if response is None:
            return False

        args = {
            "arp-ping": "no",
            "interval": "100ms",
            "count": 3,
            "interface": interface,
            "address": address,
        }
        self.lock.acquire()
        try:
            # _LOGGER.debug("Ping host query: %s", args["address"])
            ping = response("/ping", **args)
        except librouteros.exceptions.ConnectionClosed:
            self.disconnect()
            self.lock.release()
            return False

        except (
            librouteros.exceptions.TrapError,
            librouteros.exceptions.MultiTrapError,
            librouteros.exceptions.ProtocolError,
            librouteros.exceptions.FatalError,
            socket_timeout,
            socket_error,
            ssl.SSLError,
            BrokenPipeError,
            OSError,
            ValueError,
        ) as api_error:
            self.disconnect("arp_ping", api_error)
            self.lock.release()
            return False
        except:
            self.disconnect("arp_ping")
            self.lock.release()
            return False

        try:
            ping = list(ping)
        except librouteros.exceptions.ConnectionClosed as api_error:
            self.disconnect("arp_ping", api_error)
            self.lock.release()
            return False
        except:
            self.disconnect("arp_ping")
            self.lock.release()
            return False

        self.lock.release()

        for tmp in ping:
            if "received" in tmp and tmp["received"] > 0:
                _LOGGER.debug("Ping host success: %s", args["address"])
                return True

        _LOGGER.debug("Ping host failure: %s", args["address"])
        return False

    @staticmethod
    def _current_milliseconds():
        return int(round(time() * 1000))

    def is_accounting_and_local_traffic_enabled(self) -> (bool, bool):
        # Returns:
        #   1st bool: Is accounting enabled
        #   2nd bool: Is account-local-traffic enabled

        if not self.connection_check():
            return False, False

        response = self.path("/ip/accounting")
        if response is None:
            return False, False

        for item in response:
            if "enabled" not in item:
                continue
            if not item["enabled"]:
                return False, False

        for item in response:
            if "account-local-traffic" not in item:
                continue
            if not item["account-local-traffic"]:
                return True, False

        return True, True

    # ---------------------------
    #   take_accounting_snapshot
    #   Returns float -> period in seconds between last and current run
    # ---------------------------
    def take_accounting_snapshot(self) -> float:
        """Get accounting data"""
        if not self.connection_check():
            return 0

        accounting = self.path("/ip/accounting", return_list=False)

        self.lock.acquire()
        try:
            # Prepare command
            take = accounting("snapshot/take")
        except librouteros.exceptions.ConnectionClosed:
            self.disconnect()
            self.lock.release()
            return 0
        except (
            librouteros.exceptions.TrapError,
            librouteros.exceptions.MultiTrapError,
            librouteros.exceptions.ProtocolError,
            librouteros.exceptions.FatalError,
            socket_timeout,
            socket_error,
            ssl.SSLError,
            BrokenPipeError,
            OSError,
            ValueError,
        ) as api_error:
            self.disconnect("accounting_snapshot", api_error)
            self.lock.release()
            return 0
        except:
            self.disconnect("accounting_snapshot")
            self.lock.release()
            return 0

        try:
            list(take)
        except librouteros.exceptions.ConnectionClosed as api_error:
            self.disconnect("accounting_snapshot", api_error)
            self.lock.release()
            return 0
        except:
            self.disconnect("accounting_snapshot")
            self.lock.release()
            return 0

        self.lock.release()

        # First request will be discarded because we cannot know when the last data was retrieved
        # prevents spikes in data
        if not self.accounting_last_run:
            self.accounting_last_run = self._current_milliseconds()
            return 0

        # Calculate time difference in seconds and return
        time_diff = self._current_milliseconds() - self.accounting_last_run
        self.accounting_last_run = self._current_milliseconds()
        return time_diff / 1000
