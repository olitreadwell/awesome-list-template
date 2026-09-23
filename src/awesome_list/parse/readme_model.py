"""The entry model: what a parsed readme looks like to every rule and export."""

from __future__ import annotations

from dataclasses import dataclass

TAG_AXES = ("type", "access", "status")


@dataclass(frozen=True, slots=True)
class ListTag:
    """One tag on one axis, for example type=Data."""

    axis: str
    label: str


@dataclass(frozen=True, slots=True)
class Heading:
    """A markdown heading, in document order."""

    level: int
    text: str
    line: int


@dataclass(frozen=True, slots=True)
class ListEntry:
    """One entry: a link, a description, tags, and where it came from."""

    name: str
    url: str
    description: str
    tags: tuple[ListTag, ...]
    line: int
    raw: str
    depth: int = 1
    has_separator: bool = True
    nested_under_entry: bool = False
    unknown_tags: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class ListGroup:
    """A bullet that names a group, with its indented entries."""

    name: str
    line: int
    entries: tuple[ListEntry, ...]


@dataclass(frozen=True, slots=True)
class ListSection:
    """A level 2 section, with its entries and groups."""

    name: str
    line: int
    entries: tuple[ListEntry, ...]
    groups: tuple[ListGroup, ...]

    @property
    def all_entries(self) -> tuple[ListEntry, ...]:
        """Return every entry in the section, groups included."""
        grouped = tuple(entry for group in self.groups for entry in group.entries)
        return self.entries + grouped


@dataclass(frozen=True, slots=True)
class ListDocument:
    """A parsed readme."""

    title: str
    tagline: str
    sections: tuple[ListSection, ...]
    headings: tuple[Heading, ...] = ()

    @property
    def entries(self) -> tuple[ListEntry, ...]:
        """Return every entry in the list, in document order."""
        grouped = tuple(
            entry for section in self.sections for entry in section.all_entries
        )
        return grouped

    def section_named(self, name: str) -> ListSection | None:
        """Return the section with this name, case sensitive, or None."""
        for section in self.sections:
            if section.name == name:
                return section
        return None
