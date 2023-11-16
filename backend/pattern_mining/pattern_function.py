from pattern_mining.domains import ObjectArgument
from pattern_mining.table_manager import TableManager


class PatternFunction:

    def __init__(self, object_arity):
        self.arity = object_arity

    def to_string(self):
        raise NotImplementedError()

    def get_ebnf_descriptor(self):
        raise NotImplementedError()

    def create_function_evaluation_table(self, table_manager: TableManager, arguments):
        raise NotImplementedError()

