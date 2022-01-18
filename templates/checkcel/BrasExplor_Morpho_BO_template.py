from checkcel import Checkplate
from checkcel.validators import FloatValidator, DateValidator, NoValidator
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
        ("% of transplant survival (7)", FloatValidator(min=0, max=100)),
        ("Specific surface (8)", FloatValidator()),
        ("Specific surface picture (9)", NoValidator()),
        ("Weight (10)", FloatValidator()),
        ("Characteristics (11)", NoValidator()),
        ("Flowering date (12)", DateValidator()),
        ("Flowering date (50%) (13)", DateValidator()),
        ("Flowering date (100%) (14)", DateValidator()),
        ("Seeds/plant (15)", FloatValidator(min=0, max=1)),
        ("Seeds weight (16)", FloatValidator()),
        ("F/D Biomass ratio (17)", FloatValidator(min=0, max=1)),
        ("A/R Biomass ratio (18)", FloatValidator(min=0, max=1))
    ])
