import pandas as pd
from pandas import DataFrame
from pm4py import OCEL

from pattern_mining.tables.table import Table


class EventIndex(Table):

    def __init__(self, event_type):
        '''
        An EventTable (after calling EventTable.create) simply stores an dataframe with rows indexed by the event ids
        of an event type, but with no further information.

        :param event_type: The event type.
        '''
        super().__init__(event_type)

    def create(self, ocel: OCEL):
        all_events = ocel.events[:]
        events = all_events[all_events['ocel:activity'] == self.eventType]
        events_index = pd.DataFrame(index=events['ocel:eid'])
        self.table = events_index

    def join(self, df: DataFrame):
        if 'ocel:eid' not in df.columns:
            raise ValueError()
        index = self.table
        event_indexed_df = index.merge(df, left_index=True, right_on='ocel:eid', how='left')
        event_indexed_df.set_index(index.index, inplace=True)
        return event_indexed_df