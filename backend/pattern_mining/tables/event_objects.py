from pm4py import OCEL

from pattern_mining.tables.table import Table


class EventObjects(Table):

    def __init__(self, event_type, object_type):
        '''
        An EventObjectsTable records which objects of a specific type are associated with an event.

        :param event_type: The event type.
        :param object_type: The object type.
        '''
        super().__init__(event_type)
        self.objectType = object_type

    def create(self, ocel: OCEL):
        all_events = ocel.events[:]
        all_relations = ocel.relations[:][["ocel:eid", "ocel:oid", "ocel:type"]]
        typed_relations = all_relations[all_relations["ocel:type"] == self.objectType]
        events = all_events[all_events['ocel:activity'] == self.eventType][["ocel:eid"]]
        relations = events.merge(typed_relations, on=["ocel:eid"], how="inner")
        self.table = relations[["ocel:eid", "ocel:oid"]]
