"""Browser fetch adapter for the existing content validation and quota owner."""

from __future__ import annotations

import asyncio
import importlib
import json
import time
from collections import deque
from typing import Any

from ...application.social_candidates import JOKE_METADATA_SECONDS, JokeCatalog
from ...application.social_content import (
    SocialCategory,
    SocialContentRejectionError,
    SocialProvider,
    default_provider,
    prepare_social_content,
)
from ...application.social_fetch import SocialFetchRequest, SocialFetchResult
from ..social_api import MAX_RESPONSE_BYTES, social_endpoint


class BrowserSocialWorker:
    def __init__(self) -> None:
        self._results: deque[SocialFetchResult] = deque()
        self._tasks: set[asyncio.Future[None]] = set()
        self._closed = False

    def start(
        self, category: SocialCategory, token: object,
        provider: SocialProvider | None = None, *,
        request: SocialFetchRequest | None = None,
    ) -> None:
        if self._closed:
            return
        task = asyncio.ensure_future(self._fetch(category, token, provider, request))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _fetch(
        self, category: SocialCategory, token: object,
        provider: SocialProvider | None, request: SocialFetchRequest | None,
    ) -> None:
        selected = provider or default_provider(category)
        try:
            fetch = importlib.import_module("pyodide.http").pyfetch
            url = "https://v2.jokeapi.dev/info" if request and request.metadata else social_endpoint(
                category, selected, request=request,
            )
            response = await asyncio.wait_for(fetch(
                url, redirect="error", credentials="omit", headers={"Accept": "application/json"},
            ), 8)
            if response.status == 429:
                self._results.append(SocialFetchResult(token, category, failure="rate",
                                                        retry_at=time.time() + 60))
                return
            if not response.ok:
                self._results.append(SocialFetchResult(
                    token, category,
                    failure="empty" if response.status == 400 else "access"
                    if response.status in (401, 403, 404, 410) else "temporary",
                    retry_at=time.time() + 60,
                ))
                return
            body = await response.bytes()
            if len(body) > MAX_RESPONSE_BYTES:
                raise ValueError("Oversized social response")
            payload: Any = json.loads(body)
            if request and request.metadata:
                bounds = payload["jokes"]["idRange"]["de"]
                catalog = JokeCatalog(bounds[0], bounds[1], time.time() + JOKE_METADATA_SECONDS)
                self._results.append(SocialFetchResult(token, category, catalog=catalog))
                return
            if selected == SocialProvider.WITZAPI:
                if not isinstance(payload, list) or len(payload) != 1:
                    raise ValueError("Unexpected joke envelope")
                payload = payload[0]
            if request and request.id_range:
                identity = payload.get("id")
                if type(identity) is not int or not request.id_range[0] <= identity <= request.id_range[1]:
                    raise ValueError("Unrequested joke identity")
            try:
                content = prepare_social_content(category, payload, provider=selected)
            except SocialContentRejectionError as error:
                self._results.append(SocialFetchResult(
                    token, category, failure="rejected", reason=error.reason,
                    rejected_id=payload.get("id") if isinstance(payload, dict) else None,
                ))
                return
            self._results.append(SocialFetchResult(token, category, content))
        except asyncio.CancelledError:
            return
        except (ImportError, ValueError, KeyError, TypeError, OSError, TimeoutError):
            self._results.append(SocialFetchResult(token, category, failure="temporary",
                                                    retry_at=time.time() + 60))

    def poll(self) -> SocialFetchResult | None:
        return self._results.popleft() if self._results else None

    def close(self) -> None:
        self._closed = True
        for task in self._tasks:
            task.cancel()
        self._results.clear()
