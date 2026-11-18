from flask import Blueprint
from .users_data import get_user
bp = Blueprint("v2", __name__, url_prefix="/users")

@bp.route("/<int:uid>")
def get(uid):
    u = get_user(uid)
    if not u:
        return {"error": "nf"}, 404
    return {
        "id": uid,
        "first_name": u["f"],
        "last_name": u["l"],
        "email": u["email"]
 }
