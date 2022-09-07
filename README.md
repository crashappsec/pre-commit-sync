# Sync pre-commit

Sync pre-commit additional_dependencies from package manager lock files

To do that simply annotate the dependency with the lock file which should be
used to source the version from:

```yaml
- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v0.971
  hooks:
    - id: mypy
      additional_dependencies:
        - pytest # sync:poetry.lock
```

Currently supported lock files:

- `poetry.lock`
- `yarn.lock`

To use in the project add pre-commit hook:

```yaml
- repo: https://github.com/miki725/pre-commit-sync
  rev: main
  hooks:
    - id: pre-commit-sync
```
