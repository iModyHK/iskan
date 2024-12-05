from . import db  # Use relative import
from flask_login import UserMixin
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from .models import User  # Import the User model

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cluster = db.Column(db.String(50), nullable=False)
    villa = db.Column(db.String(50), nullable=False)
    floors = db.Column(db.String(50), nullable=True, default='دورين')
    type = db.Column(db.String(50), nullable=True, default='أفراد')
    status = db.Column(db.String(50), nullable=False, default='شاغرة')

    def update_status(self):
        if self.tenants and any(not tenant.archived for tenant in self.tenants):
            self.status = 'مشغولة'
        else:
            self.status = 'شاغرة'
        db.session.commit()

class Tenant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cluster = db.Column(db.String(50), nullable=False)
    villa = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    tenant_id = db.Column(db.String(50), nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    workplace = db.Column(db.String(100), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=True)
    property = db.relationship('Property', backref=db.backref('tenants', lazy=True))
    archived = db.Column(db.Boolean, default=False)
    eviction_date = db.Column(db.Date, nullable=True)  # New column

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<User {self.username}>'