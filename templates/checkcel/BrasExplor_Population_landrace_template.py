from checkcel import Checkplate
from checkcel.validators import DateValidator, NoValidator, UniqueValidator, SetValidator, IntValidator
from collections import OrderedDict


class MyTemplate(Checkplate):
    empty_ok = True
    validators = OrderedDict([
        ("Population name", UniqueValidator()),
        ("Sampling date", DateValidator(empty_ok=False)),
        ("Collector", NoValidator()),
        ("Country", SetValidator(empty_ok=False, valid_values=["Algeria", "Egypt", "France", "Italy", "Slovenia", "Tunisia", "Spain"])),
        ("Region", NoValidator()),
        ("Province", NoValidator()),
        ("Locality", NoValidator()),
        ("Town", NoValidator()),
        ("GPS", NoValidator()),
        ("Altitude", IntValidator(min=0)),
        ("Place (#1)", SetValidator(valid_values=["family garden", "market", "field", "private collection", "other"])),
        ("Origin (#2)", NoValidator()),
        ("Source (#3)", SetValidator(valid_values=["friends", "neighbors", "parents", "exchange", "purchase", "market", "seed merchant", "local production", "other"])),
        ("Purchased (#4)", SetValidator(valid_values=["never", "regularly", "occasionally", ""])),
        ("Purchased where [#4)", NoValidator()),
        ("Exchanged (#5)", SetValidator(valid_values=["never", "regularly", "occasionally", ""])),
        ("Exchanged with whom (#5)", NoValidator()),
        ("Propagation (#6)", NoValidator()),
        ("Similarity (#7)", SetValidator(valid_values=["no", "yes"])),
        ("Isolation precaution (#7)", NoValidator()),
        ("Conservation duration (#8)", IntValidator(min=0)),
        ("Storage conditions (#8)", NoValidator()),
        ("Importance (#9)", SetValidator(valid_values=["rare", "infrequent", "frequent", "abundant"])),
        ("Sowing period (#10)", NoValidator()),
        ("Harvest period (#11)", NoValidator()),
        ("Irrigation (#12)", SetValidator(valid_values=["yes", "no"])),
        ("Irrigation frequency (#12)", NoValidator()),
        ("Informant (#13)", NoValidator()),
        ("Human food (#14)", SetValidator(valid_values=["no", "yes", ""])),
        ("Forage (#14)", SetValidator(valid_values=["no", "yes", ""])),
        ("Part used (#15)", SetValidator(valid_values=["root", "leaves", "roots + leaves", "other"])),
        ("Number of recipes (#16)", IntValidator(min=0)),
        ("Destination (#17)", SetValidator(valid_values=["family", "local market", "elsewhere market", ""])),
        ("Destination where (#17)", NoValidator()),
        ("Destination how (#17)", NoValidator()),
        ("Taste qualities (#18)", NoValidator()),
        ("Why kept (#19)", NoValidator()),
        ("When abandoned (#20)", NoValidator()),
        ("Why abandoned (#20)", NoValidator()),
        ("Grown duration (#21)", NoValidator()),
        ("Cultivated (#22)", NoValidator()),
        ("Comments (#23)", NoValidator())
    ])
