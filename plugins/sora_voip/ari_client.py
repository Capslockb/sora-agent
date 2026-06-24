"""
Asterisk ARI Client
===================
Async HTTP/WebSocket client for Asterisk REST Interface.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import aiohttp

log = logging.getLogger("sora.voip.ari")


@dataclass
class AriEvent:
    """Normalized ARI event."""
    event_type: str
    channel: Dict[str, Any]
    args: List[str] = None
    raw: Dict[str, Any] = None


class AriClient:
    """Async Asterisk ARI client with WebSocket event stream."""

    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        app_name: str,
    ):
        self.url = url.rstrip("/")
        self.auth = aiohttp.BasicAuth(username, password)
        self.app_name = app_name
        self._session: Optional[aiohttp.ClientSession] = None
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._connected = False
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._ws_task: Optional[asyncio.Task] = None

    async def connect(self) -> None:
        """Establish HTTP session and WebSocket connection."""
        if self._connected:
            return

        self._session = aiohttp.ClientSession(auth=self.auth)

        # Connect WebSocket for events
        ws_url = f"{self.url.replace('http', 'ws')}/ari/events?app={self.app_name}&subscribeAll=true"
        self._ws = await self._session.ws_connect(ws_url)
        self._connected = True

        # Start event listener
        self._ws_task = asyncio.create_task(self._ws_listener())
        log.info("ARI connected", extra={"url": self.url, "app": self.app_name})

    async def disconnect(self) -> None:
        """Close connections."""
        self._connected = False
        if self._ws_task:
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                raise NotImplementedError("TODO")
        if self._ws:
            await self._ws.close()
        if self._session:
            await self._session.close()
        log.info("ARI disconnected")

    def is_connected(self) -> bool:
        return self._connected and self._ws and not self._ws.closed

    # ──────────────────────────────────────────
    # Event handling
    # ──────────────────────────────────────────

    def on_event(self, event_type: str, handler: Callable) -> None:
        """Register event handler."""
        self._event_handlers.setdefault(event_type, []).append(handler)

    def off_event(self, event_type: str, handler: Callable) -> None:
        """Unregister event handler."""
        if event_type in self._event_handlers:
            self._event_handlers[event_type].remove(handler)

    async def _ws_listener(self) -> None:
        """Listen for ARI WebSocket events."""
        try:
            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self._dispatch_event(msg.json())
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    log.error("ARI WebSocket error", extra={"error": self._ws.exception()})
                    break
        except asyncio.CancelledError:
            raise NotImplementedError("TODO")
        except Exception as e:
            log.error("ARI listener error", extra={"error": str(e)})
        finally:
            self._connected = False

    async def _dispatch_event(self, data: Dict[str, Any]) -> None:
        """Dispatch event to handlers."""
        event_type = data.get("type")
        if not event_type:
            return

        event = AriEvent(
            event_type=event_type,
            channel=data.get("channel", {}),
            args=data.get("args", []),
            raw=data,
        )

        for handler in self._event_handlers.get(event_type, []):
            try:
                await handler(event)
            except Exception as e:
                log.error("ARI handler error", extra={"event": event_type, "error": str(e)})

    # ──────────────────────────────────────────
    # ARI Operations
    # ──────────────────────────────────────────

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs,
    ) -> Any:
        """Make HTTP request to ARI."""
        if not self._session:
            raise RuntimeError("ARI not connected")

        url = f"{self.url}{path}"
        async with self._session.request(method, url, **kwargs) as resp:
            if resp.status >= 400:
                text = await resp.text()
                raise aiohttp.ClientResponseError(
                    request_info=resp.request_info,
                    history=resp.history,
                    status=resp.status,
                    message=text,
                )
            if resp.content_type == "application/json":
                return await resp.json()
            return await resp.text()

    async def register_app(self, app_name: str) -> None:
        """Register ARI application (no-op, app is registered via WebSocket subscription)."""
        log.info("ARI app registered via WebSocket", extra={"app": app_name})

    async def unregister_app(self, app_name: str) -> None:
        """Unregister ARI application."""
        raise NotImplementedError("TODO")

    async def list_apps(self) -> List[Dict[str, Any]]:
        """List registered ARI applications."""
        return await self._request("GET", "/ari/applications")

    async def originate(
        self,
        endpoint: str,
        app: str,
        appArgs: str = "",
        callerId: str = "Sora",
        timeout: int = 30,
        **extra,
    ) -> Optional[Dict[str, Any]]:
        """Originate a new call."""
        params = {
            "endpoint": endpoint,
            "app": app,
            "appArgs": appArgs,
            "callerId": callerId,
            "timeout": timeout,
        }
        params.update(extra)
        return await self._request("POST", "/ari/channels", params=params)

    async def answer(self, channel_id: str) -> None:
        """Answer a ringing channel."""
        await self._request("POST", f"/ari/channels/{channel_id}/answer")

    async def hangup(self, channel_id: str, reason: str = "normal") -> None:
        """Hang up a channel."""
        await self._request("DELETE", f"/ari/channels/{channel_id}", params={"reason": reason})

    async def get_channel(self, channel_id: str) -> Dict[str, Any]:
        """Get channel details."""
        return await self._request("GET", f"/ari/channels/{channel_id}")

    async def get_endpoints(self) -> List[Dict[str, Any]]:
        """Get PJSIP endpoints."""
        return await self._request("GET", "/ari/endpoints")

    async def external_media(
        self,
        channel_id: str,
        host: str,
        port: int,
        format: str = "slin48",
        direction: str = "both",
    ) -> Dict[str, Any]:
        """Start externalMedia on channel (for RTP streaming)."""
        return await self._request("POST", f"/ari/channels/{channel_id}/externalMedia", json={
            "host": host,
            "port": port,
            "format": format,
            "direction": direction,
        })

    async def snoop_channel(
        self,
        channel_id: str,
        snoop_id: str,
        host: str,
        port: int,
        format: str = "slin48",
    ) -> Dict[str, Any]:
        """Start snoopChannel on channel (alternative to externalMedia)."""
        return await self._request("POST", f"/ari/channels/{channel_id}/snoop", json={
            "snoopId": snoop_id,
            "host": host,
            "port": port,
            "format": format,
        })

    async def record(
        self,
        channel_id: str,
        name: str,
        format: str = "wav",
        mix: bool = True,
        max_duration: int = 0,
    ) -> Dict[str, Any]:
        """Start recording a channel."""
        return await self._request("POST", f"/ari/channels/{channel_id}/record", json={
            "name": name,
            "format": format,
            "mix": mix,
            "maxDurationSeconds": max_duration,
        })

    async def stop_recording(self, channel_id: str, name: str) -> Dict[str, Any]:
        """Stop recording a channel."""
        return await self._request("POST", f"/ari/channels/{channel_id}/record/{name}/stop")

    async def play_media(
        self,
        channel_id: str,
        media: str,
        lang: str = "en",
    ) -> Dict[str, Any]:
        """Play media to channel."""
        return await self._request("POST", f"/ari/channels/{channel_id}/play", json={
            "media": media,
            "lang": lang,
        })


async def create_ari_client(
    url: str,
    username: str,
    password: str,
    app_name: str,
) -> AriClient:
    """Factory function to create and connect ARI client."""
    client = AriClient(url, username, password, app_name)
    await client.connect()
    return client
