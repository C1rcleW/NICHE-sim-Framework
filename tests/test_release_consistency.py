"""Version references must move together across release artifacts."""
from __future__ import annotations

import re
from pathlib import Path

import family_abm

REPO = Path(__file__).resolve().parent.parent


def test_release_version_is_consistent_everywhere() -> None:
    version = family_abm.__version__
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert re.search(rf'^version = "{re.escape(version)}"$', pyproject, re.MULTILINE)

    changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(
        rf"^## \[{re.escape(version)}\] — (\d{{4}}-\d{{2}}-\d{{2}})$",
        changelog,
        re.MULTILINE,
    )
    assert match, f"CHANGELOG 缺少带日期的 [{version}] 发布段"
    release_date = match.group(1)

    citation = (REPO / "CITATION.cff").read_text(encoding="utf-8")
    assert re.search(rf'^version: "{re.escape(version)}"$', citation, re.MULTILINE)
    assert re.search(rf'^date-released: "{release_date}"$', citation, re.MULTILINE)

    readme = (REPO / "README.md").read_text(encoding="utf-8")
    assert f"当前版本 **{version}**" in readme
    assert f"Version {version}" in readme
    assert f"docs/release-notes-{version}.md" in readme

    notes = REPO / "docs" / f"release-notes-{version}.md"
    assert notes.is_file(), f"缺少发布说明 {notes.relative_to(REPO)}"

    research = (REPO / "docs" / "研究设计.md").read_text(encoding="utf-8")
    assert f"对应软件版本 v{version}" in research

    r0 = REPO / "docs" / "R0-研究决策记录.md"
    assert r0.is_file(), "缺少 R0 研究决策记录"
    assert "docs/R0-研究决策记录.md" in readme, "README 未链接 R0 决策记录"
