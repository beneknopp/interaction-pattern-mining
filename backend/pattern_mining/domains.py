class Argument:

    def __init__(self, object_type, id):
        self.objectType = object_type
        self.id = id

    def __to_string(self):
        raise NotImplementedError()

    def to_string(self):
        return self.id


class ObjectArgument(Argument):
    objectType: str
    id: str

    def __init__(self, object_type, object_id):
        super().__init__(object_type, object_id)


class ObjectVariableArgument(Argument):
    objectType: str
    id: str

    def __init__(self, object_type, variable_id):
        super().__init__(object_type, variable_id)


def equals(arg1, arg2):
    if isinstance(arg1, ObjectArgument):
        arg1: ObjectArgument
        if isinstance(arg2, ObjectVariableArgument):
            return False
        arg2: ObjectArgument
        return arg1.objectType == arg2.objectType and arg1.id == arg2.id
    arg1: ObjectVariableArgument
    if isinstance(arg2, ObjectArgument):
        return False
    arg2: ObjectVariableArgument
    return arg1.objectType == arg2.objectType and arg1.id == arg2.id
