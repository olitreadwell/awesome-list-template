# awesome-list-template

Engine and template for maintaining a curated list. It parses `readme.md` into a
typed model, checks it against the awesome.re conventions, generates the table of
contents, exports machine-readable copies, and keeps links alive on a schedule.

This repository is the engine. It is not an awesome list: no badge, no `awesome`
GitHub topic, and it is never submitted to
[sindresorhus/awesome](https://github.com/sindresorhus/awesome). Lists that use it
are separate repositories.

## Install

```bash
uv sync --group dev
cd tools && npm ci
make hooks-install
```

## Commands

```bash
make list-check    # entry grammar, tags, duplicates, URLs, TOC freshness
make toc           # rewrite the Contents section
make toc-check     # fail when the Contents section is stale
make export        # data.json, data.csv, feed.xml, sitemap.xml
make site          # optional site, only when site.enabled = true
make check         # the full gate
make check-fast    # the pre-commit subset
```

## Using it for a list

1. Copy `awesome.toml`, `Makefile`, `.githooks/`, and `ci/` into the list repo.
2. Point `awesome.toml` at the list's readme and sections.
3. Run `make list-check --report-only` first. It reports and exits zero.
4. Fix what it reports, then make it enforcing.
5. Add the engine as a dependency in the list repo's `pyproject.toml`:

   ```
   awesome-list @ git+https://github.com/olitreadwell/awesome-list-template
   ```

## Rules this engine enforces

- Entries are `- [Name](url) - Description.`, with the description starting
  uppercase and ending with a period.
- No duplicate URLs, no relative URLs, no fragment-only URLs, no tracking
  parameters.
- Every entry carries a type tag and an access tag from the configured
  vocabulary.
- The Contents section is first, one level deep at most, and never lists
  Contributing or Footnotes.
- No archived or deprecated entry in the main list. Those live in `legacy.md`.

## Layout

- `src/awesome_list/parse/` builds the model from the readme.
- `src/awesome_list/rules/` holds one rule per module.
- `src/awesome_list/toc/` renders and syncs the Contents section.
- `src/awesome_list/export/` writes data.json, data.csv, the feed, and the sitemap.
- `src/awesome_list/submission/` holds the pinned awesome.re requirements.
- `jobs/` holds the scheduled scripts. `SPEC.md` is the full contract.
