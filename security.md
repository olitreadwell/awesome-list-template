# Security

## Reporting

Report a vulnerability through GitHub's private vulnerability reporting on this
repository, or by email to the maintainer address on the profile. Please do not
open a public issue for a security problem.

## Scope

This repository runs no server. The things worth reporting are:

- A dependency with a known vulnerability, which `osv-scanner` should have
  caught first. If it did not, that is also worth reporting.
- A workflow or script that leaks a token, for example through `gh` output or a
  printed environment.
- A job script that follows a redirect from an untrusted host, or writes outside
  its stated directory.
- Content in `readme.md` that leads to a malicious page, which the link checker
  cannot judge.

## What this repository does not do

- No secrets are committed. `gitleaks` runs in the pre-commit hook and overnight.
- No analytics, no trackers, and no third-party scripts on the published site.
- No LLM calls in the pipeline.
