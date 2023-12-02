import pandas as pd
from pm4py import OCEL

from pattern_mining.tables.object_evolutions_table import ObjectEvolutionsTable
from pattern_mining.tables.table import Table


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

    def create(self, ocel: OCEL, object_evolutions_table: ObjectEvolutionsTable):
        # TODO: Refactor more
        all_events = ocel.events[:]
        all_e2o = ocel.relations[:]
        events = all_events[all_events['ocel:activity'] == self.eventType]
        e2o = pd.merge(all_e2o, events, left_on='ocel:eid', right_on='ocel:eid', how='inner')
        e2o = e2o[["ocel:eid", "ocel:oid", "ocel:qualifier", "ocel:type"]]
        object_evolutions = object_evolutions_table.table
        event_interactions = events[:]
        # extend with information about related objects
        event_interactions = pd.merge(event_interactions, e2o, on='ocel:eid', how='inner')
        # create rows corresponding to pairs of objects that interact
        event_attributes = [col for col in event_interactions.columns if not col.startswith('ocel:')]
        event_interactions = event_interactions.drop(event_attributes, axis=1)
        event_interactions = event_interactions.merge(object_evolutions, on=["ocel:oid"], how="inner")
        event_interactions = event_interactions[(event_interactions['ocel:timestamp'] >= event_interactions['ox:from'])
                                                & (event_interactions['ocel:timestamp'] < event_interactions['ox:to'])]
        event_interactions = event_interactions.drop(["ox:from", "ox:to"], axis=1)
        self.table = event_interactions