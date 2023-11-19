import pandas as pd
from pm4py import OCEL

from pattern_mining.PATTERN_FUNCTIONS import Oaval_eq, Oaval_leq, Oaval_geq, Ot_card, O2o_r, O2o_complete, E2o_r, \
    Eaval_eq
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

    def get_free_variables(self):
        return self.freePattern.get_free_variables()

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

    def get_free_variables(self):
        return self.patternFormula.get_free_variables()

    def substitute(self, object_argument: ObjectArgument, object_variable_argument: ObjectVariableArgument):
        self.patternFormula.substitute(object_argument, object_variable_argument)

    def apply(self, table_manager):
        subformula_evaluation_table = self.patternFormula.apply(table_manager)
        evaluation_table = subformula_evaluation_table[:]
        evaluation_table["ox:evaluation"] = ~evaluation_table["ox:evaluation"]
        return evaluation_table

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
        evaluation_table1 = self.patternFormula1.apply(table_manager)
        evaluation_table2 = self.patternFormula2.apply(table_manager)
        free_variables1 = self.patternFormula1.get_free_variables()
        free_variables2 = self.patternFormula2.get_free_variables()
        joint_variables = free_variables1.intersection(free_variables2)
        evaluation_table = pd.merge(
            evaluation_table1, evaluation_table2,
            how="inner",
            on=["ocel:eid"] + list(joint_variables)
        )
        evaluation_table["ox:evaluation"] = evaluation_table["ox:evaluation_x"] | evaluation_table["ox:evaluation_y"]
        evaluation_table.drop(columns=["ox:evaluation_x", "ox:evaluation_y"], inplace=True)
        return evaluation_table

    def get_free_variables(self):
        return self.patternFormula1.get_free_variables().union(self.patternFormula2.get_free_variables())

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

    def apply(self, table_manager):
        evaluation_table1 = self.patternFormula1.apply(table_manager)
        evaluation_table2 = self.patternFormula2.apply(table_manager)
        free_variables1 = self.patternFormula1.get_free_variables()
        free_variables2 = self.patternFormula2.get_free_variables()
        free_variables1_ids = {x.variableId for x in free_variables1}
        free_variables2_ids = {y.variableId for y in free_variables2}
        joint_variables_ids = free_variables1_ids.intersection(free_variables2_ids)
        evaluation_table = pd.merge(
            evaluation_table1, evaluation_table2,
            how="inner",
            on=["ocel:eid"] + list(joint_variables_ids)
        )
        evaluation_table["ox:evaluation"] = evaluation_table["ox:evaluation_x"] & evaluation_table["ox:evaluation_y"]
        evaluation_table.drop(columns=["ox:evaluation_x", "ox:evaluation_y"], inplace=True)
        return evaluation_table

    def get_free_variables(self):
        return self.patternFormula1.get_free_variables().union(self.patternFormula2.get_free_variables())

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

    def get_free_variables(self):
        return set(x for x in self.patternFormula.get_free_variables() if not equals(x, self.quantifiedVariable))

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

    def get_free_variables(self):
        return set(x for x in self.patternFormula.get_free_variables() if not equals(x, self.quantifiedVariable))

    def substitute(self, object_argument: ObjectArgument, object_variable_argument: ObjectVariableArgument):
        assert not equals(object_variable_argument, self.quantifiedVariable)
        self.patternFormula.substitute(object_argument, object_variable_argument)

    def copy(self):
        return UniversalPattern(self.quantifiedVariable, self.patternFormula.copy())

    def apply(self, table_manager: TableManager):
        return Negation(ExistentialPattern(self.quantifiedVariable, Negation(self.patternFormula.copy()))) \
            .apply(table_manager)

    def to_string(self):
        return "all(" + self.quantifiedVariable.to_string() + "," + self.patternFormula.to_string() + ")"


def get_oa_val_eq_formula(object_variable: ObjectVariableArgument, object_attribute, value):
    arguments = [object_variable]
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
    arguments = [object_variable]
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
    arguments = [object_variable]
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
    arguments = []
    return FreePatternFormula(
        FreePattern(
            Ot_card(object_type, card),
            arguments
        )
    )

def get_eaval_eq_exists_pattern(attribute: str, value) -> ExistentialPattern:
    arguments = []
    return FreePatternFormula(
            FreePattern(
                Eaval_eq(attribute, value),
                arguments
            )
        )

def get_oaval_eq_exists_pattern(object_variable: ObjectVariableArgument, attribute: str, value) -> ExistentialPattern:
    arguments = [object_variable]
    return ExistentialPattern(
        object_variable,
        FreePatternFormula(
            FreePattern(
                Oaval_eq(attribute, value),
                arguments
            )
        )
    )


def get_e2o_exists_formula(object_variable: ObjectVariableArgument, qual: str) -> ExistentialPattern:
    arguments = [object_variable]
    return ExistentialPattern(
        object_variable,
        FreePatternFormula(
            FreePattern(
                E2o_r(qual),
                arguments
            )
        )
    )


def get_e2o_forall_formula(object_variable: ObjectVariableArgument, qual: str) -> UniversalPattern:
    arguments = [object_variable]
    return UniversalPattern(
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
    arguments = [object_variable_1, object_variable_2]
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


def get_o2o_forall_exists_formula(object_variable_1: ObjectVariableArgument, qual: str,
                                  object_variable_2: ObjectVariableArgument):
    arguments = [object_variable_1, object_variable_2]
    return UniversalPattern(
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
    arguments = [object_variable_1, object_variable_2]
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
    arguments = [object_variable]
    return ExistentialPattern(
        object_variable,
        FreePatternFormula(
            FreePattern(
                O2o_complete(qual, object_type),
                arguments
            )
        )
    )


def get_existential_patterns_merge(existential_patt1: ExistentialPattern,
                                   existential_patt2: ExistentialPattern) -> ExistentialPattern:
    quantified_variable = existential_patt1.quantifiedVariable
    if not equals(quantified_variable, existential_patt2.quantifiedVariable):
        raise ValueError()
    return ExistentialPattern(
        quantified_variable,
        Conjunction(
            existential_patt1.patternFormula.copy(),
            existential_patt2.patternFormula.copy()
        )
    )
