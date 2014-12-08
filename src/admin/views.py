# coding: utf-8

from flask import (
    Blueprint,
    render_template,
    current_app,
    redirect,
    request,
    flash,
    url_for
)
from flask.ext.assets import Bundle
from flask.ext.babel import gettext as _
from flask.ext.login import (
    login_required,
    current_user,
    login_user,
    logout_user
)
from itctest.init import assets
from .forms import LoginForm
from .models import db, User


admin = Blueprint('admin', __name__, template_folder='templates', static_folder='static', url_prefix='/admin')
current_app.login_manager.login_view = 'admin.login'
current_app.login_manager.session_protection = 'base'


assets.register('css_admin_all', Bundle(
    'admin/css/uikit.css',
    filters='jinja2',
    output='final/css/admin.css'
))

assets.register('js_admin_all', Bundle(
    'http://code.jquery.com/jquery-1.11.0.min.js',
    'admin/js/uikit.min.js',
    'admin/js/core/nav.min.js',
    output='final/css/admin.js'
))


class LogOut(Exception):
    pass


@admin.route('/')
@login_required
def dashboard():
    return render_template('admin/index.html')


@admin.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated():
        raise LogOut()

    form = LoginForm() if request.method == 'POST' else LoginForm(request.args)

    if form.validate_on_submit():
        if login_user(form.user, remember=form.remember_me.data) is True:
            flash(_('Logged in successfully message'), 'success')
        else:
            flash(_('Logging failed'), 'warning')

        return redirect(form.next.data or url_for('admin.dashboard'))

    return render_template('admin/login.html', form=form)


@admin.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(request.args.get('next') or url_for('admin.login'))
