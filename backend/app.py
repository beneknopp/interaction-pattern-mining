from flask import Flask, flash, request, session
from flask_cors import cross_origin

from dtos.response import Response
from event_log_management.event_log_manager import EventLogManager
from pattern_mining.evaluation_mode import EvaluationMode
from pattern_mining.pattern_formula import PatternFormula
from pattern_mining.pattern_mining_manager import PatternMiningManager
from pattern_mining.pattern_parser import PatternParser
from pattern_mining.table_manager import TableManager
from utils.session_utils import allowed_file, make_session, get_file_extension

app = Flask(__name__)
app.secret_key = '8a28ef91377b0cf89b5fdfdb32672036'
#import warnings
#warnings.filterwarnings("error")

@app.route('/upload-ocel', methods=['GET', 'POST'])
@cross_origin()
def upload_ocel():
    # try:
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return Response.get(True)
    extension = get_file_extension(file.filename)
    if file and allowed_file(file.filename):
        make_session()
        elmo = EventLogManager()
        elmo.enter_transmitted_file(file, extension)
        pamela = PatternMiningManager(elmo.ocel)
        pamela.initialize()
        pamela.save()
        return {
            'session_key': session.get('session_key', None),
            'object_types': pamela.object_types,
            'event_types': pamela.event_types,
            'event_type_attributes': pamela.event_type_attributes,
            'object_type_attributes': pamela.object_type_attributes,
            "event_type_object_types": pamela.event_types_object_types,
            'event_type_object_relations': pamela.event_type_object_relations,
            'event_type_object_to_object_relations': pamela.event_type_object_to_object_relations,
            'variable_prefixes': pamela.variable_prefixes
        }
    return Response.get(False)

@app.route('/add-pattern', methods=['GET', 'POST'])
@cross_origin()
def add_pattern():
    raise NotImplementedError()

@app.route('/delete-pattern', methods=['GET', 'POST'])
@cross_origin()
def delete_pattern():
    raise NotImplementedError()


@app.route('/set-event-types', methods=['GET', 'POST'])
@cross_origin()
def set_event_types():
    session_key = request.args.get('sessionKey')
    session['session_key'] = session_key
    selected_event_types = request.get_json()
    pamela: PatternMiningManager = PatternMiningManager.load()
    pamela.set_event_types_filter(selected_event_types)
    pamela.load_tables(selected_event_types)
    pamela.save_base_table_evaluation()
    resp = {
        "patterns": {
            event_type: {
                "basic_patterns" : list(pamela.searched_basic_patterns[event_type].keys()),
                "interaction_patterns": {
                        object_type: list(patterns.keys())
                        for object_type, patterns in pamela.searched_interaction_patterns[event_type].items()
                },
                "custom_patterns": list(pamela.custom_patterns[event_type].keys())
            }
            for event_type in selected_event_types
        }
    }
    pamela.save()
    return resp


@app.route('/search-plans', methods=['GET'])
@cross_origin()
def load_search_plans():
    session_key = request.args.get('sessionKey')
    session['session_key'] = session_key
    pamela: PatternMiningManager = PatternMiningManager.load()
    event_types = pamela.event_types_filter
    pamela.load_default_search_plans(event_types)
    resp = {
        "patterns": {
            event_type: {
                "basic_patterns" : list(pamela.searched_basic_patterns[event_type].keys()),
                "interaction_patterns": {
                        object_type: list(patterns.keys())
                        for object_type, patterns in pamela.searched_interaction_patterns[event_type].items()
                },
                "custom_patterns": list(pamela.custom_patterns[event_type].keys())
            }
            for event_type in event_types
        }
    }
    pamela.save()
    return resp


@app.route('/register-custom-pattern', methods=['GET', 'POST'])
@cross_origin()
def register_custom_pattern():
    session_key = request.args.get('sessionKey')
    session['session_key'] = session_key
    body = request.get_json()
    event_type = body["event_type"]
    pattern_id = body["pattern_id"]
    pamela: PatternMiningManager = PatternMiningManager.load()
    variable_type_lookup = pamela.variable_prefixes_reverse
    objects = pamela.objects[["ocel:oid", "ocel:type"]]
    papa = PatternParser(variable_type_lookup, objects)
    is_valid = papa.parse(pattern_id)
    if is_valid:
        pattern: PatternFormula = papa.get()
        pamela.register_custom_pattern(event_type, pattern)
        pamela.save()
    return Response.get(is_valid)


@app.route('/load-tables', methods=['GET'])
@cross_origin()
def load_tables():
    session_key = request.args.get('sessionKey')
    session['session_key'] = session_key
    pamela: PatternMiningManager = PatternMiningManager.load()
    event_types = pamela.event_types_filter
    pamela.load_tables(event_types)
    pamela.save_base_table_evaluation()
    #pamela.visualize_base_table_creation_eval()
    pamela.save()
    return Response.get(True)


@app.route('/search', methods=['GET'])
@cross_origin()
def search():
    session_key = request.args.get('sessionKey')
    complementary_mode = request.args.get('complementaryMode')
    merge_mode = request.args.get('mergeMode')
    minimal_support = request.args.get('minimalSupport')
    session['session_key'] = session_key
    pamela: PatternMiningManager = PatternMiningManager.load()
    pamela.complementaryMode = True if complementary_mode == "true" else False
    pamela.mergeMode = True if merge_mode == "true" else False
    pamela.doSplit = True
    pamela.maxSplitRecursionDepth = 1
    pamela.evaluationMode = EvaluationMode.TIME
    event_types = pamela.event_types_filter
    minimal_support = 0
    pamela.search_models(event_types, minimal_support)
    pamela.save_evaluation()
    pamela.save_split_evaluation()
    pamela.visualize_global_scores()
    pamela.visualize_splits()
    pamela.save()
    #resp = pamela.get_model_response()
    return Response.get(True)


@app.route('/get-model', methods=['GET','POST'])
@cross_origin()
def get_model():
    session_key = request.args.get('sessionKey')
    session['session_key'] = session_key
    pamela: PatternMiningManager = PatternMiningManager.load()
    body = request.get_json()
    event_type = body["event-type"]
    object_types = body["object-types"]
    pattern_ids = body["split-pattern-ids"]
    resp = pamela.get_split_response(event_type, pattern_ids, object_types)
    return resp


if __name__ == '__main__':
    app.run(debug=False)

