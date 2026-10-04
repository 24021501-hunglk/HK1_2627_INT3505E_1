from flask import jsonify, request
import uuid

ERROR_BASE = "http://localhost:5000/probs"

class ApiProblem(Exception):
    def __init__(self, status, title, detail=None, type_path=None, **extra):
        self.status = status
        self.title = title
        self.detail = detail

        if type_path:
            self.type = f"{ERROR_BASE}/{type_path}"
        else:
            self.type = "about:blank"

        self.extra = extra


def problem(status, title, detail=None, type_path=None, **extra):
    body = {
        "type": (
            f"{ERROR_BASE}/{type_path}"
            if type_path
            else "about:blank"
        ),
        "title": title,
        "status": status,
        "instance": request.path,
        "trace_id": str(uuid.uuid4())
    }

    if detail:
        body["detail"] = detail

    body.update(extra)

    response = jsonify(body)
    response.status_code = status
    response.headers["Content-Type"] = "application/problem+json"

    return response