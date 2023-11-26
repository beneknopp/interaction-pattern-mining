import time
import warnings
from itertools import product

import numpy as np
from flask import session
from matplotlib import pyplot as plt
from mlxtend.frequent_patterns import apriori, fpmax, association_rules
from pandas import DataFrame
from pm4py import OCEL

import os
import pickle

import pandas as pd

from pattern_mining.model import Model
from utils.misc_utils import is_categorical_data_type, list_equals

pd.options.mode.chained_assignment = None
warnings.simplefilter("ignore", FutureWarning)

from pattern_mining.PATTERN_FORMULAS import get_ot_card_formula, get_e2o_exists_formula, get_o2o_exists_exists_formula, \
    get_o2o_exists_forall_formula, get_o2o_complete_formula, get_oaval_eq_exists_pattern, ExistentialPattern, \
    get_existential_patterns_merge, get_e2o_forall_formula, get_o2o_forall_exists_formula, get_eaval_eq_pattern, \
    UniversalPattern, get_universal_patterns_merge, get_anti_pattern
from pattern_mining.domains import ObjectVariableArgument
from pattern_mining.pattern_formula import PatternFormula
from pattern_mining.table_manager import TableManager
from utils.session_utils import get_session_path

evaluation_mode = True


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
                 categorical_search_min_entropy=0.01,
                 categorical_search_max_entropy=2.0,
                 categorical_variables_max_labels=10,
                 max_initial_patterns=1000,
                 max_bootstrap_pattern_merge_recursion=100000,
                 pattern_merge_subsumption_ratio=0.995,
                 min_split_information_gain=0.1,
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
        self.sessionKey = session.get('session_key', None)
        self.ocel = ocel
        self.__preprocess_ocel()
        self.entropyAttributesSplit = entropy_attributes_split
        self.entropySplitRecursionLevels = entropy_split_recursion_levels
        self.categoricalSearchMinEntropy = categorical_search_min_entropy
        self.categoricalSearchMaxEntropy = categorical_search_max_entropy
        self.categoricalVariablesMaxLabels = categorical_variables_max_labels
        self.maxInitialPatterns = max_initial_patterns
        self.maxBootstrapPatternMergeRecursion = max_bootstrap_pattern_merge_recursion
        self.patternMergeSubsumptionRatio = pattern_merge_subsumption_ratio
        self.minSplitInformationGain = min_split_information_gain
        self.minSupport = min_support

    def __preprocess_ocel(self):
        events = self.ocel.events
        object_changes = self.ocel.object_changes
        # TODO: handle timezones
        events["ocel:timestamp"] = pd.to_datetime(events["ocel:timestamp"].dt.tz_localize(None))
        object_changes["ocel:timestamp"] = pd.to_datetime(object_changes["ocel:timestamp"].dt.tz_localize(None))

    def visualize_results(self):
        eval_df = pd.DataFrame(self.evaluation_records)
        minimal_frequencies_strs = [str(round(x*100)/100) for x in self.minimal_frequencies]
        for event_type in eval_df["event_type"].values:
            #support_sums = eval_df[eval_df["event_type"] == event_type][["min_support_" + min_support_str + "_sum_of_itemsets_supports" for min_support_str in min_support_strings]].values.tolist()[0]
            #entropies = eval_df[eval_df["event_type"] == event_type][["min_support_" + min_support_str + "_supports_entropy" for min_support_str in min_support_strings]].values.tolist()[0]
            #scores = eval_df[eval_df["event_type"] == event_type][["min_support_" + min_support_str + "_score" for min_support_str in min_support_strings]].values.tolist()[0]
            scores = eval_df[eval_df["event_type"] == event_type][["partition_construction_approach_scores_" + event_inclusion_step for event_inclusion_step in minimal_frequencies_strs]].values.tolist()[0]
            viz_table = pd.DataFrame({
                #"Sum of Supports": support_sums,
                #"Support Entropy": entropies,
                "score": scores,
                "% events included": minimal_frequencies_strs
            })
            #plt.plot(viz_table['Minimal Pattern Support'], viz_table["Sum of Supports"], label="Sum of Supports")
            #plt.plot(viz_table['Minimal Pattern Support'], viz_table['Support Entropy'], label='Support Entropy')
            plt.plot(viz_table['% events included'], viz_table['score'], label='score')
            # Add labels and title
            plt.xlabel('% events included')
            plt.legend()  # Show legend with labels
            plt.title('Partition method for event type ' + event_type)
            path = get_session_path()
            path = os.path.join(path, event_type + "_eval" + ".png")
            plt.savefig(path)
            plt.clf()


    def save_evaluation(self):
        eval = pd.DataFrame(self.evaluation_records)
        path = get_session_path()
        for event_type in eval["event_type"].values:
            #pattern_supports: DataFrame = self.pattern_supports[event_type]
            #path = get_session_path()
            #path1 = os.path.join(path, "pattern_supports_" + event_type + ".xlsx")
            #pattern_supports.to_excel(path1)
            #path1 = os.path.join(path, "pattern_supports_" + event_type + ".csv")
            #pattern_supports.to_csv(path1)
            min_support_to_maximal_pattern_supports = self.maximal_pattern_supports[event_type]
            for minimal_support, maximal_pattern_supports in min_support_to_maximal_pattern_supports.items():
                maximal_pattern_supports: DataFrame
                #path2 = os.path.join(path, "maximal_pattern_supports_" + event_type + "_" + str(minimal_support) + ".xlsx")
                #maximal_pattern_supports.to_excel(path2)
                path2 = os.path.join(path,"maximal_pattern_supports_" + event_type + "_" + str(minimal_support) + ".csv")
                maximal_pattern_supports.to_csv(path2)
            #association_rules: DataFrame = self.association_rules[event_type]
            #path3 = os.path.join(path, "association_rules_" + event_type + ".xlsx")
            #association_rules.to_excel(path3)
        eval_path = os.path.join(path, "evaluation.xlsx")
        eval.to_excel(eval_path)
        config_str = "maxInitialPatterns: " + str(self.maxInitialPatterns) +"\n"
        config_str += "maxBootstrapPatternMergeRecursion: " + str(self.maxBootstrapPatternMergeRecursion) + "\n"
        eval_config_path = os.path.join(path, "evaluation_config.txt")
        with open(eval_config_path, "w") as wf:
            wf.write(config_str)

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
        search_plans = {
            event_type: list(id_to_pattern.keys())
            for event_type, id_to_pattern in self.searched_basic_patterns.items()
        }
        for event_type, object_type_to_interaction_patterns in self.searched_interaction_patterns.items():
            for object_type, id_to_pattern in object_type_to_interaction_patterns.items():
                search_plans[event_type] += list(id_to_pattern.keys())
        return search_plans

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

    def __make_default_search_plans(self):
        if self.entropyAttributesSplit:
            self.__make_entropy_attributes_split()
        self.searched_basic_patterns = {}
        self.searched_interaction_patterns = {}
        self.object_categorical_attribute_patterns = {}
        for event_type in self.event_types:
            self.searched_basic_patterns[event_type] = {}
            self.searched_interaction_patterns[event_type] = {
                object_type: {} for object_type in self.event_types_object_types[event_type]}
            self.__make_default_search_plan(event_type)

    def __make_default_independent_pattern_plans(self):
        self.searched_independent_patterns = {}
        for event_type in self.event_types:
            self.searched_independent_patterns[event_type] = {}

    def __add_basic_pattern(self, event_type, pattern: PatternFormula):
        pattern_id = pattern.to_string()
        self.searched_basic_patterns[event_type][pattern_id] = pattern

    def __add_interaction_pattern(self, event_type, object_type, pattern: PatternFormula):
        pattern_id = pattern.to_string()
        self.searched_interaction_patterns[event_type][object_type][pattern_id] = pattern

    def __delete_interaction_pattern(self, event_type, object_type, pattern_id: str):
        del self.searched_interaction_patterns[event_type][object_type][pattern_id]

    def __make_entropy_attributes_split(self):
        raise NotImplementedError("Please implement me")

    def __make_default_search_plan(self, event_type):
        self.__make_event_attributes_default_patterns(event_type)
        self.__make_object_attributes_default_patterns(event_type)
        self.__make_event_type_to_object_default_patterns(event_type)
        self.__make_event_type_objects_to_objects_default_patterns(event_type)
        self.__make_misc_patterns(event_type)

    def __make_event_attributes_default_patterns(self, event_type):
        for attribute, dtype in self.event_attribute_data_types[event_type].items():
            if is_categorical_data_type(dtype):
                # TODO: unify, maybe build TableManager already in __init__
                labels = set(self.ocel.events[attribute].dropna().values)
                if len(labels) > self.categoricalVariablesMaxLabels:
                    continue
                for label in labels:
                    eaval_eq_exists_pattern = get_eaval_eq_pattern(attribute, label)
                    self.__add_basic_pattern(event_type, eaval_eq_exists_pattern)

    def __make_object_attributes_default_patterns(self, event_type):
        self.object_categorical_attribute_patterns[event_type] = {}
        for object_type in self.event_types_object_types[event_type]:
            self.object_categorical_attribute_patterns[event_type][object_type] = {}
            object_variable_id = self.variable_prefixes[object_type]
            object_variable_argument = ObjectVariableArgument(object_type, object_variable_id)
            for attribute, dtype in self.object_attribute_data_types[object_type].items():
                if is_categorical_data_type(dtype):
                    # TODO: unify, maybe build TableManager already in __init__
                    labels = set(self.objects[attribute].dropna().values)
                    labels = labels.union(set(self.ocel.object_changes[attribute].dropna().values))
                    if len(labels) > self.categoricalVariablesMaxLabels:
                        continue
                    self.object_categorical_attribute_patterns[event_type][object_type][attribute] = []
                    for label in labels:
                        oaval_eq_exists_pattern = get_oaval_eq_exists_pattern(object_variable_argument, attribute,
                                                                              label)
                        self.object_categorical_attribute_patterns[event_type][object_type][attribute].append(oaval_eq_exists_pattern)
                        self.__add_interaction_pattern(event_type, object_type, oaval_eq_exists_pattern)

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
                        o2o_forall_exists_pattern = get_o2o_forall_exists_formula(object_variable_1, qual, object_variable_2)
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
        self.__make_object_type_cardinality_patterns(event_type)

    def __make_object_type_cardinality_patterns(self, event_type):
        relations = self.ocel.relations
        event_type_relations = relations[relations["ocel:activity"] == event_type]
        et_ot_cardinalities = event_type_relations.groupby(['ocel:eid', 'ocel:type'])['ocel:oid'].nunique()
        ot_cardinalities = et_ot_cardinalities.groupby('ocel:type').value_counts(normalize=True). \
            unstack(fill_value=0)#.to_dict(orient='index')
        np.seterr(divide='ignore')
        ot_cardinalities["entropy"] = ot_cardinalities.iloc[:, 1:].apply(lambda row: -np.sum(row * np.log2(row)), axis=1)
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

    def search_models(self, event_types):
        self.evaluation_records = {
            "event_type": [],
            "run": [],
            "recall": [],
            "precision": [],
            "discrimination": [],
            "simplicity": [],
            "rule_splits": [],
            "time": []
        }
        self.minimal_frequencies = [0.05*(i) for i in range(21)]
        pattern: PatternFormula
        self.pattern_supports = {}
        self.maximal_pattern_supports = {}
        self.anti_patterns = {}
        self.base_tables = {}
        self.models = {}
        for event_type in event_types:
            event_object_types = self.event_types_object_types[event_type]
            print("Starting for event type '" + event_type + "'.")
            table_manager = TableManager(self.ocel, event_type, event_object_types)
            base_table = self.__make_bootstrap_table(event_type, table_manager)
            if len(base_table.columns) > self.maxInitialPatterns:
                raise RuntimeError ("More bootstrap patterns found than allowed by the 'max_initial_patterns' "
                                      "parameter.")
            base_table = self.__merge_interaction_patterns(event_type, base_table, table_manager)
            base_table = self.__add_anti_patterns(event_type, base_table)
            model = self.__make_models(event_type, base_table)

            self.base_tables[event_type] = base_table
            print("Finished for event type '" + event_type + "'.")


    def __get_boolean_table_average_entropy(self, table: DataFrame, columns):
        average_entropy = 0
        n = len(table)
        for col in columns:
            boolean_sum = table[col].sum()
            if boolean_sum == n or boolean_sum == 0:
                entropy = 0
            else:
                entropy = -(np.log2(boolean_sum / n) * boolean_sum / n + np.log2((n - boolean_sum) / n) * (n - boolean_sum) / n)
            average_entropy += entropy
        return average_entropy / n

    def __make_bootstrap_table(self, event_type: str, table_manager: TableManager) -> DataFrame:
        base_table = table_manager.get_event_index()
        basic_patterns = self.searched_basic_patterns[event_type]
        interaction_patterns = self.searched_interaction_patterns[event_type]
        self.evaluation_records["event_type"].append(event_type)
        for pattern_id, pattern in basic_patterns.items():
            evaluation = pattern.evaluate(table_manager)
            base_table.loc[:, pattern_id] = evaluation
        for object_type, patterns in interaction_patterns.items():
            for pattern_id, pattern in patterns.items():
                evaluation = pattern.evaluate(table_manager)
                base_table.loc[:, pattern_id] = evaluation
        return base_table

    def __merge_interaction_patterns(self, event_type, base_table: DataFrame, table_manager:TableManager):
        total_count = 0
        interaction_patterns = self.searched_interaction_patterns[event_type]
        for object_type, patterns in interaction_patterns.items():
            if self.event_type_object_types_variability[event_type][object_type]:
                count, base_table = self.__merge_variable_types_existential_patterns(
                    patterns.values(), base_table, table_manager, event_type, object_type)
                total_count += count
        return base_table

    def __add_anti_patterns(self,event_type, base_table):
        pattern_ids_and_pattern = list(self.searched_basic_patterns[event_type].items())
        pattern_ids_and_pattern += [(pattern_id, pattern)
                                    for object_type, interaction_patterns in self.searched_interaction_patterns[event_type].items()
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


    def __make_models(self, event_type, base_table: DataFrame):
        self.maximal_pattern_supports[event_type] = {}
        working_table = base_table[:]
        #informative_columns = [col for col in working_table.columns
        #                       if not (working_table[col].astype(bool).all() or (~working_table[col]).astype(bool).all())]
        #working_table = working_table[informative_columns]
        self.__make_fpgrowth_models(event_type, working_table)

    def __make_fpgrowth_models(self, event_type, base_table):
        path = get_session_path()
        object_types = self.event_types_object_types[event_type]
        for i in range(len(self.minimal_frequencies)):
            if i == 0:
                minimal_frequency = 1 / (len(base_table) + 1)
            elif i == len(self.minimal_frequencies) - 1:
                minimal_frequency = 1 - (len(base_table) + 1)
            else:
                minimal_frequency = self.minimal_frequencies[i]
            minimal_frequency_str = str(round(minimal_frequency*100)/100)
            pattern_supports = fpmax(base_table, min_support=minimal_frequency, use_colnames=True)
            pattern_supports["itemsets"] = pattern_supports["itemsets"].apply(lambda x: sorted(x))
            model = Model(pattern_supports, base_table, event_type, object_types)
            splitter_groups = self.__get_splitter_groups(event_type)
            model.make_splits(self.minSplitInformationGain, splitter_groups)
            simplified_patterns = self.__simplify_mining_results(event_type, pattern_supports)
            supports_sum = sum(simplified_patterns["support"])
            supports_entropy = simplified_patterns.iloc[:, :1].apply(lambda row: -(row / supports_sum * np.log2(row))).sum()[0]
            total_complexity = self.__get_total_complexity(simplified_patterns)
            pattern_complexity = self.__get_pattern_complexity(simplified_patterns)
            path1 = os.path.join(path, "pattern_supports_" + event_type + "_min_freq_" + minimal_frequency_str + ".xlsx")
            simplified_patterns.to_excel(path1)

    def __get_splitter_groups(self, event_type):
        patterns = self.object_categorical_attribute_patterns[event_type]
        split_patterns = []
        for object_type, cat_att_to_patts in patterns.items():
            cat_patts = []
            for cat_att, patts in cat_att_to_patts.items():
                split_patterns[object_type][cat_att] = []
                for patt in patts:
                    anti_patt = self.anti_patterns[event_type][patt.to_string()]
                    cat_patts.append(patt)
                    cat_patts.append(anti_patt)
            split_patterns.append((cat_att, cat_patts))
        return split_patterns

    def __simplify_mining_results(self, event_type, pattern_supports):
        simplified_patterns = pattern_supports.copy()
        pattern_descriptors = pattern_supports["itemsets"]
        merged_descriptors = self.__post_pattern_merge(event_type, pattern_descriptors)
        distinct_descriptors = self.__factor_out_valid_patterns(merged_descriptors)
        simplified_patterns["itemsets"] = distinct_descriptors
        return simplified_patterns

    def __post_pattern_merge(self, event_type, pattern_descriptors):
        merged_descriptors = pattern_descriptors.apply(
            lambda descriptor:
                self.__merge_patterns_per_descriptor(event_type, descriptor)
        )
        return merged_descriptors

    def __factor_out_valid_patterns(self, pattern_descriptors):
        valid_patterns = set.intersection(*(set(descriptor_list) for descriptor_list in pattern_descriptors))
        distinct_descriptors = pattern_descriptors.apply(lambda lst: [item for item in lst if item not in valid_patterns])
        return distinct_descriptors

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

    def __get_total_complexity(self, pattern_supports):
        return len(set([pattern_id for descriptor in pattern_supports["itemsets"].values for pattern_id in descriptor]))

    def __get_pattern_complexity(self, pattern_supports):
        return sum(pattern_supports["support"] * pattern_supports["itemsets"].apply(lambda x: len(x) + 1))

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
                            event_type, object_type, evaluation_scores, bootstrap_index, bootstrap_pattern_id, old_merged_index, old_merged_pattern_id, new_merged_score, creates, deletes)
                    continue
                new_merged_pattern: ExistentialPattern = get_existential_patterns_merge([bootstrap_pattern, old_merged_pattern])
                new_merged_pattern_id = new_merged_pattern.to_string()
                new_merged_evaluation = new_merged_pattern.evaluate(table_manager)
                new_merged_score = float(new_merged_evaluation["ox:evaluation"].sum()) / total_events
                evaluation_scores[str(new_index)] = new_merged_score
                if new_merged_score >= self.minSupport:
                    update = True
                    count += 1
                    creates[str(new_index)] = new_merged_pattern
                    index_to_pattern_id[str(new_index)] = new_merged_pattern_id
                    base_table.loc[:, new_merged_pattern_id] = new_merged_evaluation
                    indexed_merged_patterns.append((new_index, new_merged_pattern))
                    creates, deletes = self.__update_creates_deletes(
                        event_type, object_type,evaluation_scores, bootstrap_index, bootstrap_pattern_id, old_merged_index, old_merged_pattern_id, new_merged_score, creates, deletes)
                    total_number_of_patterns = len(base_table.columns) - len(deletes)
                    if total_number_of_patterns >= self.maxInitialPatterns:
                        import warnings
                        warnings.warn(
                            "Pattern merge recursion pre-terminated because maximal number "
                            + "of patterns as set by max_bootstrap_patterns was reached.")
                        update = False
                        break
                checked_indices = checked_indices + [new_index]
        #base_table.drop(columns=[index_to_pattern_id[str(delete_index)] for delete_index in deletes], inplace=True)
        for create_pattern in creates.values():
            self.__add_interaction_pattern(event_type, object_type, create_pattern)
        return count, base_table

    def __update_creates_deletes(self, event_type, object_type, evaluation_scores, bootstrap_index, bootstrap_pattern_id, old_merged_index, old_merged_pattern_id, new_merged_score, creates, deletes):
        bootstrap_score = evaluation_scores[str(bootstrap_index)]
        old_merged_score = evaluation_scores[str(old_merged_index)]
        if new_merged_score / bootstrap_score > self.patternMergeSubsumptionRatio:
            if bootstrap_index not in deletes:
                deletes = deletes + [bootstrap_index]
                #self.__delete_interaction_pattern(event_type, object_type, bootstrap_pattern_id)
        if new_merged_score / old_merged_score > self.patternMergeSubsumptionRatio:
            if old_merged_index not in deletes:
                deletes = deletes + [old_merged_index]
                if len(old_merged_index) == 1:
                    pass
                    #self.__delete_interaction_pattern(event_type, object_type, old_merged_pattern_id)
                else:
                    pass
                    #del creates[str(old_merged_index)]
        return creates, deletes
