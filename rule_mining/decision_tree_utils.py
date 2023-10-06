import math

import numpy as np

from pandas import Interval

from logics.utils import Conjunction, Disjunction, Expression, BinaryExpression, BinaryOperator, AtomicExpression


class DecisionTreeNode:

    def __init__(self, instances, parent = None):
        self.parent = parent
        self.instances = instances
        self.children = []
        self.is_leaf = False

    def turn_to_leaf(self, target_feature):
        self.children = None
        total = len(self.instances)
        self.classes = set(self.instances[target_feature].values)
        self.weighted_classes = {
            target_class: float(len(self.instances[self.instances[target_feature] == target_class])) / total
            for target_class in self.classes
        }
        self.is_leaf = True

    def delete_training_data(self):
        self.instances = None
        if self.children is not None:
            for arc in self.children:
                arc.child.delete_training_data()

    def set_split_feature(self, split_feature):
        self.split_feature = split_feature


class DecisionTreeArc:

    def __init__(self, parent, child, condition: Expression):
        self.parent = parent
        self.child = child
        self.condition = condition


class DecisionTreeLeaf:

    def __init__(self, instances, classes, weighted_classes):
        self.instances = instances,
        self.classes = classes
        self.weighted_classes = weighted_classes


class DecisionTree:

    def __init__(self, min_information_gain: float = 0.0):
        self.min_information_gain = min_information_gain

    def fit(self, instances, feature_names, target_class):
        self.target_class = target_class
        self.feature_names = feature_names
        self.root = DecisionTreeNode(instances)
        self.target_class_values = instances[target_class].values
        self.expand(self.root)
        self.collect_garbage()

    def get_entropy(self, array):
        unique_elements, counts = np.unique(array, return_counts=True)
        total_count = len(array)
        relative_frequencies = counts / total_count
        entropy = -sum(map(lambda rf: rf*math.log(rf)/math.log(2), relative_frequencies))
        return entropy

    def expand(self, node):
        instances = node.instances
        target_labels = instances[self.target_class].values
        entropy = self.get_entropy(target_labels)
        total = len(instances)
        feature_split_entropies = {}
        for feature in self.feature_names:
            # TODO: treat non-categorical features
            feature_values = set(instances[feature].values)
            feature_split_entropy = 0
            for value in feature_values:
                value_share = instances[instances[feature] == value]
                value_share_entropy = self.get_entropy(value_share[self.target_class].values)
                value_share_total = len(value_share)
                feature_split_entropy = feature_split_entropy + value_share_entropy * value_share_total / total
            feature_split_entropies[feature] = feature_split_entropy
        best_split_feature = min(feature_split_entropies, key=feature_split_entropies.get)
        information_gain = entropy - feature_split_entropies[best_split_feature]
        if information_gain < self.min_information_gain:
            node.turn_to_leaf(self.target_class)
        else:
            self.split_node(node, best_split_feature)

    def parse_condition(self, attribute, value):
        if isinstance(value, Interval):
            left_expression_a = AtomicExpression(value.left)
            left_expression_b = AtomicExpression(attribute)
            open_left = value.open_left
            operator_left = BinaryOperator.SMALLER if open_left else BinaryOperator.SMALLER_EQUALS
            condition_left = BinaryExpression(left_expression_a, left_expression_a, operator_left)
            right_expression_a = AtomicExpression(attribute)
            right_expression_b = AtomicExpression(value.right)
            open_right = value.open_right
            operator_right = BinaryOperator.SMALLER if open_right else BinaryOperator.SMALLER_EQUALS
            condition_right = BinaryExpression(right_expression_a, right_expression_b, operator_right)
            condition = Conjunction([condition_left, condition_right])
        else:
            expression_a = AtomicExpression(attribute)
            expression_b = AtomicExpression(value)
            operator = BinaryOperator.EQUALS
            condition = BinaryExpression(expression_a, expression_b, operator)
        return condition


    def split_node(self, node, split_feature):
        node.set_split_feature(split_feature)
        instances = node.instances
        feature_values = set(instances[split_feature].values)
        for value in feature_values:
            value_share = instances[instances[split_feature] == value]
            child = DecisionTreeNode(value_share, node)
            condition = self.parse_condition(split_feature, value)
            arc = DecisionTreeArc(node, child, condition)
            node.children.append(arc)
            self.expand(child)

    def collect_garbage(self):
        self.root.delete_training_data()

    def add_reverse_function(self):
        self.reverse_function = {
            target_class_value: Disjunction()
            for target_class_value in self.target_class_values
        }
        node = self.root
        conjunction = Conjunction()
        self.__construct_reverse_function_recursive(node, conjunction)

    def __construct_reverse_function_recursive(self, node: DecisionTreeNode, conjunction: Conjunction):
        if node.is_leaf:
            for target_class_value in node.classes:
                disjunction: Disjunction = self.reverse_function[target_class_value]
                disjunction.add_operand(conjunction)
            return
        arc: DecisionTreeArc
        for arc in node.children:
            new_conjunction = Conjunction(
                operands= conjunction.operands + [arc.condition]
            )
            child = arc.child
            self.__construct_reverse_function_recursive(child, new_conjunction)
