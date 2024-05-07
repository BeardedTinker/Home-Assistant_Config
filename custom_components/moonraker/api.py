"""moonraker Client."""

from moonraker_api import MoonrakerClient, MoonrakerListener


class MoonrakerApiClient(MoonrakerListener):
    """Moonraker communication API."""

    def __init__(
        self, url, session, port: int = 7125, api_key: str = None, tls: bool = False
    ):
        """Init."""
        self.running = False
        if api_key == "":
            api_key = None
        if port is None:
            port = 7125
        self.client = MoonrakerClient(
            listener=self,
            host=url,
            port=port,
            session=session,
            api_key=api_key,
            ssl=tls,
        )

    async def start(self) -> None:
        """Start the websocket connection."""
        self.running = True
        return await self.client.connect()

    async def stop(self) -> None:
        """Stop the websocket connection."""
        self.running = False
        await self.client.disconnect()
