from pattern_mining.domains import ObjectArgument, ObjectVariableArgument, equals, Argument
from pattern_mining.pattern_function import PatternFunction
from pattern_mining.table_manager import TableManager


def arguments_validity(pattern_function: PatternFunction, arguments: list):
    arguments_complete = len(arguments) == pattern_function.arity
    all_arguments_variables_or_objects = all(
        type(x) in {ObjectArgument, ObjectVariableArgument} for x in arguments)
    arguments_valid = arguments_complete and all_arguments_variables_or_objects
    return arguments_valid


def arguments_completeness(objects: list):
    all_arguments_bound = all(type(x) == ObjectArgument for x in objects)
    return all_arguments_bound


class FreePattern:
    patternFunction: PatternFunction
    arguments: []  # index -> ObjectArgument | ObjectVariableArgument

    def __init__(self, pattern_function: PatternFunction, arguments: list):
        assert arguments_validity(pattern_function, arguments)
        self.patternFunction = pattern_function
        self.arguments = arguments

    def apply(self, table_manager: TableManager):
        return self.patternFunction.create_function_evaluation_table(table_manager, self.arguments)

    def get_free_variables(self):
        x: ObjectVariableArgument
        return set(x.variableId for x in self.arguments)

    def substitute(self, object_arg: ObjectArgument, object_variable_arg: ObjectVariableArgument):
        for i, arg in self.arguments.items():
            if equals(arg, object_variable_arg):
                self.arguments[i] = object_arg

    def copy(self):
        return FreePattern(self.patternFunction, self.arguments)

    def to_string(self):
        function_identifier = self.patternFunction.to_string()
        arg: Argument
        arg_string = ",".join(map(lambda arg: arg.to_string(), self.arguments))
        identifier = function_identifier + "(" + arg_string + ")"
        return identifier
