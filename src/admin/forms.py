
import wtforms as wtf
from flask import flash
from flask.ext.babel import gettext as _

from itctest.forms import Form, wForm
from itctest.widgets import WidgetPrebind

from .models import User, db


class LoginForm(Form):
    login = wtf.TextField(_('Login or Email'), validators=[wtf.validators.Required()], widget=WidgetPrebind(
        wtf.widgets.TextInput(),
        class_='uk-width-1-1 uk-form-large',
        placeholder=_('Login or Email'),
        size=30
    ))
    password = wtf.PasswordField(_('Password'), validators=[wtf.validators.Required()], widget=WidgetPrebind(
        wtf.widgets.PasswordInput(),
        class_='uk-width-1-1 uk-form-large',
        placeholder=_('Password'),
        size=30
    ))
    remember_me = wtf.BooleanField(_(u'Remember me'))
    next = wtf.HiddenField()

    def validate(self):
        if not Form.validate(self):
            return False

        user = User.query.filter(db.func.lower(User.login) == self.login.data.lower(), User.activity == True).first()

        if not user or not user.check_password(self.password.data):
            self.errors.update({'form': [_('Invalid user or password message')]})
            return False

        self.user = user

        return True