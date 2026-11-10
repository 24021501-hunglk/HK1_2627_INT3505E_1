from flask import Blueprint, jsonify
from sqlalchemy import text

from app.extensions import db

health_bp = Blueprint("health", __name__)

@health_bp.get("/healthz")
def liveness():
    return jsonify({
        "status": "alive"
    }), 200

@health_bp.get("/ready")
def readiness():
    try:
        db.session.execute(text("SELECT 1"))

        return jsonify({
            "status": "ready",
            "database": "connected"
        }), 200

    except Exception:
        db.session.rollback()

        return jsonify({
            "status": "not_ready",
            "database": "disconnected"
        }), 503