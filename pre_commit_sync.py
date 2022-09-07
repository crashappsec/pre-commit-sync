# -*- coding: utf-8 -*-
import argparse
import re
import typing
from pathlib import Path

from poetry.factory import Factory
from poetry.repositories.repository import Repository
from pyarn.lockfile import Lockfile


class Yarn:
    lockfiles = {}

    @classmethod
    def lockfile(cls, path: Path):
        if path not in cls.lockfiles:
            cls.lockfiles[path] = Lockfile.from_file(path)
        return cls.lockfiles[path]

    @classmethod
    def version_for(cls, package: str, lockfile: Path) -> str:
        lock = cls.lockfile(lockfile)
        package = next(i for i in lock.packages() if i.name == package)
        return package.version


class Poetry:
    lockfiles: typing.Dict[Path, Repository] = {}

    @classmethod
    def lockfile(cls, path: Path) -> Repository:
        cwd = path.resolve().parent
        if cwd not in cls.lockfiles:
            cls.lockfiles[cwd] = (
                Factory().create_poetry(cwd=cwd).locker.locked_repository()
            )
        return cls.lockfiles[cwd]

    @classmethod
    def version_for(cls, package: str, lockfile: Path) -> str:
        lock = cls.lockfile(lockfile)
        package = next(i for i in lock.search(package) if i.name == package)
        return package.version


SYNC_PATTERN = re.compile(
    r"""
    ^
    (?P<prefix>
        \s+
        -
        \s+
    )
    (?P<quote>['"]?)
    (?P<package>.+?)(@.+?)?
    ['"]?
    (?P<sync>
    \s+
        [#]\s+sync:(?P<lockfile>.+)
    )
    $
    """,
    re.VERBOSE,
)

LOCK_MAPPING = {
    "poetry.lock": Poetry,
    "yarn.lock": Yarn,
}


def sync(text: str, path: Path):
    for line in text.splitlines():
        search = SYNC_PATTERN.search(line)
        if search:
            prefix = search.group("prefix")
            quote = search.group("quote") or '"'
            package = search.group("package")
            lockfile = (path.parent / search.group("lockfile")).resolve()
            sync_comment = search.group("sync")
            version = LOCK_MAPPING[lockfile.name].version_for(package, lockfile)
            yield f"{prefix}{quote}{package}@{version}{quote}{sync_comment}"
        else:
            yield line


parser = argparse.ArgumentParser(
    description="Sync pre-commit additional_dependencies from package manager lock files"
)
parser.add_argument("paths", metavar="PATH", type=Path, nargs="+", help="path to sync")
parser.add_argument(
    "-w",
    "--write",
    action="store_true",
    help="when provided write files back. otherise prints results to stdout",
)


def main():
    args = parser.parse_args()
    for path in args.paths:
        to_sync = Path(path).resolve()
        if to_sync.suffix not in [".yaml", ".yml"]:
            continue
        data = "\n".join(sync(to_sync.read_text(), to_sync)).strip() + "\n"
        if args.write:
            path.write_text(data)
        else:
            print(data)


if __name__ == "__main__":
    main()
