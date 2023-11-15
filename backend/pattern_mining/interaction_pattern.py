class InteractionPattern():

    def __init__(self):
        pass

    def __evaluate(self, ocel, event):
        raise NotImplementedError()

    def __substitute(self, object_variable, object_id):
        raise NotImplementedError()

    def evaluate(self, ocel, event):
        self.__evaluate(ocel, event)

    def substitute(self, object_variable, object_id):
        self.__substitute(object_variable, object_id)
