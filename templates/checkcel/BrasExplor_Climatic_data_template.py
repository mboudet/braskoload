from checkcel import Checkplate
from checkcel.validators import FloatValidator, NoValidator
from collections import OrderedDict


class MyTemplate(Checkplate):
    validators = OrderedDict([
        ("Population id", NoValidator()),
        ("Measurement time", NoValidator()),
        ("Surface temperature", FloatValidator()),
        ("Air temperature", FloatValidator()),
        ("Rainfall", FloatValidator()),
    ])
