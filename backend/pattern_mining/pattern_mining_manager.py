from flask import session
from mlxtend.frequent_patterns import apriori
from pm4py import OCEL

import os
import pickle

import pandas as pd

from pattern_mining.GROUND_PATTERNS import E2O_R, O2O_R
from pattern_mining.PATTERN_FORMULAS import get_ot_card_formula, get_e2o_exists_formula, get_o2o_exists_exists_formula,\
    get_o2o_exists_forall_formula, get_o2o_complete_formula
from pattern_mining.PATTERN_FUNCTIONS import O2o_complete, O2o_r, E2o_r, Ot_card, Oaval_geq
from pattern_mining.domains import ObjectVariableArgument
from pattern_mining.pattern_formula import PatternFormula
from pattern_mining.table_manager import TableManager
from utils.session_utils import get_session_path


class PatternMiningManager:

    @classmethod
    def get_name(cls):
        session_key = session.get('session_key', None)
        name = 'pamela_' + str(session_key)
        return name

    @classmethod
    def load(cls):
        name = PatternMiningManager.get_name()
        session_path = get_session_path()
        path = os.path.join(session_path, name + ".pkl")
        with open(path, "rb") as rf:
            return pickle.load(rf)

    def __init__(self, ocel: OCEL,
                 entropy_attributes_split=False,
                 entropy_split_recursion_levels=4,
                 card_search_min=0.2,
                 card_search_max=1.0,
                 exclude_singleton_card_search=True,
                 min_support=0.05):
        """
         This class will conduct the pattern mining.

           entropy_attributes_split (bool)
                If True, this object makes an entropy-based search for threshold for numerical attributes
                (at event and object attributes) at which they should be split. The resulting thresholds will be
                translated into patterns for the default search plan.
           entropy_split_recursion_levels (int)
                The maximum number of thresholds to be determined for the numerical attributes.
           card_search_min (float)
                The minimal relative frequency of a cardinality of an object type at an event type. If the threshold is
                not reached, the respective pattern will not be searched for.
           card_search_max (float)
                The maximal relative frequency of a cardinality of an object type at an event type. If the threshold is
                exceeded, the respective pattern will not be searched for.
           exclude_singleton_card_search (bool)
                If True, cardinality patterns will not be searched for cardinality 1 (because this would usually be
                information that is redundant to what is represented in the model layer).
            min_support (float)
                The minimal support of a pattern to be returned by the pattern mining procedure.
         """
        #self.session_key = session_key
        self.sessionKey = session.get('session_key', None)
        self.ocel = ocel
        self.entropyAttributesSplit = entropy_attributes_split
        self.entropySplitRecursionLevels = entropy_split_recursion_levels
        self.cardSearchMin = card_search_min
        self.cardSearchMax = card_search_max
        self.excludeSingletonCardSearch = exclude_singleton_card_search
        self.minSupport = min_support

    def save(self):
        name = PatternMiningManager.get_name()
        path = get_session_path()
        path = os.path.join(path, name + ".pkl")
        with open(path, "wb") as wf:
            pickle.dump(self, wf)

    def initialize(self):
        self.__preprocess_event_log()
        self.__create_variable_prefixes()
        self.__make_default_search_plans()

    def get_search_plans(self):
        return { et: list(id_to_pattern.keys()) for et, id_to_pattern in self.search_patterns.items() }

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
        if self.entropyAttributesSplit:
            self.__make_entropy_attributes_split()
        self.search_patterns = {}
        for event_type in self.event_types:
            self.search_patterns[event_type] = {}
            self.__make_default_search_plan(event_type)

    def __add_pattern(self, event_type, pattern: PatternFormula):
        pattern_id = pattern.to_string()
        self.search_patterns[event_type][pattern_id] = pattern

    def __make_entropy_attributes_split(self):
        raise NotImplementedError("Please implement me")

    def __make_default_search_plan(self, event_type):
        self.__make_event_attributes_default_patterns(event_type)
        self.__make_event_type_to_object_default_patterns(event_type)
        self.__make_event_type_objects_to_objects_default_patterns(event_type)
        self.__make_misc_patterns(event_type)

    def __make_event_attributes_default_patterns(self, event_type):
        pass

    def __make_event_type_to_object_default_patterns(self, event_type):
        for object_type in self.event_types_object_types[event_type]:
            object_variable_id = self.variable_prefixes[object_type]
            object_variable_argument = ObjectVariableArgument(object_type, object_variable_id)
            quals = self.event_type_object_relations[event_type][object_type]
            for qual in quals:
                e2o_pattern = get_e2o_exists_formula(object_variable_argument, qual)
                self.__add_pattern(event_type, e2o_pattern)

    def __make_event_type_objects_to_objects_default_patterns(self, event_type):
        for object_type_1, relation_info in self.event_type_object_to_object_relations[event_type].items():
            object_variable_id_1 = self.variable_prefixes[object_type_1]
            object_variable_1 = ObjectVariableArgument(object_type_1, object_variable_id_1)
            for object_type_2, quals in relation_info.items():
                for qual in quals:
                    object_variable_id_2 = self.variable_prefixes[object_type_2]
                    object_variable_2 = ObjectVariableArgument(object_type_2, object_variable_id_2)
                    o2o_exists_exists_pattern = get_o2o_exists_exists_formula(object_variable_1, qual, object_variable_2)
                    o2o_exists_forall_pattern = get_o2o_exists_forall_formula(object_variable_1, qual, object_variable_2)
                    o2o_exists_complete_pattern = get_o2o_complete_formula(object_variable_1, qual, object_type_2)
                    self.__add_pattern(event_type, o2o_exists_exists_pattern)
                    self.__add_pattern(event_type, o2o_exists_forall_pattern)
                    self.__add_pattern(event_type, o2o_exists_complete_pattern)

    def __make_misc_patterns(self, event_type):
        self.__make_object_type_cardinality_patterns(event_type)

    def __make_object_type_cardinality_patterns(self, event_type):
        relations = self.ocel.relations
        event_type_relations = relations[relations["ocel:activity"] == event_type]
        et_ot_cardinalities = event_type_relations.groupby(['ocel:eid', 'ocel:type'])['ocel:oid'].nunique()
        ot_cardinalities = et_ot_cardinalities.groupby('ocel:type').value_counts(normalize=True).\
            unstack(fill_value=0).to_dict(orient='index')
        filtered_ot_cardinalities = {
            object_type: {
                card: relative_frequency
                for card, relative_frequency in card_relfreqs.items()
                if self.cardSearchMin <= relative_frequency <= self.cardSearchMax
                and not (card == 1 and self.excludeSingletonCardSearch)
            }
            for object_type, card_relfreqs in ot_cardinalities.items()
        }
        for object_type, card_relfreqs in filtered_ot_cardinalities.items():
            cards = card_relfreqs.keys()
            for card in cards:
                card_pattern = get_ot_card_formula(object_type, card)
                self.__add_pattern(event_type, card_pattern)

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

    def search(self):
        ocel = self.ocel
        events = ocel.events
        pattern: PatternFormula
        self.pattern_supports = {}
        #for event_type in self.event_types:
        for event_type in ["send package"] + self.event_types:
            print("Creating analytical tables for '" + event_type + "'")
            table_manager = TableManager(ocel, event_type, self.event_types_object_types[event_type])
            print("Mining patterns for '" + event_type + "'")
            event_type_events = events[events["ocel:activity"] == event_type]
            base_table = table_manager.get_event_index()
            patterns = self.search_patterns[event_type].items()
            n_patterns = len(patterns)
            i = 1
            p = E2o_r("shipper")
            p.create_function_evaluation_table(table_manager, [ObjectVariableArgument("employees", "emp")])
            import time
            for pattern_id, pattern in patterns:
                print("Creating base table column " + str(i) + "/" + str(n_patterns) + ", for pattern " + pattern_id + "...")
                start_time = time.time()
                evaluation = pattern.evaluate(table_manager)
                base_table = pd.concat([base_table, evaluation], axis=1)
                end_time = time.time()
                elapsed_time = end_time - start_time
                print("elapsed time: " + str(elapsed_time))
                i = i + 1
            print("Applying apriori...")
            pattern_supports = apriori(base_table, min_support=self.minSupport, use_colnames=True)
            print("Finished mining patterns for event type '" + event_type + "'.")
            self.pattern_supports[event_type] = pattern_supports