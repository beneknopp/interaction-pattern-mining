from pandas import Series
from pattern_mining.table_manager import TableManager


class GroundPattern:

    def __init__(self):
        pass

    def apply(self, tmg: TableManager) -> Series:
        '''
        Evaluates the ground pattern on all the events of a particular event type in an event log.
        The event log projection to that event type is represented by a TableManager.

        :param tmg: the TableManager
        :return: a series of boolean values, indexed by event ids
        '''
        raise NotImplementedError()
