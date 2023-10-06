from enum import Enum


class Operator(Enum):

    def print_sml(self):
        raise Exception("Abstract parent class method called")


class UnaryOperator(Operator):
    NOT = "NOT"

    def print_sml(self):
        return "not"


class BinaryOperator(Operator):

    SMALLER = "SMALLER"
    SMALLER_EQUALS = "SMALLER_EQUALS"
    EQUALS = "EQUALS"

    def print_sml(self):
        if self == BinaryOperator.SMALLER:
            return "<"
        if self == BinaryOperator.SMALLER_EQUALS:
            return "<="
        if self == BinaryOperator.EQUALS:
            return "="


class NAryOperator(Operator):

    AND = "AND"
    OR = "OR"

    def print_sml(self):
        if self == NAryOperator.AND:
            return "andalso"
        if self == NAryOperator.OR:
            return "orelse"


class Expression:

    def __init__(self):
        pass

    def print_sml(self):
        raise Exception("Abstract parent class method called")


class AtomicExpression(Expression):

    def __init__(self, value):
        self.value = value

    def print_sml(self):
        return str(self.value)


class UnaryExpression(Expression):

    def __init__(self, operand, operator: UnaryOperator):
        super().__init__()
        self.operand = operand
        self.operator = operator

    def print_sml(self):
        operator_str = self.operator.print_sml()
        operand_str = self.operand.print_sml()
        if operand_str.startswith("(") and operand_str.endswith(")"):
            operand_str = operand_str[1:-1]
        return "{} ({})".format(operator_str, operand_str)


class BinaryExpression(Expression):

    def __init__(self, operand_a: Expression, operand_b: Expression, operator: Operator):
        super().__init__()
        self.operand_a = operand_a
        self.operand_b = operand_b
        self.operator = operator

    def print_sml(self):
        operand_a_str = self.operand_a.print_sml()
        operator_str = self.operator.print_sml()
        operand_b_str = self.operand_b.print_sml()
        if operand_a_str.startswith("(") and operand_a_str.endswith(")"):
            operand_a_str = operand_a_str[1:-1]
        if operand_b_str.startswith("(") and operand_b_str.endswith(")"):
            operand_b_str = operand_b_str[1:-1]
        return "({}) {} ({})".format(operand_a_str, operator_str, operand_b_str)


class NAryExpression(Expression):

    def __init__(self, operator: NAryOperator, operands=None):
        super().__init__()
        if operands is None:
            operands = []
        self.operands = operands
        self.operator = operator

    def add_operand(self, operand):
        self.operands.append(operand)

    def print_sml(self):
        print_str = ""
        operator_str = self.operator.print_sml()
        operand: Expression
        n = len(self.operands)
        for idx in range(n):
            operand = self.operands[idx]
            operand_str = operand.print_sml()
            if operand_str.startswith("(") and operand_str.endswith(")"):
                operand_str = operand_str[1:-1]
            print_str += "(" + operand_str + ")"
            if idx < n - 1:
                print_str += operator_str
        return print_str


class Conjunction(NAryExpression):

    def __init__(self, operands=None):
        super().__init__(NAryOperator.AND, operands)

    def print_sml(self):
        if len(self.operands) == 0:
            return "True"
        else:
            return super().print_sml()


class Disjunction(NAryExpression):

    def __init__(self, operands=None):
        super().__init__(NAryOperator.OR, operands)

    def print_sml(self):
        if len(self.operands) == 0:
            return "False"
        else:
            return super().print_sml()