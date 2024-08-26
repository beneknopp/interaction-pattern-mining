from enum import Enum

from pattern_mining.PATTERN_FORMULAS import ExistentialPattern, UniversalPattern, Negation, Conjunction, Disjunction, \
    FreePatternFormula
from pattern_mining.PATTERN_FUNCTIONS import Eaval_eq, Eaval_leq, Eaval_geq, Oaval_eq, Oaval_geq, Oaval_leq, Ot_card, \
    E2o_r, O2o_r, O2o_complete
from pattern_mining.domains import ObjectVariableArgument, ObjectArgument
from pattern_mining.free_pattern import FreePattern
from pattern_mining.pattern_formula import PatternFormula


class PatternParser:

    def __init__(self, variable_type_lookup, objects):
        self.variable_type_lookup = variable_type_lookup
        self.objects = objects
        self.formula = None

    def parse(self, pattern_id: str) -> bool:
        formula = self.__parse_recursively(pattern_id)
        self.formula = formula
        return formula.is_well_formed()

    def __parse_recursively(self, pattern_id: str):
        operator_id = pattern_id[:pattern_id.index("(")]
        if operator_id in ["ex", "all"]:
            variable = pattern_id[pattern_id.index("(")+1:pattern_id.index(",")]
            variable_type_prefix = "".join(filter(lambda char: not char.isdigit(), variable))
            object_type = self.variable_type_lookup[variable_type_prefix]
            inner_pattern_id = pattern_id[pattern_id.index(",")+1:-1]
            inner_formula = self.__parse_recursively(inner_pattern_id)
            if operator_id == "ex":
                return ExistentialPattern(ObjectVariableArgument(object_type, variable), inner_formula)
            return UniversalPattern(ObjectVariableArgument(object_type, variable), inner_formula)
        if operator_id in ["and", "or"]:
            outer_open_index = pattern_id.index("(")
            first_formula_open_index = pattern_id[outer_open_index+1:].index("(")
            first_formula_closing_index = self.__find_closing_bracket_index(pattern_id, first_formula_open_index)
            second_formula_open_index = pattern_id[first_formula_closing_index+1:].index("(")
            second_formula_closing_index = self.__find_closing_bracket_index(pattern_id, second_formula_open_index)
            first_inner_pattern_id = pattern_id[first_formula_open_index+1:first_formula_closing_index]
            second_inner_pattern_id = pattern_id[second_formula_open_index+1:second_formula_closing_index]
            first_inner_formula = self.__parse_recursively(first_inner_pattern_id)
            second_inner_formula = self.__parse_recursively(second_inner_pattern_id)
            if operator_id == "and":
                return Conjunction(first_inner_formula, second_inner_formula)
            return Disjunction(first_inner_formula, second_inner_formula)
        if operator_id == "not":
            inner_pattern_id = pattern_id[pattern_id.index("(")+1:-1]
            inner_formula = self.__parse_recursively(inner_pattern_id)
            return Negation(inner_formula)
        term = pattern_id
        return self.__get_free_pattern_formula(term)

    def __get_free_pattern_formula(self, term):
        pattern_function = None
        arguments = self.__parse_arguments_strs(term)
        if term.startswith("eaval_eq_"):
            parameter_opening_index = term.index("{")
            parameter_closing_index = term.index("}")
            event_attribute, value = term[parameter_opening_index+1:parameter_closing_index].split(",")
            pattern_function = Eaval_eq(event_attribute, value)
        elif term.startswith("eaval_leq_"):
            parameter_opening_index = term.index("{")
            parameter_closing_index = term.index("}")
            event_attribute, value = term[parameter_opening_index+1:parameter_closing_index].split(",")
            value = float(value)
            pattern_function = Eaval_leq(event_attribute, value)
        elif term.startswith("eaval_geq_"):
            parameter_opening_index = term.index("{")
            parameter_closing_index = term.index("}")
            event_attribute, value = term[parameter_opening_index+1:parameter_closing_index].split(",")
            value = float(value)
            pattern_function = Eaval_geq(event_attribute, value)
        elif term.startswith("oaval_eq"):
            parameter_opening_index = term.index("{")
            parameter_closing_index = term.index("}")
            object_attribute, value = term[parameter_opening_index + 1:parameter_closing_index].split(",")
            pattern_function = Oaval_eq(object_attribute, value)
        elif term.startswith("oaval_leq"):
            parameter_opening_index = term.index("{")
            parameter_closing_index = term.index("}")
            object_attribute, value = term[parameter_opening_index + 1:parameter_closing_index].split(",")
            value = float(value)
            pattern_function = Oaval_leq(object_attribute, value)
        elif term.startswith("oaval_geq"):
            parameter_opening_index = term.index("{")
            parameter_closing_index = term.index("}")
            object_attribute, value = term[parameter_opening_index + 1:parameter_closing_index].split(",")
            value = float(value)
            pattern_function = Oaval_geq(object_attribute, value)
        elif term.startswith("ot_card"):
            parameter_opening_index = term.index("{")
            parameter_closing_index = term.index("}")
            object_type, card = term[parameter_opening_index + 1:parameter_closing_index].split(",")
            card = int(card)
            pattern_function = Ot_card(object_type, card)
        elif term.startswith("e2o_"):
            parameter_opening_index = term.index("{")
            parameter_closing_index = term.index("}")
            qualifier = term[parameter_opening_index + 1:parameter_closing_index]
            pattern_function = E2o_r(qualifier)
        elif term.startswith("o2o_"):
            parameter_opening_index = term.index("{")
            parameter_closing_index = term.index("}")
            qualifier = term[parameter_opening_index + 1:parameter_closing_index]
            pattern_function = O2o_r(qualifier)
        elif term.startswith("o2o_complete_"):
            parameter_opening_index = term.index("{")
            parameter_closing_index = term.index("}")
            qualifier, object_type = term[parameter_opening_index + 1:parameter_closing_index].split(",")
            pattern_function = O2o_complete(qualifier, object_type)
        return FreePatternFormula(FreePattern(pattern_function, arguments))

    def get(self) -> PatternFormula:
        return self.formula

    def __find_closing_bracket_index(self, s, open_index):
        nested_level = 0
        for i in range(open_index + 1, len(s)):
            char = s[i]
            if char == '(':
                nested_level += 1
            elif char == ')':
                if nested_level == 0:
                    return i
                else:
                    nested_level -= 1
        raise ValueError

    def __parse_arguments_strs(self, term):
        term_r = term[::-1]
        arguments_str_r = term_r[term_r.index(")") + 1: term_r.index("(")]
        arguments_str = arguments_str_r[::-1]
        arguments_strs = arguments_str.split(",")
        if len(arguments_strs) == 1 and len(arguments_strs[0]) == 0:
            return []
        arguments = []
        for argument_str in arguments_strs:
            prefix = ""
            digit_found = False
            i = 0
            for char in argument_str:
                if char.isdigit():
                    digit_found = True
                    break
                prefix += char
                i = i + 1
            if digit_found or i == len(argument_str):
                if prefix in self.variable_type_lookup:
                    object_type = self.variable_type_lookup[prefix]
                    is_digit = True
                    while is_digit and i < len(argument_str):
                        char = argument_str[i]
                        is_digit = char.isdigit()
                        prefix += char
                        i = i + 1
                    if i == len(argument_str):
                        variable_id = argument_str
                        argument = ObjectVariableArgument(object_type, variable_id)
                        arguments.append(argument)
                        continue
            object_id = argument_str
            if object_id not in self.objects["ocel:oid"]:
                raise ValueError("Argument '" + argument_str + "' is neither an object identifier in this log, nor is it a valid variable identifier.")
            object_type = self.objects[self.objects["ocel:oid"] == object_id]["ocel:type"]
            argument = ObjectArgument(object_type, object_id)
            arguments.append(argument)
        return arguments



