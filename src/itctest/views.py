# coding: utf-8

from flask import (
    Blueprint,
    current_app,
    render_template,
    abort,
    g
)
from flask.ext.assets import Bundle
from admin.models import User
from .init import app, assets, lm, db
from .models import Article, NewsArticle


assets.register('css_common_all', Bundle(
	'css/normalize.css',
	'css/common.css',
#	filters='jinja2',
	output='css/final/itctest.css'
))


@app.before_request
def before_request():
    Article.language = g.language
    NewsArticle.language = g.language


@app.route('/')
def index():
    article = Article.query.filter(Article.slug == 'main_page').first()

    if not article:
        abort(404)

    return render_template('index.html', article=article)


@app.route('/about')
def about():
    article = Article.query.filter(Article.slug == 'about_page').first()
    print('123')

    #if not article:
    #    abort(404)
	return render_template('about.html', article=article)


@app.route('/contacts')
def contacts():
	pass

@app.errorhandler(401)
def not_authorized(error):
    return render_template('401.html', error=error), 401


@app.errorhandler(404)
def error_404(error):
    return render_template('404.html', error=error), 404


@app.errorhandler(500)
def error_500(error):
    return render_template('500.html', error=error), 500


@app.errorhandler(501)
def not_implemented(error):
    return render_template('501.html', error=error), 501


@lm.user_loader
def load_user(user_id):
    try:
        user = User.query.filter(User.id == user_id, User.activity == True).first()
        return user
    except Exception as e:
        current_app.logger.exception(e)
