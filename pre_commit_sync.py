# -*- coding: utf-8 -*-
import abc
import argparse
import re
import typing
from pathlib import Path

from poetry.factory import Factory
from poetry.repositories.repository import Repository
from pyarn.lockfile import Lockfile


class Manager(abc.ABC):
    comparator: str = NotImplemented

    @classmethod
    @abc.abstractmethod
    def version_for(cls, package: str, lockfile: Path) -> str:
        """ """


class Yarn(Manager):
    comparator = "@"
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


class Poetry(Manager):
    comparator = "=="
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


MANAGER_MAPPING: typing.Dict[str, typing.Type[Manager]] = {
    "poetry.lock": Poetry,
    "yarn.lock": Yarn,
}


PACKAGE_PATTERN = re.compile(
    rf"""
    ^
    (?P<prefix>
        \s+
        -
        \s+
    )
    (?P<quote>['"]?)
    (?P<package>.+?)
    (({'|'.join(i.comparator for i in MANAGER_MAPPING.values())}).+?)?
    ['"]?
    (?P<sync>
    \s+
        [#]\s+sync:(?P<lockfile>.+)
    )
    $
    """,
    re.VERBOSE,
)


REV_PATTERN = re.compile(
    r"""
    ^
    (?P<prefix>
        \s+
        rev:
        \s+
    )
    (?P<quote>['"]?)
    (?P<version>.+?)
    ['"]?
    (?P<sync>
    \s+
        [#]\s+
        sync
        :
        (?P<package>.+)
        :
        (?P<lockfile>.+)
    )
    $
    """,
    re.VERBOSE,
)


def sync(text: str, path: Path):
    for line in text.splitlines():
        package_search = PACKAGE_PATTERN.search(line)
        rev_search = REV_PATTERN.search(line)
        if package_search:
            prefix = package_search.group("prefix")
            quote = package_search.group("quote") or '"'
            package = package_search.group("package")
            lockfile = (path.parent / package_search.group("lockfile")).resolve()
            sync_comment = package_search.group("sync")
            manager = MANAGER_MAPPING[lockfile.name]
            version = manager.version_for(package, lockfile)
            yield f"{prefix}{quote}{package}{manager.comparator}{version}{quote}{sync_comment}"
        elif rev_search:
            prefix = rev_search.group("prefix")
            quote = rev_search.group("quote") or ""
            package = rev_search.group("package")
            lockfile = (path.parent / rev_search.group("lockfile")).resolve()
            sync_comment = rev_search.group("sync")
            manager = MANAGER_MAPPING[lockfile.name]
            version = manager.version_for(package, lockfile)
            yield f"{prefix}{quote}{version}{quote}{sync_comment}"
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
