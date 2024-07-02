import pandas as pd
from pm4py import OCEL

from pattern_mining.tables.object_evolutions_table import ObjectEvolutionsTable
from pattern_mining.tables.table import Table
import math


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
        all_events = ocel.events[:]
        all_e2o = ocel.relations[:]
        events = all_events[all_events['ocel:activity'] == self.eventType]
        e2o = pd.merge(all_e2o, events, left_on='ocel:eid', right_on='ocel:eid', how='inner')
        e2o = e2o[["ocel:eid", "ocel:oid", "ocel:qualifier", "ocel:type"]]
        object_evolutions = object_evolutions_table.table
        event_interactions = events[:]
        # extend with information about related objects
        event_interactions = event_interactions.merge(e2o, on='ocel:eid', how='inner')
        # create rows corresponding to pairs of objects that interact
        event_attributes = [col for col in event_interactions.columns if not col.startswith('ocel:')]
        event_interactions = event_interactions.drop(event_attributes, axis=1)
        object_evolutions_windows = object_evolutions[["object_evolution_index", "ocel:oid", "ox:from", "ox:to"]]
        event_interactions = self.__merge_event_interactions_with_evolutions(
            event_interactions,
            object_evolutions_windows
        )
        self.table = event_interactions

    def __merge_event_interactions_with_evolutions(self, event_interactions, object_evolutions_windows):
        n_event_interactions = len(event_interactions)
        batches = math.floor(n_event_interactions / 5000 ) + 1
        while True:
            event_interactions_split = []
            splits_with_evolutions = []
            batch_size = n_event_interactions / batches
            for i in range(batches):
                event_interactions_split.append(
                    event_interactions.iloc[round(i * batch_size):round((i + 1) * batch_size)]
                )
            try:
                for sub_split in event_interactions_split:
                    sub_split_with_evolutions = sub_split.merge(object_evolutions_windows, on=["ocel:oid"], how="inner")
                    sub_split_with_evolutions = sub_split_with_evolutions[
                        (sub_split_with_evolutions['ocel:timestamp'] >= sub_split_with_evolutions['ox:from'])
                        & (sub_split_with_evolutions['ocel:timestamp'] < sub_split_with_evolutions['ox:to'])
                    ]
                    sub_split_with_evolutions = sub_split_with_evolutions.drop(["ox:from", "ox:to"], axis=1)
                    splits_with_evolutions.append(sub_split_with_evolutions)
                break
            except:
                print("Merging of event interactions with object evolutions failed, likely because of memory issues. "
                      + "Trying to split...")
                batches = batches + 1
        conc_interactions = pd.concat(splits_with_evolutions)
        return conc_interactions