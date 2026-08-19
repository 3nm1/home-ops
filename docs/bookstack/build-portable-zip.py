#!/usr/bin/env python3
"""Build BookStack Portable ZIP imports from docs/bookstack markdown."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_MANIFEST = ROOT / "manifest.json"
DEFAULT_OUTPUT = ROOT / "dist"

H1_LINE = re.compile(r"^#\s+(.+?)\s*$")
MD_LINK = re.compile(r"(\[[^\]]*\])\(([^)]+)\)")


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def page_title(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        match = H1_LINE.match(line)
        if match:
            return match.group(1).strip()
    return fallback


def strip_leading_h1(markdown: str) -> str:
    """Remove the first H1 line; BookStack uses it as the page name separately."""
    lines = markdown.splitlines(keepends=True)
    index = 0
    while index < len(lines) and not lines[index].strip():
        index += 1
    if index >= len(lines) or not H1_LINE.match(lines[index].rstrip("\r\n")):
        return markdown
    index += 1
    while index < len(lines) and not lines[index].strip():
        index += 1
    return "".join(lines[index:])


def bookstack_page_slug(title: str) -> str:
    """Approximate BookStack page slug from the H1 title (same as imported page name)."""
    table = str.maketrans(
        {"å": "a", "ä": "a", "ö": "o", "Å": "a", "Ä": "a", "Ö": "o"}
    )
    slug = title.translate(table).lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug).strip("-")
    return slug


def bookstack_book_slug(book_dir: str, book: dict, config: dict) -> str:
    if slug := book.get("slug"):
        return slug
    prefix = config.get("book_dir_prefix", "book-")
    replacement = config.get("book_slug_prefix", "bok-")
    if book_dir.startswith(prefix):
        return replacement + book_dir[len(prefix) :]
    return book_dir


def iter_page_filenames(book: dict) -> list[str]:
    filenames: list[str] = []
    for chapter in book.get("chapters", []):
        filenames.extend(chapter.get("pages", []))
    filenames.extend(book.get("pages", []))
    return filenames


@dataclass(frozen=True)
class PageRef:
    book_dir: str
    filename: str


@dataclass
class LinkContext:
    base_url: str
    book_slugs: dict[str, str]
    page_slugs: dict[PageRef, str]
    docs_root: Path

    @classmethod
    def from_manifest(cls, manifest: dict, docs_root: Path) -> LinkContext:
        config = manifest.get("bookstack", {})
        base_url = config.get("base_url", "https://bookstack.engstrom.live").rstrip("/")
        book_slugs: dict[str, str] = {}
        page_slugs: dict[PageRef, str] = {}

        for book in manifest["books"]:
            book_dir = book["dir"]
            book_slugs[book_dir] = bookstack_book_slug(book_dir, book, config)
            for filename in iter_page_filenames(book):
                page_path = docs_root / book_dir / filename
                raw = page_path.read_text(encoding="utf-8")
                title = page_title(raw, page_path.stem.replace("-", " ").title())
                page_slugs[PageRef(book_dir, filename)] = bookstack_page_slug(title)

        return cls(base_url, book_slugs, page_slugs, docs_root)

    def bookstack_url(self, ref: PageRef, anchor: str = "") -> str | None:
        book_slug = self.book_slugs.get(ref.book_dir)
        page_slug = self.page_slugs.get(ref)
        if not book_slug or not page_slug:
            return None
        url = f"{self.base_url}/books/{book_slug}/page/{page_slug}"
        if anchor:
            url += f"#{anchor}"
        return url


def resolve_markdown_link(source_page: Path, target: str, docs_root: Path) -> tuple[Path, str] | None:
    target_path, _, anchor = target.partition("#")
    if not target_path or not target_path.endswith(".md"):
        return None
    if target_path.startswith(("http://", "https://", "mailto:")):
        return None

    resolved = (source_page.parent / target_path).resolve()
    docs_root = docs_root.resolve()
    if docs_root not in resolved.parents and resolved != docs_root:
        return None
    if not resolved.is_file():
        return None
    return resolved, anchor


def rewrite_bookstack_links(markdown: str, source_page: Path, links: LinkContext) -> str:
    def replace(match: re.Match[str]) -> str:
        text, target = match.group(1), match.group(2)
        resolved = resolve_markdown_link(source_page, target, links.docs_root)
        if not resolved:
            return match.group(0)

        path, anchor = resolved
        ref = PageRef(path.parent.name, path.name)
        url = links.bookstack_url(ref, anchor)
        if not url:
            return match.group(0)
        return f"{text}({url})"

    return MD_LINK.sub(replace, markdown)


def build_page(
    page_id: int,
    path: Path,
    priority: int,
    links: LinkContext | None,
) -> dict:
    raw = path.read_text(encoding="utf-8")
    name = page_title(raw, path.stem.replace("-", " ").title())
    body = strip_leading_h1(raw)
    if links is not None:
        body = rewrite_bookstack_links(body, path, links)
    return {
        "id": page_id,
        "name": name,
        "markdown": body,
        "priority": priority,
    }


def build_book(book: dict, docs_root: Path, links: LinkContext | None) -> dict:
    book_dir = docs_root / book["dir"]
    if not book_dir.is_dir():
        raise FileNotFoundError(f"Book directory not found: {book_dir}")

    next_id = 1
    chapter_priority = 1
    chapters = []

    for chapter in book.get("chapters", []):
        page_priority = 1
        pages = []
        for filename in chapter.get("pages", []):
            page_path = book_dir / filename
            if not page_path.is_file():
                raise FileNotFoundError(f"Page not found: {page_path}")
            pages.append(build_page(next_id, page_path, page_priority, links))
            next_id += 1
            page_priority += 1
        chapters.append(
            {
                "id": next_id,
                "name": chapter["name"],
                "priority": chapter_priority,
                "pages": pages,
            }
        )
        next_id += 1
        chapter_priority += 1

    book_pages = []
    page_priority = 1
    for filename in book.get("pages", []):
        page_path = book_dir / filename
        if not page_path.is_file():
            raise FileNotFoundError(f"Page not found: {page_path}")
        book_pages.append(build_page(next_id, page_path, page_priority, links))
        next_id += 1
        page_priority += 1

    payload = {
        "id": 1,
        "name": book["name"],
        "chapters": chapters,
    }
    if book_pages:
        payload["pages"] = book_pages
    return payload


def write_zip(output_path: Path, book_data: dict, instance_id: str) -> None:
    export = {
        "instance": {
            "id": instance_id,
            "version": "home-ops-docs",
        },
        "exported_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "book": book_data,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("data.json", json.dumps(export, ensure_ascii=False, indent=2))
        zf.writestr("files/.keep", "")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build BookStack Portable ZIP files from docs/bookstack markdown."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Path to manifest.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output directory for ZIP files",
    )
    parser.add_argument(
        "--book",
        action="append",
        dest="books",
        metavar="DIR",
        help="Only build selected book dir(s), e.g. book-06-familj",
    )
    parser.add_argument(
        "--no-link-rewrite",
        action="store_true",
        help="Keep relative .md links (for debugging)",
    )
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    links = None if args.no_link_rewrite else LinkContext.from_manifest(manifest, ROOT)
    instance_id = "engstrom-home-ops"
    selected = set(args.books or [])
    built = 0

    for book in manifest["books"]:
        book_dir = book["dir"]
        if selected and book_dir not in selected:
            continue
        book_data = build_book(book, ROOT, links)
        zip_name = f"{book_dir}.zip"
        output_path = args.output / zip_name
        write_zip(output_path, book_data, instance_id)
        page_count = sum(len(ch.get("pages", [])) for ch in book_data["chapters"])
        page_count += len(book_data.get("pages", []))
        print(f"Wrote {output_path} ({page_count} pages)")
        built += 1

    if built == 0:
        print("No books built. Check --book filters.", file=sys.stderr)
        return 1
    print(f"\nImport in BookStack: Settings -> Import -> upload ZIP from {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
