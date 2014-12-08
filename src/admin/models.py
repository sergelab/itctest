# coding: utf-8

import sqlalchemy as sa
from sqlalchemy.ext.hybrid import hybrid_property
from flask import current_app
from flask.ext.babel import gettext as _
from flask.ext.login import UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from blinker import Namespace


user_signals = Namespace()
user_created = user_signals.signal('user_created')
user_deleted = user_signals.signal('user_deleted')

db = SQLAlchemy(current_app) if 'sqlalchemy' not in current_app.extensions.keys() else current_app.extensions.get('sqlalchemy').db


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String, unique=True, nullable=False)
    pw_hash = db.Column(db.String)
    firstname = db.Column(db.String)
    lastname = db.Column(db.String)
    activity = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, db.DefaultClause(db.func.now()))

    def __unicode__(self):
        return u'{0}'.format(self.fullname)

    @hybrid_property
    def fullname(self):
        data = []

        if self.firstname:
            data.append(self.firstname)

        if self.lastname:
            data.append(self.lastname)

        if not data:
            data.append(self.login)

        return u' '.join(data)

    @property
    def password(self):
        return self.pw_hash

    @password.setter
    def password(self, password):
        if password:
            self.pw_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pw_hash, password)
