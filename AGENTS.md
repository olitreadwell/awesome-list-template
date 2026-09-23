# Agent instructions

This repository maintains an awesome list. Read `SPEC.md` before changing
behaviour: it is the contract, and `AUTOMATIONS.md` lists what each automation is
allowed to do.

## Hard rules

- Never write entry text, section prose, or descriptions. A human contributes
  those words, and the triage job copies them verbatim. awesome.re rejects lists
  and pull requests that are AI-generated.
- Never let the build write `readme.md`. The build reads it. Only `make toc`
  rewrites the Contents block and only `make stats` rewrites stats segments, and
  only when asked.
- Never hand-write or hand-edit a stars segment. Run `make stats`: it reads the
  GitHub API once, writes `github-stats.json`, and keeps the rest of the line
  byte for byte. When `gh` fails, it keeps the last known numbers and changes
  nothing.
- Never point a main-list entry at an archived copy or a deprecated tool. It
  moves to `legacy.md` or it comes out.
- No CI badge in `readme.md`, and no `awesome` or `awesome-list` GitHub topic on
  this template repo. It is a template, not a list.
- No hosted workflow may be the only path to a check. `make check` is the gate.
- Do not edit a recorded guideline rule in
  `src/awesome_list/submission/awesome_re_rules.py` without also updating the
  upstream citation and hash.

## Workflow

- Tests first. Every rule starts with a clean fixture, a dirty fixture, and a
  failing test.
- `make check-fast` runs on commit, `make check` on push. Do not use
  `--no-verify` on a branch offered for review.
- Rules are pure functions: entry in, violations out. Filesystem, network, and
  subprocess work belongs in `cli/`, `links/`, or `jobs/`.

## Layout

- `src/awesome_list/parse/` turns `readme.md` into the entry model.
- `src/awesome_list/rules/` holds one rule per module, named for the rule.
- `src/awesome_list/toc/` renders and syncs the Contents section.
- `src/awesome_list/github/` formats repo stats and is the only module that
  calls `gh`. Rules stay pure; the snapshot stays offline.
- `src/awesome_list/export/` writes the machine-readable outputs.
- `src/awesome_list/site/` builds the optional site.
- `src/awesome_list/submission/` holds the pinned awesome.re requirements.
- `jobs/` holds the scheduled scripts. They shell out to the CLI and to `gh`.
