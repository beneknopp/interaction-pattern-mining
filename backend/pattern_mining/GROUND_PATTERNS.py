from pattern_mining.domains import ObjectArgument
from pattern_mining.ground_pattern import GroundPattern
from pattern_mining.table_manager import TableManager
from utils.ocel_utils import get_event_objects_of_type, get_object_attribute_at_event_time


class EAVAL_EQ(GroundPattern):

    def __init__(self, event_attribute, value):
        super().__init__()
        self.eventAttribute = event_attribute
        self.value = value

    def apply(self, table_manager: TableManager):
        event_index = table_manager.eventIndex
        event_table = table_manager.eventTable
        condition = event_table[event_table[self.eventAttribute]] == self.value
        evaluated = event_table[condition]
        evaluated = event_index.join(evaluated)
        return evaluated


class EAVAL_LEQ(GroundPattern):

    def __init__(self, event_attribute, value):
        super().__init__()
        self.eventAttribute = event_attribute
        self.value = value

    def apply(self, table_manager: TableManager):
        event_index = table_manager.eventIndex
        event_table = table_manager.eventTable
        condition = event_table[event_table[self.eventAttribute]] <= self.value
        evaluated = event_table[condition]
        evaluated = event_index.join(evaluated)
        return evaluated


class EAVAL_GEQ(GroundPattern):

    def __init__(self, event_attribute, value):
        super().__init__()
        self.eventAttribute = event_attribute
        self.value = value

    def apply(self, table_manager: TableManager):
        event_index = table_manager.eventIndex
        event_table = table_manager.eventTable
        condition = event_table[event_table[self.eventAttribute]] >= self.value
        evaluated = event_table[condition]
        evaluated = event_index.join(evaluated)
        return evaluated


class OAVAL_EQ(GroundPattern):

    def __init__(self, object_attribute, value, object_id):
        super().__init__()
        self.objectId = object_id
        self.objectAttribute = object_attribute
        self.value = value

    def apply(self, table_manager: TableManager, event):
        object_attribute_value = get_object_attribute_at_event_time(ocel, event, self.objectId, self.objectAttribute)
        return str(self.value) == str(object_attribute_value)


class OAVAL_LEQ(GroundPattern):

    def __init__(self, object_attribute, value, object_id):
        super().__init__()
        self.objectId = object_id
        self.objectAttribute = object_attribute
        self.value = value

    def apply(self, table_manager: TableManager, event):
        object_attribute_value = get_object_attribute_at_event_time(ocel, event, self.objectId, self.objectAttribute)
        return float(object_attribute_value) <= float(self.value)


class OAVAL_GEQ(GroundPattern):

    def __init__(self, object_attribute, value, object_id):
        super().__init__()
        self.objectId = object_id
        self.objectAttribute = object_attribute
        self.value = value

    def apply(self, table_manager: TableManager, event):
        object_attribute_value = get_object_attribute_at_event_time(ocel, event, self.objectId, self.objectAttribute)
        return float(object_attribute_value) >= float(self.value)


class E2O_R(GroundPattern):

    def __init__(self, qual: str, object_id):
        super().__init__()
        self.qual = qual
        self.objectId = object_id

    def apply(self, table_manager: TableManager):
        event_index = table_manager.eventIndex.table
        event_interactions = table_manager.eventInteractionTable.table
        condition1 = event_interactions['ocel:qualifier'] == self.qual
        condition2 = event_interactions['ocel:oid'] == self.objectId
        event_interaction_matches = event_interactions[condition1 & condition2]
        evaluated = event_index.index.isin(event_interaction_matches['ocel:eid'])
        return evaluated


class O2O_R(GroundPattern):

    def __init__(self, qual: str, object_id1: ObjectArgument, object_id2: ObjectArgument):
        super().__init__()
        self.qual = qual
        self.objectId1 = object_id1
        self.objectId2 = object_id2

    def apply(self, table_manager: TableManager):
        event_index = table_manager.eventIndex.table
        object_interactions = table_manager.objectInteractionTable.table
        condition1 = object_interactions['ocel:qualifier'] == self.qual
        condition2 = object_interactions['ocel:oid_x'] == self.objectId1
        condition3 = object_interactions['ocel:oid_y'] == self.objectId2
        event_interaction_matches = object_interactions[condition1 & condition2 & condition3]
        evaluated = event_index.index.isin(event_interaction_matches['ocel:eid'])
        return evaluated


class O2O_COMPLETE(GroundPattern):

    def __init__(self, qual: str, object_type: str, object_id: str):
        super().__init__()
        self.qual = qual
        self.objectType = object_type
        self.objectId = object_id

    def apply(self, table_manager: TableManager, event):
        o2o = ocel.o2o
        o2o_condition1 = o2o["ocel:oid"] == self.objectId
        o2o_condition2 = o2o["ocel:qualifier"] == self.qual
        r_objects = set(o2o[o2o_condition1 & o2o_condition2]["ocel:oid_2"].values)
        e2o = ocel.relations
        ot_condition1 = e2o["ocel:eid"] == event
        ot_condition2 = e2o["ocel:type"] == self.objectType
        event_object_type_objects = set(e2o[ot_condition1 & ot_condition2]["ocel:oid"].values)
        e2o_condition = r_objects.issubset(event_object_type_objects)
        return e2o_condition


class OT_CARD(GroundPattern):

    def __init__(self, object_type: str, card: int):
        super().__init__()
        self.objectType = object_type
        self.card = card

    def apply(self, table_manager: TableManager, event):
        event_objects = get_event_objects_of_type(ocel, event, self.objectType)
        return len(event_objects) == self.card