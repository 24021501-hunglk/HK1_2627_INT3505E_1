from datetime import date
from functools import wraps
from pathlib import Path

import yaml
from flask import Flask, jsonify, request, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Load the OpenAPI specification from the YAML file.
SPEC_PATH = Path(__file__).parent / "openapi.yaml"

with open(SPEC_PATH, "r", encoding="utf-8") as file:
    OPENAPI_SPEC = yaml.safe_load(file)

TASKS = [
    {
        "id": 1,
        "title": "Complete API",
        "status": "in_progress",
        "priority": "high",
        "dueDate": "2026-10-15",
        "assigneeId": 101
    },
    {
        "id": 2,
        "title": "Write documentation",
        "status": "todo",
        "priority": "medium",
        "dueDate": "2026-10-20",
        "assigneeId": 102
    },
    {
        "id": 3,
        "title": "Test endpoints",
        "status": "done",
        "priority": "low",
        "dueDate": "2026-10-18",
        "assigneeId": 101
    }
]

VALID_STATUSES = {"todo", "in_progress", "done"}
VALID_PRIORITIES = {"low", "medium", "high"}

REQUIRED_FIELDS = {
    "title",
    "status",
    "priority",
    "dueDate",
    "assigneeId"
}

EDITABLE_FIELDS = REQUIRED_FIELDS.copy()


def problem_response(status, title, detail, instance):
    """Return an RFC 9457-style problem response."""
    body = {
        "type": f"https://example.com/problems/{title.lower().replace(' ', '-')}",
        "title": title,
        "status": status,
        "detail": detail,
        "instance": instance
    }

    response = jsonify(body)
    response.status_code = status
    response.content_type = "application/problem+json"
    return response


def validate_task_data(data, partial=False):
    """Validate task fields and values."""
    if not isinstance(data, dict):
        return "Request body must be a JSON object."

    if not partial:
        missing = REQUIRED_FIELDS - data.keys()
        if missing:
            return f"Missing required fields: {', '.join(sorted(missing))}"

    unknown = data.keys() - EDITABLE_FIELDS
    if unknown:
        return f"Unknown fields: {', '.join(sorted(unknown))}"

    if "title" in data:
        if not isinstance(data["title"], str) or not data["title"].strip():
            return "title must be a non-empty string."

    if "status" in data:
        if data["status"] not in VALID_STATUSES:
            return "status must be todo, in_progress, or done."

    if "priority" in data:
        if data["priority"] not in VALID_PRIORITIES:
            return "priority must be low, medium, or high."

    if "dueDate" in data:
        if not isinstance(data["dueDate"], str):
            return "dueDate must be a date in YYYY-MM-DD format."
        try:
            date.fromisoformat(data["dueDate"])
        except ValueError:
            return "dueDate must be a valid date in YYYY-MM-DD format."

    if "assigneeId" in data:
        value = data["assigneeId"]
        if isinstance(value, bool) or not isinstance(value, int):
            return "assigneeId must be an integer."

    return None


def find_task(task_id):
    """Find a task by its ID."""
    return next(
        (task for task in TASKS if task["id"] == task_id),
        None
    )


# --------------------------------------------------
# OpenAPI documentation endpoints
# --------------------------------------------------

@app.get("/openapi.json")
def openapi_json():
    """Return the OpenAPI specification as JSON."""
    return jsonify(OPENAPI_SPEC)


@app.get("/docs")
def swagger_docs():
    """Display Swagger UI."""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Tasks API - Swagger UI</title>
        <link rel="stylesheet"
              href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
    </head>
    <body>
        <div id="swagger-ui"></div>

        <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js">
        </script>
        <script>
            SwaggerUIBundle({
                url: "/openapi.json",
                dom_id: "#swagger-ui",
                presets: [
                    SwaggerUIBundle.presets.apis
                ],
                layout: "BaseLayout"
            });
        </script>
    </body>
    </html>
    """
    return Response(html, mimetype="text/html")

#get /v1/tasks
@app.get("/v1/tasks")
def list_tasks():
    try:
        limit = int(request.args.get("limit", 20))
        page = int(request.args.get("page", 1))
    except ValueError:
        return problem_response(
            422, "Validation Error",
            "limit and page must be integers.", request.path
        )

    if not 1 <= limit <= 100 or page < 1:
        return problem_response(
            422, "Validation Error",
            "limit must be 1-100 and page must be positive.",
            request.path
        )

    status = request.args.get("status")

    if status and status not in VALID_STATUSES:
        return problem_response(
            422, "Validation Error",
            "Invalid status filter.", request.path
        )

    results = TASKS.copy()

    if status:
        results = [
            task for task in results
            if task["status"] == status
        ]

    start = (page - 1) * limit
    end = start + limit
    page_data = results[start:end]

    next_url = None
    if end < len(results):
        next_url = (
            f"/v1/tasks?limit={limit}&page={page + 1}"
            + (f"&status={status}" if status else "")
        )

    return jsonify({
        "data": page_data,
        "limit": limit,
        "next": next_url
    })

#post /v1/tasks
@app.post("/v1/tasks")
def create_task():
    data = request.get_json(silent=True)

    error = validate_task_data(data)
    if error:
        return problem_response(
            422, "Validation Error", error, request.path
        )

    new_id = max((task["id"] for task in TASKS), default=0) + 1

    task = {"id": new_id, **data}
    TASKS.append(task)

    return jsonify(task), 201

#get /v1/tasks/<id>
@app.get("/v1/tasks/<int:task_id>")
def get_task(task_id):
    task = find_task(task_id)

    if task is None:
        return problem_response(
            404, "Not Found",
            f"Task with id {task_id} was not found.",
            request.path
        )

    return jsonify(task)

#patch /v1/tasks/<id>
@app.patch("/v1/tasks/<int:task_id>")
def update_task(task_id):
    task = find_task(task_id)

    if task is None:
        return problem_response(
            404, "Not Found",
            f"Task with id {task_id} was not found.",
            request.path
        )

    data = request.get_json(silent=True)

    error = validate_task_data(data, partial=True)
    if error:
        return problem_response(
            422, "Validation Error", error, request.path
        )

    if not data:
        return problem_response(
            422, "Validation Error",
            "Provide at least one field to update.",
            request.path
        )

    task.update(data)

    return jsonify(task), 200

#delete /v1/tasks/<id>
@app.delete("/v1/tasks/<int:task_id>")
def delete_task(task_id):
    task = find_task(task_id)

    if task is None:
        return problem_response(404, "Not Found", f"Task with id {task_id} was not found.", request.path)

    TASKS.remove(task)

    return "", 204


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)