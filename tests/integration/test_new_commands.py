"""The commands added for links, repo setup, exports, and the submission gate."""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path

from awesome_list.cli.run_compliance_audit import main as compliance_main
from awesome_list.cli.run_export import main as export_main
from awesome_list.cli.run_links import main as links_main
from awesome_list.cli.run_repo_setup import main as repo_setup_main
from awesome_list.cli.run_submission_check import main as submission_main

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "readme"
CONFIG = str(FIXTURES / "awesome.toml")
README = str(FIXTURES / "clean.md")


def test_links_prints_the_generated_config(capsys: object) -> None:
    assert links_main(["--config", CONFIG, "--print-config"]) == 0
    printed = capsys.readouterr().out  # type: ignore[attr-defined]

    assert "cache = true" in printed
    assert "max_retries = 2" in printed


def _record(store: list[list[str]], command: Sequence[str]) -> None:
    store.append([str(part) for part in command])


def _recorder(store: list[list[str]]) -> Callable[[Sequence[str]], int]:
    def record(command: Sequence[str]) -> int:
        _record(store, command)
        return 0

    return record


def _string_recorder(store: list[list[str]]) -> Callable[[Sequence[str]], str]:
    def record(command: Sequence[str]) -> str:
        _record(store, command)
        return "{}"

    return record


def test_links_diff_only_hands_lychee_the_new_urls(
    capsys: object, tmp_path: Path
) -> None:
    seen: list[list[str]] = []
    base = Path(README).read_text(encoding="utf-8")
    added = base.replace(
        "## Footnotes",
        "- [Fresh](https://fresh.example.com/) - new this branch.\n\n## Footnotes",
        1,
    )
    branch = tmp_path / "clean.md"
    branch.write_text(added, encoding="utf-8")

    status = links_main(
        ["--config", CONFIG, "--readme", str(branch), "--diff", "--base-ref", "HEAD"],
        run=_recorder(seen),
        git_show=lambda revision: base,
    )

    assert status == 0
    assert seen[0][-1] == "https://fresh.example.com/"
    assert "links-diff: 1 new URLs" in capsys.readouterr().out  # type: ignore[attr-defined]


def test_links_diff_with_nothing_new_never_runs_lychee(capsys: object) -> None:
    text = Path(README).read_text(encoding="utf-8")
    called: list[list[str]] = []

    status = links_main(
        ["--config", CONFIG, "--readme", README, "--diff"],
        run=_recorder(called),
        git_show=lambda revision: text,
    )

    assert status == 0
    assert called == []
    assert "no new URLs" in capsys.readouterr().out  # type: ignore[attr-defined]


def test_repo_setup_is_a_dry_run_until_apply(capsys: object) -> None:
    assert repo_setup_main(["--config", CONFIG, "--slug", "a/b"]) == 0
    printed = capsys.readouterr().out  # type: ignore[attr-defined]

    assert "dry run" in printed
    assert "gh api -X PATCH repos/a/b" in printed
    assert "curl" not in printed


def test_repo_setup_apply_runs_one_gh_command_per_setting() -> None:
    seen: list[list[str]] = []

    status = repo_setup_main(
        ["--config", CONFIG, "--slug", "a/b", "--apply"],
        runner=_string_recorder(seen),
    )

    assert status == 0
    assert [command[0] for command in seen] == ["gh", "gh", "gh"]
    assert any("topics" in " ".join(command) for command in seen)


def test_export_writes_three_files(tmp_path: Path) -> None:
    out = tmp_path / "exports"

    status = export_main(
        [
            "--config",
            CONFIG,
            "--readme",
            README,
            "--out",
            str(out),
            "--today",
            "2026-09-23",
        ]
    )

    assert status == 0
    assert sorted(path.name for path in out.iterdir()) == [
        "data.csv",
        "data.json",
        "data.ndjson",
    ]
    assert "2026-09-23" in (out / "data.json").read_text(encoding="utf-8")


def test_export_check_fails_when_the_files_are_missing(tmp_path: Path) -> None:
    status = export_main(
        [
            "--config",
            CONFIG,
            "--readme",
            README,
            "--out",
            str(tmp_path / "exports"),
            "--check",
        ]
    )

    assert status == 1


def test_export_check_passes_after_a_write(tmp_path: Path) -> None:
    out = tmp_path / "exports"
    export_main(["--config", CONFIG, "--readme", README, "--out", str(out)])

    assert (
        export_main(
            ["--config", CONFIG, "--readme", README, "--out", str(out), "--check"]
        )
        == 0
    )


def test_submission_check_fails_the_fixture_and_says_why(capsys: object) -> None:
    status = submission_main(["--config", CONFIG, "--readme", README, "--reminders"])
    printed = capsys.readouterr().out  # type: ignore[attr-defined]

    assert status == 1
    assert "awesome badge: readme links the awesome badge" in printed
    assert "fail contributing" in printed
    assert "not checkable here" in printed


def test_compliance_audit_reports_drift_from_injected_settings(capsys: object) -> None:
    status = compliance_main(
        ["--config", CONFIG, "--slug", "a/b"],
        fetch=lambda slug: {"description": "", "topics": ["awesome"]},
    )
    printed = capsys.readouterr().out  # type: ignore[attr-defined]

    assert status == 1
    assert "drift topics" in printed
    assert "drift description" in printed


def test_compliance_audit_report_only_exits_zero(capsys: object) -> None:
    status = compliance_main(
        ["--config", CONFIG, "--slug", "a/b", "--report-only"],
        fetch=lambda slug: {"description": "", "topics": []},
    )

    assert status == 0
    assert "drifted" in capsys.readouterr().out  # type: ignore[attr-defined]


def test_run_due_script_runs_an_overdue_job(repo_root: Path, tmp_path: Path) -> None:
    jobs_dir = tmp_path / "jobs"
    jobs_dir.mkdir()
    marker = tmp_path / "ran"
    script = jobs_dir / "links.sh"
    script.write_text(f"#!/usr/bin/env bash\nprintf ran > {marker}\n", encoding="utf-8")
    script.chmod(0o755)
    due = jobs_dir / "run-due.sh"
    due.write_text(
        (repo_root / "jobs" / "run-due.sh").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    due.chmod(0o755)

    result = subprocess.run(
        ["bash", str(due)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert marker.exists()
    assert "links" in result.stdout
    assert (tmp_path / ".state" / "links.last").exists()


def test_run_due_script_skips_a_fresh_job(repo_root: Path, tmp_path: Path) -> None:
    jobs_dir = tmp_path / "jobs"
    jobs_dir.mkdir()
    marker = tmp_path / "ran"
    script = jobs_dir / "links.sh"
    script.write_text(f"#!/usr/bin/env bash\nprintf ran > {marker}\n", encoding="utf-8")
    script.chmod(0o755)
    due = jobs_dir / "run-due.sh"
    due.write_text(
        (repo_root / "jobs" / "run-due.sh").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    due.chmod(0o755)
    state = tmp_path / ".state"
    state.mkdir()
    import time

    (state / "links.last").write_text(str(int(time.time())), encoding="utf-8")

    result = subprocess.run(
        ["bash", str(due)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert not marker.exists()
    assert "up to date" in result.stdout


def test_links_diff_falls_back_when_origin_head_is_missing(capsys: object) -> None:
    text = Path(README).read_text(encoding="utf-8")
    tried: list[str] = []

    def show(revision: str) -> str:
        tried.append(revision)
        if revision.startswith("origin/HEAD"):
            raise SystemExit("no such ref")
        return text

    status = links_main(
        ["--config", CONFIG, "--readme", README, "--diff"],
        run=_recorder([]),
        git_show=show,
    )

    assert status == 0
    assert tried[0].startswith("origin/HEAD")
    assert tried[1].startswith("origin/main")


def test_links_diff_uses_an_explicit_base_ref_verbatim(capsys: object) -> None:
    text = Path(README).read_text(encoding="utf-8")
    tried: list[str] = []

    def show(revision: str) -> str:
        tried.append(revision)
        return text

    links_main(
        ["--config", CONFIG, "--readme", README, "--diff", "--base-ref", "v1.0.0"],
        run=_recorder([]),
        git_show=show,
    )

    assert tried == ["v1.0.0:clean.md"]


def test_compliance_audit_qualifies_a_bare_repo_slug(capsys: object) -> None:
    seen: list[str] = []

    def fetch(slug: str) -> dict[str, object]:
        seen.append(slug)
        return {"default_branch": "main", "topics": ["awesome"]}

    compliance_main(
        ["--config", CONFIG, "--slug", "owner/awesome-example"], fetch=fetch
    )

    assert seen == ["owner/awesome-example"]


def test_compliance_audit_qualifies_the_config_slug_with_the_origin_owner(
    capsys: object,
) -> None:
    seen: list[str] = []

    def fetch(slug: str) -> dict[str, object]:
        seen.append(slug)
        return {"default_branch": "main", "topics": []}

    compliance_main(["--config", CONFIG], fetch=fetch)

    assert len(seen) == 1
    owner, _, name = seen[0].partition("/")
    assert owner
    assert name == "awesome-example"


def test_repo_setup_sends_topics_as_an_array() -> None:
    seen: list[list[str]] = []

    repo_setup_main(
        ["--config", CONFIG, "--slug", "a/b", "--apply"],
        runner=_string_recorder(seen),
    )

    topics = " ".join(seen[1])

    assert "names[]=awesome " in topics
    assert "names[]=curated-list" in topics
    assert '["awesome"' not in topics
