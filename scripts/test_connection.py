"""Quick AX7 connection checks against a running API."""
import json
import sys
import urllib.error
import urllib.request
import uuid

BASE = "http://127.0.0.1:5000"


def request(method, path, data=None, headers=None, origin=None):
    hdrs = dict(headers or {})
    if origin:
        hdrs["Origin"] = origin
    body = None
    if data is not None:
        if isinstance(data, bytes):
            body = data
        else:
            body = json.dumps(data).encode()
            hdrs.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(BASE + path, data=body, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read()


def main() -> int:
    ok = True

    code, _, body = request("GET", "/api/jobs")
    print(f"1. GET /api/jobs -> {code}")
    ok &= code == 200 and b"jobs" in body

    code, _, login_body = request(
        "POST",
        "/api/auth/login",
        {"email": "demo.seeker@hirehub.test", "password": "demo1234"},
    )
    print(f"2. POST /api/auth/login -> {code}")
    ok &= code == 200
    token = json.loads(login_body.decode())["access_token"]

    code, _, prof_body = request(
        "GET",
        "/api/auth/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    print(f"   GET /api/auth/profile -> {code}")
    ok &= code == 200 and b"user" in prof_body

    code, _, _ = request("GET", "/api/auth/profile")
    print(f"3. GET /api/auth/profile (no token) -> {code}")
    ok &= code == 401

    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    boundary = "----Boundary" + uuid.uuid4().hex
    multipart = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="avatar"; '
        f'filename="test.png"\r\nContent-Type: image/png\r\n\r\n'
    ).encode() + png + f"\r\n--{boundary}--\r\n".encode()
    code, _, upload_body = request(
        "POST",
        "/api/me/avatar",
        data=multipart,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    print(f"4. POST /api/me/avatar -> {code}")
    if code == 200:
        avatar_url = json.loads(upload_body.decode()).get("user", {}).get("avatar_url")
        print(f"   avatar_url={avatar_url}")
        ok &= bool(avatar_url)
    else:
        print(f"   body={upload_body.decode()[:200]}")
        ok = False

    code, hdrs, _ = request(
        "OPTIONS",
        "/api/jobs",
        origin="http://localhost:3000",
        headers={
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization,Content-Type",
        },
    )
    allow_origin = hdrs.get("Access-Control-Allow-Origin") or hdrs.get(
        "access-control-allow-origin"
    )
    print(f"5. CORS preflight -> {code}, Allow-Origin={allow_origin}")
    ok &= code == 200 and allow_origin == "http://localhost:3000"

    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
