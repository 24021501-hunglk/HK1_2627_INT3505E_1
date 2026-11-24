from datetime import datetime, timezone
from email.utils import format_datetime
from functools import wraps
from flask import request, jsonify, make_response
import logging

log = logging.getLogger("sunset")


def http_date(dt):
    return format_datetime(dt, usegmt=True)


def deprecate_at(sunset_date, replacement=None):
    def wrap(fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            now = datetime.now(timezone.utc)

            log.warning(
                "deprecated_call %s %s",
                request.path,
                request.remote_addr
            )

            if now >= sunset_date:
                response = make_response(jsonify({
                    "error": "gone",
                    "sunset": http_date(sunset_date),
                    "use_instead": replacement
                }), 410)
            else:
                result = fn(*args, **kwargs)
                response = make_response(result)

            response.headers["Sunset"] = http_date(sunset_date)
            response.headers["Deprecation"] = "true"

            if replacement:
                response.headers["Link"] = (
                    f'<{replacement}>; rel="successor-version"'
                )

            return response

        return inner

    return wrap