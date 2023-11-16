import pandas as pd
from pm4py import OCEL

from pattern_mining.tables.table import Table, create_event_interaction_table, create_object_evolutions_table


class EventInteractionTable(Table):

    def __init__(self, event_type, object_types):
        '''
        An EventInteractionTable (after calling EventInteractionTable.create) stores per event of a particular event type
        the associated objects and their attributes at time of the event occurrence.

        :param event_type: The event type.
        :param object_types: A pre-selection of object types relevant for that event type.
        '''
        super().__init__(event_type)
        self.objectTypes = object_types

    def create(self, ocel: OCEL):
        # TODO: Refactor more
        all_events = ocel.events[:]
        all_e2o = ocel.relations[:]
        all_objects = ocel.objects[:]
        all_object_changes = ocel.object_changes[:]
        events = all_events[all_events['ocel:activity'] == self.eventType]
        e2o = pd.merge(all_e2o, events, left_on='ocel:eid', right_on='ocel:eid', how='inner')
        e2o = e2o[["ocel:eid", "ocel:oid", "ocel:qualifier", "ocel:type"]]
        objects = all_objects[all_objects['ocel:type'].isin(self.objectTypes)]
        object_changes = all_object_changes[all_object_changes['ocel:type'].isin(self.objectTypes)]
        object_evolutions = create_object_evolutions_table(objects, events, object_changes)
        table = create_event_interaction_table(events, e2o, object_evolutions)
        self.table = table