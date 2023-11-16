from pandas import DataFrame

from pattern_mining.domains import ObjectVariableArgument, ObjectArgument, equals
from pattern_mining.table_manager import TableManager


class PatternFormula:

    def __init__(self):
        pass

    def evaluate(self, table_manager):
        evaluation_table = self.apply(table_manager)
        evaluation = evaluation_table.set_index('ocel:eid')['ox:evaluation'].squeeze()
        return evaluation

    def apply(self, table_manager: TableManager) -> DataFrame:
        raise NotImplementedError()

    def substitute(self, object_argument: ObjectArgument, object_variable_argument: ObjectVariableArgument):
        raise NotImplementedError()

    def copy(self):
        raise NotImplementedError()

    def to_string(self):
        raise NotImplementedError()
