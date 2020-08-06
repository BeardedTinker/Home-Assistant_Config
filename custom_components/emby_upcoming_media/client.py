"""Client."""
import datetime
import requests
import logging

_LOGGER = logging.getLogger(__name__)


class EmbyClient:
    """Client class"""

    def __init__(self, host, api_key, ssl, port, max_items, user_id):
        """Init."""
        self.data = {}
        self.host = host
        self.ssl = "s" if ssl else ""
        self.port = port
        self.api_key = api_key
        self.user_id = user_id
        self.max_items = max_items

    def get_view_categories(self):
        """This will pull the list of all View Categories on Emby"""
        try:
            url = "http{0}://{1}:{2}/Users/{3}/Views".format(
                self.ssl, self.host, self.port, self.user_id
            )
            api = requests.get(url, timeout=10)
        except OSError:
            _LOGGER.warning("Host %s is not available", self.host)
            self._state = "%s cannot be reached" % self.host
            return

        if api.status_code == 200:
            self.data["ViewCategories"] = api.json()["Items"]

        else:
            _LOGGER.info("Could not reach url %s", url)
            self._state = "%s cannot be reached" % self.host

        return self.data["ViewCategories"]

    def get_data(self, categoryId):
        try:
            url = "http{0}://{1}:{2}/Users/{3}/Items/Latest?Limit={4}&Fields=CommunityRating,Studios,PremiereDate,Genres&ParentId={5}&api_key={6}&GroupItems=false".format(
                self.ssl,
                self.host,
                self.port,
                self.user_id,
                self.max_items,
                categoryId,
                self.api_key,
            )
            _LOGGER.info("Making API call on URL %s", url)
            api = requests.get(url, timeout=10)
        except OSError:
            _LOGGER.warning("Host %s is not available", self.host)
            self._state = "%s cannot be reached" % self.host
            return

        if api.status_code == 200:
            self._state = "Online"
            self.data[categoryId] = api.json()[: self.max_items]

        else:
            _LOGGER.info("Could not reach url %s", url)
            self._state = "%s cannot be reached" % self.host
            return

        return self.data[categoryId]

    def get_image_url(self, itemId, imageType):
        url = "http{0}://{1}:{2}/Items/{3}/Images/{4}?maxHeight=360&maxWidth=640&quality=90".format(
            self.ssl, self.host, self.port, itemId, imageType
        )
        return url
