import pandas as pd
import numpy as np
from pandas import DataFrame
from pm4py import OCEL


class Table:

    def __init__(self, event_type):
        self.eventType = event_type
        self.table = None

    def get(self) -> DataFrame:
        return self.table[:]
