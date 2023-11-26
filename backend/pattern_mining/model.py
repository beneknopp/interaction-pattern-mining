from utils.misc_utils import list_equals


class Model:

    def __init__(self, supports, base_table, event_type, object_types):
        self.supports = supports
        self.base_table = base_table
        self.event_type = event_type
        self.object_types = object_types
        self.pattern_ids = []
        self.__retrieve_pattern_ids()

    def __retrieve_pattern_ids(self):
        for itemsets in self.supports["itemsets"].values:
            self.pattern_ids += itemsets
        self.pattern_ids = list(set(self.pattern_ids))

    def make_splits(self, min_split_information_gain, splitter_groups):
        self.min_split_information_gain = min_split_information_gain
        split_paths = {}
        partitioner = self.supports["itemsets"]
        self.__recursive_split(self.base_table.copy(), partitioner, splitter_groups)
        return split_paths

    def __recursive_split(self, E, partitioner, splitter_groups):
        max_information_gain = 0
        pattern_ids = E.columns
        best_partition = None
        best_partitioners = None
        remaining_splitter_groups = None
        remaining_pattern_ids = None
        subsplits = []
        split_attribute = None
        for cat_att, patterns in splitter_groups:
            split_pattern_ids = list(map(lambda pat: pat.to_string(), patterns))
            information_gain, partition, partitioners = self.__get_split_information_gain(E, partitioner, split_pattern_ids)
            if information_gain > max_information_gain:
                max_information_gain = information_gain
                split_attribute = cat_att
                remaining_pattern_ids = [pid for pid in pattern_ids if pid not in split_pattern_ids]
                best_partition = partition
                best_partitioners = partitioners
                remaining_splitter_groups = [(attr, patts) for (attr,patts) in splitter_groups if not attr == split_attribute]
        if max_information_gain > self.min_split_information_gain:
            for i in range(len(best_partition)):
                E_ = best_partition[i][remaining_pattern_ids]
                sub_partitions = self.__recursive_split(E_, best_partitioners, remaining_splitter_groups)
                subsplits.append(sub_partitions)
        else:
            return (partitioner, E)
        return [split_attribute, subsplits]

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
            Q[i] = [P[j] for j in range(n) if list_equals(A[i], A[j])]
            Q_[i] = [P_[j] for j in range(n) if list_equals(A[i], A[j])]
            E_i = E[:]
            E_i["any_in_Qi"] = False
            for P_j in Q[i]:
                E_i["any_in_Qi"] = E_i["any_in_Qi"] | E_i[P_j].all(axis=1)
            E_i = E_i[E_i["any_in_Qi"]].drop(columns=["any_in_Qi"], inplace=False)
            E_[i] = E_i
        for i in range(n):
            # support of Pi' in Ei
            E_i = E_[i]
            Pi_ = P_[i]
            support_E_i = E_i[E_i[Pi_].all(axis=1)]
            support_E = E[E[Pi_].all(axis=1)]
            new_support = len(support_E_i)/len(E_i) if len(E_i) > 0 else 0
            old_support = len(support_E)/len(E)
            information_gain += len(E_i)/len(E) * abs(new_support - old_support)
        return information_gain, E_, Q_,
