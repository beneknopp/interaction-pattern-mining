import copy
import math
import warnings
from functools import reduce
from itertools import product

import numpy as np
import seaborn as sns
from flask import session
from matplotlib import pyplot as plt
from mlxtend.frequent_patterns import fpmax, association_rules
from pandas import DataFrame
from pm4py import OCEL

import os
import pickle

import pandas as pd

from pattern_mining.evaluation_mode import EvaluationMode
from pattern_mining.model import Model
from utils.misc_utils import is_categorical_data_type, list_equals

pd.options.mode.chained_assignment = None
warnings.simplefilter("ignore", FutureWarning)

from pattern_mining.PATTERN_FORMULAS import get_ot_card_formula, get_e2o_exists_formula, get_o2o_exists_exists_formula, \
    get_o2o_exists_forall_formula, get_o2o_complete_formula, get_oaval_eq_exists_pattern, get_oaval_eq_forall_pattern, ExistentialPattern, \
    get_existential_patterns_merge, get_e2o_forall_formula, get_o2o_forall_exists_formula, get_eaval_eq_pattern, \
    UniversalPattern, get_universal_patterns_merge, get_anti_pattern
from pattern_mining.domains import ObjectVariableArgument
from pattern_mining.pattern_formula import PatternFormula
from pattern_mining.table_manager import TableManager
from utils.session_utils import get_session_path

evaluation_mode = True


class PatternMiningManager:

    def __init__(self, ocel: OCEL,
                 complementary_mode=True,
                 merge_mode=True,
                 evaluation_mode=EvaluationMode.NONE,
                 entropy_attributes_split=False,
                 make_cardinality_patterns=True,
                 entropy_split_recursion_levels=4,
                 categorical_search_min_entropy=0.01,
                 categorical_search_max_entropy=3.0,
                 categorical_variables_max_labels_EVENT=35,
                 categorical_variables_max_labels_OBJECT=80,
                 max_initial_patterns=300,
                 max_bootstrap_pattern_merge_recursion=100000,
                 pattern_merge_subsumption_ratio=0.995,
                 min_atomic_pattern_frequency=0.0,
                 min_support=0.005
                 ):
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
           categorical_variables_max_labels (int)
                Categorical attributes will by default be translated into patterns that check if an object at an event has a specific label.
                If we have more labels for an attribute than specified by this 'parameter categorical_variables_max_labels', these patterns
                will not be built.
           max_initial_patterns (int)
                Mining for frequent itemsets can be computationally expensive for large number of patterns. For the Apriori algorithm, the
                upper limit of 30 is a good choice. If you only mine for maximal frequent itemsets (FPGrowth), a higher threshold can be chosen.
           max_bootstrap_pattern_merge_recursion (int)
                Mining for frequent itemsets can be computationally expensive for large number of patterns. This threshold limits the number of
                rounds in which new patterns are formed by merging with bootstrap patterns.
           min_split_information_gain (float)
                When splitting a partitioner based on object attributes, this is the threshold for information gain through a single split step.
           min_support (float)
                The minimal support of a pattern to be returned by the pattern mining procedure.
         """
        # self.session_key = session_key
        self.evaluationMode = None
        self.event_types_filter = None
        self.evaluation_records = None
        self.table_managers = None
        self.sessionKey = session.get('session_key', None)
        self.ocel = ocel
        self.__preprocess_ocel()
        self.complementaryMode = complementary_mode
        self.mergeMode = merge_mode
        self.minAtomicPatternFrequency = min_atomic_pattern_frequency
        self.entropyAttributesSplit = entropy_attributes_split
        self.makeCardinalityPatterns = make_cardinality_patterns
        self.entropySplitRecursionLevels = entropy_split_recursion_levels
        self.categoricalSearchMinEntropy = categorical_search_min_entropy
        self.categoricalSearchMaxEntropy = categorical_search_max_entropy
        self.categoricalVariablesMaxLabelsEVENT = categorical_variables_max_labels_EVENT
        self.categoricalVariablesMaxLabelsOBJECT = categorical_variables_max_labels_OBJECT
        self.maxInitialPatterns = max_initial_patterns
        self.maxBootstrapPatternMergeRecursion = max_bootstrap_pattern_merge_recursion
        self.patternMergeSubsumptionRatio = pattern_merge_subsumption_ratio
        self.minSupport = min_support

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
            loaded_object = pickle.load(rf)
            try:
                loaded_object.table_managers = {}
                for event_type in loaded_object.event_types_filter:
                    table_manager = TableManager.load(event_type)
                    loaded_object.table_managers[event_type] = table_manager
            except FileNotFoundError:
                pass
            return loaded_object

    def __preprocess_ocel(self):
        self.ocel.events.replace('', np.nan, inplace=True)
        self.ocel.object_changes.replace('', np.nan, inplace=True)
        self.ocel.objects.replace('', np.nan, inplace=True)
        events = self.ocel.events
        object_changes = self.ocel.object_changes
        # TODO: handle timezones properly and safely
        try:
            events["ocel:timestamp"] = pd.to_datetime(events["ocel:timestamp"].dt.tz_localize(None))
            object_changes["ocel:timestamp"] = pd.to_datetime(object_changes["ocel:timestamp"].dt.tz_localize(None))
        except:
            pass

    def visualize_base_table_creation_eval(self):
        base_table_eval = pd.DataFrame(self.base_table_evaluation)
        scatter_plot = sns.scatterplot(x='number_of_events', y='number_of_relation_types', hue='time',
                                       data=base_table_eval,
                                       palette='gray_r', edgecolor='k', linewidth=1)
        # cbar = plt.colorbar(scatter_plot.get_children()[0], label='Z Range')
        plt.xlabel('Number of events')
        plt.ylabel('Number of relationship types')
        plt.title('Runtimes for Auxiliary Table Creation')
        path = get_session_path()
        path = os.path.join(path, "eval_base_table_creation" + ".png")
        plt.savefig(path)
        plt.clf()

    def save_evaluation(self):
        eval = pd.DataFrame(self.evaluation_records)
        path = get_session_path()
        session_key_str = session.get("session_key", "???")
        for event_type in eval["event_type"].values:
            min_support_to_maximal_pattern_supports = self.maximal_pattern_supports[event_type]
            for minimal_support, maximal_pattern_supports in min_support_to_maximal_pattern_supports.items():
                maximal_pattern_supports: DataFrame
                path2 = os.path.join(path, "maximal_pattern_supports_" + event_type + "_" + str(
                    minimal_support) + "_" + session_key_str + ".csv")
                maximal_pattern_supports.to_csv(path2)
        eval_path = os.path.join(path, "eval_pattern_" + session_key_str + ".xlsx")
        eval.to_excel(eval_path)
        config_str = "maxInitialPatterns: " + str(self.maxInitialPatterns) + "\n"
        config_str += "maxBootstrapPatternMergeRecursion: " + str(self.maxBootstrapPatternMergeRecursion) + "\n"
        config_str += "complementaryMode: " + str(self.complementaryMode) + "\n"
        config_str += "mergeMode: " + str(self.mergeMode) + "\n"
        eval_config_path = os.path.join(path, "evaluation_config_" + session_key_str + ".txt")
        with open(eval_config_path, "w") as wf:
            wf.write(config_str)

    def save(self):
        name = PatternMiningManager.get_name()
        if self.table_managers is not None:
            table_manager: TableManager
            for table_manager in self.table_managers.values():
                table_manager.save()
        path = get_session_path()
        path = os.path.join(path, name + ".pkl")
        self_copy = copy.copy(self)
        self_copy.table_managers = None
        with open(path, "wb") as wf:
            pickle.dump(self_copy, wf)

    def initialize(self):
        self.__preprocess_event_log()
        self.__create_variable_prefixes()
        self.__initialize_search_plans()

    def get_search_plans(self):
        search_plans = {
            event_type: list(id_to_pattern.keys())
            for event_type, id_to_pattern in self.searched_basic_patterns.items()
        }
        for event_type, object_type_to_interaction_patterns in self.searched_interaction_patterns.items():
            for object_type, id_to_pattern in object_type_to_interaction_patterns.items():
                search_plans[event_type] += list(id_to_pattern.keys())
        return search_plans

    def __preprocess_event_log(self):
        self.event_types = sorted(list(set(self.ocel.events["ocel:activity"].values)))
        self.event_types_filter = self.event_types
        self.object_types = sorted(list(set(self.ocel.objects["ocel:type"].values)))
        self.objects = self.ocel.objects
        self.__preprocess_attributes()
        self.__preprocess_relations()

    def __preprocess_attributes(self):
        self.__load_event_type_attribute_info()
        self.__load_object_type_attribute_info()
        self.__determine_attribute_data_types()

    def __preprocess_relations(self):
        self.number_of_object_to_object_relation_types = {
            event_type: 0 for event_type in self.event_types
        }
        self.number_of_event_to_object_relation_types = {
            event_type: 0 for event_type in self.event_types
        }
        self.__load_event_type_object_type_info()
        self.__load_event_type_object_relations_info()
        self.__load_event_type_object_to_object_relations_info()

    def __load_event_type_object_type_info(self):
        e2o = self.ocel.relations
        self.event_types_object_types = e2o.groupby('ocel:activity')['ocel:type'].agg(lambda x: list(set(x))).to_dict()
        self.event_type_object_types_variability = e2o.groupby('ocel:activity') \
            .apply(lambda event_type_group: event_type_group.groupby('ocel:type')
                   .apply(lambda group: group.groupby("ocel:eid")['ocel:oid'].nunique().gt(1).any())
                   .to_dict()) \
            .to_dict()

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
            # TODO
            if object_type == "@@cumcount":
                continue
            self.object_type_attributes[object_type] = []
            for attribute in object_attributes:
                if group[attribute].notna().any():
                    self.object_type_attributes[object_type].append(attribute)
        for object_type, group in object_type_change_groups:
            # TODO
            if object_type == "@@cumcount":
                continue
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
                # TODO
                if object_attribute == "@@cumcount":
                    continue
                data_type = self.__determine_object_attribute_data_type(object_attribute)
                self.object_attribute_data_types[object_type][object_attribute] = data_type

    def __determine_event_attribute_data_type(self, attribute):
        return self.ocel.events.dtypes.to_dict()[attribute]

    def __determine_object_attribute_data_type(self, attribute):
        objects = self.ocel.objects
        object_changes = self.ocel.object_changes
        dtype1 = objects.dtypes.to_dict()[attribute]
        if attribute not in object_changes.dtypes:
            return dtype1
        dtype2 = object_changes.dtypes.to_dict()[attribute]
        if objects[attribute].isna().all():
            return dtype2
        if object_changes[attribute].isna().all():
            return dtype1
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
                self.number_of_event_to_object_relation_types[event_type] += len(qualifiers)
                self.event_type_object_relations[event_type][object_type] = qualifiers

    def __load_event_type_object_to_object_relations_info(self):
        self.event_type_object_to_object_relations = {}
        self.event_type_object_to_object_multi_relations = {}
        e2o = self.ocel.relations.copy().drop_duplicates()
        o2o = self.ocel.o2o.copy().drop_duplicates()
        o2o.rename(columns={"ocel:qualifier": "o2o_qualifier"}, inplace=True)
        for event_type in self.event_types:
            event_type_e2o = e2o[e2o["ocel:activity"] == event_type]
            e2o2o = pd.merge(event_type_e2o, o2o, on='ocel:oid')
            e2o2o2e = pd.merge(e2o2o, event_type_e2o, left_on=["ocel:eid", "ocel:oid_2"],
                               right_on=["ocel:eid", "ocel:oid"])
            e2o2o2e = e2o2o2e[["ocel:eid", "ocel:oid_x", "ocel:type_x", "o2o_qualifier", "ocel:oid_y", "ocel:type_y"]]
            e2o2o2e.drop_duplicates(inplace=True)
            self.event_type_object_to_object_relations[event_type] = {
                object_type_x: {
                    object_type_y: []
                    for object_type_y in self.object_types
                }
                for object_type_x in self.object_types
            }
            subgroups_existential = e2o2o2e.groupby(['ocel:type_x', 'ocel:type_y'])
            for key, subgroup in subgroups_existential:
                qualifiers = list(set(subgroup['o2o_qualifier']))
                object_type_x, object_type_y = key
                self.event_type_object_to_object_relations[event_type][object_type_x][object_type_y] = qualifiers
                self.number_of_object_to_object_relation_types[event_type] += len(qualifiers)
            # multi-relations between type x and type y: objects of type x can habe multiple relations to objects of type y
            self.event_type_object_to_object_multi_relations[event_type] = {
                object_type_x: {
                    object_type_y: []
                    for object_type_y in self.object_types
                }
                for object_type_x in self.object_types
            }
            for object_type_x in self.event_types_object_types[event_type]:
                for object_type_y in self.event_types_object_types[event_type]:
                    type_x_filter = e2o2o2e[e2o2o2e["ocel:type_x"] == object_type_x]
                    type_filter = type_x_filter[type_x_filter["ocel:type_y"] == object_type_y]
                    qualifiers = set(type_filter["o2o_qualifier"].values)
                    for qualifier in qualifiers:
                        qualifier_filter = type_filter[type_filter["o2o_qualifier"] == qualifier]
                        subgroups = qualifier_filter.groupby(["ocel:eid", "ocel:oid_x"])
                        if (subgroups.size() > 1).any():
                            self.event_type_object_to_object_multi_relations[event_type][object_type_x][
                                object_type_y].append(qualifier)

    def load_default_search_plans(self, event_types):
        self.__initialize_search_plans()
        if self.entropyAttributesSplit:
            self.__make_entropy_attributes_split()
        for event_type in event_types:
            self.__make_default_search_plan(event_type)

    def __make_default_independent_pattern_plans(self):
        self.searched_independent_patterns = {}
        for event_type in self.event_types:
            self.searched_independent_patterns[event_type] = {}

    def __add_basic_pattern(self, event_type, pattern: PatternFormula):
        pattern_id = pattern.to_string()
        self.patterns_by_ids[pattern_id] = pattern
        self.searched_basic_patterns[event_type][pattern_id] = pattern

    def __add_interaction_pattern(self, event_type, object_type, pattern: PatternFormula):
        pattern_id = pattern.to_string()
        self.patterns_by_ids[pattern_id] = pattern
        self.searched_interaction_patterns[event_type][object_type][pattern_id] = pattern

    def __delete_interaction_pattern(self, event_type, object_type, pattern_id: str):
        del self.searched_interaction_patterns[event_type][object_type][pattern_id]

    def __make_entropy_attributes_split(self):
        raise NotImplementedError("Please implement me")

    def __make_default_search_plan(self, event_type):
        self.__make_event_attributes_default_patterns(event_type)
        self.__make_object_attributes_default_patterns(event_type)
        #self.__make_event_type_to_object_default_patterns(event_type)
        #self.__make_event_type_objects_to_objects_default_patterns(event_type)
        self.__make_misc_patterns(event_type)

    def __make_event_attributes_default_patterns(self, event_type):
        for attribute, dtype in self.event_attribute_data_types[event_type].items():
            if is_categorical_data_type(dtype):
                # TODO: unify, maybe build TableManager already in __init__
                labels = set(self.ocel.events[attribute].dropna().values)
                if len(labels) > self.categoricalVariablesMaxLabelsEVENT:
                    continue
                for label in labels:
                    eaval_eq_exists_pattern = get_eaval_eq_pattern(attribute, label)
                    self.__add_basic_pattern(event_type, eaval_eq_exists_pattern)

    def __make_object_attributes_default_patterns(self, event_type):
        table_manager = self.table_managers[event_type]
        self.object_categorical_attribute_patterns[event_type] = {}
        for object_type in self.event_types_object_types[event_type]:
            self.object_categorical_attribute_patterns[event_type][object_type] = {}
            object_variable_id = self.variable_prefixes[object_type]
            object_variable_argument = ObjectVariableArgument(object_type, object_variable_id)
            for attribute, dtype in self.object_attribute_data_types[object_type].items():
                if is_categorical_data_type(dtype):
                    e2o_exploded = table_manager.get_event_interaction_table()
                    e2o_exploded = e2o_exploded[e2o_exploded["ocel:type"] == object_type]
                    object_evolutions = table_manager.get_object_evolutions_table()
                    object_evolutions = object_evolutions[[attribute, "object_evolution_index"]]
                    e2o_exploded = e2o_exploded.merge(
                        object_evolutions,
                        on="object_evolution_index"
                    )
                    labels = e2o_exploded[attribute].unique()
                    if len(labels) > self.categoricalVariablesMaxLabelsOBJECT:
                        continue
                    self.object_categorical_attribute_patterns[event_type][object_type][attribute] = []
                    for label in labels:
                        oaval_eq_exists_pattern = get_oaval_eq_exists_pattern(object_variable_argument, attribute,
                                                                              label)
                        self.object_categorical_attribute_patterns[event_type][object_type][attribute].append(
                            oaval_eq_exists_pattern)
                        self.__add_interaction_pattern(event_type, object_type, oaval_eq_exists_pattern)
                        #if self.event_type_object_types_variability[event_type][object_type]:
                            #oaval_eq_forall_pattern = get_oaval_eq_forall_pattern(object_variable_argument, attribute,
                             #                                                     label)
                            #self.object_categorical_attribute_patterns[event_type][object_type][attribute].append(
                                #oaval_eq_forall_pattern)
                            #self.__add_interaction_pattern(event_type, object_type, oaval_eq_forall_pattern)

    def __make_event_type_to_object_default_patterns(self, event_type):
        for object_type in self.event_types_object_types[event_type]:
            object_variable_id = self.variable_prefixes[object_type]
            object_variable_argument = ObjectVariableArgument(object_type, object_variable_id)
            quals = self.event_type_object_relations[event_type][object_type]
            for qual in quals:
                ###############################
                ##### exists x:  e2o_r(x) #####
                ###############################
                e2o_exists_pattern = get_e2o_exists_formula(object_variable_argument, qual)
                self.__add_interaction_pattern(event_type, object_type, e2o_exists_pattern)
                if self.event_type_object_types_variability[event_type][object_type]:
                    ###############################
                    ##### forall x:  e2o_r(x) #####
                    ###############################
                    e2o_forall_pattern = get_e2o_forall_formula(object_variable_argument, qual)
                    self.__add_interaction_pattern(event_type, object_type, e2o_forall_pattern)

    def __make_event_type_objects_to_objects_default_patterns(self, event_type):
        for object_type_1, relation_info in self.event_type_object_to_object_relations[event_type].items():
            object_variable_id_1 = self.variable_prefixes[object_type_1]
            object_variable_1 = ObjectVariableArgument(object_type_1, object_variable_id_1)
            for object_type_2, quals in relation_info.items():
                for qual in quals:
                    object_variable_id_2 = self.variable_prefixes[object_type_2]
                    object_variable_2 = ObjectVariableArgument(object_type_2, object_variable_id_2)
                    ########################################
                    ##### exists x: exists y: o2o(x,y) #####
                    ########################################
                    o2o_exists_exists_pattern = get_o2o_exists_exists_formula(object_variable_1, qual,
                                                                              object_variable_2)
                    self.__add_interaction_pattern(event_type, object_type_1, o2o_exists_exists_pattern)
                    if self.event_type_object_types_variability[event_type][object_type_1]:
                        ########################################
                        ##### forall x: exists y: o2o(x,y) #####
                        ########################################
                        o2o_forall_exists_pattern = get_o2o_forall_exists_formula(object_variable_1, qual,
                                                                                  object_variable_2)
                        self.__add_interaction_pattern(event_type, object_type_1, o2o_forall_exists_pattern)
        for object_type_1, multi_relation_info in self.event_type_object_to_object_multi_relations[event_type].items():
            object_variable_id_1 = self.variable_prefixes[object_type_1]
            object_variable_1 = ObjectVariableArgument(object_type_1, object_variable_id_1)
            for object_type_2, quals in multi_relation_info.items():
                for qual in quals:
                    object_variable_id_2 = self.variable_prefixes[object_type_2]
                    object_variable_2 = ObjectVariableArgument(object_type_2, object_variable_id_2)
                    ########################################
                    ##### exists x: forall y: o2o(x,y) #####
                    ########################################
                    o2o_exists_forall_pattern = get_o2o_exists_forall_formula(
                        object_variable_1, qual, object_variable_2)
                    #############################################
                    ##### exists x: complete o2o(x, y_type) #####
                    #############################################
                    o2o_exists_complete_pattern = get_o2o_complete_formula(object_variable_1, qual, object_type_2)
                    self.__add_interaction_pattern(event_type, object_type_1, o2o_exists_forall_pattern)
                    self.__add_interaction_pattern(event_type, object_type_1, o2o_exists_complete_pattern)

    def __make_misc_patterns(self, event_type):
        if self.makeCardinalityPatterns:
            self.__make_object_type_cardinality_patterns(event_type)

    def __make_object_type_cardinality_patterns(self, event_type):
        relations = self.ocel.relations
        event_type_relations = relations[relations["ocel:activity"] == event_type]
        et_ot_cardinalities = event_type_relations.groupby(['ocel:eid', 'ocel:type'])['ocel:oid'].nunique()
        ot_cardinalities = et_ot_cardinalities.groupby('ocel:type').value_counts(normalize=True). \
            unstack(fill_value=0)
        np.seterr(divide='ignore')
        ot_cardinalities["entropy"] = ot_cardinalities.iloc[:, 1:].apply(lambda row: -np.sum(row * np.log2(row)),
                                                                         axis=1)
        ot_cardinalities = ot_cardinalities[
            (ot_cardinalities["entropy"] >= self.categoricalSearchMinEntropy) &
            (ot_cardinalities["entropy"] <= self.categoricalSearchMaxEntropy)]
        ot_cardinalities.drop(columns=["entropy"], inplace=True)
        if len(ot_cardinalities) == 0:
            return
        ot_cardinalities_dict = ot_cardinalities.apply(lambda row: row.index[row.gt(0)].tolist(), axis=1).to_dict()
        for object_type, cards in ot_cardinalities_dict.items():
            for card in cards:
                card_pattern = get_ot_card_formula(object_type, card)
                self.__add_basic_pattern(event_type, card_pattern)

    def __create_variable_prefixes(self):
        used_prefixes = set()
        self.variable_prefixes = {}
        self.variable_prefixes_reverse = {}
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
            self.variable_prefixes_reverse[prefix] = object_type
            used_prefixes.add(prefix)

    def __initialize_search_plans(self):
        self.searched_basic_patterns = {}
        self.searched_interaction_patterns = {}
        self.custom_patterns = {}
        self.object_categorical_attribute_patterns = {}
        self.patterns_by_ids = {}
        for event_type in self.event_types:
            self.searched_basic_patterns[event_type] = {}
            self.searched_interaction_patterns[event_type] = {
                object_type: {} for object_type in self.event_types_object_types[event_type]}
            self.custom_patterns[event_type] = {}

    def load_tables(self, event_types):
        self.table_managers = {}
        self.base_table_creation_times = {}
        self.base_table_evaluation = {
            "event_type": [],
            "number_of_events": [],
            "number_of_objects": [],
            "number_of_object_to_object_relations": [],
            "number_of_event_to_object_relations": [],
            "time": []
        }
        for i in range(len(event_types)):
            event_type = event_types[i]
            event_object_types = self.event_types_object_types[event_type]
            print("Starting to load auxiliary tables for event type '" + event_type + "', " + str(i + 1) + "/" + str(
                len(event_types)) + ".")
            import time
            start = time.time()
            table_manager = TableManager(self.ocel, event_type, event_object_types)
            self.table_managers[event_type] = table_manager
            end = time.time()
            runtime = end - start
            print("Finished loading auxiliary tables for event type '" + event_type + "', " + str(i + 1) + "/" + str(
                len(event_types)) + ", time: " + str(runtime))
            number_of_event_to_object_relations = 0
            for object_type in self.event_types_object_types[event_type]:
                number_of_event_to_object_relations += len(table_manager.get_event_objects(object_type))
            number_of_object_to_object_relations = len(table_manager.get_object_interaction_table())
            number_of_events = len(table_manager.get_event_index())
            self.base_table_creation_times[event_type] = runtime
            self.base_table_evaluation["event_type"].append(event_type)
            self.base_table_evaluation["number_of_events"].append(number_of_events)
            self.base_table_evaluation["number_of_objects"].append(
                len(set(table_manager.get_object_evolutions_table()["ocel:oid"].values)))
            self.base_table_evaluation["number_of_event_to_object_relations"].append(
                number_of_event_to_object_relations)
            self.base_table_evaluation["number_of_object_to_object_relations"].append(
                number_of_object_to_object_relations)
            self.base_table_evaluation["time"].append(runtime)

    def __configure_search(self, selected_pattern_ids):
        for event_type, event_type_patterns in selected_pattern_ids["patterns"].items():
            self.searched_basic_patterns[event_type] = {
                k: p for k, p in self.searched_basic_patterns[event_type].items()
                if k in event_type_patterns["basic_patterns"]
            }
            self.searched_interaction_patterns[event_type] = {
                ot: {
                    k: p
                    for k, p in ps.items()
                    if k in event_type_patterns["interaction_patterns"][ot]}
                for ot, ps in self.searched_interaction_patterns[event_type].items()
            }
            self.custom_patterns[event_type] = {
                k: p for k, p in self.custom_patterns[event_type].items()
                if k in event_type_patterns["custom_patterns"]
            }

    def search_models(self, event_types, selected_pattern_ids, minimal_support):
        from copy import deepcopy
        searched_basic_patterns = deepcopy(self.searched_basic_patterns)
        searched_interaction_patterns = deepcopy(self.searched_interaction_patterns)
        custom_patterns = deepcopy(self.custom_patterns)
        self.__configure_search(selected_pattern_ids)
        self.__make_base_tables(event_types)
        resp = self.__search_models(event_types, minimal_support)
        self.searched_basic_patterns = searched_basic_patterns
        self.searched_interaction_patterns = searched_interaction_patterns
        self.custom_patterns = custom_patterns
        return resp

    def search_rules(self, event_types, selected_pattern_ids, target_pattern_description, max_rule_ante_length, min_rule_ante_support):
        from copy import deepcopy
        searched_basic_patterns = deepcopy(self.searched_basic_patterns)
        searched_interaction_patterns = deepcopy(self.searched_interaction_patterns)
        custom_patterns = deepcopy(self.custom_patterns)
        self.__configure_search(selected_pattern_ids)
        self.__make_base_tables(event_types)
        self.__search_rules(event_types, target_pattern_description, max_rule_ante_length, min_rule_ante_support)
        self.searched_basic_patterns = searched_basic_patterns
        self.searched_interaction_patterns = searched_interaction_patterns
        self.custom_patterns = custom_patterns

    def __make_base_tables(self, event_types):
        self.base_tables = {}
        self.anti_patterns = {}
        for i in range(len(event_types)):
            event_type = event_types[i]
            print("Starting to search patterns for event type '" + event_type + "', " + str(i + 1) + "/" + str(
                len(event_types)) + ".")
            table_manager = self.table_managers[event_type]
            base_table = self.__make_bootstrap_table(event_type, table_manager)
            #if len(base_table.columns) > self.maxInitialPatterns:
            #    raise RuntimeError("More bootstrap patterns found than allowed by the 'max_initial_patterns' "
            #                       "parameter.")
            if self.mergeMode:
                base_table = self.__merge_interaction_patterns(event_type, base_table, table_manager)
            if self.complementaryMode:
                base_table = self.__add_anti_patterns(event_type, base_table)
            self.base_tables[event_type] = base_table

    def __search_models(self, event_types, minimal_support):
        resp = {
            "model_evaluations": {},
            "all_patterns": {}
        }
        self.pattern_supports = {}
        self.maximal_pattern_supports = {}
        self.models = {}
        for event_type in event_types:
            self.__make_models(event_type, minimal_support)
            print("Finished searching patterns for event type '" + event_type + "'.")
            resp[event_type] = {}
            model = self.models[event_type]
            pattern_ids = model.pattern_ids
            pattern_ids = sorted(pattern_ids)
            resp["all_patterns"][event_type] = pattern_ids
            eval = {}
            eval["recall"] = model.get_recall()
            eval["precision"] = model.get_precision()
            eval["discrimination"] = model.get_discrimination()
            eval["simplicity"] = model.get_simplicity()
            resp["model_evaluations"][event_type] = eval
        return resp

    def __search_rules(self, event_types, target_pattern_description, max_rule_ante_length, min_rule_ante_support):
        for event_type in event_types:
            self.__make_rules(event_type, target_pattern_description, max_rule_ante_length, min_rule_ante_support)

    def __make_rules(self, event_type, target_pattern_description, max_rule_ante_length, min_rule_ante_support):
        base_table = self.base_tables[event_type]
        n = len(base_table)
        allowed = [
            # .... descriptive patterns ...
            'ex(De,oaval_eq_{OnTime,False}(De))',
        ]
        # comment in if filter "allowed" active
        #base_table = base_table.drop(columns=[x for x in base_table.columns if x not in allowed])
        target_pattern_prevalence = (base_table[target_pattern_description] == True).sum() / n
        from mlxtend.frequent_patterns import apriori, association_rules
        base_table_target_pattern = base_table[:]
        print(list(base_table_target_pattern.columns))
        frequent_itemsets_target_pattern = apriori(
            base_table_target_pattern, min_support=target_pattern_prevalence*min_rule_ante_support, use_colnames=True, max_len=max_rule_ante_length+1
        )
        rules_target_pattern = association_rules(frequent_itemsets_target_pattern, metric="lift", min_threshold=1.0)
        rules_target_pattern = rules_target_pattern[rules_target_pattern["consequents"].apply(
            lambda c: len(c) == 1 and target_pattern_description in c
        )]
        path = get_session_path()
        session_key_str = session.get("session_key", "???")
        friendly_event_type_string = event_type.strip().replace(":", "")
        base_table_path = os.path.join(path, "base_table_" + friendly_event_type_string + "_" + session_key_str + ".xlsx")
        base_table_target_pattern.to_excel(base_table_path)
        if rules_target_pattern is not None:
            rules_target_pattern["length"] = rules_target_pattern["antecedents"].apply(lambda a: len(a))
            rules_target_pattern = rules_target_pattern[rules_target_pattern["antecedent support"] > min_rule_ante_support]
            rules_target_pattern["event_count_antecedent"] = np.round(rules_target_pattern["antecedent support"] * n)
            rules_target_pattern["event_count_rule"] = np.round(rules_target_pattern["support"] * n)
            rules_target_pattern.sort_values(by=["lift", "event_count_antecedent"], ascending=[False, True], inplace=True)
            rule_path = os.path.join(path, friendly_event_type_string + "rules_" + target_pattern_description + "_" + session_key_str + ".xlsx")
            rules_target_pattern.to_excel(rule_path)

    def __make_bootstrap_table(self, event_type: str, table_manager: TableManager) -> DataFrame:
        basic_patterns = self.searched_basic_patterns[event_type]
        interaction_patterns = self.searched_interaction_patterns[event_type]
        custom_patterns = self.custom_patterns[event_type]
        searched_patterns = {}
        for pattern_id, pattern in basic_patterns.items():
            searched_patterns[pattern_id] = pattern
        for object_type, patterns in interaction_patterns.items():
            for pattern_id, pattern in patterns.items():
                searched_patterns[pattern_id] = pattern
        for pattern_id, pattern in custom_patterns.items():
            searched_patterns[pattern_id] = pattern
        evaluated_pattern_series = []
        evaluated_pattern_keys = []
        for pattern_id, pattern in searched_patterns.items():
            print(pattern_id)
            evaluation = pattern.evaluate(table_manager)["ox:evaluation"]
            evaluated_pattern_series.append(evaluation)
            evaluated_pattern_keys.append(pattern_id)
        base_table = pd.concat(
            objs = evaluated_pattern_series,
            keys = evaluated_pattern_keys,
            axis = 1
        )
        path = get_session_path()
        base_table_path = os.path.join(path, "base_table_" + event_type.replace(":","") + ".xlsx")
        base_table.to_excel(base_table_path)
        return base_table

    def __merge_interaction_patterns(self, event_type, base_table: DataFrame, table_manager: TableManager):
        total_count = 0
        interaction_patterns = self.searched_interaction_patterns[event_type]
        for object_type, patterns in interaction_patterns.items():
            if self.event_type_object_types_variability[event_type][object_type]:
                count, base_table = self.__merge_variable_types_existential_patterns(
                    patterns.values(), base_table, table_manager, event_type, object_type)
                total_count += count
        return base_table

    def __add_anti_patterns(self, event_type, base_table):
        pattern_ids_and_pattern = list(self.searched_basic_patterns[event_type].items())
        pattern_ids_and_pattern += [(pattern_id, pattern)
                                    for object_type, interaction_patterns in
                                    self.searched_interaction_patterns[event_type].items()
                                    for pattern_id, pattern in interaction_patterns.items()]
        self.anti_patterns[event_type] = {}
        for pattern_id, pattern in pattern_ids_and_pattern:
            # KISS
            anti_pattern_eval = ~base_table[pattern_id].astype(bool)
            anti_pattern = get_anti_pattern(pattern)
            anti_pattern_id = anti_pattern.to_string()
            object_type = pattern.get_object_type()
            if object_type is None:
                self.__add_basic_pattern(event_type, anti_pattern)
                self.anti_patterns[event_type][pattern_id] = anti_pattern
            else:
                self.__add_interaction_pattern(event_type, object_type, anti_pattern)
                self.anti_patterns[event_type][pattern_id] = anti_pattern
            base_table[anti_pattern_id] = anti_pattern_eval
        return base_table

    def __make_models(self, event_type, minimal_support):
        self.maximal_pattern_supports[event_type] = {}
        base_table = self.base_tables[event_type]
        working_table = base_table[:]
        self.__make_fpgrowth_models(event_type, working_table, minimal_support)

    def __make_fpgrowth_models(self, event_type, base_table, minimal_support):
        minimal_support = minimal_support if minimal_support > 0 else 1 / (len(base_table) + 1)
        object_types = self.event_types_object_types[event_type]
        path = get_session_path()
        pattern_supports = fpmax(base_table, min_support=minimal_support, use_colnames=True)
        valid_patterns, pattern_supports = self.__extract_valid_patterns(pattern_supports)
        valid_patterns_df = pd.DataFrame({"support": [1.0], "itemsets": [frozenset(valid_patterns)]})
        postprocessed_pattern_supports = self.__postprocess_pattern_supports_frame(pattern_supports)
        postprocessed_valid_patterns   = self.__postprocess_pattern_supports_frame(valid_patterns_df)
        model = Model(pattern_supports, postprocessed_pattern_supports, postprocessed_valid_patterns, base_table, event_type,
                      object_types, evaluation_mode=self.evaluationMode)
        pattern_path = os.path.join(path, "pattern_supports_" + event_type + "_min_freq_" + str(minimal_support) + ".xlsx")
        self.models[event_type] = model
        pattern_supports.to_excel(pattern_path)

    def __simplify_mining_results(self, event_type, pattern_supports):
        simplified_patterns = pattern_supports.copy()
        pattern_descriptors = pattern_supports["itemsets"]
        merged_descriptors = self.__post_pattern_merge(event_type, pattern_descriptors)
        return merged_descriptors

    def __post_pattern_merge(self, event_type, pattern_descriptors):
        merged_descriptors = pattern_descriptors.apply(
            lambda descriptor:
            self.__merge_patterns_per_descriptor(event_type, descriptor)
        )
        return merged_descriptors

    def __extract_valid_patterns(self, pattern_supports):
        valid_patterns = set.intersection(*(set(descriptor_list) for descriptor_list in pattern_supports["itemsets"]))
        reduced_pattern_supports = pattern_supports[:]
        reduced_pattern_supports["reduced_itemsets"] = pattern_supports["itemsets"].apply(
            lambda x: frozenset([item for item in x if item not in valid_patterns])
        )
        reduced_pattern_supports.drop(columns=["itemsets"], inplace=True)
        reduced_pattern_supports.rename(columns={"reduced_itemsets": "itemsets"}, inplace=True)
        return valid_patterns, reduced_pattern_supports

    def __factor_out_valid_patterns(self, pattern_descriptors):
        valid_patterns = set.intersection(*(set(descriptor_list) for descriptor_list in pattern_descriptors))
        distinct_descriptors = pattern_descriptors.apply(
            lambda lst: [item for item in lst if item not in valid_patterns])
        return distinct_descriptors, valid_patterns

    def __merge_patterns_per_descriptor(self, event_type, descriptor):
        basic_patterns = self.searched_basic_patterns[event_type]
        object_type_patterns = self.searched_interaction_patterns[event_type]
        pattern_ids_to_pattern = basic_patterns.copy()
        pattern_ids_to_pattern.update({
            pattern.to_string(): pattern
            for object_type, patterns in object_type_patterns.items()
            for pattern_id, pattern in patterns.items()
        })
        merged_descriptor = []
        singleton_types_existential_patterns = {}
        variable_types_universal_patterns = {}
        for pattern_id in descriptor:
            pattern: PatternFormula = pattern_ids_to_pattern[pattern_id]
            if isinstance(pattern, ExistentialPattern):
                pattern: ExistentialPattern
                variable = pattern.quantifiedVariable
                object_type = variable.objectType
                is_singleton_type = not self.event_type_object_types_variability[event_type][object_type]
                if is_singleton_type:
                    if object_type not in singleton_types_existential_patterns:
                        singleton_types_existential_patterns[object_type] = []
                    singleton_types_existential_patterns[object_type].append(pattern)
                else:
                    merged_descriptor.append(pattern_id)
            if isinstance(pattern, UniversalPattern):
                pattern: UniversalPattern
                variable = pattern.quantifiedVariable
                object_type = variable.objectType
                is_variable_type = self.event_type_object_types_variability[event_type][object_type]
                if is_variable_type:
                    if object_type not in variable_types_universal_patterns:
                        variable_types_universal_patterns[object_type] = []
                    variable_types_universal_patterns[object_type].append(pattern)
                else:
                    merged_descriptor.append(pattern_id)
        for singleton_type, existential_patterns in singleton_types_existential_patterns.items():
            merged_pattern = get_existential_patterns_merge(existential_patterns)
            merged_pattern_id = merged_pattern.to_string()
            merged_descriptor.append(merged_pattern_id)
            self.searched_interaction_patterns[event_type][singleton_type][merged_pattern_id] = merged_pattern
        for variable_type, universal_patterns in variable_types_universal_patterns.items():
            merged_pattern = get_universal_patterns_merge(universal_patterns)
            merged_pattern_id = merged_pattern.to_string()
            merged_descriptor.append(merged_pattern_id)
            self.searched_interaction_patterns[event_type][variable_type][merged_pattern_id] = merged_pattern
        return merged_descriptor

    def __merge_variable_types_existential_patterns(self, patterns, base_table, table_manager, event_type, object_type):
        existential_patterns = list(filter(lambda pat: isinstance(pat, ExistentialPattern), patterns))
        bootstrap_patterns = list(map(lambda pat: ({pat[0]}, pat[1]), enumerate(existential_patterns)))
        total_events = len(base_table)
        index_to_pattern_id = {
            str(pat[0]): pat[1].to_string()
            for pat in bootstrap_patterns
        }
        evaluation_scores = {
            str(pat[0]): base_table[index_to_pattern_id[str(pat[0])]].sum() / total_events
            for pat in bootstrap_patterns
        }
        # for create indices also store the pattern to save it in the PatternMiningManager
        creates = {}
        deletes = []
        checked_indices = [index for index, patt in bootstrap_patterns]
        update = True
        count = 0
        rounds = 0
        indexed_merged_patterns = bootstrap_patterns.copy()
        new_columns = []
        while update and rounds < self.maxBootstrapPatternMergeRecursion:
            rounds = rounds + 1
            update = False
            candidate_tuples = product(bootstrap_patterns, indexed_merged_patterns)
            indexed_merged_patterns = []
            for indexed_bootstrap_pattern, indexed_merged_pattern in candidate_tuples:
                bootstrap_index, bootstrap_pattern = indexed_bootstrap_pattern
                bootstrap_pattern_id = bootstrap_pattern.to_string()
                old_merged_index, old_merged_pattern = indexed_merged_pattern
                old_merged_pattern_id = old_merged_pattern.to_string()
                if bootstrap_index.issubset(old_merged_index):
                    continue
                new_index = old_merged_index.union(bootstrap_index)
                if new_index in checked_indices:
                    if str(new_index) in creates:
                        new_merged_score = evaluation_scores[str(new_index)]
                        creates, deletes = self.__update_creates_deletes(
                            event_type, object_type, evaluation_scores, bootstrap_index, bootstrap_pattern_id,
                            old_merged_index, old_merged_pattern_id, new_merged_score, creates, deletes)
                    continue
                new_merged_pattern: ExistentialPattern = get_existential_patterns_merge(
                    [bootstrap_pattern, old_merged_pattern])
                new_merged_pattern_id = new_merged_pattern.to_string()
                new_merged_evaluation = new_merged_pattern.evaluate(table_manager)
                new_merged_score = float(new_merged_evaluation["ox:evaluation"].sum()) / total_events
                evaluation_scores[str(new_index)] = new_merged_score
                if new_merged_score >= self.minSupport:
                    update = True
                    count += 1
                    creates[str(new_index)] = new_merged_pattern
                    index_to_pattern_id[str(new_index)] = new_merged_pattern_id
                    new_merged_evaluation.rename(columns={"ox:evaluation": new_merged_pattern_id}, inplace=True)
                    new_columns.append(new_merged_evaluation)
                    indexed_merged_patterns.append((new_index, new_merged_pattern))
                    creates, deletes = self.__update_creates_deletes(
                        event_type, object_type, evaluation_scores, bootstrap_index, bootstrap_pattern_id,
                        old_merged_index, old_merged_pattern_id, new_merged_score, creates, deletes)
                    total_number_of_patterns = len(base_table.columns) + len(new_columns) - len(deletes)
                    if total_number_of_patterns >= self.maxInitialPatterns:
                        import warnings
                        warnings.warn(
                            "Pattern merge recursion pre-terminated because maximal number "
                            + "of patterns as set by max_bootstrap_patterns was reached.")
                        update = False
                        break
                checked_indices = checked_indices + [new_index]
        if len(new_columns) > 0:
            new_columns_frame = pd.concat(new_columns, axis=1)
            base_table = pd.concat([base_table, new_columns_frame], axis=1)
        base_table.drop(columns=[index_to_pattern_id[str(delete_index)] for delete_index in deletes], inplace=True)
        for create_pattern in creates.values():
            self.__add_interaction_pattern(event_type, object_type, create_pattern)
        return count, base_table

    def __update_creates_deletes(self, event_type, object_type, evaluation_scores, bootstrap_index,
                                 bootstrap_pattern_id, old_merged_index, old_merged_pattern_id, new_merged_score,
                                 creates, deletes):
        bootstrap_score = evaluation_scores[str(bootstrap_index)]
        old_merged_score = evaluation_scores[str(old_merged_index)]
        if new_merged_score / bootstrap_score > self.patternMergeSubsumptionRatio:
            if bootstrap_index not in deletes:
                deletes = deletes + [bootstrap_index]
                self.__delete_interaction_pattern(event_type, object_type, bootstrap_pattern_id)
        if new_merged_score / old_merged_score > self.patternMergeSubsumptionRatio:
            if old_merged_index not in deletes:
                deletes = deletes + [old_merged_index]
                if len(old_merged_index) == 1:
                    pass
                    self.__delete_interaction_pattern(event_type, object_type, old_merged_pattern_id)
                else:
                    pass
                    del creates[str(old_merged_index)]
        return creates, deletes

    def save_base_table_evaluation(self):
        base_table_eval = pd.DataFrame(self.base_table_evaluation)
        path = get_session_path()
        session_key_str = session.get("session_key", "???")
        eval_path = os.path.join(path, "base_table_evaluation_" + session_key_str + ".xlsx")
        base_table_eval.to_excel(eval_path)
        config_str = "maxInitialPatterns: " + str(self.maxInitialPatterns) + "\n"
        config_str += "maxBootstrapPatternMergeRecursion: " + str(self.maxBootstrapPatternMergeRecursion) + "\n"
        config_str += "complementaryMode: " + str(self.complementaryMode) + "\n"
        config_str += "mergeMode: " + str(self.mergeMode) + "\n"
        eval_config_path = os.path.join(path, "base_table_eval_config_" + session_key_str + ".txt")
        with open(eval_config_path, "w") as wf:
            wf.write(config_str)

    def visualize_global_scores(self):
        eval_df = pd.DataFrame(self.evaluation_records)
        for event_type in self.event_types_filter:
            et_eval_df = eval_df[eval_df["event_type"] == event_type]
            fig, ax1 = plt.subplots()
            ax1.plot(et_eval_df['minimal_frequency'], et_eval_df['precision'], linestyle='-', label='precision',
                     color='tab:blue')
            ax1.plot(et_eval_df['minimal_frequency'], et_eval_df['recall'], linestyle='--', label='recall',
                     color='tab:orange')
            ax1.plot(et_eval_df['minimal_frequency'], et_eval_df['discrimination'], linestyle=':',
                     label='discrimination', color='tab:red')
            ax2 = ax1.twinx()
            ax2.semilogy(et_eval_df['minimal_frequency'], et_eval_df['simplicity'], label='simplicity',
                         color='tab:green', base=10)
            ax1.legend(loc='upper center')
            ax2.legend(loc='lower center')
            ax1.set_xlabel('Minimal pattern set frequency')
            ax1.set_ylabel('Scores (Prec, Rec, Discr)', color='tab:blue')
            ax2.set_ylabel('Simplicity (log10 scale)', color='tab:red')
            plt.title('Complementary mode = ' + str(self.complementaryMode) + "; Merge mode = " + str(self.mergeMode))
            path = get_session_path()
            path = os.path.join(path, "event_type_viz_" + event_type + "_" + self.sessionKey + ".png")
            plt.savefig(path)
            plt.clf()

    def visualize_splits(self):
        pass

    def set_event_types_filter(self, selected_event_types):
        self.event_types_filter = selected_event_types

    def save_split_evaluation(self):
        eval_df = pd.DataFrame(self.split_evaluation_records)
        path = get_session_path()
        session_key_str = session.get("session_key", "???")
        eval_path = os.path.join(path, "eval_split_" + self.evaluationMode.value + "_" + session_key_str + ".xlsx")
        eval_df.to_excel(eval_path)

    def register_custom_pattern(self, event_type, pattern: PatternFormula):
        pattern_id = pattern.to_string()
        self.custom_patterns[event_type][pattern_id] = pattern
        self.patterns_by_ids[pattern_id] = pattern

    def __partition_info_to_response(self, partition_info, object_types):
        keep = partition_info["object-type"].isin(object_types) | partition_info["object-type"].isna()
        partition_info_filtered = partition_info[keep]
        partition_info_filtered.sort_values(by="support", ascending=False, inplace=True)
        groups = partition_info_filtered.groupby("partition-id", sort=False)
        i = 0
        resp = {}
        if len(groups) == 0:
            return { 0 : {
                "pattern_ids": [],
                "pretty_pattern_ids": [],
                "support": 1.0,
                "argument_ids": {} }
            }
        for partition_id, group in groups:
            pattern_ids = list(filter(lambda pid: pd.notna(pid), group["pattern-id"].to_list()))
            pretty_patterns = group["pattern"].apply(
                lambda p: self.__get_formula_TeX(p)
                if pd.notna(p)
                else "$$\\emptyset$$"
            ).to_list()
            pretty_patterns = list(set(pretty_patterns))
            pretty_patterns = sorted(pretty_patterns)
            support = group["support"].to_list()[0]
            resp[i] = {
                "pattern_ids": pattern_ids,
                "pretty_pattern_ids": pretty_patterns,
                "support": support,
                "argument_ids": {}
            }
            for object_type in object_types:
                ot_arguments = group[group["object-type"] == object_type]["arguments"]
                ot_arguments = reduce(lambda x, y: x.union(y), ot_arguments) if len(ot_arguments) > 0 else set()
                resp[i]["argument_ids"][object_type] = list(ot_arguments)
            i = i + 1
        merged_resp = {}
        indices = {}
        pattern_sets = []
        j = 0
        # If we apply object type filters, some partitions may fall together
        for part in resp.values():
            key = str(sorted(part["pattern_ids"]))
            if key not in pattern_sets:
                pattern_sets.append(key)
                index = j
                indices[key] = index
                merged_resp[index] = {}
                merged_resp[index]["support"] = 0
                merged_resp[index]["pattern_ids"] = part["pattern_ids"]
                merged_resp[index]["pretty_pattern_ids"] = part["pretty_pattern_ids"]
                merged_resp[index]["argument_ids"] = part["argument_ids"]
                j += 1
            else:
                index = indices[key]
            merged_resp[index]["support"] += part["support"]
        return merged_resp


    def __partition_info_response(self, partition_info, valid_patterns, object_types):
        resp1 = self.__partition_info_to_response(partition_info, object_types)
        resp2 = self.__partition_info_to_response(valid_patterns, object_types)
        merged_resp = {}
        merged_resp["partitions"] = resp1
        merged_resp["valid_patterns"] = resp2[0]
        return merged_resp

    def get_model_response(self, event_type, object_types=None):
        if object_types is None:
            object_types = self.object_types
        model: Model = self.models[event_type]
        partition_info = model.postprocessed_pattern_supports
        valid_patterns = model.postprocessed_valid_patterns
        return self.__partition_info_response(partition_info, valid_patterns, object_types)

    def __make_partition_info(self, E, Q):
        print()
        supports_dict = {
            "itemsets": Q,
            "support": [E[pattern_ids].all(axis=1).sum() / len(E) for pattern_ids in Q]
        }
        df = pd.DataFrame(supports_dict)
        df = self.__postprocess_pattern_supports_frame(df)
        return df

    def __postprocess_pattern_supports_frame(self, pattern_supports):
        df = (pattern_supports.explode("itemsets").reset_index()
              .rename(columns={"index": "partition-id", "itemsets": "pattern-id"}))
        df["pattern"] = df["pattern-id"].apply(lambda p_id: self.patterns_by_ids[p_id]
            if pd.notna(p_id)
            else np.nan
        )
        df["object-type"] = df["pattern"].apply(lambda p: p.get_object_types() if pd.notna(p) else set())
        df["object-type"] = df["object-type"].apply(lambda ots: ots if len(ots) > 0 else set([np.nan]))
        df = df.explode("object-type").reset_index().drop("index", axis=1)
        if(len(df) > 0):
            df["arguments"] = df.apply(lambda row:
                row["pattern"].get_typed_arguments(row["object-type"]) if pd.notna(row["pattern"]) else set(), axis=1)
        else:
            df["arguments"] = pd.Series()
        return df

    def __get_formula_TeX(self, p: PatternFormula):
        return "$$\\mathit{" + p.to_TeX() + "}$$"

