from pattern_mining.pattern_function import PatternFunction


class EAVAL_EQ(PatternFunction):

    object_arity = 0
    function_identifier = "EAVAL_EQ"
    pattern_syntax = "'(' EATTR ',' VAL ')'"

    def __init__(self, ea, v):
        super().__init__(self.object_arity)
        self.ea = ea
        self.v = v
    def apply_(self, ocel, event, objects):
        events = ocel.events
        event_row = events[events["ocel:eid"] == event]
        event_v = event_row[self.ea]
        return str(self.v) == str(event_v)

    def get_pattern_syntax_(self):
        return self.function_identifier + self.pattern_syntax

    @classmethod
    def parse_(cls, definition):
        definition_split = [x.strip() for x in definition.split(",")]
        assert definition_split[0].startswith("EAVAL(")
        assert definition_split[1].endswith(")")
        ea = definition_split[0].removeprefix("EAVAL(").strip()
        v = definition_split[1][:-1]
        return cls(ea, v)


class EAVAL_LEQ(PatternFunction):

    object_arity = 0
    function_identifier = "EAVAL_LEQ"
    pattern_syntax = "'(' EATTR ',' VAL ')'"

    def __init__(self, ea, v):
        super().__init__(self.object_arity)
        self.ea = ea
        self.v = v

    def apply_(self, ocel, event, objects):
        events = ocel.events
        event_row = events[events["ocel:eid"] == event]
        event_v = event_row[self.ea]
        return float(event_v) <= float(self.v)

    def get_pattern_syntax_(self):
        return self.function_identifier + self.pattern_syntax

    @classmethod
    def parse_(cls, definition):
        definition_split = [x.strip() for x in definition.split(",")]
        assert definition_split[0].startswith("EAVAL_LEQ(")
        assert definition_split[1].endswith(")")
        ea = definition_split[0].removeprefix("EAVAL_LEQ(").strip()
        v = definition_split[1][:-1]
        return cls(ea, v)


class E2O_R(PatternFunction):

    object_arity = 1
    function_identifier = "E2O_R"
    pattern_syntax = "'(' QUAL ',' OBJ ')'"

    def __init__(self, r):
        super().__init__(self.object_arity)
        self.r = r

    def apply_(self, ocel, event, objects):
        object = objects[0]
        relations = ocel.relations
        condition1 = relations["ocel:eid"] == event
        condition2 = relations["ocel:qualifier"] == self.r
        condition3 = relations["ocel:oid"] == object
        return len(relations[condition1 & condition2 & condition3]) > 0

    def get_pattern_syntax_(self):
        return self.function_identifier + self.pattern_syntax

    @classmethod
    def parse_(cls, definition):
        raise NotImplementedError()


class O2O_R(PatternFunction):

    object_arity = 2
    function_identifier = "O2O_R"
    pattern_syntax = "'(' QUAL ',' OBJ ',' OBJ ')'"

    def __init__(self, r):
        super().__init__(self.object_arity)
        self.r = r

    def apply_(self, ocel, event, objects):
        object1, object2 = objects
        o2o = ocel.o2o
        o2o_condition1 = o2o["ocel:oid"] == object1
        o2o_condition2 = o2o["ocel:qualifier"] == self.r
        o2o_condition3 = o2o["ocel:oid_2"] == object2
        o2o_condition = len(o2o[o2o_condition1 & o2o_condition2 & o2o_condition3]) > 0
        if not o2o_condition:
            return False
        e2o = ocel.relations
        e2o_condition1 = e2o["ocel:eid"] == event
        e2o_condition2a = e2o["ocel:oid"] == object1
        e2o_condition2b = e2o["ocel:oid"] == object2
        e2o_condition_a = len(e2o[e2o_condition1 & e2o_condition2a]) > 0
        e2o_condition_b = len(e2o[e2o_condition1 & e2o_condition2b]) > 0
        return e2o_condition_a and e2o_condition_b

    def get_pattern_syntax_(self):
        return self.function_identifier + self.pattern_syntax

    @classmethod
    def parse_(cls, definition):
        raise NotImplementedError()


class O2O_COMPLETE(PatternFunction):

    object_arity = 1
    function_identifier = "O2O_COMPLETE"
    pattern_syntax = "'(' QUAL ',' OBJ ')'"

    def __init__(self, r):
        super().__init__(self.object_arity)
        self.r = r

    def apply_(self, ocel, event, objects):
        object = objects[0]
        o2o = ocel.o2o
        o2o_condition1 = o2o["ocel:oid"] == object
        o2o_condition2 = o2o["ocel:qualifier"] == self.r
        r_objects = set(o2o[o2o_condition1 & o2o_condition2]["ocel:oid_2"].values)
        e2o = ocel.relations
        event_objects = set(e2o[e2o["ocel:eid"] == event]["ocel:oid"].values)
        e2o_condition =  r_objects.issubset(event_objects)
        return e2o_condition

    def get_pattern_syntax_(self):
        return self.function_identifier + self.pattern_syntax

    @classmethod
    def parse_(cls, definition):
        raise NotImplementedError()