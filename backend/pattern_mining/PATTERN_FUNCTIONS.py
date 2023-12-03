import pandas as pd

from pattern_mining.domains import Argument, ObjectArgument, ObjectVariableArgument
from pattern_mining.pattern_function import PatternFunction

from pattern_mining.GROUND_PATTERNS import EAVAL_EQ, EAVAL_LEQ, E2O_R, O2O_R, O2O_COMPLETE, OAVAL_EQ, OAVAL_LEQ, \
    OAVAL_GEQ, EAVAL_GEQ, OT_CARD
from pattern_mining.table_manager import TableManager


class Eaval_eq(PatternFunction):
    object_arity = 0

    def __init__(self, event_attribute, value):
        super().__init__(self.object_arity)
        self.eventAttribute = event_attribute
        self.value = value

    def bind(self, object_ids):
        assert len(object_ids) == self.object_arity
        return EAVAL_EQ(self.eventAttribute, self.value)

    def create_function_evaluation_table(self, table_manager: TableManager, arguments):
        evaluated = table_manager.get_event_table()
        evaluated["ox:evaluation"] = evaluated[self.eventAttribute] == self.value
        return evaluated[["ocel:eid", "ox:evaluation"]]

    def get_ebnf_descriptor(self):
        raise NotImplementedError()

    def to_string(self):
        return "eaval_eq_{" + self.eventAttribute + "," + str(self.value) + "}"

    def to_TeX(self, args):
        return self.eventAttribute + "=" + str(self.value)


class Eaval_leq(PatternFunction):
    object_arity = 0

    def __init__(self, event_attribute, value):
        super().__init__(self.object_arity)
        self.eventAttribute = event_attribute
        self.value = value

    def bind(self, object_ids):
        assert len(object_ids) == self.object_arity
        return EAVAL_LEQ(self.eventAttribute, self.value)

    def create_function_evaluation_table(self, table_manager: TableManager, arguments):
        evaluated = table_manager.get_event_table()
        evaluated["ox:evaluation"] = evaluated[self.eventAttribute] <= self.value
        return evaluated[["ocel:eid", "ox:evaluation"]]

    def to_string(self):
        return "eaval_leq_{" + self.eventAttribute + "," + str(self.value) + "}"

    def to_TeX(self, args):
        return self.eventAttribute + "\\leq" + str(self.value)

    def get_ebnf_descriptor(self):
        raise NotImplementedError()


class Eaval_geq(PatternFunction):
    object_arity = 0

    def __init__(self, event_attribute, value):
        super().__init__(self.object_arity)
        self.eventAttribute = event_attribute
        self.value = value

    def bind(self, object_ids):
        assert len(object_ids) == self.object_arity
        return EAVAL_GEQ(self.eventAttribute, self.value)

    def create_function_evaluation_table(self, table_manager: TableManager, arguments):
        evaluated = table_manager.get_event_table()
        evaluated["ox:evaluation"] = evaluated[self.eventAttribute] >= self.value
        return evaluated[["ocel:eid", "ox:evaluation"]]

    def to_string(self):
        return "eaval_geq_{" + self.eventAttribute + "," + str(self.value) + "}"

    def to_TeX(self, args):
        return self.eventAttribute + "\\geq" + str(self.value)

    def get_ebnf_descriptor(self):
        raise NotImplementedError()



class Oaval_eq(PatternFunction):
    object_arity = 1

    def __init__(self, object_attribute, value):
        super().__init__(self.object_arity)
        self.objectAttribute = object_attribute
        self.value = value

    def bind(self, object_ids):
        assert len(object_ids) == self.object_arity
        return OAVAL_EQ(self.objectAttribute, self.value, object_ids[0])

    def create_function_evaluation_table(self, table_manager: TableManager, arguments):
        arg: ObjectVariableArgument = arguments[0]
        variable_id = arg.id
        object_type = arg.objectType
        evaluated = table_manager.get_event_interaction_table()
        evaluated.rename(columns={"ocel:oid": variable_id}, inplace=True)
        evaluated = evaluated[evaluated["ocel:type"] == object_type]
        evaluated["ox:evaluation"] = evaluated[self.objectAttribute] == self.value
        return evaluated[["ocel:eid", variable_id, "ox:evaluation"]]

    def to_string(self):
        return "oaval_eq_{" + self.objectAttribute + "," + str(self.value) + "}"

    def to_TeX(self, args):
        return self.objectAttribute + "(" + args[0] + ")" + "=" + str(self.value)

    def get_ebnf_descriptor(self):
        raise NotImplementedError()


class Oaval_leq(PatternFunction):
    object_arity = 1

    def __init__(self, object_attribute, value):
        super().__init__(self.object_arity)
        self.objectAttribute = object_attribute
        self.value = value

    def bind(self, object_ids):
        assert len(object_ids) == self.object_arity
        return OAVAL_LEQ(self.objectAttribute, self.value, object_ids[0])

    def create_function_evaluation_table(self, table_manager: TableManager, arguments):
        arg: ObjectVariableArgument = arguments[0]
        variable_id = arg.id
        object_type = arg.objectType
        evaluated = table_manager.get_event_interaction_table()
        evaluated.rename(columns={"ocel:oid": variable_id}, inplace=True)
        evaluated = evaluated[evaluated["ocel:type"] == object_type]
        evaluated["ox:evaluation"] = evaluated[self.objectAttribute] <= self.value
        return evaluated[["ocel:eid", variable_id, "ox:evaluation"]]

    def to_string(self):
        return "oaval_leq_{" + self.objectAttribute + "," + str(self.value) + "}"

    def to_TeX(self, args):
        return self.objectAttribute + "(" + args[0] + ")" + "\\leq" + str(self.value)

    def get_ebnf_descriptor(self):
        raise NotImplementedError()


class Oaval_geq(PatternFunction):
    object_arity = 1

    def __init__(self, object_attribute, value):
        super().__init__(self.object_arity)
        self.objectAttribute = object_attribute
        self.value = value

    def bind(self, object_ids):
        assert len(object_ids) == self.object_arity
        return OAVAL_GEQ(self.objectAttribute, self.value, object_ids[0])

    def create_function_evaluation_table(self, table_manager: TableManager, arguments):
        arg: ObjectVariableArgument = arguments[0]
        variable_id = arg.id
        object_type = arg.objectType
        evaluated = table_manager.get_event_interaction_table()
        evaluated.rename(columns={"ocel:oid": variable_id}, inplace=True)
        evaluated = evaluated[evaluated["ocel:type"] == object_type]
        evaluated["ox:evaluation"] = evaluated[self.objectAttribute] >= self.value
        return evaluated[["ocel:eid", variable_id, "ox:evaluation"]]

    def to_string(self):
        return "oaval_geq_{" + self.objectAttribute + "," + str(self.value) + "}"

    def to_TeX(self, args):
        return self.objectAttribute + "(" + args[0] + ")" + "\\geq" + str(self.value)

    def get_ebnf_descriptor(self):
        raise NotImplementedError()


class Ot_card(PatternFunction):
    object_arity = 0

    def __init__(self, object_type, card):
        super().__init__(self.object_arity)
        self.objectType = object_type
        self.card = card

    def bind(self, object_ids):
        assert len(object_ids) == self.object_arity
        return OT_CARD(self.objectType, self.card)

    def create_function_evaluation_table(self, table_manager: TableManager, arguments):
        interaction_table = table_manager.get_event_interaction_table()
        evaluated = interaction_table.groupby("ocel:eid").apply(lambda group: group[group["ocel:type"] == self.objectType]["ocel:oid"].nunique())\
            .reset_index(name="card")
        evaluated["ox:evaluation"] = evaluated["card"] == self.card
        return evaluated[["ocel:eid", "ox:evaluation"]]

    def to_string(self):
        return "ot_card_{" + self.objectType + "," + str(self.card) + "}"

    def to_TeX(self, args):
        return "#_{" + self.objectType + "}=" + self.card

    def get_ebnf_descriptor(self):
        raise NotImplementedError()



class E2o_r(PatternFunction):
    object_arity = 1

    def __init__(self, qual):
        super().__init__(self.object_arity)
        self.qual = qual

    def bind(self, object_ids):
        assert len(object_ids) == self.object_arity
        return E2O_R(self.qual, object_ids[0])

    def create_function_evaluation_table(self, table_manager: TableManager, arguments):
        arg: ObjectVariableArgument = arguments[0]
        variable_id = arg.id
        object_type = arg.objectType
        interaction_table = table_manager.get_event_interaction_table()
        interaction_table["is_r"] = (interaction_table["ocel:qualifier"] == self.qual)
        interaction_table["is_type"] = (interaction_table["ocel:type"] == object_type)
        interaction_table["is_r_of_type"] = (interaction_table["is_r"] & interaction_table["is_type"])
        evaluated = interaction_table.groupby(["ocel:eid","ocel:oid"])['is_r_of_type'].max().reset_index(name="ox:evaluation")
        evaluated.rename(columns={"ocel:oid": variable_id}, inplace=True)
        return evaluated[["ocel:eid", variable_id, "ox:evaluation"]]

    def to_string(self):
        return "e2o_{" + self.qual + "}"

    def to_TeX(self, args):
        return self.qual + "(" + args[0] + ")"

    def get_ebnf_descriptor(self):
        raise NotImplementedError()


class O2o_r(PatternFunction):
    object_arity = 2

    def __init__(self, qual):
        super().__init__(self.object_arity)
        self.qual = qual

    def bind(self, object_ids):
        assert len(object_ids) == self.object_arity
        return O2O_R(self.qual, object_ids[0], object_ids[1])

    def create_function_evaluation_table(self, table_manager: TableManager, arguments):
        arg1, arg2 = arguments
        arg1: ObjectVariableArgument
        arg2: ObjectVariableArgument
        variable_id1 = arg1.id
        variable_id2 = arg2.id
        source_object_type = arg1.objectType
        target_object_type = arg2.objectType

        source_type_event_objects = table_manager.get_event_objects(source_object_type)
        source_type_event_objects.rename(columns={"ocel:oid": "ocel:oid_1"}, inplace=True)
        target_type_event_objects = table_manager.get_event_objects(target_object_type)
        target_type_event_objects.rename(columns={"ocel:oid": "ocel:oid_2"}, inplace=True)

        evaluated = source_type_event_objects.merge(target_type_event_objects, on="ocel:eid")
        evaluated.rename(columns={"ocel:oid_1": variable_id1, "ocel:oid_2": variable_id2}, inplace=True)
        evaluated.drop_duplicates(inplace=True)

        o2o = table_manager.get_o2o(source_object_type)
        evaluated = evaluated.merge(o2o, left_on=[variable_id1, variable_id2], right_on=["ocel:oid", "ocel:oid_2"], how="left")
        evaluated["r_flag"] = evaluated["ocel:qualifier"] == self.qual
        evaluated = evaluated.groupby(["ocel:eid", variable_id1, variable_id2])['r_flag'].sum().reset_index(name="r_flags")
        evaluated["ox:evaluation"] = evaluated["r_flags"] > 0
        return evaluated[["ocel:eid", variable_id1, variable_id2, "ox:evaluation"]]

    def to_string(self):
        return "o2o_{" + self.qual + "}"

    def to_TeX(self, args):
        return self.qual + "(" + args[0] + "," + args[1] + ")"

    def get_ebnf_descriptor(self):
        raise NotImplementedError()



class O2o_complete(PatternFunction):
    object_arity = 1

    def __init__(self, qual, object_type):
        super().__init__(self.object_arity)
        self.qual = qual
        self.objectType = object_type
        self.bindingsTable = None

    def create_function_evaluation_table(self, table_manager: TableManager, arguments):
        arg = arguments[0]
        arg: ObjectVariableArgument
        variable_id = arg.id
        source_object_type = arg.objectType
        target_object_type = self.objectType
        source_type_event_objects = table_manager.get_event_objects(source_object_type)
        target_type_event_objects = table_manager.get_event_objects(target_object_type)
        evaluated = source_type_event_objects[:]
        evaluated.rename(columns={"ocel:oid": variable_id}, inplace=True)
        o2o_table = table_manager.get_o2o(source_object_type)
        source_type_event_objects["ocel:qualifier"] = self.qual
        target_type_event_objects["ocel:qualifier"] = self.qual
        source_type_event_objects["target_object_type"] = target_object_type
        object_interactions = table_manager.get_object_interaction_table()
        relations_at_object = source_type_event_objects.merge(o2o_table,
                                                              left_on=["ocel:oid", "ocel:qualifier",
                                                                       "target_object_type"],
                                                              right_on=["ocel:oid", "ocel:qualifier", "ocel:type_2"]
                                                              ).groupby(["ocel:eid", "ocel:oid"]).size().reset_index()
        relations_at_object.rename(columns={0: "relations_at_object"}, inplace=True)
        evaluated = evaluated.merge(relations_at_object,
                                    left_on=["ocel:eid", variable_id],
                                    right_on=["ocel:eid", "ocel:oid"])[["ocel:eid", variable_id, "relations_at_object"]]
        relations_at_event = source_type_event_objects.merge(object_interactions,
                                                             left_on=["ocel:oid", "ocel:qualifier",
                                                                      "target_object_type"],
                                                             right_on=["ocel:oid_x", "ocel:qualifier", "ocel:type_y"]
                                                             ).groupby(["ocel:eid_x", "ocel:oid"]).size().reset_index()
        relations_at_event.rename(columns={0: "relations_at_event"}, inplace=True)
        evaluated = evaluated.merge(relations_at_event,
                                    left_on=["ocel:eid", variable_id],
                                    right_on=["ocel:eid_x", "ocel:oid"])[
            ["ocel:eid", variable_id, "relations_at_object", "relations_at_event"]]
        evaluated["ox:evaluation"] = evaluated["relations_at_object"] <= evaluated["relations_at_event"]
        return evaluated[["ocel:eid", variable_id, "ox:evaluation"]]

    def to_string(self):
        return "o2o_complete_{" + self.qual + "," + self.objectType + "}"

    def to_TeX(self, args):
        return self.qual + "_{" + self.objectType + "}^{complete}(" + args[0] + ")"

    def get_ebnf_descriptor(self):
        raise NotImplementedError()

