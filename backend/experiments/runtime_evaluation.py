import os
import time

from pm4py import read_ocel2_sqlite, read_ocel_json

from pattern_mining.pattern_mining_manager import PatternMiningManager


def run_log(log, log_name):
    pamela = PatternMiningManager(log, has_session=False)
    pamela.initialize()
    all_event_types = log.events["ocel:activity"].unique()
    for event_type in all_event_types:
        ts1 = time.time()
        table_manager = pamela.load_auxiliary_table(event_type)
        ts2 = time.time()
        time_diff = ts2 - ts1
        number_of_event_to_object_relations = 0
        for object_type in pamela.event_types_object_types[event_type]:
            number_of_event_to_object_relations += len(table_manager.get_event_objects(object_type))
        number_of_object_to_object_relations = len(table_manager.get_object_interaction_table())
        print(
            "Log: {0}, Event type: {1}, Auxiliary table creation time: {2}, Event-to-object relations: {3}, Object-to-object relations: {4}"
            .format(log_name, event_type, time_diff, number_of_event_to_object_relations, number_of_object_to_object_relations)
        )

def run_logistics():
    path = "/logs/ContainerLogistics.sqlite"
    full_path = os.getcwd() + path
    log = read_ocel2_sqlite(full_path)
    run_log(log, "Logistics")

def run_o2csim():
    path = "/logs/order-management.sqlite"
    full_path = os.getcwd() + path
    log = read_ocel2_sqlite(full_path)
    run_log(log, "O2C-Sim")

def run_sap():
    path = "/logs/ocel2-p2p.sqlite"
    full_path = os.getcwd() + path
    log = read_ocel2_sqlite(full_path)
    run_log(log, "SAP")

def run_github():
    path = "/logs/angular_github_commits_ocel.jsonocel"
    full_path = os.getcwd() + path
    log = read_ocel_json(full_path)
    run_log(log, "Git")

if __name__ == "__main__":
    run_logistics()
    run_o2csim()
    run_sap()
    run_github()