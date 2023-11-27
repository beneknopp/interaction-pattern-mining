import os
import pickle

from flask import session

from pattern_mining.tables.event_index import EventIndex
from pattern_mining.tables.event_interaction_table import EventInteractionTable
from pattern_mining.tables.event_objects import EventObjects
from pattern_mining.tables.event_table import EventTable
from pattern_mining.tables.o2o_table import O2OTable
from pattern_mining.tables.object_interaction_table import ObjectInteractionTable
from utils.session_utils import get_session_path


#TODO: get_evaluation_base_table(object_types) that returns a dataframe with columns: event_id and all possible combinations
# of values for the object types at the respective event
class TableManager:

    @classmethod
    def get_name(cls, event_type):
        session_key = session.get('session_key', None)
        name = 'tabea_' + event_type + "_" + str(session_key)
        return name

    def save(self):
        name = TableManager.get_name(self.eventType)
        path = get_session_path()
        path = os.path.join(path, name + ".pkl")
        with open(path, "wb") as wf:
            pickle.dump(self, wf)

    @classmethod
    def load(cls, event_type):
        name = TableManager.get_name(event_type)
        session_path = get_session_path()
        path = os.path.join(session_path, name + ".pkl")
        with open(path, "rb") as rf:
            return pickle.load(rf)

    def __init__(self, ocel, event_type, object_types):
        '''
        A class that maintains analytical tables that can be used for an effective evaluation of pattern formulas.
        One object maintains these tables for one particular event type.

        :param ocel: The object-centric event log
        :param event_type: The particular event type
        :param object_types: A pre-selection of object types that are associated with that event type
        '''
        self.eventType = event_type
        self.objectTypes = object_types
        event_index = EventIndex(self.eventType)
        event_index.create(ocel)
        event_objects = {}
        for object_type in self.objectTypes:
            event_objects_of_type = EventObjects(self.eventType, object_type)
            event_objects_of_type.create(ocel)
            event_objects[object_type] = event_objects_of_type
        o2o_tables = {}
        for object_type in self.objectTypes:
            o2o_of_source_type = O2OTable(self.eventType, object_type)
            o2o_of_source_type.create(ocel)
            o2o_tables[object_type] = o2o_of_source_type
        event_table = EventTable(self.eventType)
        event_table.create(ocel)
        event_interaction_table = EventInteractionTable(self.eventType, self.objectTypes)
        event_interaction_table.create(ocel)
        object_interaction_table = ObjectInteractionTable(self.eventType, self.objectTypes)
        object_interaction_table.create(ocel)
        self.eventIndex = event_index
        self.eventObjects = event_objects
        self.eventTable = event_table
        self.o2oTables = o2o_tables
        self.eventInteractionTable = event_interaction_table
        self.objectInteractionTable = object_interaction_table

    def get_event_index(self):
        return self.eventIndex.table[:]

    def get_event_objects(self, object_type):
        return self.eventObjects[object_type].table[:]

    def get_event_table(self):
        return self.eventTable.table[:]

    def get_o2o(self, object_type):
        return self.o2oTables[object_type].table[:]

    def get_event_interaction_table(self):
        return self.eventInteractionTable.table[:]

    def get_object_interaction_table(self):
        return self.objectInteractionTable.table[:]


