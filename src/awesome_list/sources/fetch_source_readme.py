"""Fetch upstream list readmes over HTTPS, and fail soft when they are down."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from urllib.error import URLError
from urllib.request import Request, urlopen

TIMEOUT_SECONDS = 20
USER_AGENT = (
    "awesome-list-template/0.1 (+https://github.com/olitreadwell/awesome-list-template)"
)


class SourceFetchError(RuntimeError):
    """Raised when an upstream readme cannot be read."""


def fetch_readme(url: str) -> str:
    """Return the text at this URL, raising SourceFetchError on any failure."""
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body: bytes = response.read()
            return body.decode("utf-8", errors="replace")
    except (URLError, OSError, TimeoutError) as error:
        raise SourceFetchError(f"{url}: {error}") from error


def fetch_source_readmes(
    urls: Iterable[str], *, fetch: Callable[[str], str] = fetch_readme
) -> tuple[dict[str, str], tuple[str, ...]]:
    """Return the readme per URL, plus the URLs that could not be read.

    One unreachable source must not stop the others: a report built from three
    of four lists still tells a maintainer something.
    """
    readmes: dict[str, str] = {}
    unread: list[str] = []
    for url in urls:
        try:
            readmes[url] = fetch(url)
        except (SourceFetchError, OSError):
            unread.append(url)
    return readmes, tuple(unread)
