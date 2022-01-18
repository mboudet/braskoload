from checkcel import Checkplate
from checkcel.validators import FloatValidator, NoValidator
from collections import OrderedDict


class MyTemplate(Checkplate):
    validators = OrderedDict([
        ("Population id", NoValidator()),
        ("NPK analysis", NoValidator()),
        ("pH", FloatValidator(min=0, max=14)),
        ("Soil depth", FloatValidator(min=0, max=14)),
        ("Soil water potential", FloatValidator()),
        ("Soil structure", NoValidator()),
        ("Daily solar radiation", FloatValidator()),
        ("Watering volume", FloatValidator())
        ("Climatic data file", NoValidator())
    ])
