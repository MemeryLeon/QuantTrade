from __future__ import annotations

from pathlib import Path

from app.domains.source_identity import SourceIdentityMode, SourceIdentityStatus
from app.infrastructure.source_identity import SourceIdentityProvider


def test_source_identity_uses_immutable_build_when_all_fields_exist(tmp_path: Path) -> None:
    provider = SourceIdentityProvider(
        root=tmp_path,
        environ={
            "QUANTTRADE_BUILD_GIT_SHA": "abc123",
            "QUANTTRADE_SOURCE_TREE_DIGEST": "tree123",
            "QUANTTRADE_BACKEND_IMAGE_DIGEST": "image123",
        },
    )

    result = provider.get_identity()

    assert result.status == SourceIdentityStatus.AVAILABLE
    assert result.identity is not None
    assert result.identity.mode == SourceIdentityMode.IMMUTABLE_BUILD
    assert result.identity.build_git_sha == "abc123"
    assert result.identity.backend_image_digest == "image123"


def test_source_identity_rejects_dirty_local_git_workspace(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()

    def run_git(args: tuple[str, ...]) -> str:
        if args[0] == "status":
            return " M backend/app/main.py"
        raise AssertionError(f"unexpected git call: {args}")

    provider = SourceIdentityProvider(root=tmp_path, environ={}, git_runner=run_git)

    result = provider.get_identity()

    assert result.status == SourceIdentityStatus.UNAVAILABLE
    assert result.identity is None
    assert result.error_code == "WORKSPACE_DIRTY"


def test_source_identity_accepts_clean_local_git_workspace(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()

    def run_git(args: tuple[str, ...]) -> str:
        responses = {
            ("status", "--porcelain", "--untracked-files=normal"): "",
            ("rev-parse", "HEAD"): "git-sha",
            ("rev-parse", "HEAD^{tree}"): "tree-digest",
        }
        return responses[args]

    provider = SourceIdentityProvider(root=tmp_path, environ={}, git_runner=run_git)

    result = provider.get_identity()

    assert result.status == SourceIdentityStatus.AVAILABLE
    assert result.identity is not None
    assert result.identity.mode == SourceIdentityMode.LOCAL_GIT
    assert result.identity.platform_git_sha == "git-sha"
    assert result.identity.git_workspace_clean is True


def test_source_identity_rejects_missing_identity(tmp_path: Path) -> None:
    provider = SourceIdentityProvider(root=tmp_path, environ={})

    result = provider.get_identity()

    assert result.status == SourceIdentityStatus.UNAVAILABLE
    assert result.identity is None
    assert result.error_code == "SOURCE_IDENTITY_UNAVAILABLE"
