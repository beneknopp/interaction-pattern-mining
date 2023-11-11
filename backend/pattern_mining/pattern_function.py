class PatternFunction():

    def __init__(self, arity):
        self.arity = arity

    def apply_(self, ocel, event, objects):
        raise NotImplementedError("Pattern function should be specified")

    def get_pattern_syntax_(self):
        raise NotImplementedError("Pattern syntax should be specified")

    @classmethod
    def parse_(cls, definition):
        raise NotImplementedError("Parser should be specified")

    def apply(self, ocel, event, objects):
        if not len(objects) == self.arity:
            raise ValueError("Invalid number of objects passed")
        self.apply_(ocel, event, objects)

    def get_pattern_syntax(self):
        self.get_pattern_syntax_()

    @classmethod
    def parse(cls, definition):
        return cls.parse_(definition)