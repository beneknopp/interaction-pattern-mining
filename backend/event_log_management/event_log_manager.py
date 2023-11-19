import os
import pickle

from flask import session
from pm4py import read_ocel2_sqlite, read_ocel2_xml

from utils.session_utils import get_session_path


class EventLogManager:

    @classmethod
    def get_name(cls):
        session_key = session.get('session_key', None)
        name = 'elmo_' + str(session_key)
        return name

    @classmethod
    def load(cls, name):
        path = os.getcwd()
        path = os.path.join(path, name + ".pkl")
        with open(path, "rb") as rf:
            return pickle.load(rf)

    def __init__(self):
        self.sessionKey = session.get('session_key')
        self.name = EventLogManager.get_name()
        self.ocel = None
        self.event_types = None
        self.object_types = None
        self.event_types_object_types = None

    def save(self):
        path = os.getcwd()
        path = os.path.join(path, self.name + ".pkl")
        with open(path, "wb") as wf:
            pickle.dump(self, wf)

    def enter_transmitted_file(self, file, extension):
        session_path = get_session_path()
        file_path = os.path.join(session_path, self.name + "." + extension)
        file.save(file_path)
        if extension == "sql":
            self.ocel = read_ocel2_sqlite(file_path)
        if extension == "xml":
            self.ocel = read_ocel2_xml(file_path)
        raise ValueError()