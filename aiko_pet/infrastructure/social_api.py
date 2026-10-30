"""Reviewed free endpoints, bounded HTTP and one data-only daemon worker."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import timezone
from email.utils import parsedate_to_datetime
from queue import Empty, Queue
from threading import Thread
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from ..application.social_candidates import (
    JOKE_METADATA_SECONDS,
    MAX_JOKE_ID,
    JokeCatalog,
    RejectionReason,
)
from ..application.social_content import (
    PreparedSocialContent,
    SocialCategory,
    SocialContentRejectionError,
    SocialProvider,
    default_provider,
    prepare_social_content,
)
from ..application.social_fetch import (
    FetchFailure,
    SocialFetchRequest,
    SocialFetchResult,
)

MAX_RESPONSE_BYTES = 16_384
REQUEST_TIMEOUT_SECONDS = 8


class _NoRedirects(HTTPRedirectHandler):
    def redirect_request(
        self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> None:
        # Access changes require review, never a request to another endpoint.
        return None


urlopen = build_opener(_NoRedirects()).open


class SocialFetchError(ValueError):
    def __init__(
        self, failure: FetchFailure, retry_at: float | None = None, *,
        rejected_id: int | None = None, reason: RejectionReason | None = None,
    ) -> None:
        super().__init__("Social provider temporarily unavailable")
        self.failure: FetchFailure = failure
        self.retry_at: float | None = retry_at
        self.rejected_id = rejected_id
        self.reason: RejectionReason | None = reason


@dataclass(frozen=True, slots=True)
class SocialHttpResponse:
    content: PreparedSocialContent
    retry_at: float | None = None


def social_endpoint(
    category: SocialCategory,
    provider: SocialProvider | None = None,
    *, request: SocialFetchRequest | None = None,
) -> str:
    if (
        not isinstance(category, SocialCategory)
        or provider is not None
        and not isinstance(provider, SocialProvider)
    ):
        raise ValueError("Unknown social endpoint")
    provider = provider or default_provider(category)
    if request is not None and (request.metadata or request.id_range is not None):
        if (provider != SocialProvider.JOKEAPI
                or category not in (SocialCategory.SINGLE, SocialCategory.TWO_PARTS)):
            raise ValueError("Only JokeAPI supports candidate requests")
        if request.metadata:
            if request.id_range is not None:
                raise ValueError("Metadata request cannot select content")
            return "https://v2.jokeapi.dev/info"
        assert request.id_range is not None
        lower, upper = request.id_range
        if (type(lower) is not int or type(upper) is not int
                or not 0 <= lower <= upper <= MAX_JOKE_ID):
            raise ValueError("Invalid JokeAPI ID range")
    if category == SocialCategory.HOROSCOPE:
        raise ValueError("No horoscope HTTP endpoint exists")
    if provider == SocialProvider.QUOTATIONS and category == SocialCategory.SINGLE:
        return "https://api.zitat-service.de/v1/quote?language=de"
    if provider != default_provider(category):
        raise ValueError("Unreviewed social provider/category")
    if category == SocialCategory.FACT:
        return "https://uselessfacts.jsph.pl/api/v2/facts/random?language=de"
    endpoint = (
        "https://v2.jokeapi.dev/joke/Any?lang=de&safe-mode"
        "&blacklistFlags=nsfw,religious,political,racist,sexist,explicit"
        f"&type={category.value}"
    )
    if request is not None and request.id_range is not None:
        lower, upper = request.id_range
        endpoint += f"&idRange={lower}-{upper}"
    return endpoint


def _date(value: str | None) -> float | None:
    if not value:
        return None
    try:
        date = parsedate_to_datetime(value)
        return date.replace(tzinfo=date.tzinfo or timezone.utc).timestamp()
    except (ValueError, TypeError, OverflowError):
        return None


def _retry_at(
    headers: Any, now: float, *, limited: bool = False, success: bool = False
) -> float | None:
    remaining = headers.get("RateLimit-Remaining") if headers is not None else None
    if (
        success
        and isinstance(remaining, str)
        and remaining.isascii()
        and remaining.isdigit()
        and int(remaining) > 0
    ):
        # JokeAPI sends Retry-After on ordinary successes too: it describes the
        # next reset, not a mandatory wait while requests remain available.
        return None
    retry = headers.get("Retry-After") if headers is not None else None
    until = None
    if isinstance(retry, str):
        until = (
            now + int(retry) if retry.isascii() and retry.isdigit() else _date(retry)
        )
    exhausted = headers is not None and headers.get("RateLimit-Remaining") == "0"
    reset = _date(headers.get("RateLimit-Reset")) if headers is not None else None
    if limited or exhausted:
        until = max(
            (v for v in (until, reset) if v is not None and v > now), default=now + 900
        )
    if until is not None and now < until <= 253402300799:
        return until
    return None


def fetch_social_response(
    category: SocialCategory,
    provider: SocialProvider | None = None,
    *, request: SocialFetchRequest | None = None,
) -> SocialHttpResponse:
    if request is not None and request.metadata:
        raise ValueError("Metadata is not social content")
    http_request = Request(
        social_endpoint(category, provider, request=request),
        headers={
            "Accept": "application/json",
            "User-Agent": "AikoDesktopPet/1.0",
        },
    )
    retry_at = None
    try:
        with urlopen(http_request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            retry_at = _retry_at(
                getattr(response, "headers", None), time.time(), success=True
            )
            body = response.read(MAX_RESPONSE_BYTES + 1)
        if len(body) > MAX_RESPONSE_BYTES:
            raise ValueError("Social response exceeds size limit")
        payload = json.loads(body.decode("utf-8"))
        if request is not None and request.id_range is not None:
            identifier = payload.get("id") if isinstance(payload, dict) else None
            if (type(identifier) is not int
                    or not request.id_range[0] <= identifier <= request.id_range[1]):
                raise ValueError("Provider returned an unrequested joke identity")
        try:
            content = prepare_social_content(category, payload, provider=provider)
        except SocialContentRejectionError as error:
            identifier = payload.get("id") if isinstance(payload, dict) else None
            if ((provider or default_provider(category)) == SocialProvider.JOKEAPI
                    and type(identifier) is int and 0 <= identifier <= MAX_JOKE_ID):
                raise SocialFetchError(
                    "rejected", retry_at, rejected_id=identifier, reason=error.reason
                ) from None
            raise
        return SocialHttpResponse(content, retry_at)
    except HTTPError as error:
        try:
            now = time.time()
            if (error.code == 400
                    and (provider or default_provider(category))
                    == SocialProvider.JOKEAPI
                    and request is not None and request.id_range is not None):
                try:
                    raw = error.read(MAX_RESPONSE_BYTES + 1)
                    data = json.loads(raw) if len(raw) <= MAX_RESPONSE_BYTES else None
                except (ValueError, UnicodeError, OSError):
                    data = None
                if (isinstance(data, dict) and data.get("error") is True
                        and data.get("internalError") is False
                        and type(data.get("code")) is int and data["code"] == 106):
                    raise SocialFetchError(
                        "empty", _retry_at(error.headers, now, success=True),
                        reason="no_match",
                    ) from None
            if error.code == 429:
                raise SocialFetchError(
                    "rate", _retry_at(error.headers, now, limited=True)
                ) from None
            access = error.code in (401, 403, 404, 410) or 300 <= error.code < 400
            retry_at = _retry_at(error.headers, now)
            raise SocialFetchError(
                "access" if access else "temporary",
                max(retry_at or now, now + (86400 if access else 60)),
            )
        finally:
            error.close()
    except (URLError, TimeoutError, OSError):
        raise SocialFetchError("temporary", time.time() + 60) from None
    except SocialFetchError:
        raise
    except (ValueError, UnicodeError):
        raise SocialFetchError("invalid", retry_at) from None


def fetch_joke_catalog() -> tuple[JokeCatalog, float | None]:
    """One bounded metadata call; the scheduler reserves its provider budget."""
    request = Request(
        "https://v2.jokeapi.dev/info",
        headers={"Accept": "application/json", "User-Agent": "AikoDesktopPet/1.0"},
    )
    retry_at = None
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            retry_at = _retry_at(response.headers, time.time(), success=True)
            raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError("Oversized metadata")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Metadata must be an object")
        bounds = data["jokes"]["idRange"]["de"]
        if (data.get("error") is not False or not isinstance(bounds, list)
                or len(bounds) != 2 or any(type(v) is not int for v in bounds)
                or not 0 <= bounds[0] <= bounds[1] <= MAX_JOKE_ID):
            raise ValueError("Invalid German joke bounds")
        return JokeCatalog(
            bounds[0], bounds[1], time.time() + JOKE_METADATA_SECONDS
        ), retry_at
    except HTTPError as error:
        try:
            now = time.time()
            if error.code == 429:
                raise SocialFetchError(
                    "rate", _retry_at(error.headers, now, limited=True)
                ) from None
            access = error.code in (401, 403, 404, 410) or 300 <= error.code < 400
            raise SocialFetchError(
                "access" if access else "temporary", now + (86400 if access else 60)
            ) from None
        finally:
            error.close()
    except (URLError, TimeoutError, OSError):
        raise SocialFetchError("temporary", time.time() + 60) from None
    except (ValueError, TypeError, KeyError, UnicodeError):
        raise SocialFetchError("invalid", retry_at) from None


def fetch_social_content(
    category: SocialCategory,
    provider: SocialProvider | None = None,
) -> PreparedSocialContent:
    return fetch_social_response(category, provider).content


class HttpSocialContentWorker:
    """Only one fetch may exist, even across disable/re-enable transitions."""

    def __init__(self) -> None:
        self._results: Queue[SocialFetchResult] = Queue(maxsize=1)
        self._active = False
        self._closed = False

    def start(
        self,
        category: SocialCategory,
        token: object,
        provider: SocialProvider | None = None,
        *, request: SocialFetchRequest | None = None,
    ) -> None:
        if self._closed or self._active:
            raise RuntimeError("Social worker is closed or already fetching")
        if request is not None:
            social_endpoint(category, provider, request=request)
        self._active = True

        def fetch() -> None:
            try:
                if request is not None and request.metadata:
                    catalog, retry_at = fetch_joke_catalog()
                    result = SocialFetchResult(
                        token, category, catalog=catalog, retry_at=retry_at
                    )
                else:
                    response = (fetch_social_response(category, provider)
                                if request is None else fetch_social_response(
                                    category, provider, request=request))
                    result = SocialFetchResult(
                        token, category, response.content, retry_at=response.retry_at
                    )
            except SocialFetchError as error:
                result = SocialFetchResult(
                    token, category, failure=error.failure, retry_at=error.retry_at,
                    rejected_id=error.rejected_id, reason=error.reason,
                )
            except Exception:
                # Never expose provider bodies or exception text to the UI.
                result = SocialFetchResult(
                    token, category, failure="temporary", retry_at=time.time() + 60
                )
            self._results.put(result)

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
