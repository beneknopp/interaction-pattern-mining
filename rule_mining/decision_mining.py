import os
import pickle
import pandas as pd
from pandas import DataFrame
from pm4py.objects.petri_net.obj import PetriNet
from sklearn.tree import DecisionTreeClassifier
from p_decision_tree.DecisionTree import DecisionTree
from event_log_processing.event_log_manager import EventLogManager
from rule_mining.decision_tree_utils import DecisionTree
from rule_mining.guard_utils import FlatEstimator
from logics.utils import Conjunction, Disjunction


class DecisionMiner:
    '''
    Mining guards (rules) for transitions in an object-centric Petri net.
    '''

    @classmethod
    def load(cls, name):
        path = os.getcwd()
        path = os.path.join(path, "rule_mining")
        path = os.path.join(path, name + ".pkl")
        with open(path, "rb") as rf:
            return pickle.load(rf)

    def __init__(self, name, object_types, petri_nets, alignments, event_log_manager: EventLogManager):
        """
        Create an object to conduct decision mining.

        :param name: The name of this DecisionMiner (for persistence purposes)
        :param object_types: The object types found in the object-centric Petri net.
        :param petri_nets: A dictionary storing for each object type the corresponding simple Petri net.
        :param alignments: A list of CaseAlignments storing for each object type the alignments of trace variants found in the
        passed enriched event frame (event_objects_attributes_frame).
        :param event_log_manager: For accessing the required data (frames).

        """
        if not set(object_types) == set(petri_nets.keys()):
            raise Exception("Petri nets do not describe the passed object types")
        if not set(object_types) == set(alignments.keys()):
            raise Exception("Alignments do not describe the passed object types")
        self.name = name
        self.__object_types = object_types
        self.__petri_nets = petri_nets
        self.__alignments = alignments
        self.__event_objects_attributes_frame = event_log_manager.get_event_object_attributes_frame()
        self.__o2o_frame = event_log_manager.get_o2o_frame()
        self.__attributes = list(
            filter(lambda x: x.startswith("ocim:attr:"), self.__event_objects_attributes_frame.columns)
        )

    def save(self):
        path = os.getcwd()
        path = os.path.join(path, "rule_mining")
        path = os.path.join(path, self.name + ".pkl")
        with open(path, "wb") as wf:
            pickle.dump(self, wf)

    def create_analytics_base_tables(self):
        """
        Enriches the alignments with information about the object attributes at each state.
        """
        analytics_base_tables = {}
        decision_pairs = {}
        event_frame: DataFrame = self.__event_objects_attributes_frame
        for object_type in self.__object_types:
            ot_alignments = self.__alignments[object_type]
            exploded_ot_alignments = map(lambda alm:
                    list(map(lambda move: [alm.case_id, move[0][1], move[1][0]], alm.alignment)),
                    ot_alignments)
            exploded_ot_alignments = [move for case_list in exploded_ot_alignments for move in case_list]
            ot_alignments_frame = pd.DataFrame(exploded_ot_alignments,
                columns= ["ocel:oid", "transition_name", "event_activity"]
            )
            event_frame["has_event"] = 1
            event_frame["event_counter"] = event_frame.groupby('ocel:oid')['has_event'].cumsum()
            event_frame.drop("has_event", axis=1, inplace=True)
            ot_alignments_frame["has_event"] = ot_alignments_frame.apply(lambda row: 0 if row["event_activity"] == ">>" else 1, axis = 1)
            ot_alignments_frame['event_counter'] = ot_alignments_frame.groupby('ocel:oid')['has_event'].cumsum()
            ot_alignments_frame.drop("has_event", axis=1, inplace=True)
            ot_enriched_alignments = event_frame.merge(ot_alignments_frame, on = ["ocel:oid", "event_counter"])
            ot_enriched_alignments.drop(["event_counter"], axis= 1, inplace=True)
            ###
            # Associate moves with decisions at places
            ###
            ot_petri_net = self.__petri_nets[object_type]
            arcs = ot_petri_net.arcs
            decision_pairs_ot = pd.DataFrame(list(map(
                lambda arc: [arc.source.name, arc.target.name],
                    filter(lambda arc: type(arc.target) == PetriNet.Transition and len(arc.source.out_arcs) > 1, arcs))),
                columns = ["place_id", "transition_name"]
            )
            decision_pairs[object_type] = decision_pairs_ot
            analytics_base_table = ot_enriched_alignments.merge(decision_pairs_ot, on=["transition_name"])
            analytics_base_tables[object_type] = analytics_base_table
        self.__decision_pairs = decision_pairs
        self.__analytics_base_tables = analytics_base_tables

    def __apply_decision_tree_mining(self, group):
        # Extract the target and features from the group
        target = group["transition_name"]
        feature_names = self.__attributes + ["shoe_size"]
        features = group[feature_names]
        # TODO: Robustness for missing / unclean data
        features = features.dropna(axis=1)
        feature_names = list(features.columns)
        # Create and fit a Decision Tree model
        model = DecisionTreeClassifier(min_impurity_decrease=0.0)
        model.fit(features, target)
        #model = DecisionTree(features.values, feature_names, target.tolist(), "entropy")
        return model

    def bin_numerical_features(self, features, df):
        column_types = df.dtypes.to_dict()
        for feature in features:
            if not (column_types[feature] == float):
                continue
            # TODO: generic solution for non-categoricals
            df[feature] = pd.cut(df[feature], bins=20)
        return df

    def build_flat_estimators(self):
        flat_estimators = {}
        for object_type in self.__object_types:
            analytics_base_table = self.__analytics_base_tables[object_type]
            decision_point_groups = analytics_base_table.groupby("place_id")
            decision_trees = {}
            for place_id, group in decision_point_groups:
                features = self.__attributes
                # TODO: Robustness for missing / unclean data
                features = list(group[features].dropna(axis=1).columns)
                preprocesses_group = self.bin_numerical_features(features, group)
                preprocesses_group["shoe_size"] = group.apply(lambda row: 42 if row["transition_name"].startswith("e3") else 38, axis = 1)
                feature_names = features + ["shoe_size"]
                decision_tree = DecisionTree(min_information_gain=0.1)
                target_class = "transition_name"
                decision_tree.fit(preprocesses_group, feature_names, target_class)
                decision_tree.add_reverse_function()
                decision_trees[place_id] = decision_tree
            decision_pairs = self.__decision_pairs[object_type]
            transition_names = set(decision_pairs["transition_name"].values)
            flat_estimators_ot = {}
            for transition_name in transition_names:
                condition: Conjunction = Conjunction()
                transition_preset = set(decision_pairs[decision_pairs["transition_name"] == transition_name]["place_id"]\
                    .values)
                for place_id in transition_preset:
                    decision_tree: DecisionTree = decision_trees[place_id]
                    disjunction: Disjunction = decision_tree.reverse_function[transition_name]
                    condition.add_operand(disjunction)
                flat_estimators_ot[transition_name] = condition
            flat_estimators[object_type] = flat_estimators_ot
        self.flat_estimators = flat_estimators

    def mine_decision_rules(self):
        self.create_analytics_base_tables()
        self.build_flat_estimators()
