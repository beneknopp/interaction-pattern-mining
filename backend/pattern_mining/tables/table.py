import pandas as pd
import numpy as np
from pandas import DataFrame
from pm4py import OCEL


def create_object_evolutions_table(object_table, event_table, object_change_table) -> DataFrame:
    mintime = min(min(event_table["ocel:timestamp"].values), min(object_change_table["ocel:timestamp"].values))
    maxtime = max(max(event_table["ocel:timestamp"].values), max(object_change_table["ocel:timestamp"].values))
    maxtime = maxtime + np.timedelta64(365, 'D')
    changetimes = object_change_table["ocel:timestamp"].values
    if len(changetimes) > 0:
        mintime = min(mintime, changetimes.min())
    object_table["ocel:field"] = pd.NA
    object_table.loc[:, "ocel:timestamp"] = mintime
    object_evolutions = pd.concat([object_table, object_change_table])
    object_evolutions['ocel:timestamp'] = pd.to_datetime(object_evolutions['ocel:timestamp'], utc=False)
    object_evolutions.reset_index(drop=True, inplace=True)
    object_evolutions["ox:from"] = object_evolutions['ocel:timestamp']
    object_evolutions.drop("ocel:timestamp", axis=1, inplace=True)
    object_evolutions.drop("ocel:type", axis=1, inplace=True)
    object_evolutions["ox:to"] = pd.to_datetime(maxtime, utc=False)
    object_evolutions.sort_values(["ocel:oid", "ox:from"], inplace=True)
    prev_oid = None
    prev_index = None
    not_attribute_columns = ["ocel:oid", "ocel:type", "ocel:field", "ox:from", "ox:to"]
    for index, row in object_evolutions.iterrows():
        oid = row["ocel:oid"]
        if oid == prev_oid:
            field = row["ocel:field"]
            time = row["ox:from"]
            object_evolutions.at[prev_index, "ox:to"] = time
            for col in object_evolutions.columns:
                if col not in not_attribute_columns and col != field:
                    object_evolutions.at[index, col] = object_evolutions.at[prev_index, col]
        prev_oid = oid
        prev_index = index
    object_evolutions.drop("ocel:field", axis=1, inplace=True)
    return object_evolutions


def create_event_interaction_table(events, e2o, object_evolutions) -> DataFrame:
    df = events[:]
    # extend with information about related objects
    df = pd.merge(df, e2o, on='ocel:eid', how='inner')
    # create rows corresponding to pairs of objects that interact
    event_attributes = [col for col in df.columns if not col.startswith('ocel:')]
    df = df.drop(event_attributes, axis=1)
    df = df.merge(object_evolutions, on=["ocel:oid"], how="inner")
    df = df[(df['ocel:timestamp'] >= df['ox:from']) & (df['ocel:timestamp'] < df['ox:to'])]
    df = df.drop(["ox:from", "ox:to"], axis=1)
    return df


def create_object_interaction_table(events, e2o, o2o, object_evolutions) -> DataFrame:
    df = events[:]
    # extend with information about related objects
    df = pd.merge(df, e2o, on='ocel:eid', how='inner') \
        .drop("ocel:qualifier", axis=1)
    # create rows corresponding to pairs of objects that interact
    df = pd.merge(df, df, on="ocel:eid", how="inner")
    df = df \
        .rename(columns={'ocel:timestamp_x': 'ocel:timestamp'}) \
        .drop("ocel:timestamp_y", axis=1)
    df = df \
        .merge(o2o, left_on=['ocel:oid_x', 'ocel:oid_y'], right_on=["ocel:oid", "ocel:oid_2"],
               how='left') \
        .drop(["ocel:oid", "ocel:oid_2"], axis=1)
    attributes = [col for col in object_evolutions.columns if
                  col not in ["ocel:oid", "ox:from", "ox:to"]]
    df = df.merge(object_evolutions, left_on=["ocel:oid_x"], right_on=["ocel:oid"], how="inner")
    df = df[(df['ocel:timestamp'] >= df['ox:from']) & (df['ocel:timestamp'] < df['ox:to'])]
    df = df.rename(columns={key: key + "_x" for key in attributes})
    df = df.drop(["ox:from", "ox:to", "ocel:oid"], axis=1)
    df = df.merge(object_evolutions, left_on=["ocel:oid_y"], right_on=["ocel:oid"], how="inner")
    df = df[(df['ocel:timestamp'] >= df['ox:from']) & (df['ocel:timestamp'] < df['ox:to'])]
    df = df.rename(columns={key: key + "_y" for key in attributes})
    df = df.drop(["ox:from", "ox:to", "ocel:oid"], axis=1)
    return df


class Table:

    def __init__(self, event_type):
        self.eventType = event_type
        self.table = None

    def create(self, ocel: OCEL):
        raise NotImplementedError()

    def get(self) -> DataFrame:
        return self.table
