import os
from datetime import date, datetime
from config import ALLOWED_PER_PAGE, BASE_DIR, DEFAULT_PAGE_SIZE

def parse_date(s: str | None) -> date:
    """return date object from 'YYYY-MM-DD' string; default to today on error or if None/empty"""
    if not s:
        return datetime.now().date()
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return datetime.now().date()

def parse_per_page(value: str | None) -> int:
    """return per_page as int if in ALLOWED_PER_PAGE; default to DEFAULT_PAGE_SIZE on error or if None/empty"""
    try:
        v = int(value) if value else 30
    except ValueError:
        v = DEFAULT_PAGE_SIZE
    return v if v in ALLOWED_PER_PAGE else 30

def parse_page(value: str | None) -> int:
    """return page as int > 0; default to 1 on error or if None/empty"""
    try:
        v = int(value) if value else 1
    except ValueError:
        v = 1
    return v if v > 0 else 1

def parse_filter(value: str | None) -> str:
    """return filter as "boxed" or "all"; default to "boxed" on error or if None/empty"""
    # default = "boxed"
    return "all" if value == "all" else "boxed"

def list_images_for_day(day: date, image_filter: str) -> list[dict]:
    """
    Given a date, find images in BASE_DIR/YYYY/MM/DD (if present).
    Returns a list of dicts containing file details
    Filtering: .jpg files (case-insensitive); if image_filter = "boxed", only names with '_boxed' before extension.
    Sorted descending by filename (newest-looking names first).
    """
    year = day.strftime("%Y")
    month = day.strftime("%m")
    day = day.strftime("%d")
    day_dir = os.path.join(BASE_DIR, year, month, day)

    if not os.path.exists(day_dir) or not os.path.isdir(day_dir):
        return []

    results: list[str] = []
    for file_name in os.listdir(day_dir):
        file_path = os.path.join(day_dir, file_name)
        if not os.path.isfile(file_path):
            continue

        if not file_name.lower().endswith(".jpg"):
            continue

        if image_filter == "boxed" and not "boxed" in file_name:
            continue

        stat = os.stat(file_path)
        image_details = {
            "name": file_name,
            "year": year,
            "month": month,
            "day": day,
            "file_size_kb": stat.st_size // 1024,
            "mtime_str": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")}
        results.append(image_details)

    # Sort by filename descending (typical camera names embed timestamps)
    results = results[::-1]
    return results


def paginate(items: list, page: int, per_page: int):
    """Paginate a list of items. Returns (page_items, total_items, total_pages)."""
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    page_items = items[start:end]
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 1
    return page_items, total, total_pages
