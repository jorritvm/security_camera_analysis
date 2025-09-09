import os
from pathlib import Path
from datetime import date, datetime, timedelta


from flask import Flask, render_template, request, url_for, send_file, abort

from app_helpers import *
from config import BASE_DIR, ALLOWED_PER_PAGE, WEBSERVER_PORT

app = Flask(__name__)




# -------------------------
# Routes
# -------------------------
@app.route("/")
def gallery():
    # Sanitize query params
    q_date: date = parse_date(request.args.get("date"))
    per_page: int = parse_per_page(request.args.get("per_page"))
    page: int = parse_page(request.args.get("page"))
    img_filter: str = parse_filter(request.args.get("filter"))

    # Gather and paginate
    images = list_images_for_day(q_date, image_filter=img_filter)
    page_items, total, total_pages = paginate(images, page, per_page)

    # Prev/Next day
    prev_date = q_date - timedelta(days=1)
    next_date = q_date + timedelta(days=1)

    return render_template(
        "gallery.html",
        images=page_items,
        total=total,
        page=page,
        total_pages=total_pages,
        per_page=per_page,
        allowed_per_page=ALLOWED_PER_PAGE,
        img_filter=img_filter,
        date_str=f"{q_date:%Y-%m-%d}",
        prev_date=f"{prev_date:%Y-%m-%d}",
        next_date=f"{next_date:%Y-%m-%d}",
        base_dir=str(BASE_DIR),
    )


@app.route("/img/<year>/<month>/<day>/<file_name>")
def serve_image(year, month, day, file_name):
    print("serve_image", year, month, day, file_name)
    """Safely serve images from BASE_DIR"""
    file_path = os.path.join(BASE_DIR, year, month, day, file_name)
    print(file_path)

    if not os.path.isfile(file_path):
        abort(404)

    return send_file(file_path)


if __name__ == "__main__":
    # Run development server
    app.run(host="0.0.0.0", port=WEBSERVER_PORT, debug=True)
