import numpy as np
import pandas as pd
from pm4py import OCEL

from pattern_mining.tables.table import Table


class ObjectEvolutionsTable(Table):

    def __init__(self, event_type, object_types):
        '''
        An ObjectEvolutionsTable (after calling ObjectEvolutionsTable.create) stores per object
        the object attributes at each point in time, that is, by per row an object and its attributes as well
        as the time window in which the attribute assignment is valid.

        :param event_type: The event type.
        :param object_types: A pre-selection of object types relevant for that event type.
        '''
        super().__init__(event_type)
        self.objectTypes = object_types

    def create(self, ocel: OCEL):
        all_events = ocel.events[:]
        all_e2o = ocel.relations[:]
        all_objects = ocel.objects[:]
        all_object_changes = ocel.object_changes[:]
        events = all_events[all_events['ocel:activity'] == self.eventType]
        objects = all_objects[all_objects['ocel:type'].isin(self.objectTypes)]
        object_changes = all_object_changes[all_object_changes['ocel:type'].isin(self.objectTypes)]
        # event-type specific table: filter out irrelevant objects
        event_oids = all_e2o.merge(events, on="ocel:eid")[["ocel:oid"]].drop_duplicates()
        objects = objects.merge(event_oids, on="ocel:oid", how="inner")
        object_changes = object_changes.merge(event_oids, on="ocel:oid", how="inner")
        del all_events
        del all_e2o
        del all_objects
        del all_object_changes
        #########################
        change_times = object_changes["ocel:timestamp"].values
        event_times = events["ocel:timestamp"].values
        mintime = min(min(event_times), min(change_times)) if len(change_times) > 0 else min(event_times)
        maxtime = max(max(event_times), max(change_times)) if len(change_times) > 0 else max(event_times)
        maxtime = maxtime + pd.Timedelta(365, 'D')
        changetimes = object_changes["ocel:timestamp"].values
        if len(changetimes) > 0:
            mintime = min(mintime, changetimes.min())
        objects["ocel:field"] = pd.NA
        objects.loc[:, "ocel:timestamp"] = mintime
        object_evolutions = pd.concat([objects, object_changes])
        object_evolutions['ocel:timestamp'] = pd.to_datetime(object_evolutions['ocel:timestamp'], utc=False)
        object_evolutions.reset_index(drop=True, inplace=True)
        object_evolutions["ox:from"] = object_evolutions['ocel:timestamp']
        object_evolutions.drop("ocel:timestamp", axis=1, inplace=True)
        object_evolutions.drop("ocel:type", axis=1, inplace=True)
        object_evolutions["ox:to"] = pd.to_datetime(maxtime, utc=False)
        object_evolutions.sort_values(["ocel:oid", "ox:from"], inplace=True)
        mask = object_evolutions["ocel:oid"] == object_evolutions["ocel:oid"].shift(-1)
        object_evolutions.loc[mask, "ox:to"] = object_evolutions["ox:from"].shift(-1)
        not_attribute_columns = ["ocel:oid", "ocel:type", "ocel:field", "ox:from", "ox:to"]
        attribute_columns = [col for col in object_evolutions.columns if col not in not_attribute_columns]
        # forward-fill: propagate attribute value changes to future change points
        object_evolutions[attribute_columns] = object_evolutions[["ocel:oid"] + attribute_columns].groupby('ocel:oid').ffill()
        object_evolutions.drop("ocel:field", axis=1, inplace=True)
        object_evolutions["object_evolution_index"] = object_evolutions.index
        self.table = object_evolutions
