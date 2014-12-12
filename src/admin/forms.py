
import wtforms as wtf
from wtforms.validators import (
    Required,
    Optional
)
from flask import flash
from flask.ext.babel import gettext as _, lazy_gettext as __

from itctest.forms import (
    Form,
    wForm,
    TranslatableForm,
    TranslatableFieldsForm,
    TranslatableFieldList
)
from itctest.widgets import (
    WidgetPrebind,
    TranslatableFormWidget,
    TranslatableTabWidget
)
from itctest.models import Article

from .models import db, User


class ArticleTranslatableForm(TranslatableFieldsForm):
    title = wtf.TextField(__('Article title label'), validators=[Required()], widget=WidgetPrebind(wtf.widgets.TextInput(), class_='uk-width-1-1'))
    text = wtf.TextField(__('Article text label'), validators=[Required()], widget=WidgetPrebind(wtf.widgets.TextArea(), rows="15", cols="100", class_='uk-width-1-1'))


class ArticleForm(TranslatableForm):
    slug = wtf.TextField(__('Article slug label'), widget=WidgetPrebind(
        wtf.widgets.TextInput(),
        size=40,
    ), validators=[Required()])
    translatable_fields = TranslatableFieldList(
        wtf.FormField(ArticleTranslatableForm, widget=WidgetPrebind(
            TranslatableFormWidget()
        )), widget=WidgetPrebind(TranslatableTabWidget()), label=''
    )
    activity = wtf.BooleanField(_('Article activity flag label'))


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
