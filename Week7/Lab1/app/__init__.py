from flask import Flask

from config import Config
from app.extensions import db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    from app.models import Product, Order, OrderItem
    from app.api.products import products_bp
    from app.api.orders import orders_bp
    from app.api.health import health_bp

    app.register_blueprint(
        products_bp,
        url_prefix="/api/v1/products"
    )
    
    app.register_blueprint(
        orders_bp,
        url_prefix="/api/v1/orders"
    )
    
    app.register_blueprint(health_bp)

    with app.app_context():
        db.create_all()

    return app