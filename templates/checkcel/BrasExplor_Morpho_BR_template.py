from checkcel import Checkplate
from checkcel.validators import FloatValidator, NoValidator, DateValidator
from collections import OrderedDict


class MyTemplate(Checkplate):
    validators = OrderedDict([
        ("Population id", NoValidator()),
        ("% of emergence (1)", FloatValidator(min=0, max=100)),
        ("Emergence picture (2)", NoValidator()),
        ("% of survival (3)", FloatValidator(min=0, max=100)),
        ("Occurrence time (4)", DateValidator()),
        ("Foliar surface (5)", FloatValidator()),
        ("Foliar surface picture (6)", NoValidator()),
        ("Specific surface (7)", FloatValidator()),
        ("Specific surface picture (8)", NoValidator()),
        ("Weight (9)", FloatValidator()),
        ("Characteristics (10)", NoValidator()),
        ("Flowering date (11)", DateValidator()),
        ("Flowering date (50%) (12)", DateValidator()),
        ("Flowering date (100%) (13)", DateValidator()),
        ("Seeds/plant (14)", FloatValidator(min=0, max=1)),
        ("Seeds weight (15)", FloatValidator()),
        ("F/D Biomass ratio (16)", FloatValidator(min=0, max=1)),
        ("A/R Biomass ratio (17)", FloatValidator(min=0, max=1))
    ])
