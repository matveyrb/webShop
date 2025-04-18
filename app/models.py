from app import db
from flask_login import UserMixin
from datetime import datetime


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product')
    user = db.relationship('User')


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    orders = db.relationship('Order', backref='customer', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = password

    def check_password(self, password):
        return self.password_hash == password

    def get_cart_count(self):
        from app.models import CartItem  # Импорт здесь чтобы избежать циклических импортов
        return CartItem.query.filter_by(user_id=self.id).count()


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), index=True)
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    category = db.Column(db.String(50))
    image = db.Column(db.String(100))
    stock = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')
    total = db.Column(db.Float)
    items = db.relationship('OrderItem', backref='order', lazy='dynamic')


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)
    product = db.relationship('Product')


class VisitLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(15))
    user_agent = db.Column(db.String(200))
    page_url = db.Column(db.String(100))
    referrer = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class SalesStat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer)
    amount = db.Column(db.Float)
    date = db.Column(db.Date, default=datetime.utcnow)

