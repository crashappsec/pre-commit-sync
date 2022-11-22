# Sync `pre-commit`

Sync [pre-commit](https://pre-commit.com/) versions from lock files.

## Why?

Pre-commit is a great tool for running lint/formatting/etc pre-commit
hooks. As it is a language-agnostic tool, it's configuration file is
therefore independent from any of the traditional package managers such
as `poetry` or `yarn`. Most package managers now have a lock file which
allows to pin dependencies to specific versions for more reliable builds
as well as security considerations. Pre-commit has similar behavior
by allowing to pin specific revisions of repos of hooks to be run. It
even allows to update those revisions via `autoupdate` command. Nothing
however enforces that those revisions match pinned versions in a lock
file. This can make devs sad due to local tools not matching pre-commit
hooks. In addition it can cause security concerns as pre-commit can
install versions of packages not formally reviewed in the dependency
management process.

This pre-commit hook is an attempt to make that better. By annotating
pre-commit configuration file with a source of where to sync the
versions from, this hook will sync those versions from the official lock
file(s).

## Syncing

Currently supported lock files:

- `poetry.lock` (Python)
- `yarn.lock` (JavaScript)

### Repo Rev

If the hooks repo revision should be synced with a package from lock
file, add a comment specifying with which package version should be
synced with. For example:

```yaml
- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v0.971 # sync:mypy:poetry.lock
  hooks:
    - id: mypy
      additional_dependencies:
        - pytest # sync:poetry.lock
```

### Additional Dependencies

If you install any additional dependencies for specific hooks,
they can be synced as well. Simply specify which lock file to sync version with.
For example:

```yaml
- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v0.971 # sync:mypy:poetry.lock
  hooks:
    - id: mypy
      additional_dependencies:
        - "pytest==7.2.0" # sync:poetry.lock
        - boto3-stubs # sync:poetry.lock
```

Note that if the initially the version is missing, on first run the version
will be added as per the lock file.

## Using

To use this hook, add it to pre-commit configuration:

```yaml
- repo: https://github.com/miki725/pre-commit-sync
  rev: main
  hooks:
    - id: pre-commit-sync
```

You can keep the sync version up-to-date with:

```sh
pre-commit autoupdate
```
