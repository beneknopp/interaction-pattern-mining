import time
from itertools import product

import numpy as np
from flask import session
from mlxtend.frequent_patterns import apriori, fpmax, association_rules
from pandas import DataFrame
from pm4py import OCEL

import os
import pickle

import pandas as pd

from utils.misc_utils import is_categorical_data_type

pd.options.mode.chained_assignment = None

from pattern_mining.PATTERN_FORMULAS import get_ot_card_formula, get_e2o_exists_formula, get_o2o_exists_exists_formula, \
    get_o2o_exists_forall_formula, get_o2o_complete_formula, get_oaval_eq_exists_pattern, ExistentialPattern, \
    get_existential_patterns_merge, get_e2o_forall_formula, get_o2o_forall_exists_formula
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
                 # TODO: do we need this?
                 merged_formula_subsumption_th=1.01,
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
           merged_formula_subsumption_th (float)
                Two patterns at an event type that are existentially quantified for the same variable object type can be merged into
                a single pattern that is a conjunction of the subpatterns of the two existential patterns. For example, if multiple
                employees (variable object type) work at a "send package" event and there exists one employee with role "shipment" and there
                exists one employee with event-to-object relationship "shipper", we should check whether this is one and the same employee.
                If the ratio between the support of the merged pattern in the event log and the support of one of the simpler patterns in the event
                log is above merged_formula_subsumption_th, the simpler pattern will be deleted (excluded from the bootstrap search).
           categorical_variables_max_labels (int)
                Categorical attributes will by default be translated into patterns that check if an object at an event has a specific label.
                If we have more labels for an attribute than specified by this 'parameter categorical_variables_max_labels', these patterns
                will not be built.
           min_support (float)
                The minimal support of a pattern to be returned by the pattern mining procedure.
         """
        # self.session_key = session_key
        self.sessionKey = session.get('session_key', None)
        self.ocel = ocel
        self.entropyAttributesSplit = entropy_attributes_split
        self.entropySplitRecursionLevels = entropy_split_recursion_levels
        self.categoricalSearchMinEntropy = categorical_search_min_entropy
        self.categoricalSearchMaxEntropy = categorical_search_max_entropy
        self.categoricalVariablesMaxLabels = categorical_variables_max_labels
        self.mergedFormulaSubsumptionThreshold = merged_formula_subsumption_th
        self.minSupport = min_support

    def save_evaluation(self):
        path = get_session_path()
        for event_type in self.event_types:
            pattern_supports: DataFrame = self.pattern_supports[event_type]
            #path1 = os.path.join(path, "pattern_supports_" + event_type + ".xlsx")
            #pattern_supports.to_excel(path1)
            path1 = os.path.join(path, "pattern_supports_" + event_type + ".csv")
            pattern_supports.to_csv(path1)
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
        eval = pd.DataFrame(self.evaluation_records)
        eval.to_excel(eval_path)

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
            for event_type, id_to_pattern in self.search_basic_patterns.items()
        }
        for event_type, object_type_to_interaction_patterns in self.search_interaction_patterns.items():
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
        e2o = self.ocel.relations[:].drop_duplicates()
        o2o = self.ocel.o2o[:].drop_duplicates()
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
        self.search_basic_patterns = {}
        self.search_interaction_patterns = {}
        for event_type in self.event_types:
            self.search_basic_patterns[event_type] = {}
            self.search_interaction_patterns[event_type] = {
                object_type: {} for object_type in self.event_types_object_types[event_type]}
            self.__make_default_search_plan(event_type)

    def __add_basic_pattern(self, event_type, pattern: PatternFormula):
        pattern_id = pattern.to_string()
        self.search_basic_patterns[event_type][pattern_id] = pattern

    def __add_interaction_pattern(self, event_type, object_type, pattern: PatternFormula):
        pattern_id = pattern.to_string()
        self.search_interaction_patterns[event_type][object_type][pattern_id] = pattern

    def __make_entropy_attributes_split(self):
        raise NotImplementedError("Please implement me")

    def __make_default_search_plan(self, event_type):
        self.__make_event_attributes_default_patterns(event_type)
        self.__make_object_attributes_default_patterns(event_type)
        self.__make_event_type_to_object_default_patterns(event_type)
        self.__make_event_type_objects_to_objects_default_patterns(event_type)
        self.__make_misc_patterns(event_type)

    def __make_event_attributes_default_patterns(self, event_type):
        pass

    def __make_object_attributes_default_patterns(self, event_type):
        for object_type in self.event_types_object_types[event_type]:
            object_variable_id = self.variable_prefixes[object_type]
            object_variable_argument = ObjectVariableArgument(object_type, object_variable_id)
            for attribute, dtype in self.object_attribute_data_types[object_type].items():
                if is_categorical_data_type(dtype):
                    # TODO: unify, maybe build TableManager already in __init__
                    labels = set(self.objects[attribute].dropna().values)
                    labels = labels.union(set(self.ocel.object_changes[attribute].dropna().values))
                    for label in labels:
                        oaval_eq_exists_pattern = get_oaval_eq_exists_pattern(object_variable_argument, attribute,
                                                                              label)
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

    def search(self):
        max_itemsets_minimal_supports = [round(100.0 * 0.05 * (i + 1)) / 100.0 for i in range(20)]
        self.evaluation_records = {
            "event_type": [],
            "number_of_bootstrap_patterns": [],
            "number_of_merged_patterns": [], "pattern_evaluation_time": [],
            "itemset_mining_time": [], "number_of_itemsets": [],
        }
        for min_support in max_itemsets_minimal_supports:
            self.evaluation_records["min_support_" + str(min_support) + "_fp_time"] = []
            self.evaluation_records["min_support_" + str(min_support) + "_number_of_itemsets"] = []
        ocel = self.ocel
        pattern: PatternFormula
        self.pattern_supports = {}
        self.maximal_pattern_supports = {}
        self.association_rules = {}
        event_type_object_types = list(self.event_types_object_types.items())
        #for event_type, event_object_types in [("send package", ["items", "products", "packages", "employees"])] + event_type_object_types:
        for event_type, event_object_types in event_type_object_types:
            print("Starting for event type '" + event_type + "'.")
            table_manager = TableManager(ocel, event_type, event_object_types)
            start_time = time.time()
            base_table = self.__make_bootstrap_table(event_type, table_manager)
            base_table = self.__merge_interaction_patterns(event_type, table_manager, base_table)
            end_time = time.time()
            elapsed_time = end_time - start_time
            self.evaluation_records["pattern_evaluation_time"].append(elapsed_time)
            pattern_supports = self.__search_frequent_itemsets(base_table)
            self.evaluation_records["number_of_itemsets"].append(len(pattern_supports))
            self.pattern_supports[event_type] = pattern_supports
            #self.__search_association_rules(event_type, pattern_supports)
            self.__search_maximal_frequent_itemsets(event_type, base_table, max_itemsets_minimal_supports)
            print("Finished for event type '" + event_type + "'.")

    def __make_bootstrap_table(self, event_type: str, table_manager: TableManager) -> DataFrame:
        base_table = table_manager.get_event_index()
        basic_patterns = self.search_basic_patterns[event_type]
        interaction_patterns = self.search_interaction_patterns[event_type]
        number_of_bootstrap_patterns = len(basic_patterns) + sum(
            len(ot_pats) for ot_pats in interaction_patterns.values())
        self.evaluation_records["event_type"].append(event_type)
        self.evaluation_records["number_of_bootstrap_patterns"].append(number_of_bootstrap_patterns)
        start_time = time.time()
        for pattern_id, pattern in basic_patterns.items():
            evaluation = pattern.evaluate(table_manager)
            base_table.loc[:, pattern_id] = evaluation
        for object_type, patterns in interaction_patterns.items():
            for pattern_id, pattern in patterns.items():
                evaluation = pattern.evaluate(table_manager)
                base_table.loc[:, pattern_id] = evaluation
        return base_table

    def __merge_interaction_patterns(self, event_type, table_manager:TableManager, base_table: DataFrame):
        total_count = 0
        interaction_patterns = self.search_interaction_patterns[event_type]
        for object_type, patterns in interaction_patterns.items():
            if self.event_type_object_types_variability[event_type][object_type]:
                count, base_table = self.__merge_variable_types_existential_patterns(patterns.values(), base_table,
                                                                                     table_manager)
                total_count += count
        self.evaluation_records["number_of_merged_patterns"].append(total_count)
        return base_table

    def __search_frequent_itemsets(self, base_table: DataFrame):
        start_time = time.time()
        pattern_supports = apriori(base_table, min_support=self.minSupport, use_colnames=True)
        # readability
        end_time = time.time()
        elapsed_time = end_time - start_time
        self.evaluation_records["itemset_mining_time"].append(elapsed_time)
        pattern_supports["itemsets"] = pattern_supports["itemsets"].apply(lambda x: sorted(x))
        return pattern_supports

    def __search_maximal_frequent_itemsets(self, event_type, base_table: DataFrame, max_itemsets_minimal_supports: list):
        self.maximal_pattern_supports[event_type] = {}
        for min_support in max_itemsets_minimal_supports:
            start_time = time.time()
            maximal_pattern_supports = fpmax(base_table, min_support=min_support, use_colnames=True)
            end_time = time.time()
            elapsed_time = end_time - start_time
            self.evaluation_records["min_support_" + str(min_support) + "_fp_time"].append(elapsed_time)
            self.evaluation_records["min_support_" + str(min_support) + "_number_of_itemsets"].append(
                len(maximal_pattern_supports))
            maximal_pattern_supports["itemsets"] = maximal_pattern_supports["itemsets"].apply(lambda x: sorted(x))
            self.maximal_pattern_supports[event_type][min_support] = maximal_pattern_supports

    def __search_association_rules(self, event_type, pattern_supports: DataFrame):
        rules = association_rules(pattern_supports, metric="confidence", min_threshold=0.7)
        self.association_rules[event_type] = rules

    def __merge_variable_types_existential_patterns(self, patterns, base_table, table_manager):
        existential_patterns = list(filter(lambda pat: isinstance(pat, ExistentialPattern), patterns))
        indexed_merged_patterns = list(map(lambda pat: (pat[1], {pat[0]}), enumerate(existential_patterns)))
        checkedIndices = [{k} for k in range(len(existential_patterns))]
        update = True
        count = 0
        while update:
            update = False
            candidate_tuples = product(existential_patterns, indexed_merged_patterns)
            indexed_merged_patterns = []
            for pattern, indexed_merged_pattern in candidate_tuples:
                k = existential_patterns.index(pattern)
                merged_pattern, Index = indexed_merged_pattern
                newIndex = Index.union({k})
                if newIndex in checkedIndices:
                    continue
                new_merged_pattern: ExistentialPattern = get_existential_patterns_merge(pattern, merged_pattern)
                new_merged_pattern_id = new_merged_pattern.to_string()
                evaluation = new_merged_pattern.evaluate(table_manager)
                if float(evaluation.sum()) / len(evaluation) >= self.minSupport:
                    update = True
                    count += 1
                    base_table.loc[:, new_merged_pattern_id] = evaluation
                    indexed_merged_patterns.append((merged_pattern, newIndex))
                checkedIndices = checkedIndices + [newIndex]
        return count, base_table
