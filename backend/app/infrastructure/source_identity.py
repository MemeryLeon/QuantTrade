from __future__ import annotations

import os
import subprocess
from collections.abc import Callable, Mapping
from pathlib import Path

from app.domains.source_identity import (
    SourceIdentity,
    SourceIdentityMode,
    SourceIdentityResult,
    SourceIdentityStatus,
)


GitRunner = Callable[[tuple[str, ...]], str]


class SourceIdentityProvider:
    def __init__(
        self,
        root: Path,
        environ: Mapping[str, str] | None = None,
        git_runner: GitRunner | None = None,
    ) -> None:
        self._root = root
        self._environ = environ if environ is not None else os.environ
        self._git_runner = git_runner

    def get_identity(self) -> SourceIdentityResult:
        immutable = self._immutable_build_identity()
        if immutable is not None:
            return SourceIdentityResult(
                status=SourceIdentityStatus.AVAILABLE,
                identity=immutable,
                error_code=None,
                error_message=None,
            )

        if (self._root / ".git").exists():
            return self._local_git_identity()

        return SourceIdentityResult(
            status=SourceIdentityStatus.UNAVAILABLE,
            identity=None,
            error_code="SOURCE_IDENTITY_UNAVAILABLE",
            error_message="missing local git workspace and immutable build identity",
        )

    def _immutable_build_identity(self) -> SourceIdentity | None:
        build_git_sha = self._environ.get("QUANTTRADE_BUILD_GIT_SHA")
        source_tree_digest = self._environ.get("QUANTTRADE_SOURCE_TREE_DIGEST")
        backend_image_digest = self._environ.get("QUANTTRADE_BACKEND_IMAGE_DIGEST")
        if not build_git_sha and not source_tree_digest and not backend_image_digest:
            return None
        if not build_git_sha or not source_tree_digest or not backend_image_digest:
            return None
        return SourceIdentity(
            mode=SourceIdentityMode.IMMUTABLE_BUILD,
            platform_git_sha=None,
            platform_source_tree_digest=source_tree_digest,
            backend_image_digest=backend_image_digest,
            build_git_sha=build_git_sha,
            git_workspace_clean=None,
        )

    def _local_git_identity(self) -> SourceIdentityResult:
        status = self._run_git(("status", "--porcelain", "--untracked-files=normal"))
        if status:
            return SourceIdentityResult(
                status=SourceIdentityStatus.UNAVAILABLE,
                identity=None,
                error_code="WORKSPACE_DIRTY",
                error_message="local git workspace has uncommitted or untracked files",
            )
        git_sha = self._run_git(("rev-parse", "HEAD"))
        tree_digest = self._run_git(("rev-parse", "HEAD^{tree}"))
        return SourceIdentityResult(
            status=SourceIdentityStatus.AVAILABLE,
            identity=SourceIdentity(
                mode=SourceIdentityMode.LOCAL_GIT,
                platform_git_sha=git_sha,
                platform_source_tree_digest=tree_digest,
                backend_image_digest=None,
                build_git_sha=None,
                git_workspace_clean=True,
            ),
            error_code=None,
            error_message=None,
        )

    def _run_git(self, args: tuple[str, ...]) -> str:
        if self._git_runner is not None:
            return self._git_runner(args)
        completed = subprocess.run(
            ("git", *args),
            cwd=self._root,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
        return completed.stdout.strip()

