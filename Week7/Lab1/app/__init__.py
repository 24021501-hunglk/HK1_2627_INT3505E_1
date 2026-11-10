from flask import Flask

from config import Config
from app.extensions import db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    from app.models.product import Product
    from app.api.products import products_bp

    app.register_blueprint(
        products_bp,
        url_prefix="/api/v1/products"
    )

    with app.app_context():
        db.create_all()

    return app