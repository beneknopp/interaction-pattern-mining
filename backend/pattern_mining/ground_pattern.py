from pm4py import OCEL

from pattern_mining.table_manager import TableManager


class GroundPattern:

    def __init__(self):
        pass

    def apply(self, tmg: TableManager, event):
        raise NotImplementedError()