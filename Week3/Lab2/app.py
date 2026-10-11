from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
import logging

from errors import ApiProblem, problem

app = Flask(__name__)

logging.basicConfig(level=logging.ERROR)

@app.errorhandler(ApiProblem)
def handle_api_problem(error):
    return problem(
        status=error.status,
        title=error.title,
        detail=error.detail,
        type_path=(
            error.type.replace("http://localhost:5000/probs/", "")
            if error.type != "about:blank"
            else None
        ),
        **error.extra
    )

@app.errorhandler(HTTPException)
def handle_http_exception(error):
    return problem(
        status=error.code,
        title=error.name,
        detail=error.description
    )

@app.errorhandler(Exception)
def handle_unexpected_exception(error):
    app.logger.exception("Unexpected server error")

    return problem(
        status=500,
        title="Internal Server Error",
        detail="An unexpected error occurred."
    )

RESOURCE = {
    1: {
        "id": 1,
        "name": "resource 1"
    },
    2: {
        "id": 2,
        "name": "resource 2"
    }
}


@app.get("/resources/<int:id>")
def get_resource(id):

    resource = RESOURCE.get(id)

    if resource is None:
        raise ApiProblem(
            status=404,
            title="resource not found",
            detail=f"resource with id {id} does not exist.",
            type_path="resource-not-found",
            resource_id=id
        )

    return jsonify(resource)

###unexpected error route for testing
@app.get("/test-error")
def test_error():
    x = 1 / 0
    return jsonify({"result": x})


if __name__ == "__main__":
    app.run(debug=False)