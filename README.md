# Ensure CHANGELOG versions are linked

For repositories abiding by [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), this ensures that all versions (except `Unreleased`) are linked to their respective URLs.

```
usage: changelog-versions-linked [-h] [-v] [-C DIR] [--url-template URL_TEMPLATE] [--no-ci-skip] [--insert-eof | --insert-after-re REGEX | --insert-before-re REGEX] [filenames ...]

Ensure all version links are present in the changelog.

positional arguments:
  filenames             Explicit CHANGELOG filenames to check.

options:
  -h, --help            show this help message and exit
  -v                    Verbosity (of LOGGER). WARNING by default, -v: INFO, -vv: DEBUG
  -C DIR                Change to this directory before running.
  --url-template URL_TEMPLATE
                        Explicit template for generating URLs, where <VERSION> will be replaced
  --no-ci-skip          Force to still run even on CI
  --insert-eof          Add new URL lines at the end of the file (default insert method).
  --insert-after-re REGEX
                        Add new URL lines after the first line found matching the regular expression.
  --insert-before-re REGEX
                        Insert new URL lines before the first line found matching the regular expression.

```

By default it assumes it's being run from a Git repository and attempts to:

- Operate on ANY `CHANGELOG.md` filenames in the repository
- Guess the URL based off `git remote` found:
  - If GitHub or GitLab detected, assume it uses releases
- Blindly adds the link to the bottom of the `CHANGELOG.md` file

These can be overridden with the appropriate command-line arguments:

```bash
$ changelog-versions-linked  # Default behavior
$ changelog-versions-linked --insert-after-re '<!-- AFTER ME -->'
$ changelog-versions-linked --url-template 'https://example.com/releases/<VERSION>'
$ changelog-versions-linked HISTORY.md  # Custom changelog file
```

Also available as a [pre-commit](https://pre-commit.com/#usage) hook:

```yaml
# .pre-commit-config.yaml
repos:
- repo: https://github.com/Treehouse-Digital/changelog-versions-linked
  rev: 0.1.0
  hooks:
    - id: changelog-versions-linked
```

## Contributing

This repo uses [uv](https://docs.astral.sh/uv/) to perform package managing.

After cloning down the repository:

```bash
uv sync
uv run changelog-versions-linked
```
