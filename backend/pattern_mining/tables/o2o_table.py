from pm4py import OCEL

from pattern_mining.tables.table import Table


class O2OTable(Table):

    def __init__(self, event_type, object_type):
        '''
        An O2OTable (after calling O2OTable.create) stores relationship information between objects.

        :param event_type: The event type. Objects are prefiltered, we only consider those who occur at this event type.
        '''
        super().__init__(event_type)
        self.objectType = object_type

    def create(self, ocel: OCEL):
        o2o = ocel.o2o
        objects = ocel.objects
        event_objects = ocel.relations
        event_type_event_objects = event_objects[event_objects["ocel:activity"] == self.eventType][
            ["ocel:eid", "ocel:oid"]]
        table = o2o[:]
        table = table[table["ocel:oid"].isin(event_type_event_objects["ocel:oid"])][
            ["ocel:oid", "ocel:qualifier", "ocel:oid_2"]]
        table = table.merge(objects, left_on="ocel:oid", right_on="ocel:oid", how="inner")[
            ["ocel:oid", "ocel:type", "ocel:qualifier", "ocel:oid_2"]]
        table = table.merge(objects, left_on="ocel:oid_2", right_on="ocel:oid", how="inner")[
            ["ocel:oid_x", "ocel:type_x", "ocel:qualifier", "ocel:oid_y", "ocel:type_y"]]
        table = table.rename(columns={"ocel:oid_x": "ocel:oid",
                                      "ocel:type_x": "ocel:type",
                                      "ocel:oid_y": "ocel:oid_2",
                                      "ocel:type_y": "ocel:type_2"})
        self.table = table
