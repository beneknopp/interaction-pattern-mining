from pm4py import OCEL

from pattern_mining.PATTERN_FUNCTIONS import Oaval_eq, Oaval_leq, Oaval_geq, Ot_card, O2o_r, O2o_complete, E2o_r
from pattern_mining.domains import ObjectVariableArgument, ObjectArgument, equals
from pattern_mining.free_pattern import FreePattern
from pattern_mining.pattern_formula import PatternFormula
from pattern_mining.table_manager import TableManager
from utils.ocel_utils import get_event_objects_of_type


class FreePatternFormula(PatternFormula):
    freePattern: FreePattern

    def __init__(self, free_pattern):
        super().__init__()
        self.freePattern = free_pattern

    def apply(self, table_manager):
        return self.freePattern.apply(table_manager)

    def substitute(self, object_arg: ObjectArgument, object_variable_arg: ObjectVariableArgument):
        self.freePattern.substitute(object_arg, object_variable_arg)

    def copy(self):
        return FreePatternFormula(self.freePattern.copy())

    def to_string(self):
        return self.freePattern.to_string()


class Negation(PatternFormula):
    patternFormula: PatternFormula

    def __init__(self, pattern_formula: PatternFormula):
        super().__init__()
        self.patternFormula = pattern_formula

    def copy(self):
        return Negation(self.patternFormula.copy())

    def substitute(self, object_argument: ObjectArgument, object_variable_argument: ObjectVariableArgument):
        self.patternFormula.substitute(object_argument, object_variable_argument)


    def apply(self, table_manager):
        raise NotImplementedError()

    def to_string(self):
        return "not(" + self.patternFormula.to_string() + ")"



class Disjunction(PatternFormula):
    patternFormula1: PatternFormula
    patternFormula2: PatternFormula

    def __init__(self, pattern_formula1: PatternFormula, pattern_formula2: PatternFormula):
        super().__init__()
        self.patternFormula1 = pattern_formula1
        self.patternFormula2 = pattern_formula2

    def apply(self, table_manager):
        return self.patternFormula1.apply(table_manager) | self.patternFormula2.apply(table_manager)

    def substitute(self, object_argument: ObjectArgument, object_variable_argument: ObjectVariableArgument):
        self.patternFormula1.substitute(object_argument, object_variable_argument)
        self.patternFormula2.substitute(object_argument, object_variable_argument)

    def copy(self):
        return Disjunction(self.patternFormula1.copy(), self.patternFormula2.copy())

    def to_string(self):
        return "or(" + self.patternFormula1.to_string() + "," + self.patternFormula2.to_string() + ")"


class Conjunction(PatternFormula):
    patternFormula1: PatternFormula
    patternFormula2: PatternFormula

    def __init__(self, pattern_formula1: PatternFormula, pattern_formula2: PatternFormula):
        super().__init__()
        self.patternFormula1 = pattern_formula1
        self.patternFormula2 = pattern_formula2

    def substitute(self, object_argument: ObjectArgument, object_variable_argument: ObjectVariableArgument):
        self.patternFormula1.substitute(object_argument, object_variable_argument)
        self.patternFormula2.substitute(object_argument, object_variable_argument)

    def copy(self):
        return Conjunction(self.patternFormula1.copy(), self.patternFormula2.copy())

    def to_string(self):
        return "and(" + self.patternFormula1.to_string() + "," + self.patternFormula2.to_string() + ")"


class ExistentialPattern(PatternFormula):
    patternFormula: PatternFormula
    quantifiedVariable: ObjectVariableArgument

    def __init__(self, quantified_variable: ObjectVariableArgument, pattern_formula: PatternFormula):
        super().__init__()
        self.quantifiedVariable = quantified_variable
        self.patternFormula = pattern_formula

    def apply(self, table_manager: TableManager):
        variable_id = self.quantifiedVariable.variableId
        subformula_evaluation_table = self.patternFormula.apply(table_manager)
        event_id_and_free_variables = [x for x in subformula_evaluation_table.columns
                                       if x not in [variable_id, "ox:evaluation"]]
        subformula_evaluation_table.drop(variable_id, axis=1, inplace=True)
        evaluation_table = subformula_evaluation_table.groupby(event_id_and_free_variables).agg('any').reset_index()
        return evaluation_table

    def substitute(self, object_argument: ObjectArgument, object_variable_argument: ObjectVariableArgument):
        assert not equals(object_variable_argument, self.quantifiedVariable)
        self.patternFormula.substitute(object_argument, object_variable_argument)

    def copy(self):
        return ExistentialPattern(self.quantifiedVariable, self.patternFormula.copy())

    def to_string(self):
        return "ex(" + self.quantifiedVariable.to_string() + "," + self.patternFormula.to_string() + ")"


class UniversalPattern(PatternFormula):
    patternFormula: PatternFormula
    quantifiedVariable: ObjectVariableArgument

    def __init__(self, quantified_variable: ObjectVariableArgument, pattern_formula: PatternFormula):
        super().__init__()
        self.quantifiedVariable = quantified_variable
        self.patternFormula = pattern_formula

    def substitute(self, object_argument: ObjectArgument, object_variable_argument: ObjectVariableArgument):
        assert not equals(object_variable_argument, self.quantifiedVariable)
        self.patternFormula.substitute(object_argument, object_variable_argument)

    def copy(self):
        return UniversalPattern(self.quantifiedVariable, self.patternFormula.copy())

    def to_string(self):
        return "all(" + self.quantifiedVariable.to_string() + "," + self.patternFormula.to_string() + ")"


def get_oa_val_eq_formula(object_variable: ObjectVariableArgument, object_attribute, value):
    arguments = {
        0: object_variable
    }
    return ExistentialPattern(
        object_variable,
        FreePatternFormula(
            FreePattern(
                Oaval_eq(object_attribute, value),
                arguments
            )
        )
    )


def get_oa_val_leq_formula(object_variable: ObjectVariableArgument, object_attribute, value):
    arguments = {
        0: object_variable
    }
    return ExistentialPattern(
        object_variable,
        FreePatternFormula(
            FreePattern(
                Oaval_leq(object_attribute, value),
                arguments
            )
        )
    )


def get_oa_val_geq_formula(object_variable: ObjectVariableArgument, object_attribute, value):
    arguments = {
        0: object_variable
    }
    return ExistentialPattern(
        object_variable,
        FreePatternFormula(
            FreePattern(
                Oaval_geq(object_attribute, value),
                arguments
            )
        )
    )


def get_ot_card_formula(object_type, card):
    arguments = {}
    return FreePatternFormula(
        FreePattern(
            Ot_card(object_type, card),
            arguments
        )
    )


def get_e2o_exists_formula(object_variable: ObjectVariableArgument, qual: str) -> ExistentialPattern:
    arguments = {
        0: object_variable
    }
    return ExistentialPattern(
        object_variable,
        FreePatternFormula(
            FreePattern(
                E2o_r(qual),
                arguments
            )
        )
    )


def get_o2o_exists_exists_formula(object_variable_1: ObjectVariableArgument, qual: str,
                                  object_variable_2: ObjectVariableArgument):
    arguments = {
        0: object_variable_1,
        1: object_variable_2
    }
    return ExistentialPattern(
        object_variable_1,
        ExistentialPattern(
            object_variable_2,
            FreePatternFormula(
                FreePattern(
                    O2o_r(qual),
                    arguments
                )
            )
        )
    )


def get_o2o_exists_forall_formula(object_variable_1: ObjectVariableArgument, qual: str,
                                  object_variable_2: ObjectVariableArgument):
    arguments = {
        0: object_variable_1,
        1: object_variable_2
    }
    return ExistentialPattern(
        object_variable_1,
        UniversalPattern(
            object_variable_2,
            FreePatternFormula(
                FreePattern(
                    O2o_r(qual),
                    arguments
                )
            )
        )
    )


def get_o2o_complete_formula(object_variable: ObjectVariableArgument, qual: str, object_type: str):
    arguments = {
        0: object_variable
    }
    return ExistentialPattern(
        object_variable,
        FreePatternFormula(
            FreePattern(
                O2o_complete(qual, object_type),
                arguments
            )
        )
    )
