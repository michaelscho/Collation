
import argparse
import re
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth
import config

def find_collation_files(book, chapter_range=None):
    """
    Find final HTML collation tables for a book and optional chapter range.

    Searches output/final/BOOK/ for files matching the naming convention
    used by collations.xqm. Files are sorted by chapter number and filename.

    If no chapter range is specified, all matching files are selected.

    Args:
        book: Book number.
        chapter_range: Optional tuple (chapter_min, chapter_max).

    Returns:
        list: Paths to the matching final HTML files.
    """

    final_dir = (
        Path(__file__).resolve().parent
        / "output"
        / "final"
        / f"{book:02d}"
    )

    if not final_dir.is_dir():
        print(f"ERROR: Directory not found: {final_dir}")
        return []

    # Match the filename convention used by collations.xqm
    pattern = re.compile(
        rf"([A-Za-z]+(?:_[A-Za-z]+)*)_{book:02d}_chapter_(\d+)_final\.html"
    )

    files = []

    for file_path in final_dir.iterdir():
        if not file_path.is_file():
            continue

        match = pattern.fullmatch(file_path.name)

        if not match:
            continue

        chapter = int(match.group(2))

        if chapter_range is not None:
            chapter_min, chapter_max = chapter_range

            if not chapter_min <= chapter <= chapter_max:
                continue

        files.append((chapter, file_path))

    # Sort by chapter number and filename
    files.sort(key=lambda item: (item[0], item[1].name))

    return [file_path for chapter, file_path in files]


def upload_collation(file_path):
    """
    Upload a final HTML collation table to eXist-db via WebDAV.

    Uses the destination URL and credentials defined in config.py.
    The file is uploaded via HTTP PUT. Existing files with the same
    name may be overwritten without confirmation.

    Args:
        file_path: Path to the final HTML file.

    Returns:
        bool: True if the upload succeeds, False otherwise.
    """

    upload_url = (
        config.collations_upload_url.rstrip("/")
        + "/"
        + file_path.name
    )

    print(f"Uploading: {file_path.name}", flush=True)

    try:
        with file_path.open("rb") as file:
            response = requests.put(
                upload_url,
                data=file,
                auth=HTTPBasicAuth(
                    config.user_exist,
                    config.pw_exist
                ),
                headers={"Content-Type": "text/html; charset=utf-8"},
                timeout=120
            )

        response.raise_for_status()

    except (requests.RequestException, OSError) as error:
        print(f"  ERROR: Upload failed: {error}")
        return False

    print(f"  Upload successful. HTTP {response.status_code}")
    return True

def main():
    """
    Execute the collation table upload workflow.

    Parses command-line arguments to select a book, a single
    chapter, a chapter range, or all available tables.

    Finds the corresponding final HTML files, uploads them to
    eXist-db, and displays a summary of successful and failed uploads.

    Exits with status code 1 if no files are found or any upload fails.
    """
    parser = argparse.ArgumentParser(
        description="Upload final collation tables to eXist-db."
    )

    parser.add_argument(
        "book",
        type=int,
        help="Book number"
    )

    parser.add_argument(
        "chapters",
        nargs="?",
        help="Chapter number or range, e.g. 5 or 100-104"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Upload all final HTML tables for the selected book"
    )

    args = parser.parse_args()

    # Validate arguments
    if args.book < 1:
        parser.error("Book number must be positive.")

    if args.all and args.chapters:
        parser.error("Specify either a chapter range or --all, not both.")

    if not args.all and not args.chapters:
        parser.error("Specify a chapter number, a range, or --all.")

    chapter_range = None

    if not args.all:
        match = re.fullmatch(r"(\d+)(?:-(\d+))?", args.chapters)

        if not match:
            parser.error("Invalid chapter range. Use e.g. 5 or 100-104.")

        chapter_min = int(match.group(1))
        chapter_max = int(match.group(2) or match.group(1))

        if chapter_min > chapter_max:
            parser.error("The starting chapter cannot exceed the ending chapter.")

        chapter_range = (chapter_min, chapter_max)

    # Find matching files
    files = find_collation_files(args.book, chapter_range)

    if not files:
        print("No matching final HTML files found.")
        raise SystemExit(1)

    print("\n" + "=" * 40)
    print(f"UPLOAD COLLATIONS - BOOK {args.book:02d}")
    print("=" * 40)
    print(f"Files found: {len(files)}")
    print()

    # Upload files
    successful = 0
    failed = 0

    for index, file_path in enumerate(files, start=1):
        print(f"[{index}/{len(files)}]", end=" ")

        if upload_collation(file_path):
            successful += 1
        else:
            failed += 1

        print()

    # Final summary
    print("=" * 40)
    print("UPLOAD COMPLETED")
    print("=" * 40)
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
