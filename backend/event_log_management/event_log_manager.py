import os
import pickle

from pm4py import read_ocel2_sqlite

from rest_utils.helpers import get_session_path


class EventLogManager:

    @classmethod
    def load(cls, name):
        path = os.getcwd()
        path = os.path.join(path, name + ".pkl")
        with open(path, "rb") as rf:
            return pickle.load(rf)

    def __init__(self, session_key):
        self.session_key = session_key
        self.name = "elmo_" + str(session_key)
        self.ocel = None
        self.event_types = None
        self.object_types = None
        self.event_types_object_types  = None

    def save(self):
        path = os.getcwd()
        path = os.path.join(path, self.name + ".pkl")
        with open(path, "wb") as wf:
            pickle.dump(self, wf)

    def enter_transmitted_file(self, file):
        file_path = os.path.join(
            get_session_path(self.session_key),
            self.name
        )
        file.save(file_path)
        self.ocel = read_ocel2_sqlite(file_path)

    def initialize_log(self):
#        self.event_types = sorted(list(set(self.ocel.events["ocel:activity"].values)))
 #       self.object_types = sorted(list(set(self.ocel.objects["ocel:type"].values)))
  #      e2o = self.ocel.relations
   #     self.event_types_object_types = e2o.groupby('ocel:activity')['ocel:type'].agg(lambda x: list(set(x))).to_dict()
        return #"Hallo"