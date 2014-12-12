# coding: utf-8

from flask import current_app
from flask.ext.wtf import Form as secureForm
from wtforms import Form as wForm
from wtforms import HiddenField, FieldList
from flask.ext.login import current_user
from brpr.flask.data import AttrDict
from brpr.flask.widgets import WidgetPrebind

#from defender.fields import ROTextField
#from defender.widgets import ReadonlyStringWidget



class Form(secureForm):
    TIME_LIMIT = 360000


class TranslatableFieldList(FieldList): pass


class TranslatableFieldsForm(wForm):
    language = HiddenField('Language field (hidden)')

    def __init__(self, *args, **kwargs):
        super(TranslatableFieldsForm, self).__init__(*args, **kwargs)

    def process(self, formdata=None, obj=None, use_label=False, *args, **kwargs):
        lang = kwargs.get('language')

        if lang:  # TODO: Make an mechanizm!
            for f in self._fields:
                field = getattr(self, f)

                if not use_label:
                    field.label.text = lang.upper()

        super(TranslatableFieldsForm, self).process(formdata, obj, **kwargs)


class TranslatableForm(Form):
    def __init__(self, *args, **kwargs):
        self.languages = current_app.config.get('LANGUAGES', [])
        obj = kwargs.get('obj', None)
        use_label = kwargs.get('use_label', False)

        if obj:
            if not hasattr(obj, '__translatable_mapper__') or not hasattr(obj, 'translatable_fields'):
                raise Exception('Object must inherit Translatable mixin')

            data = dict(obj.__dict__.items())
            translated_fields = self._get_translated_fields(obj)
            values = dict()
            ex_values = dict()

            for idx, l in enumerate(self.languages):
                tr_fields = {f: unicode('') if f != 'language' else unicode(l.lower()) for f in translated_fields}
                tr_fields.update({'use_label': use_label})
                v = values.setdefault(l.lower(), AttrDict(tr_fields))

            d = data.get('translatable_fields', dict())

            for idx, l in enumerate(d):
                if l.language.lower() in values.keys():
                    tr_fields = {f: getattr(l, f, unicode('')) if l != 'language' else getattr(l, f, unicode('')).lower() for f in translated_fields}
                    tr_fields.update({'use_label': use_label})
                    v = ex_values.setdefault(l.language.lower(), AttrDict(tr_fields))

            values = dict(values.items() + ex_values.items())

            self._translation_values = sorted(values.values())

        super(TranslatableForm, self).__init__(*args, **kwargs)

    def process(self, formdata=None, obj=None, **kwargs):
        super(TranslatableForm, self).process(formdata, obj, **kwargs)

        for fn in self._get_translated_form_fields():
            field = getattr(self, fn)

            for trans_val in self._translation_values:
                field.process(formdata=formdata, data=self._translation_values)

    def _get_translated_fields(self, obj=None):
        """
        Получение из объекта названий полей требующих перевода, включая поле language
        """
        return [f[0] for f in obj.__translatable_mapper__.columns.items() if f[0] not in ['id', obj.__tablename__ + '_id']] if obj else []

    def _get_translated_form_fields(self):
        """ Получение из формы полей TranslatableFieldList """
        return [fn for fn in self._fields if getattr(self, fn).type == 'TranslatableFieldList']

    def populate_obj(self, obj):
        for fname in self._get_translated_form_fields():
            if fname in self:
                translated_fields = self._get_translated_fields(obj)
                field = getattr(self, fname)

                for entry in field.entries:
                    form_translated_fields = [f for f in entry._fields if f in translated_fields]
                    l = None

                    if 'language' in form_translated_fields:
                        l = entry.__getattr__('language')

                    lang = l.data.upper() if l else None

                    wlf = {f: unicode(entry.__getattr__(f).data) if f != 'language' else unicode(entry.__getattr__(f).data.lower()) for f in form_translated_fields}
                    obj.write_translatable_fields(**wlf)
    
                self.__delitem__(fname)

        super(TranslatableForm, self).populate_obj(obj)
