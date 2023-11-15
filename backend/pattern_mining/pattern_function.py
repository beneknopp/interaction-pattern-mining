class PatternFunction:

    def __init__(self, object_arity):
        self.arity = object_arity

    def apply_(self, ocel, event, objects):
        raise NotImplementedError()

    def get_pattern_syntax_(self):
        raise NotImplementedError()

    @classmethod
    def parse_(cls, definition):
        raise NotImplementedError()

    def apply(self, ocel, event, objects):
        if not len(objects) == self.arity:
            raise ValueError("Invalid number of objects passed")
        self.apply_(ocel, event, objects)

    def get_pattern_syntax(self):
        self.get_pattern_syntax_()

    @classmethod
    def parse(cls, definition):
        try:
            pat = cls.parse_(definition)
            return pat
        except AssertionError:
            raise ValueError("Pattern constructor called with invalid definition string")