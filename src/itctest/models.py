# coding: utf-8

import sqlalchemy as sa

from .translatable import Translatable, TranslatableColumn
from .init import db


class Article(db.Model, Translatable):
    __tablename__ = 'articles'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String)
    title = TranslatableColumn(db.String, tsweight='A')
    text = TranslatableColumn(db.Text, tsweight='B')
    activity = db.Column(db.Boolean, default=True)


class NewsArticle(db.Model, Translatable):
    __tablename__ = 'news_articles'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String)
    title = TranslatableColumn(db.String, tsweight='A')
    text = TranslatableColumn(db.Text, tsweight='B')
    activity = db.Column(db.Boolean, default=True)
    pub_date = db.Column(db.DateTime, default=sa.func.now())    

    __mapper_args__ = {
        'order_by': pub_date.asc()
    }
