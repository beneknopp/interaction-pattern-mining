import numpy as np
import pandas as pd

from utils.misc_utils import list_equals


class ModelSplit:

    def __init__(self, information_gain, split_attribute, split_patterns, subsplit):
        self.information_gain = information_gain
        self.split_attribute = split_attribute
        self.split_patterns = split_patterns
        self.subsplit = subsplit
        self.partitioner = None
        self.E = None

    def to_string(self):
        if self.partitioner is not None:
            return str(self.partitioner)
        else:
            subsplit_str = ",".join([subs.to_string() for subs in self.subsplit]) if self.subsplit is not None else ""
            return str(self.information_gain) + "," + self.split_attribute + subsplit_str

class Model:

    def __init__(self, partitioner, events_satisfactions, event_type, object_types):
        self.min_split_information_gain = None
        self.split_paths = None
        self.partitioner = partitioner
        self.events_satisfactions = events_satisfactions
        self.event_type = event_type
        self.object_types = object_types
        self.pattern_ids = []
        self.__retrieve_pattern_ids()

    def __retrieve_pattern_ids(self):
        for pattern_set in self.partitioner:
            self.pattern_ids += pattern_set
        self.pattern_ids = list(set(self.pattern_ids))

    def make_splits(self, min_split_information_gain, splitter_groups, max_depth = 1):
        self.min_split_information_gain = min_split_information_gain
        split_paths = self.__recursive_split(self.events_satisfactions.copy(), self.partitioner, splitter_groups, max_depth)
        self.split_paths = split_paths
        return split_paths

    def __recursive_split(self, E, partitioner, splitter_groups, depth):
        if depth == 0:
            final_split = ModelSplit(None, None, None, None)
            final_split.partitioner = partitioner
            final_split.E = E
            return final_split
        max_information_gain = 0
        pattern_ids = E.columns
        best_partition = None
        best_partitioners = None
        remaining_splitter_groups = None
        remaining_pattern_ids = None
        subsplits = []
        split_attribute = None
        best_split_pattern_ids = None
        for cat_att, patterns in splitter_groups:
            split_pattern_ids = list(map(lambda pat: pat.to_string(), patterns))
            information_gain, partition, partitioners = self.__get_split_information_gain(E, partitioner, split_pattern_ids)
            if information_gain > max_information_gain:
                max_information_gain = information_gain
                split_attribute = cat_att
                remaining_pattern_ids = [pid for pid in pattern_ids if pid not in split_pattern_ids]
                best_partition = partition
                best_partitioners = partitioners
                best_split_pattern_ids = split_pattern_ids
                remaining_splitter_groups = [(attr, patts) for (attr,patts) in splitter_groups if not attr == split_attribute]
        if max_information_gain < self.min_split_information_gain:
            final_split = ModelSplit(None, None, None, None)
            final_split.partitioner = partitioner
            final_split.E = E
            return final_split
        for i in range(len(best_partition)):
            E_ = best_partition[i][remaining_pattern_ids]
            sub_partitioner = best_partitioners[i]
            sub_partitions = self.__recursive_split(E_, sub_partitioner, remaining_splitter_groups, depth - 1)
            subsplits.append(sub_partitions)
        return ModelSplit(max_information_gain, split_attribute, best_split_pattern_ids, subsplits)

    def __get_split_information_gain(self, E, partitioner, split_pattern_ids):
        if len(E) == 0:
            return 0
        information_gain = 0
        n = len(partitioner)
        # See paper 'Mining Interaction Patterns', Theorem 2
        A = {}
        P = {}
        P_ = {}
        Q = {}
        Q_ = {}
        E_ = {}
        for i in range(n):
            P[i] = partitioner[i]
            A[i] = [patt_id for patt_id in split_pattern_ids if patt_id in P[i]]
            P_[i] = [patt_id for patt_id in P[i] if patt_id not in A[i]]
        for i in range(n):
            do_continue = False
            for j in range(i):
                if list_equals(A[i], A[j]):
                    Q[i] = Q[j]
                    Q_[i] = Q_[j]
                    E_[i] = E_[j]
                    do_continue = True
                    break
            if do_continue:
                continue
            Q[i] = [P[j] for j in range(n) if list_equals(A[i], A[j])]
            Q_[i] = [P_[j] for j in range(n) if list_equals(A[i], A[j])]
            E_i = E[:]
            E_i["any_in_Qi"] = False
            for P_j in Q[i]:
                E_i["any_in_Qi"] = E_i["any_in_Qi"] | E_i[P_j].all(axis=1)
            E_i = E_i[E_i["any_in_Qi"]].drop(columns=["any_in_Qi"], inplace=False)
            E_[i] = E_i
        for i in range(n):
            if any(list_equals(A[i], A[j]) for j in range(i)):
                del E_[i]
                del Q_[i]
                continue
            # support of Pi' in Ei
            E_i = E_[i]
            Pi_ = P_[i]
            support_E_i = E_i[E_i[Pi_].all(axis=1)]
            support_E = E[E[Pi_].all(axis=1)]
            new_support = len(support_E_i)/len(E_i) if len(E_i) > 0 else 0
            old_support = len(support_E)/len(E)
            information_gain += len(E_i)/len(E) * abs(new_support - old_support)
        E_ = dict(enumerate(E_.values()))
        Q_ = dict(enumerate(Q_.values()))
        return information_gain, E_, Q_

    def get_precision(self):
        precision_table = pd.DataFrame(index=self.events_satisfactions.index)
        for i in range(len(self.partitioner)):
            pattern_set = self.partitioner[i]
            precision_table["ox:P_"+str(i)] = self.events_satisfactions[pattern_set].all(axis=1)
        precision_table["more_than_one_satisfying_pattern_set"] = precision_table.sum(axis=1) > 1
        imprecisely_characterized = precision_table["more_than_one_satisfying_pattern_set"].sum()
        precision = 1 - imprecisely_characterized / len(precision_table)
        return precision

    def __get_support_table(self):
        support_table = pd.DataFrame(index=self.events_satisfactions.index)
        for i in range(len(self.partitioner)):
            pattern_set = self.partitioner[i]
            support_table["ox:P_"+str(i)] = self.events_satisfactions[pattern_set].all(axis=1)
        supported = (support_table.sum(axis=1) > 0).sum()
        return supported, support_table

    def get_recall(self):
        supported, support_table = self.__get_support_table()
        recall = supported / len(support_table)
        return recall
    def get_discrimination(self):
        total_supported, support_table = self.__get_support_table()
        entropy_table = pd.DataFrame(index=support_table.columns)
        entropy_table["supported"] = support_table.sum()
        entropy_table["relative_support"] = entropy_table["supported"] / total_supported
        entropy_table["entropies"] = entropy_table["relative_support"] * np.log2(entropy_table["relative_support"])
        discrimination = - entropy_table["entropies"].sum()
        return discrimination

    def get_simplicity(self):
        total_number_of_patterns = len(set([pattern_id for pattern_set in self.partitioner for pattern_id in pattern_set]))
        simplicity = 1 / (1 + total_number_of_patterns)
        return simplicity
