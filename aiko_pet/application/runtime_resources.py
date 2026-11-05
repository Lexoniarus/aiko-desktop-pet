"""Immutable resources prepared before a desktop session can be restored."""

from dataclasses import dataclass

from .social_content import PreparedSocialContent


@dataclass(frozen=True, slots=True)
class PreparedRuntimeResources:
    local_social_content: tuple[PreparedSocialContent, ...]
