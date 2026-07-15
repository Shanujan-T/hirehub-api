import csv
import io

from flask import Response


def rows_to_csv_response(filename, headers, rows):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    data = buffer.getvalue()
    return Response(
        data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def parse_csv_file(file_storage, required_columns):
    if not file_storage:
        return [], ["file is required."]

    try:
        raw = file_storage.read()
        if isinstance(raw, bytes):
            text = raw.decode("utf-8-sig")
        else:
            text = str(raw)
    except Exception:
        return [], ["Unable to read uploaded file as UTF-8."]

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return [], ["CSV header row is missing."]

    normalized = {h.strip().lower(): h for h in reader.fieldnames if h}
    missing = [c for c in required_columns if c.lower() not in normalized]
    if missing:
        return [], [f"Missing required column(s): {', '.join(missing)}."]

    rows = []
    for row in reader:
        cleaned = {}
        for key, value in row.items():
            if key is None:
                continue
            cleaned[key.strip().lower()] = (value or "").strip() if isinstance(value, str) else value
        rows.append(cleaned)
    return rows, []
