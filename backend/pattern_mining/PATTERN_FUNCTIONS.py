from pattern_mining.pattern_function import PatternFunction

from pattern_mining.GROUND_PATTERNS import EAVAL_EQ, EAVAL_LEQ, E2O_R, O2O_R, O2O_COMPLETE, OAVAL_EQ, OAVAL_LEQ, \
    OAVAL_GEQ, EAVAL_GEQ, OT_CARD


class Eaval_eq(PatternFunction):

    object_arity = 0

    def __init__(self, event_attribute, value):
        super().__init__(self.object_arity)
        self.eventAttribute = event_attribute
        self.value = value

    def bind(self, object_ids):
        assert len(object_ids) == self.object_arity
        return EAVAL_EQ(self.eventAttribute, self.value)

    def to_string(self):
        return "eaval_eq_{" + self.eventAttribute + "," + str(self.value) + "}"


class Eaval_leq(PatternFunction):

    object_arity = 0

    def __init__(self, event_attribute, value):
        super().__init__(self.object_arity)
        self.eventAttribute = event_attribute
        self.value = value

    def bind(self, object_ids):
        assert len(object_ids) == self.object_arity
        return EAVAL_LEQ(self.eventAttribute, self.value)

    def to_string(self):
        return "eaval_leq_{" + self.eventAttribute + "," + str(self.value) + "}"


class Eaval_geq(PatternFunction):

    object_arity = 0

    def __init__(self, event_attribute, value):
        super().__init__(self.object_arity)
        self.eventAttribute = event_attribute
        self.value = value

    def bind(self, object_ids):
        assert len(object_ids) == self.object_arity
        return EAVAL_GEQ(self.eventAttribute, self.value)

    def to_string(self):
        return "eaval_geq_{" + self.eventAttribute + "," + str(self.value) + "}"


class Oaval_eq(PatternFunction):

    object_arity = 1

    def __init__(self, object_attribute, value):
        super().__init__(self.object_arity)
        self.objectAttribute = object_attribute
        self.value = value

    def bind(self, object_ids):
        assert len(object_ids) == self.object_arity
        return OAVAL_EQ(self.objectAttribute, self.value, object_ids[0])

    def to_string(self):
        return "oaval_eq_{" + self.objectAttribute + "," + str(self.value) + "}"


class Oaval_leq(PatternFunction):

    object_arity = 1

    def __init__(self, object_attribute, value):
        super().__init__(self.object_arity)
        self.objectAttribute = object_attribute
        self.value = value

    def bind(self, object_ids):
        assert len(object_ids) == self.object_arity
        return OAVAL_LEQ(self.objectAttribute, self.value, object_ids[0])

    def to_string(self):
        return "oaval_leq_{" + self.objectAttribute + "," + str(self.value) + "}"


class Oaval_geq(PatternFunction):

    object_arity = 1

    def __init__(self, object_attribute, value):
        super().__init__(self.object_arity)
        self.objectAttribute = object_attribute
        self.value = value

    def bind(self, object_ids):
        assert len(object_ids) == self.object_arity
        return OAVAL_GEQ(self.objectAttribute, self.value, object_ids[0])

    def to_string(self):
        return "oaval_geq_{" + self.objectAttribute + "," + str(self.value) + "}"


class E2o_r(PatternFunction):

    object_arity = 1

    def __init__(self, qual):
        super().__init__(self.object_arity)
        self.qual = qual

    def bind(self, object_ids):
        assert len(object_ids) == self.object_arity
        return E2O_R(self.qual, object_ids[0])

    def to_string(self):
        return "e2o_{" + self.qual + "}"


class O2o_r(PatternFunction):

    object_arity = 2

    def __init__(self, qual):
        super().__init__(self.object_arity)
        self.qual = qual

    def bind(self, object_ids):
        assert len(object_ids) == self.object_arity
        return O2O_R(self.qual, object_ids[0], object_ids[1])

    def to_string(self):
        return "o2o_{" + self.qual + "}"


class O2o_complete(PatternFunction):

    object_arity = 1

    def __init__(self, qual, object_type):
        super().__init__(self.object_arity)
        self.qual = qual
        self.objectType = object_type

    def bind(self, object_ids):
        assert len(object_ids) == self.object_arity
        return O2O_COMPLETE(self.qual, self.objectType, object_ids[0])

    def to_string(self):
        return "o2o_complete_{" + self.qual + "," + self.objectType + "}"


class Ot_card(PatternFunction):

    object_arity = 0

    def __init__(self, object_type, card):
        super().__init__(self.object_arity)
        self.objectType = object_type
        self.card = card

    def bind(self, object_ids):
        assert len(object_ids) == self.object_arity
        return OT_CARD(self.objectType, self.card)

    def to_string(self):
        return "ot_card_{" + self.objectType + "," + str(self.card) + "}"
