import os
import uuid
from datetime import datetime, date

from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, current_app, abort)
from flask_login import login_required, current_user
from PIL import Image, UnidentifiedImageError
from sqlalchemy import or_

from app import db
from app.models import Item, User

bp = Blueprint("items", __name__)

CATEGORIES = ["Bag", "Bottle", "ID Card", "Phone", "Electronics",
              "Books", "Keys", "Wallet", "Clothing", "Other"]
ALLOWED_EXT = {"png", "jpg", "jpeg"}


def save_image(file):
    """Validate and save an uploaded photo. Returns the saved file name,
    or None if no file was chosen. Raises ValueError for bad files."""
    if not file or not file.filename:
        return None

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXT:
        raise ValueError("Only PNG, JPG and JPEG images are allowed.")

    try:
        Image.open(file.stream).verify()   # checks it is a real image
    except (UnidentifiedImageError, OSError):
        raise ValueError("The uploaded file is not a valid image.")
    file.stream.seek(0)

    name = f"{uuid.uuid4().hex}.{ext}"
    folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    file.save(os.path.join(folder, name))
    return name


@bp.app_errorhandler(413)
def file_too_large(e):
    flash("The image is too large. Maximum size is 5 MB.", "danger")
    return redirect(url_for("items.list_items"))


@bp.route("/report/<kind>", methods=["GET", "POST"])
@login_required
def report(kind):
    if kind not in ("lost", "found"):
        abort(404)

    today = date.today().isoformat()

    def show_form(form):
        return render_template("report.html", kind=kind, categories=CATEGORIES,
                               form=form, today=today)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "")
        location = request.form.get("location", "").strip()
        date_str = request.form.get("date", "")

        if not title or not location or not date_str or category not in CATEGORIES:
            flash("Please fill in title, category, location and date.", "danger")
            return show_form(request.form)

        try:
            item_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Enter a valid date.", "danger")
            return show_form(request.form)

        if item_date > date.today():
            flash("The date cannot be in the future.", "danger")
            return show_form(request.form)

        try:
            filename = save_image(request.files.get("image"))
        except ValueError as err:
            flash(str(err), "danger")
            return show_form(request.form)

        item = Item(kind=kind, title=title, description=description,
                    category=category, location=location, date=item_date,
                    image_path=filename, user_id=current_user.id)
        db.session.add(item)
        db.session.commit()
        flash(f"Your {kind} item was reported successfully.", "success")
        return redirect(url_for("items.item_detail", item_id=item.id))

    return show_form({})


@bp.route("/items")
def list_items():
    q = request.args.get("q", "").strip()
    kind = request.args.get("kind", "")
    category = request.args.get("category", "")

    query = Item.query
    if kind in ("lost", "found"):
        query = query.filter_by(kind=kind)
    if category in CATEGORIES:
        query = query.filter_by(category=category)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Item.title.ilike(like),
                                 Item.description.ilike(like),
                                 Item.location.ilike(like)))

    items = query.order_by(Item.created_at.desc()).all()
    return render_template("items.html", items=items, categories=CATEGORIES,
                           q=q, kind=kind, category=category)


@bp.route("/item/<int:item_id>")
@login_required
def item_detail(item_id):
    item = db.session.get(Item, item_id)
    if item is None:
        abort(404)
    reporter = db.session.get(User, item.user_id)
    return render_template("item_detail.html", item=item, reporter=reporter)


@bp.route("/my-items")
@login_required
def my_items():
    items = (Item.query.filter_by(user_id=current_user.id)
             .order_by(Item.created_at.desc()).all())
    return render_template("my_items.html", items=items)


@bp.route("/item/<int:item_id>/delete", methods=["POST"])
@login_required
def delete_item(item_id):
    item = db.session.get(Item, item_id)
    if item is None:
        abort(404)
    if item.user_id != current_user.id and current_user.role != "admin":
        abort(403)

    if item.image_path:
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], item.image_path)
        if os.path.exists(path):
            os.remove(path)

    db.session.delete(item)
    db.session.commit()
    flash("Item deleted.", "success")
    return redirect(url_for("items.my_items"))