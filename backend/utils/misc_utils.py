import numpy as np


def is_numeric_data_type(data_type):
    return data_type == float or data_type == np.float or data_type == int


def is_categorical_data_type(data_type):
    return data_type == object or data_type == str


