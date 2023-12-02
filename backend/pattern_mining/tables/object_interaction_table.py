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
        all_events = ocel.events[:]
        all_e2o = ocel.relations[:]
        o2o = ocel.o2o[:]
        events = all_events[all_events['ocel:activity'] == self.eventType]
        e2o = pd.merge(all_e2o, events, left_on='ocel:eid', right_on='ocel:eid', how='inner')
        e2o = e2o[["ocel:eid", "ocel:oid", "ocel:qualifier", "ocel:type"]]
        object_evolutions = object_evolutions_table.get()
        interaction_table = events[:]
        # extend with information about related objects
        interaction_table = pd.merge(interaction_table, e2o, on='ocel:eid', how='inner') \
            .drop("ocel:qualifier", axis=1)
        # create rows corresponding to pairs of objects that interact
        interaction_table = pd.merge(interaction_table, interaction_table, on="ocel:eid", how="inner", suffixes=('_x', '_y'))
        # reduce load a bit by not keeping every pair twice
        interaction_table = interaction_table[interaction_table['ocel:oid_y'] <= interaction_table['ocel:oid_x']]
        interaction_table = interaction_table \
            .rename(columns={'ocel:timestamp_x': 'ocel:timestamp'}) \
            .drop("ocel:timestamp_y", axis=1)
        # change to left join if also interested in interactions between non-iterrelated objects
        # for example, for comparing object attributes between objects that are not in a qualified relationship
        #.merge(o2o, left_on=['ocel:oid_x', 'ocel:oid_y'], right_on=["ocel:oid", "ocel:oid_2"], how='left') \
        interaction_table = interaction_table \
            .merge(o2o, left_on=['ocel:oid_x', 'ocel:oid_y'], right_on=["ocel:oid", "ocel:oid_2"], how='inner') \
            .drop(["ocel:oid", "ocel:oid_2"], axis=1)
        attributes = [col for col in object_evolutions.columns if col not in ["ocel:oid", "ox:from", "ox:to"]]
        interaction_table = interaction_table.merge(object_evolutions, left_on=["ocel:oid_x"], right_on=["ocel:oid"], how="inner")
        interaction_table = interaction_table[(interaction_table['ocel:timestamp'] >= interaction_table['ox:from']) & (interaction_table['ocel:timestamp'] < interaction_table['ox:to'])]
        interaction_table = interaction_table.rename(columns={key: key + "_x" for key in attributes})
        interaction_table = interaction_table.drop(["ox:from", "ox:to", "ocel:oid"], axis=1)
        interaction_table = interaction_table.merge(object_evolutions, left_on=["ocel:oid_y"], right_on=["ocel:oid"], how="inner")
        interaction_table = interaction_table[(interaction_table['ocel:timestamp'] >= interaction_table['ox:from'])
                                              & (interaction_table['ocel:timestamp'] < interaction_table['ox:to'])]
        interaction_table = interaction_table.rename(columns={key: key + "_y" for key in attributes})
        interaction_table = interaction_table.drop(["ox:from", "ox:to", "ocel:oid"], axis=1)
        self.table = interaction_table
