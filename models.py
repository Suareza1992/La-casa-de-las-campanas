from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

Base = declarative_base()


class User(Base, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default='client')  # 'admin' or 'client'
    created_at = Column(DateTime, default=datetime.utcnow)

    orders = relationship('Order', back_populates='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class ProductItem(Base):
    __tablename__ = 'product_items'

    id = Column(Integer, primary_key=True)
    image_name = Column(String, nullable=False)
    caption = Column(Text, nullable=True)
    name = Column(String, nullable=True)
    price = Column(String, nullable=True)
    category = Column(String, nullable=True)

    order_items = relationship('OrderItem', back_populates='product')


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(String, default='pending')  # pending, confirmed, cancelled
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='orders')
    items = relationship('OrderItem', back_populates='order')


class OrderItem(Base):
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('product_items.id'), nullable=False)
    quantity = Column(Integer, default=1)

    order = relationship('Order', back_populates='items')
    product = relationship('ProductItem', back_populates='order_items')


engine = create_engine('sqlite:///product_data.db')
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
