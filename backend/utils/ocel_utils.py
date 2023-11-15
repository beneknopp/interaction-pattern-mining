from pm4py import OCEL


def get_event_objects(ocel: OCEL, event):
    e2o = ocel.relations
    event_entries = e2o[e2o["ocel:eid"] == event]
    event_objects = set(event_entries["ocel:oid"].values)
    return event_objects


def get_event_objects_of_type(ocel: OCEL, event, object_type):
    e2o = ocel.relations
    event_entries = e2o[e2o["ocel:eid"] == event]
    event_entries_of_type = event_entries[event_entries["ocel:type"] == object_type]
    event_objects_of_type = set(event_entries_of_type["ocel:oid"].values)
    return event_objects_of_type

def get_object_attributes_at_event_time(ocel: OCEL, event, object_identifier):
    raise NotImplementedError()

def get_object_attribute_at_event_time(ocel: OCEL, event, object_identifier, object_attribute):
    return get_object_attributes_at_event_time(ocel, event, object_identifier)[object_attribute]