
from flask.ext.wtf import Form as secureForm
from wtforms import Form as wForm


class Form(secureForm):
    TIME_LIMIT = 360000
