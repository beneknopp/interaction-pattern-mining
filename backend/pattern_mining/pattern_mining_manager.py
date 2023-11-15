import os
import pickle

import pandas as pd

from pattern_mining.GROUND_PATTERNS import EAVAL_EQ, O2O_COMPLETE
from utils.misc_utils import is_numeric_data_type, is_categorical_data_type


class PatternMiningManager():

    entropy_attributes_split = False
    entropy_split_recursion_levels = 4

    @classmethod
    def load(cls, name):
        path = os.getcwd()
        path = os.path.join(path, name + ".pkl")
        with open(path, "rb") as rf:
            return pickle.load(rf)

    def __init__(self, session_key, ocel):
        self.session_key = session_key
        self.name = "pamela_" + str(session_key)
        self.ocel = ocel

    def save(self):
        path = os.getcwd()
        path = os.path.join(path, self.name + ".pkl")
        with open(path, "wb") as wf:
            pickle.dump(self, wf)

    def initialize(self):
        self.__preprocess_event_log()
        self.__create_variable_prefixes()
        self.__make_default_search_plans()

    def __preprocess_event_log(self):
        self.__preprocess_attributes()
        self.__preprocess_relations()

    def __preprocess_attributes(self):
        self.__load_event_type_attribute_info()
        self.__load_object_type_attribute_info()
        self.__determine_attribute_data_types()

    def __preprocess_relations(self):
        self.__load_event_type_object_type_info()
        self.__load_event_type_object_relations_info()
        self.__load_event_type_object_to_object_relations_info()

    def __load_event_type_object_type_info(self):
        self.event_types = sorted(list(set(self.ocel.events["ocel:activity"].values)))
        self.object_types = sorted(list(set(self.ocel.objects["ocel:type"].values)))
        self.objects = self.ocel.objects
        e2o = self.ocel.relations
        self.event_types_object_types = e2o.groupby('ocel:activity')['ocel:type'].agg(lambda x: list(set(x))).to_dict()

    def __load_event_type_attribute_info(self):
        events = self.ocel.events
        event_columns = events.columns
        event_attributes = [c for c in event_columns if not c.startswith('ocel:')]
        event_type_groups = events.groupby('ocel:activity')
        self.event_type_attributes = {}
        for event_type, group in event_type_groups:
            self.event_type_attributes[event_type] = []
            for attribute in event_attributes:
                if group[attribute].notna().any():
                    self.event_type_attributes[event_type].append(attribute)

    def __load_object_type_attribute_info(self):
        objects = self.ocel.objects
        object_changes = self.ocel.object_changes
        object_columns = objects.columns
        object_changes_columns = object_changes.columns
        object_attributes = [c for c in object_columns if not c.startswith('ocel:')]
        object_change_attributes = [c for c in object_changes_columns if not c.startswith('ocel:')]
        object_type_groups = objects.groupby('ocel:type')
        object_type_change_groups = object_changes.groupby('ocel:type')
        self.object_type_attributes = {}
        for object_type, group in object_type_groups:
            self.object_type_attributes[object_type] = []
            for attribute in object_attributes:
                if group[attribute].notna().any():
                    self.object_type_attributes[object_type].append(attribute)
        for object_type, group in object_type_change_groups:
            for attribute in object_change_attributes:
                if group[attribute].notna().any():
                    self.object_type_attributes[object_type] = list(set(
                        self.object_type_attributes[object_type] + [attribute]
                    ))

    def __determine_attribute_data_types(self):
        self.event_attribute_data_types = {}
        self.object_attribute_data_types = {}
        for event_type, event_attributes in self.event_type_attributes.items():
            self.event_attribute_data_types[event_type] = {}
            for event_attribute in event_attributes:
                data_type = self.__determine_event_attribute_data_type(event_attribute)
                self.event_attribute_data_types[event_type][event_attribute] = data_type
        for object_type, object_attributes in self.object_type_attributes.items():
            self.object_attribute_data_types[object_type] = {}
            for object_attribute in object_attributes:
                data_type = self.__determine_object_attribute_data_type(object_attribute)
                self.object_attribute_data_types[object_type][object_attribute] = data_type

    def __determine_event_attribute_data_type(self, attribute):
        return self.ocel.events.dtypes.to_dict()[attribute]

    def __determine_object_attribute_data_type(self, attribute):
        dtype1 = self.ocel.objects.dtypes.to_dict()[attribute]
        dtype2 = self.ocel.object_changes.dtypes.to_dict()[attribute]
        if not dtype1 == dtype2:
            raise AttributeError()
        return dtype1

    def __load_event_type_object_relations_info(self):
        self.event_type_object_relations = {}
        relations = self.ocel.relations
        event_type_relations_groups = relations.groupby('ocel:activity')
        for event_type, group in event_type_relations_groups:
            self.event_type_object_relations[event_type] = {}
            subgroups = group.groupby('ocel:type')
            for object_type, subgroup in subgroups:
                qualifiers = list(set(subgroup['ocel:qualifier'].values))
                self.event_type_object_relations[event_type][object_type] = qualifiers

    def __load_event_type_object_to_object_relations_info(self):
        self.event_type_object_to_object_relations = {}
        relations = self.ocel.relations
        o2o = self.ocel.o2o
        o2o = o2o.rename(columns={'ocel:qualifier': 'ocel:o2o_qualifier'})
        df1 = pd.merge(relations, relations, on='ocel:eid')
        df2 = pd.merge(df1, o2o, left_on=['ocel:oid_x', 'ocel:oid_y'], right_on=['ocel:oid', 'ocel:oid_2'])
        event_type_groups = df2.groupby('ocel:activity_x')
        for event_type, group in event_type_groups:
            self.event_type_object_to_object_relations[event_type] = {
                object_type_x: {
                    object_type_y: []
                    for object_type_y in self.object_types
                }
                for object_type_x in self.object_types
            }
            subgroups = group.groupby(['ocel:type_x', 'ocel:type_y'])
            for key, subgroup in subgroups:
                qualifiers = list(set(subgroup['ocel:o2o_qualifier']))
                object_type_x, object_type_y = key
                self.event_type_object_to_object_relations[event_type][object_type_x][object_type_y] = qualifiers

    def __make_default_search_plans(self):
        px = O2O_COMPLETE(r="comprises")
        px.apply(self.ocel, "place_o-990001", ["o-990001"])
        if self.entropy_attributes_split:
            self.__make_entropy_attributes_split()
        self.search_patters = {}
        for event_type in self.event_types:
            self.__make_default_search_plan(event_type)

    def __make_entropy_attributes_split(self):
        raise NotImplementedError("Please implement me")

    def __make_default_search_plan(self, event_type):
        self.search_patters[event_type] = []
        self.__make_event_attributes_default_patterns(event_type)
        self.__make_event_type_to_object_default_patterns(event_type)
        self.__make_event_type_objects_to_objects_default_patterns(event_type)

    def __make_event_attributes_default_patterns(self, event_type):
        for event_attribute in self.event_type_attributes[event_type]:
            attribute_data_type = self.event_attribute_data_types[event_type][event_attribute]
            if is_numeric_data_type(attribute_data_type):
                pass
            elif is_categorical_data_type(attribute_data_type):
                attribute_values = set(self.ocel.events[event_attribute].values)
                for attribute_value in attribute_values:
                    pat = EAVAL_EQ(ea=event_attribute, v=attribute_value)
                    self.search_patters[event_type].append(pat)

    def __make_event_type_to_object_default_patterns(self, event_type):
        pass

    def __make_event_type_objects_to_objects_default_patterns(self, event_type):
        pass

    def __create_variable_prefixes(self):
        used_prefixes = set()
        self.variable_prefixes = {}
        object_ids = set(self.objects['ocel:oid'].values)
        for object_type in self.object_types:
            prefix = object_type[0]
            i = 1
            # avoid naming conflicts
            while prefix in used_prefixes and i < len(object_type):
                prefix += object_type[i]
                i = i + 1
            if prefix in object_ids:
                # TODO: increase safety by also checking for regex r"prefix[0-9]+"
                raise NameError()
            self.variable_prefixes[object_type] = prefix
            used_prefixes.add(prefix)