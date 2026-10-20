import os
from flask import Flask, jsonify, send_file, render_template_string

app = Flask(__name__)

SWAGGER_UI_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Swagger UI - Hotel Booking API</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js" crossorigin></script>
  <script>
    window.onload = () => {
      window.ui = SwaggerUIBundle({
        url: '/openAPI.yaml',
        dom_id: '#swagger-ui',
      });
    };
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    return jsonify({
        "system": "Hotel Booking API",
        "docs": "http://localhost:5000/docs",
        "spec": "http://localhost:5000/openAPI.yaml"
    })

@app.route("/openapi.yaml")
def get_spec():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    spec_path = os.path.join(base_dir, "openAPI.yaml")
    return send_file(spec_path, mimetype="text/yaml")

@app.route("/docs")
def swagger_ui():
    return render_template_string(SWAGGER_UI_HTML)

@app.route("/<path:subpath>")
def static_proxy(subpath):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, subpath)
    if os.path.exists(file_path):
        return send_file(file_path, mimetype="text/yaml")
    return jsonify({"error": "File not found"}), 404

if __name__ == "__main__":
    app.run(port=5000, debug=True)