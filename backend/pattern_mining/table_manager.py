from enum import Enum

import pandas as pd


class TableType(Enum):
    EVENTS = "EVENTS",
    O2O = "O2O"
    E2O = "E2O"
    OAVALS = "OAVALS"
    INTERACTION = "INTERACTION"


class TableManager:

    def __init__(self, ocel, event_types, object_types):
        self.ocel = ocel
        self.eventTypes = event_types
        self.objectTypes = object_types

    def create_dataframes(self):
        self.__create_basic_tables()
        self.__create_object_evolution_table()
        self.__create_attribute_enriched_event_table()
        self.__interaction_tables = {}
        for event_type in self.eventTypes:
            self.__create_interaction_table(event_type)

    def __create_basic_tables(self):
        ocel = self.ocel
        self.__event_table = ocel.events[:]
        self.__e2o_table = ocel.relations[["ocel:eid", "ocel:oid", "ocel:qualifier", "ocel:type"]][:]
        self.__o2o_table = ocel.o2o[:]
        self.__object_table = ocel.objects[:]
        self.__object_change_table = ocel.object_changes[:]

    def __create_object_evolution_table(self):
        object_table = self.__object_table
        event_table = self.__event_table
        object_change_table = self.__object_change_table
        mintime = min(event_table["ocel:timestamp"].values)
        changetimes = object_change_table["ocel:timestamp"].values
        if len(changetimes) > 0:
            mintime = min(mintime, changetimes.min())
        # TODO
        max_date_string = "31.12.2099 23:59:59"
        maxtime = pd.Timestamp(max_date_string)
        object_table["ocel:field"] = pd.NA
        object_table["ocel:timestamp"] = mintime
        object_evolutions = pd.concat([object_table, object_change_table])
        object_evolutions.reset_index(drop=True, inplace=True)
        object_evolutions["ox:from"] = object_evolutions["ocel:timestamp"]
        object_evolutions.drop("ocel:timestamp", axis=1, inplace=True)
        object_evolutions.drop("ocel:type", axis=1, inplace=True)
        object_evolutions["ox:to"] = pd.to_datetime(maxtime)
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
        self.__object_evolutions_table = object_evolutions

    def __create_attribute_enriched_event_table(self):
        event_table = self.__event_table
        e2o_table = self.__e2o_table
        object_evolution_frame = self.__object_evolutions_table
        event_objects = event_table.merge(e2o_table, on="ocel:eid")
        temp = event_objects.merge(object_evolution_frame, on="ocel:oid")
        event_objects_attributes_table = temp[(temp['ocel:timestamp'] >= temp['ox:from']) & (temp['ocel:timestamp'] < temp['ox:to'])]
        event_objects_attributes_table = event_objects_attributes_table.drop(["ox:from", "ox:to"], axis=1)
        event_objects_attributes_table.rename(columns={
            attr: "ox:attr:" + attr
            for attr in event_objects_attributes_table.columns
            if not attr.startswith("ocel:")
        }, inplace=True)
        self.__event_objects_attributes_table = event_objects_attributes_table

    def __create_interaction_table(self, event_type):
        events = self.__event_table
        event_type_events = events[events['ocel:activity'] == event_type]
        df = event_type_events[:]
        df.drop("ocel:activity", axis=1)
        # extend with information about related objects
        df = pd.merge(df, self.__e2o_table, on='ocel:eid', how='inner') \
            .drop("ocel:activity", axis=1) \
            .drop("ocel:qualifier", axis=1)
        # create rows corresponding to pairs of objects that interact
        df = pd.merge(df, df, on="ocel:eid", how="inner")
        df = df \
            .rename(columns={'ocel:timestamp_x': 'ocel:timestamp'}) \
            .drop("ocel:timestamp_y", axis=1)
        df = df \
            .merge(self.__o2o_table, left_on=['ocel:oid_x', 'ocel:oid_y'], right_on=["ocel:oid", "ocel:oid_2"],
                   how='left') \
            .drop(["ocel:oid", "ocel:oid_2"], axis=1)
        attributes = [col for col in self.__object_evolutions_table.columns if
                      col not in ["ocel:oid", "ox:from", "ox:to"]]
        df = df.merge(self.__object_evolutions_table, left_on=["ocel:oid_x"], right_on=["ocel:oid"], how="inner")
        df = df[(df['ocel:timestamp'] >= df['ox:from']) & (df['ocel:timestamp'] < df['ox:to'])]
        df = df.rename(columns={key: key + "_x" for key in attributes})
        df = df.drop(["ox:from", "ox:to", "ocel:oid"], axis=1)
        df = df.merge(self.__object_evolutions_table, left_on=["ocel:oid_y"], right_on=["ocel:oid"], how="inner")
        df = df[(df['ocel:timestamp'] >= df['ox:from']) & (df['ocel:timestamp'] < df['ox:to'])]
        df = df.rename(columns={key: key + "_y" for key in attributes})
        df = df.drop(["ox:from", "ox:to", "ocel:oid"], axis=1)
        self.__interaction_tables[event_type] = df

    def get_event_object_attributes_table(self):
        return self.__event_objects_attributes_table

    def get_e2o_table(self):
        return self.__e2o_table

    def get_o2o_table(self):
        return self.__o2o_table

    def get_objects_table(self):
        return self.__object_table

    def get_event_frame(self):
        return self.__event_table

    def get_e2o_table(self):
        return self.__e2o_table

    def get_object_evolutions_table(self):
        return self.__object_evolutions_table

    def get_interaction_table(self, event_type):
        return self.__interaction_tables[event_type]