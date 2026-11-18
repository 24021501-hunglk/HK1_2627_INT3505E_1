from flask import Blueprint, Flask
from blueprints.v1 import bp as v1_bp
from blueprints.v2 import bp as v2_bp

app = Flask(__name__)

api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")
api_v2 = Blueprint("api_v2", __name__, url_prefix="/api/v2")

api_v1.register_blueprint(v1_bp)
api_v2.register_blueprint(v2_bp)

app.register_blueprint(api_v1)
app.register_blueprint(api_v2)

if __name__ == "__main__":
    app.run(debug=True, port=5000)