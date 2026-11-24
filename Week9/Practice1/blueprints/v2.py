from flask import Blueprint, request, url_for
from .users_data import get_user, create_user, email_exists

bp = Blueprint("v2", __name__, url_prefix="/users")


@bp.route("/<int:uid>", methods=["GET"])
def get(uid):
    u = get_user(uid)

    if not u:
        return {"error": "nf"}, 404

    return {
        "id": uid,
        "first_name": u["first_name"],
        "last_name": u["last_name"],
        "email": u["email"]
    }, 200
    
@bp.route("", methods=["POST"])
def post():
    if not request.is_json:
        return {
            "error": "unsupported_media_type",
            "message": "Content-Type must be application/json"
        }, 415

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {
            "error": "bad_request",
            "message": "Invalid JSON body"
        }, 400

    required_fields = ["first_name", "last_name", "email"]

    for field in required_fields:
        value = data.get(field)

        if not isinstance(value, str) or not value.strip():
            return {
                "error": "bad_request",
                "message": f"{field} is required"
            }, 400

    first_name = data["first_name"].strip()
    last_name = data["last_name"].strip()
    email = data["email"].strip()

    if email_exists(email):
        return {
            "error": "conflict",
            "message": "Email already exists"
        }, 409

    user = create_user(first_name, last_name, email)

    return user, 201, {
        "Location": url_for("v2.get", uid=user["id"])
    }