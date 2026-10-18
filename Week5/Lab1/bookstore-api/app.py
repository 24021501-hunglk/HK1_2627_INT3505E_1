from flask import Flask, jsonify
from models import db
from routes.books import books_bp

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bookstore.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

app.register_blueprint(books_bp, url_prefix="/api/v1/books")

@app.get("/bookstore-api/health")
def health():
    return jsonify({"status": "ok"}), 200


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True, port=5000)