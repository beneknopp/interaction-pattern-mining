from pattern_mining.domains import ObjectIdentifier, ObjectVariable
from pattern_mining.pattern_function import PatternFunction


def assert_arguments_validity(pattern_function: PatternFunction, arguments: dict):
    arguments_complete = set(list(arguments.keys())) == set(range(pattern_function.arity))
    all_arguments_variables_or_objects = all(type(x) in {ObjectIdentifier, ObjectVariable} for x in arguments.values())
    valid = arguments_complete and all_arguments_variables_or_objects
    if not valid:
        raise AttributeError()


def assert_arguments_completeness(objects: list):
    all_arguments_bound = all(type(x) == ObjectIdentifier for x in objects)
    if not all_arguments_bound:
        raise ValueError()


class FreePattern:

    __patternFunction: PatternFunction
    __arguments: dict  # index -> Object | ObjectVariable

    def __init__(self, pattern_function: PatternFunction, arguments: dict):
        assert_arguments_validity(pattern_function, arguments)
        self.__patternFunction = pattern_function
        self.__arguments = arguments

    def set_argument(self, index, argument):
        if index > self.__patternFunction.arity:
            raise IndexError()
        self.__arguments[index] = argument

    def evaluate(self, ocel, event):
        argument_bindings = [self.__arguments[i] for i in range(self.__patternFunction.arity)]
        assert_arguments_completeness(argument_bindings)
        self.__patternFunction.apply(ocel, event, argument_bindings)

    def substitute(self, object_variable: ObjectVariable, object_identifier: ObjectIdentifier):
        for i, arg in self.__arguments.items():
            if arg == object_variable:
                self.__arguments[i] = object_identifier
