import pm4py
import pickle

from elmo import EventLogManager, EventLogParameters
from object_interaction_pattern_miner import ObjectInteractionPatternMiner

initial_steps = True# and False

ocel2_sqlite_path = "order-management.sqlite"
event_log_manager_name = "elmo"

if initial_steps:
    elmo = EventLogManager(event_log_manager_name)
    elmo_parameters = {
        EventLogParameters.ALLOWED_OBJECT_TYPES: ["orders", "items", "employees"],
        EventLogParameters.ALLOWED_ACTIVITIES: ["place order", "confirm order", "item out of stock", "reorder item", "pick item"]
    }
    elmo.load_ocel2_sqlite(ocel2_sqlite_path, elmo_parameters)
    elmo.create_dataframes()
    ocel = elmo.ocel2
    elmo.save()
else:
    ocel = pm4py.read_ocel2_sqlite("order-management.sqlite")
    elmo = EventLogManager.load(event_log_manager_name)

pamela = ObjectInteractionPatternMiner(ocel)
print("EOF")