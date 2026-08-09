#!/usr/bin/env python3
"""Build BookStack Portable ZIP imports from docs/bookstack markdown."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_MANIFEST = ROOT / "manifest.json"
DEFAULT_OUTPUT = ROOT / "dist"


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def page_title(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            return match.group(1).strip()
    return fallback


def build_page(page_id: int, path: Path, priority: int) -> dict:
    markdown = path.read_text(encoding="utf-8")
    name = page_title(markdown, path.stem.replace("-", " ").title())
    return {
        "id": page_id,
        "name": name,
        "markdown": markdown,
        "priority": priority,
    }


def build_book(book: dict, docs_root: Path) -> dict:
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
            pages.append(build_page(next_id, page_path, page_priority))
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
        book_pages.append(build_page(next_id, page_path, page_priority))
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
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    instance_id = "engstrom-home-ops"
    selected = set(args.books or [])
    built = 0

    for book in manifest["books"]:
        book_dir = book["dir"]
        if selected and book_dir not in selected:
            continue
        book_data = build_book(book, ROOT)
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
