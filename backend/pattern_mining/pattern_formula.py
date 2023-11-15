from pm4py import OCEL

from pattern_mining.domains import ObjectVariableArgument, ObjectArgument, equals
from pattern_mining.table_manager import TableManager


class PatternFormula:

    def __init__(self):
        pass

    def evaluate(self, table_manager: TableManager, event):
        raise NotImplementedError()

    def substitute(self, object_argument: ObjectArgument, object_variable_argument: ObjectVariableArgument):
        raise NotImplementedError()

    def copy(self):
        raise NotImplementedError()

    def to_string(self):
        raise NotImplementedError()
