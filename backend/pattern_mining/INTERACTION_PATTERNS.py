from pattern_mining.free_pattern import FreePattern
from pattern_mining.interaction_pattern import InteractionPattern


class FreePatternWrapper(InteractionPattern):

    freePattern: FreePattern

    def __init__(self, free_pattern):
        super().__init__()
        self.freePattern = free_pattern

    def __evaluate(self, ocel, event):
        self.freePattern.evaluate(ocel, event)

    def __substitute(self, object_variable, object_id):
        self.freePattern.substitute(object_variable, object_id)
        pass


class ExistentialPattern(InteractionPattern):

    ipa: InteractionPattern

    def __init__(self, ovar: ObjectVariable, ipa: InteractionPattern):
        self.ipa = ipa
        super().__init__()

    def __evaluate(self, ocel, event):
        self.ipa.evaluate()



