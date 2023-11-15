from pattern_mining.ground_pattern import GroundPattern


class PatternFunction:

    def __init__(self, object_arity):
        self.arity = object_arity

    def bind(self, object_ids) -> GroundPattern:
        raise NotImplementedError()

    def to_string(self):
        raise NotImplementedError()

    def get_ebnf_descriptor(self):
         raise NotImplementedError()

    def get_ebnf_descriptor(self):
        return self.__get_ebnf_descriptor()

