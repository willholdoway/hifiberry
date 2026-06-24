from __future__ import annotations

import aiohttp


class AcrClient:
    def __init__(self, session: aiohttp.ClientSession, host: str, port: int = 1080) -> None:
        self.base_url = f"http://{host}:{port}/api"

    async def _request(self, session, method: str, path: str, **kwargs):
        async with session.request(method, f"{self.base_url}{path}", **kwargs) as response:
            response.raise_for_status()
            return await response.json()

    async def version(self, session):
        return await self._request(session, "GET", "/version")

    async def now_playing(self, session):
        return await self._request(session, "GET", "/now-playing")

    async def player(self, session):
        return await self._request(session, "GET", "/player")

    async def volume_state(self, session):
        return await self._request(session, "GET", "/volume/state")

    async def command(self, session, command: str):
        return await self._request(session, "POST", f"/player/active/send/{command}")

    async def play(self, session):
        return await self.command(session, "play")

    async def pause(self, session):
        return await self.command(session, "pause")

    async def stop(self, session):
        return await self.command(session, "stop")

    async def next(self, session):
        return await self.command(session, "next")

    async def previous(self, session):
        return await self.command(session, "previous")

    async def set_volume(self, session, percent: float):
        return await self._request(
            session,
            "POST",
            "/volume/set",
            json={"percentage": float(percent)},
        )
