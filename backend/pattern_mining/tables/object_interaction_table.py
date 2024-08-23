import math

import pandas as pd
from pm4py import OCEL

from pattern_mining.tables.object_evolutions_table import ObjectEvolutionsTable
from pattern_mining.tables.table import Table


class ObjectInteractionTable(Table):

    def __init__(self, event_type, object_types):
        '''
        An ObjectInteractionTable (after calling ObjectInteractionTable.create) stores per event of a particular event
        type interrelated objects associated with that event, as well as the objects' attributes at time of the event
        occurrence. This means that each row of this table has an event id and two object identifiers that both occur at
        this event and also have some qualified relationship to each other.

        :param event_type: The event type.
        :param object_types: A pre-selection of object types relevant for that event type.
        '''
        super().__init__(event_type)
        self.objectTypes = object_types

    def create(self, ocel: OCEL, object_evolutions_table: ObjectEvolutionsTable):
        all_e2o = ocel.relations[:]
        o2o = ocel.o2o[:]
        events = ocel.events[["ocel:eid", "ocel:timestamp"]]
        object_evolutions = object_evolutions_table.get()
        e2o = all_e2o[all_e2o["ocel:activity"] == self.eventType]
        e2o = e2o[["ocel:eid", "ocel:oid"]]
        # extend with information about related objects
        interaction_table = pd.merge(e2o, e2o, on='ocel:eid', how='inner', suffixes=("_x", "_y")) \

        # change to left join if also interested in interactions between non-related objects
        # for example, for comparing object attributes between objects that are not in a qualified relationship
        # .merge(o2o, left_on=['ocel:oid_x', 'ocel:oid_y'], right_on=["ocel:oid", "ocel:oid_2"], how='left') \
        interaction_table = interaction_table \
            .merge(o2o, left_on=['ocel:oid_x', 'ocel:oid_y'], right_on=["ocel:oid", "ocel:oid_2"], how='inner') \
            .drop(["ocel:oid", "ocel:oid_2"], axis=1)
        # do not keep every pair twice
        interaction_table = interaction_table[
            interaction_table['ocel:oid_x'] < interaction_table['ocel:oid_y']
        ]
        # add timestamp
        interaction_table = interaction_table.merge(events, on="ocel:eid")
        object_attributes = [col for col in object_evolutions.columns if col not in ["ocel:oid", "ox:from", "ox:to"]]
        object_evolutions_windows = object_evolutions[["object_evolution_index", "ocel:oid", "ox:from", "ox:to"]]
        interaction_table = interaction_table.merge(object_evolutions_windows, left_on=["ocel:oid_x"], right_on=["ocel:oid"], how="inner")
        interaction_table = interaction_table[(interaction_table['ocel:timestamp'] > interaction_table['ox:from'])
                                            & (interaction_table['ocel:timestamp'] <= interaction_table['ox:to'])]
        interaction_table = interaction_table.rename(columns={"object_evolution_index": "object_evolution_index_x"})
        interaction_table = interaction_table.rename(columns={key: key + "_x" for key in object_attributes})
        interaction_table = interaction_table.drop(["ox:from", "ox:to", "ocel:oid"], axis=1)
        interaction_table = interaction_table.merge(object_evolutions_windows, left_on=["ocel:oid_y"], right_on=["ocel:oid"], how="inner")
        interaction_table = interaction_table[(interaction_table['ocel:timestamp'] > interaction_table['ox:from'])
                                            & (interaction_table['ocel:timestamp'] <= interaction_table['ox:to'])]
        interaction_table = interaction_table.rename(columns={"object_evolution_index": "object_evolution_index_y"})
        interaction_table = interaction_table.rename(columns={key: key + "_y" for key in object_attributes})
        interaction_table = interaction_table.drop(["ox:from", "ox:to", "ocel:oid"], axis=1)
        self.table = interaction_table
