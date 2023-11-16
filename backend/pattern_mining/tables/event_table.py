from pm4py import OCEL

from pattern_mining.tables.table import Table


class EventTable(Table):

    def __init__(self, event_type):
        '''
        An EventTable (after calling EventTable.create) stores for each event of an event type the event id (ocel:eid),
        the event timestamp (ocel:timestamp), and event attributes.
        Important! The entries are indexed by the event id.

        :param event_type: The event type.
        '''
        super().__init__(event_type)

    def create(self, ocel: OCEL):
        all_events = ocel.events[:]
        events = all_events[all_events['ocel:activity'] == self.eventType]
        self.table = events