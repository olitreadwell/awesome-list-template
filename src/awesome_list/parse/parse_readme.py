"""Turn readme.md into the entry model, using the same Markdown rules as GitHub."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from markdown_it import MarkdownIt
from markdown_it.token import Token

from awesome_list.parse.readme_model import (
    Heading,
    ListDocument,
    ListEntry,
    ListGroup,
    ListSection,
    ListTag,
    PlainBullet,
)
from awesome_list.tags import DEFAULT_TAG_VOCABULARY, TagVocabulary


def _allow_any_link(url: str) -> bool:
    """Accept every link destination so the rules can report the bad ones."""
    del url
    return True


_MARKDOWN = MarkdownIt("commonmark")

# Rules must be able to see a bad link in order to report it, so link validation
# is deliberately disabled here. Nothing in this engine fetches a URL it parsed.
_MARKDOWN.validateLink = _allow_any_link  # type: ignore[method-assign]

SKIPPED_SECTIONS = frozenset({"contents", "table of contents", "footnotes"})

TRAILING_WHITESPACE = re.compile(r"[ \t]+$")


@dataclass
class _ItemDraft:
    depth: int
    line: int
    text: str = ""
    inline: Token | None = None


@dataclass
class _GroupDraft:
    item: _ItemDraft
    entries: list[ListEntry] = field(default_factory=list)
    has_children: bool = False


@dataclass
class _SectionDraft:
    name: str
    line: int
    items: list[_ItemDraft] = field(default_factory=list)


def parse_readme(
    text: str,
    *,
    vocabulary: TagVocabulary = DEFAULT_TAG_VOCABULARY,
) -> ListDocument:
    """Parse a readme into sections, groups, and entries."""
    tokens = _MARKDOWN.parse(text)
    raw_lines = tuple(text.splitlines())
    title = ""
    tagline = ""
    headings: list[Heading] = []
    sections: list[_SectionDraft] = []
    current: _SectionDraft | None = None
    list_depth = 0
    pending: _ItemDraft | None = None
    section_level = _section_level(tokens)

    index = 0
    while index < len(tokens):
        token = tokens[index]

        if token.type == "heading_open":
            inline = tokens[index + 1] if index + 1 < len(tokens) else None
            level = int(token.tag[1]) if token.tag.startswith("h") else 0
            heading_text = _heading_text(inline)
            if heading_text:
                headings.append(
                    Heading(level=level, text=heading_text, line=_line_of(token))
                )
            if level == 1 and not title:
                title = heading_text
            elif level >= 2 and heading_text and level == section_level:
                current = _SectionDraft(name=heading_text, line=_line_of(token))
                sections.append(current)
            index += 3
            continue

        if token.type == "paragraph_open":
            inline = tokens[index + 1] if index + 1 < len(tokens) else None
            if title and not tagline and current is None and inline is not None:
                candidate = inline.content.strip()
                if candidate and not candidate.startswith("<!--"):
                    tagline = candidate
            index += 1
            continue

        if token.type == "bullet_list_open":
            list_depth += 1
        elif token.type == "bullet_list_close":
            list_depth = max(0, list_depth - 1)
        elif token.type == "list_item_open":
            pending = _ItemDraft(depth=list_depth, line=_line_of(token))
        elif token.type == "inline" and pending is not None:
            pending.text = token.content
            pending.inline = token
            if token.map:
                pending.line = token.map[0] + 1
            if current is not None and pending.text:
                current.items.append(pending)
            pending = None

        index += 1

    built_sections: list[ListSection] = []
    for draft in sections:
        if draft.name.strip().lower() in SKIPPED_SECTIONS:
            continue
        built_sections.append(_build_section(draft, vocabulary, raw_lines))

    return ListDocument(
        title=title,
        tagline=tagline,
        sections=tuple(built_sections),
        headings=tuple(headings),
        section_level=section_level,
    )


def _build_section(
    draft: _SectionDraft, vocabulary: TagVocabulary, raw_lines: tuple[str, ...]
) -> ListSection:
    entries: list[ListEntry] = []
    groups: list[_GroupDraft] = []
    plain_bullets: list[PlainBullet] = []
    last_kind: str | None = None

    for item in draft.items:
        if item.depth == 1:
            if _has_link(item):
                entry = _build_entry(item, vocabulary, depth=1, raw_lines=raw_lines)
                if entry is not None:
                    entries.append(entry)
                last_kind = "entry"
            else:
                # An unlinked bullet is only a group when something sits under
                # it. On its own it is a plain bullet, which lists use for
                # "start here" pointers.
                groups.append(_GroupDraft(item=item))
                last_kind = "group"
            continue

        if last_kind == "group" and groups:
            groups[-1].has_children = True
            entry = _build_entry(
                item, vocabulary, depth=item.depth, raw_lines=raw_lines
            )
            if entry is not None:
                groups[-1].entries.append(entry)
            continue

        entry = _build_entry(
            item,
            vocabulary,
            depth=item.depth,
            nested_under_entry=item.depth == 2 and last_kind == "entry",
            raw_lines=raw_lines,
        )
        if entry is not None:
            entries.append(entry)

    for group in groups:
        if not group.has_children:
            plain_bullets.append(
                PlainBullet(text=group.item.text.strip(), line=group.item.line)
            )

    return ListSection(
        name=draft.name,
        line=draft.line,
        entries=tuple(entries),
        plain_bullets=tuple(plain_bullets),
        groups=tuple(
            ListGroup(
                name=group.item.text.strip(),
                line=group.item.line,
                entries=tuple(group.entries),
            )
            for group in groups
            if group.has_children
        ),
    )


def _build_entry(
    item: _ItemDraft,
    vocabulary: TagVocabulary,
    *,
    depth: int,
    nested_under_entry: bool = False,
    raw_lines: tuple[str, ...] = (),
) -> ListEntry | None:
    if item.inline is None:
        return None
    name, url, tail = _split_link(item.inline)
    if url is None or name is None:
        return None

    tags: list[ListTag] = []
    unknown: list[tuple[str, str]] = []
    remainder = _strip_leading_separator(tail)
    for _ in range(8):
        match = vocabulary.match_leading(remainder)
        if match.tag is None and match.axis is None:
            break
        if match.tag is not None:
            tags.append(match.tag)
        elif match.axis and match.label:
            unknown.append((match.axis, match.label))
        if match.remainder == remainder:
            break
        remainder = match.remainder

    return ListEntry(
        name=name,
        url=url,
        description=remainder.strip(),
        tags=tuple(tags),
        line=item.line,
        raw=_raw_line(item, raw_lines),
        depth=depth,
        has_separator=tail.strip().startswith("-"),
        nested_under_entry=nested_under_entry,
        unknown_tags=tuple(unknown),
    )


def _raw_line(item: _ItemDraft, raw_lines: tuple[str, ...]) -> str:
    """Return the original line, so trailing whitespace is still visible."""
    if 1 <= item.line <= len(raw_lines):
        return raw_lines[item.line - 1]
    return item.text


def _split_link(inline: Token) -> tuple[str | None, str | None, str]:
    children = list(inline.children or [])
    name: str | None = None
    url: str | None = None
    tail: list[str] = []
    index = 0
    while index < len(children):
        child = children[index]
        if child.type == "link_open" and url is None:
            href = child.attrGet("href")
            url = href if isinstance(href, str) else ""
            index += 1
            parts: list[str] = []
            while index < len(children) and children[index].type != "link_close":
                parts.append(children[index].content)
                index += 1
            name = "".join(parts).strip()
        elif child.type == "text":
            tail.append(child.content)
        elif child.type == "code_inline":
            tail.append(f"`{child.content}`")
        index += 1
    return name, url, "".join(tail)


def _has_link(item: _ItemDraft) -> bool:
    if item.inline is None:
        return False
    return any(child.type == "link_open" for child in (item.inline.children or []))


def _section_level(tokens: list[Token]) -> int:
    """Return the heading depth this readme uses for sections.

    Lists disagree about how deep a section sits: most use ``##``, some group
    everything with ``###`` and have no ``##`` section at all. The shallowest
    heading below the title that is not itself Contents, Footnotes, or an
    unlabelled badge sets the level, falling back to ``##`` when there is none.
    """
    levels = []
    for index, token in enumerate(tokens):
        if token.type != "heading_open":
            continue
        inline = tokens[index + 1] if index + 1 < len(tokens) else None
        level = int(token.tag[1]) if token.tag.startswith("h") else 0
        name = _heading_text(inline)
        if level < 2 or not name:
            continue
        if name.strip().lower() in SKIPPED_SECTIONS:
            continue
        levels.append(level)
    return min(levels) if levels else 2


def _heading_text(inline: Token | None) -> str:
    """Return a heading's own text, with badges and trailing links dropped.

    A heading whose whole content is one link (``## [git-extras](url)``) has no
    text of its own, so the link's text becomes the name instead of nothing.
    """
    if inline is None:
        return ""
    children = list(inline.children or [])
    parts: list[str] = []
    index = 0
    while index < len(children):
        child = children[index]
        if child.type in {"image", "html_inline"}:
            break
        if child.type == "link_open":
            if parts:
                break
            index += 1
            while index < len(children) and children[index].type != "link_close":
                if children[index].type in {"text", "code_inline"}:
                    parts.append(children[index].content)
                index += 1
            break
        if child.type in {"text", "code_inline"}:
            parts.append(child.content)
        index += 1
    return "".join(parts).strip()


def _strip_leading_separator(text: str) -> str:
    remainder = text.lstrip()
    while remainder[:1] in {"-", "\u2013", "\u2014", ":"}:
        remainder = remainder[1:].lstrip()
    return remainder


def _line_of(token: Token) -> int:
    if token.map:
        return int(token.map[0]) + 1
    return 0
