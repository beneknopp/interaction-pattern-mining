class Argument:

    def __init__(self):
        pass

    def __to_string(self):
        raise NotImplementedError()

    def to_string(self):
        self.__to_string()


class ObjectArgument(Argument):

    def __init__(self, object_type, object_id):
        super().__init__()
        self.objectType = object_type
        self.objectId = object_id

    def to_string(self):
        return self.objectId


class ObjectVariableArgument:

    def __init__(self, object_type, variable_id):
        super().__init__()
        self.objectType = object_type
        self.variableId = variable_id

    def to_string(self):
        return self.variableId


def equals(arg1, arg2):
    if isinstance(arg1, ObjectArgument):
        arg1: ObjectArgument
        if isinstance(arg2, ObjectVariableArgument):
            return False
        arg2: ObjectArgument
        return arg1.objectType == arg2.objectType and arg1.objectId == arg2.objectId
    arg1: ObjectVariableArgument
    if isinstance(arg2, ObjectArgument):
        return False
    arg2: ObjectVariableArgument
    return arg1.objectType == arg2.objectType and arg1.variableId == arg2.variableId
