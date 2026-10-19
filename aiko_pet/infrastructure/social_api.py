"""Bounded HTTP reads and one daemon worker; no Tk or pet state access."""

from __future__ import annotations

import json
from queue import Empty, Queue
from threading import Thread
from urllib.request import Request, urlopen

from ..application.social_content import (
    PreparedSocialContent,
    SocialCategory,
    prepare_social_content,
)
from ..application.social_coordinator import SocialFetchResult

MAX_RESPONSE_BYTES = 16_384
REQUEST_TIMEOUT_SECONDS = 8


def social_endpoint(category: SocialCategory) -> str:
    if category == SocialCategory.FACT:
        return "https://uselessfacts.jsph.pl/api/v2/facts/random?language=de"
    return (
        "https://v2.jokeapi.dev/joke/Any?lang=de&safe-mode"
        "&blacklistFlags=nsfw,religious,political,racist,sexist,explicit"
        f"&type={category.value}"
    )


def fetch_social_content(category: SocialCategory) -> PreparedSocialContent:
    request = Request(social_endpoint(category), headers={
        "Accept": "application/json", "User-Agent": "AikoDesktopPet/1.0",
    })
    with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        body = response.read(MAX_RESPONSE_BYTES + 1)
    if len(body) > MAX_RESPONSE_BYTES:
        raise ValueError("Social response exceeds size limit")
    return prepare_social_content(category, json.loads(body.decode("utf-8")))


class HttpSocialContentWorker:
    """Only one fetch may exist, even across disable/re-enable transitions."""

    def __init__(self) -> None:
        self._results: Queue[SocialFetchResult] = Queue(maxsize=1)
        self._active = False
        self._closed = False

    def start(self, category: SocialCategory, token: object) -> None:
        if self._closed or self._active:
            raise RuntimeError("Social worker is closed or already fetching")
        self._active = True

        def fetch() -> None:
            try:
                content = fetch_social_content(category)
            except Exception:
                # Failed content is unavailable; do not expose provider error bodies.
                content = None
            self._results.put(SocialFetchResult(token, category, content))

        Thread(target=fetch, name="aiko-social-content", daemon=True).start()

    def poll(self) -> SocialFetchResult | None:
        try:
            result = self._results.get_nowait()
        except Empty:
            return None
        self._active = False
        return result

    def close(self) -> None:
        self._closed = True
