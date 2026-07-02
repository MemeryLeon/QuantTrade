from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class SourceIdentityMode(StrEnum):
    LOCAL_GIT = "local_git"
    IMMUTABLE_BUILD = "immutable_build"


class SourceIdentityStatus(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class SourceIdentity:
    mode: SourceIdentityMode
    platform_git_sha: str | None
    platform_source_tree_digest: str
    backend_image_digest: str | None
    build_git_sha: str | None
    git_workspace_clean: bool | None


@dataclass(frozen=True, slots=True)
class SourceIdentityResult:
    status: SourceIdentityStatus
    identity: SourceIdentity | None
    error_code: str | None
    error_message: str | None


class ISourceIdentityProvider(Protocol):
    def get_identity(self) -> SourceIdentityResult: ...

