import os

from werkzeug.utils import secure_filename

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


def validate_image_file(file):
    if not file or not file.filename:
        return None, None
    original = secure_filename(file.filename)
    ext = os.path.splitext(original)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return None, "Image must be JPG, JPEG, PNG, or WEBP."
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_IMAGE_BYTES:
        return None, "Image file must be 5MB or smaller."
    return original, None


def save_image_file(file, upload_dir, stored_name):
    original, error = validate_image_file(file)
    if error:
        return None, error
    if not original:
        return None, None

    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, stored_name)
    file.save(file_path)
    return stored_name, None


def save_entity_image(file, upload_dir, entity_id, public_url_prefix):
    """
    Validate and save an image as {entity_id}_{filename}.
    Returns (public_url_path, error_message).
    """
    original, error = validate_image_file(file)
    if error:
        return None, error
    if not original:
        return None, "File is required."

    stored_name = f"{entity_id}_{original}"
    _, error = save_image_file(file, upload_dir, stored_name)
    if error:
        return None, error
    return f"{public_url_prefix}/{stored_name}", None
