# Contributing

Thanks for helping keep this list useful. Two ways in: open an issue, or open a
pull request.

## Suggest a link via issue

Use the add-link issue form. Fill in what you know. The triage job checks the
URL, looks for duplicates, and replies with a verdict. A maintainer then adds
the entry, or labels the issue so the triage job opens a branch. The description
is copied from your issue word for word.

## Add a link via pull request

1. Run `make hooks-install` once after cloning.
2. Edit `readme.md`. Find the section that fits and add a bullet:

   ```
   - [Name](https://example.com/) - ▦ Data - ○ Open - what it holds.
   ```

3. Run `make list-check`. It reports missing tags, missing dashes, missing
   trailing periods, duplicate URLs, and a stale table of contents, each with a
   line number and a fix.
4. Run `make toc` if the table of contents moved, then `make check`.

The pre-commit hook runs a fast subset. The pre-push hook runs the full gate. If
you push with `--no-verify`, the nightly audit will notice.

## What makes a good entry

- Link the page that holds the data or the documentation, not a landing page.
- Describe what it is in one line, starting with a capital and ending with a
  period.
- Tag the type and the access level. Add a status tag only for tools that have
  been superseded.
- One entry per resource. If two entries point at the same thing, one of them is
  wrong.
