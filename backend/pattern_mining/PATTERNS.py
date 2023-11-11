#from PATTERNS import EAVAL, EAVAL_GEQ, E2O_R, O2O_R, O2O_R_COMPLETE
from pattern_function import PatternFunction

class EAVAL(PatternFunction):

    arity = 0
    function_identifier = "EAVAL"
    pattern_syntax = "'(' STR ',' EQ|GEQ|LEQ ',' STR ')'"

    def __init__(self, ea, op, v):
        super().__init__(self.arity)
        self.ea = ea
        self.op = op
        self.v = v

    def apply_(self, ocel, event, objects):
        print(1)
        pass

    def get_pattern_syntax_(self):
        return self.pattern_syntax

    @classmethod
    def parse_(cls, definition):
        definition_split = [x.strip() for x in definition.split(",")]
        assert definition_split[0].startswith("EAVAL(")
        assert definition_split[2].endswith(")")
        ea = definition_split[0].removeprefix("EAVAL(").strip()
        op = definition_split[1]
        v = definition_split[2][:-1]
        return cls(ea, op, v)