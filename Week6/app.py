import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from functools import wraps

from flask import Flask, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-only-change-this-secret")
ACCESS_TOKEN_TTL = 15 * 60       
REFRESH_TOKEN_TTL = 7 * 24 * 60 * 60  

users = {
    "ABC123": {
        "id": 10,
        "password_hash": generate_password_hash("abc123"),
        "scopes": ["posts:read"],
    },
    "DEF456": {
        "id": 11,
        "password_hash": generate_password_hash("def456"),
        "scopes": [],
    },
}

posts = {
    123: {
        "id": 123,
        "user_id": 10,
        "content": "Hello everyone!",
        "created_at": "2026-10-31T10:00:00Z",
        "visibility": "public",
    },
    124: {
        "id": 124,
        "user_id": 11,
        "content": "This is Alice's private post.",
        "created_at": "2026-10-31T11:00:00Z",
        "visibility": "private",
    },
}

refresh_tokens = {}

def error_response(status, code, message):
    return jsonify({"error": code, "message": message}), status

def b64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

def b64url_decode(data):
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)

def create_access_token(user, scopes):
    """Create a minimal HS256 JWT using Python's standard library."""
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user["id"]),
        "username": next(
            username for username, value in users.items()
            if value["id"] == user["id"]
        ),
        "scope": " ".join(scopes),
        "iat": now,
        "exp": now + ACCESS_TOKEN_TTL,
        "iss": "social-network-api",
        "aud": "social-network-client",
    }

    encoded_header = b64url_encode(
        json.dumps(header, separators=(",", ":")).encode("utf-8")
    )
    encoded_payload = b64url_encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    )
    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    signature = hmac.new(
        JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256
    ).digest()

    return f"{encoded_header}.{encoded_payload}.{b64url_encode(signature)}"

def decode_access_token(token):
    """Validate JWT signature, algorithm, issuer, audience and expiration."""
    try:
        header_part, payload_part, signature_part = token.split(".")
        signing_input = f"{header_part}.{payload_part}".encode("ascii")
        expected_signature = hmac.new(
            JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256
        ).digest()

        supplied_signature = b64url_decode(signature_part)
        if not hmac.compare_digest(expected_signature, supplied_signature):
            return None

        header = json.loads(b64url_decode(header_part))
        payload = json.loads(b64url_decode(payload_part))

        if header.get("alg") != "HS256":
            return None
        if payload.get("iss") != "social-network-api":
            return None
        if payload.get("aud") != "social-network-client":
            return None
        if int(payload.get("exp", 0)) <= int(time.time()):
            return None

        return payload
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return None

def issue_refresh_token(user_id, scopes):
    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    refresh_tokens[token_hash] = {
        "user_id": user_id,
        "scopes": list(scopes),
        "expires_at": int(time.time()) + REFRESH_TOKEN_TTL,
        "used": False,
    }
    return raw_token

def token_response(user, scopes):
    access_token = create_access_token(user, scopes)
    refresh_token = issue_refresh_token(user["id"], scopes)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_TTL,
        "scope": " ".join(scopes),
    }

def require_access_token(required_scope=None):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            parts = auth_header.split()

            if len(parts) != 2 or parts[0].lower() != "bearer":
                return error_response(
                    401, "unauthorized", "Access token is required."
                )

            payload = decode_access_token(parts[1])
            if payload is None:
                return error_response(
                    401, "invalid_token",
                    "Access token is invalid or has expired."
                )

            if required_scope:
                scopes = payload.get("scope", "").split()
                if required_scope not in scopes:
                    return error_response(
                        403, "insufficient_scope",
                        f"You need {required_scope} permission to access this resource."
                    )

            request.current_user_id = int(payload["sub"])
            request.current_scopes = payload.get("scope", "").split()
            return view(*args, **kwargs)

        return wrapped
    return decorator

@app.post("/api/v1/auth/login")
def login():
    data = request.form

    grant_type = data.get("grant_type")
    username = data.get("username")
    password = data.get("password")

    if not username:
        return error_response(400, "invalid_request", "Username is required.")
    if not password:
        return error_response(400, "invalid_request", "Password is required.")
    if grant_type != "password":
        return error_response(
            400, "unsupported_grant_type",
            "Grant type must be password."
        )

    user = users.get(username)
    if user is None or not check_password_hash(user["password_hash"], password):
        return error_response(
            401, "invalid_credentials", "Invalid username or password."
        )

    requested_scopes = data.get("scope", "").split()
    granted_scopes = [
        scope for scope in requested_scopes if scope in user["scopes"]
    ]

    return jsonify(token_response(user, granted_scopes)), 200

@app.post("/api/v1/auth/refresh")
def refresh():
    data = request.form

    if not data.get("refresh_token"):
        return error_response(
            400, "invalid_request", "Refresh token is required."
        )
    if data.get("grant_type") != "refresh_token":
        return error_response(
            400, "unsupported_grant_type",
            "Grant type must be refresh_token."
        )

    raw_token = data["refresh_token"]
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    record = refresh_tokens.get(token_hash)

    if (
        record is None
        or record["used"]
        or record["expires_at"] <= int(time.time())
    ):
        return error_response(
            401, "invalid_token",
            "Refresh token is invalid, expired or has been revoked."
        )

    record["used"] = True
    user = next(
        (value for value in users.values()
         if value["id"] == record["user_id"]),
        None,
    )
    if user is None:
        return error_response(401, "invalid_token", "User no longer exists.")

    return jsonify(token_response(user, record["scopes"])), 200

@app.get("/api/v1/posts/<post_id>")
@require_access_token(required_scope="posts:read")
def get_post(post_id):
    try:
        numeric_id = int(post_id)
        if numeric_id <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return error_response(
            400, "invalid_parameter",
            "Post ID must be a positive integer."
        )

    post = posts.get(numeric_id)
    if post is None:
        return error_response(
            404, "not_found", "The requested post does not exist."
        )

    if (
        post["visibility"] == "private"
        and post["user_id"] != request.current_user_id
    ):
        return error_response(
            403, "forbidden",
            "You do not have permission to view this post."
        )

    response_body = {
        "id": post["id"],
        "user_id": post["user_id"],
        "content": post["content"],
        "created_at": post["created_at"],
    }
    return jsonify(response_body), 200

@app.get("/api/v1/health")
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)