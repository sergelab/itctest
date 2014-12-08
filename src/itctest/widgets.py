
class WidgetPrebind(object):
    def __init__(self, widget, **kwargs):
        self.widget = widget
        self.kw = kwargs

    def __call__(self, field, **kwargs):
        return self.widget.__call__(field, **dict(self.kw, **kwargs))
