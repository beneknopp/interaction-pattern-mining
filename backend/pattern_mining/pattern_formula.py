from pandas import DataFrame

from pattern_mining.domains import ObjectVariableArgument, ObjectArgument, equals
from pattern_mining.table_manager import TableManager


class PatternFormula:

    def __init__(self):
        pass

    def evaluate(self, table_manager):
        event_index = table_manager.get_event_index()
        event_index["ox:evaluation"] = False
        # apply might not return an outcome for every index (if the object domain is empty)
        evaluation = self.apply(table_manager)
        evaluation = evaluation.set_index('ocel:eid')['ox:evaluation'].squeeze()
        event_index.update(evaluation)
        return event_index

    def apply(self, table_manager: TableManager) -> DataFrame:
        raise NotImplementedError()

    def get_object_type(self):
        raise NotImplementedError()

    def get_free_variables(self):
        raise NotImplementedError()

    def substitute(self, object_argument: ObjectArgument, object_variable_argument: ObjectVariableArgument):
        raise NotImplementedError()

    def copy(self):
        raise NotImplementedError()

    def to_string(self):
        raise NotImplementedError()
