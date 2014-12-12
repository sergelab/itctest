# coding: utf-8

from flask import g, current_app
import wtforms as wtf

class WidgetPrebind(object):
    def __init__(self, widget, **kwargs):
        self.widget = widget
        self.kw = kwargs

    def __call__(self, field, **kwargs):
        return self.widget.__call__(field, **dict(self.kw, **kwargs))


class TranslatableFormWidget(wtf.widgets.ListWidget):
    def __call__(self, field, **kwargs):
        html = []
        kwargs.setdefault('id', field.id)
        use_row_tag = kwargs.get('use_row_tag', False)

        for subfield in field:
            if subfield.type != 'HiddenField':
                if use_row_tag:
                    html.append('<div class="uk-form-row">')
                if self.prefix_label:
                    html.append('<label for="%s" class="uk-form-label">%s</label>' % (subfield.id, subfield.label.text))
                    html.append('<div class="uk-form-controls">%s</div>' % subfield())
                if use_row_tag:
                    html.append('</div>')
            else:
                html.append('<div style="display:none">%s</div>' % subfield())

        return wtf.widgets.HTMLString(''.join(html))


class TranslatableTabWidget(wtf.widgets.ListWidget):
    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        html = []
        html.append('<ul class="uk-tab" data-uk-tab="{{connect:\'#tab-content_{0}\'}}">'.format(field.id))

        for idx, subfield in enumerate(field):
            current = ('' if not g.language else g.language.upper()) == subfield.language.data.upper()
            html.append('<li{0}><a href="#{1}">{1}</a></li>'.format(' class="uk-active"' if current else '', subfield.language.data.upper()))

        html.append('</ul>')
        html.append('<ul id="tab-content_{0}" class="uk-switcher uk-margin">'.format(field.id))

        for idx, subfield in enumerate(field):
            html.append('<li>')
            html.append('%s' % subfield(use_row_tag=True))
            html.append('</li>')

        html.append('</ul>')

        return wtf.widgets.HTMLString(''.join(html))
