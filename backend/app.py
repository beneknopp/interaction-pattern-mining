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
    print("Uploading OCEL...")
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return Response.get(True)
    extension = get_file_extension(file.filename)
    if file and allowed_file(file.filename):
        session_key, session_path = make_session()
        print("Creating session {0} for valid OCEL {1}".format(str(session_key), file.filename))
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
    session_key = request.args.get('session-key')
    session['session_key'] = session_key
    selected_event_types = request.get_json()
    print("Setting Event types {0} for session {1}".format(str(selected_event_types), str(session_key)))
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
    session_key = request.args.get('session-key')
    session['session_key'] = session_key
    print("Loading search plans for session {0}".format(str(session_key)))
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
    session_key = request.args.get('session-key')
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
    session_key = request.args.get('session-key')
    session['session_key'] = session_key
    pamela: PatternMiningManager = PatternMiningManager.load()
    event_types = pamela.event_types_filter
    pamela.load_tables(event_types)
    pamela.save_base_table_evaluation()
    #pamela.visualize_base_table_creation_eval()
    pamela.save()
    return Response.get(True)


@app.route('/search-model', methods=['GET', 'POST'])
@cross_origin()
def searchModel():
    session_key = request.args.get('session-key')
    complementary_mode = request.args.get('complementary-mode')
    merge_mode = request.args.get('merge-mode')
    minimal_support = float(request.args.get('min-support'))
    session['session_key'] = session_key
    body = request.get_json()
    selected_pattern_ids = body["selected-patterns"]
    pamela: PatternMiningManager = PatternMiningManager.load()
    pamela.complementaryMode = True if complementary_mode == "true" else False
    pamela.mergeMode = True if merge_mode == "true" else False
    pamela.evaluationMode = EvaluationMode.TIME
    event_types = pamela.event_types_filter
    resp = pamela.search_models(event_types, selected_pattern_ids, minimal_support)
    #pamela.save_evaluation()
    #pamela.save_split_evaluation()
    #pamela.visualize_global_scores()
    #pamela.visualize_splits()
    pamela.save()
    #resp = pamela.get_model_response()
    return resp

@app.route('/search-rules', methods=['GET', 'POST'])
@cross_origin()
def searchRules():
    session_key = request.args.get('session-key')
    complementary_mode = request.args.get('complementary-mode')
    merge_mode = request.args.get('merge-mode')
    target_pattern_description = str(request.args.get('target-pattern-description'))
    max_rule_ante_length = int(request.args.get('max-rule-ante-length'))
    min_rule_ante_support = float(request.args.get('min-rule-ante-support'))
    session['session_key'] = session_key
    body = request.get_json()
    selected_pattern_ids = body["selected-patterns"]
    pamela: PatternMiningManager = PatternMiningManager.load()
    pamela.complementaryMode = True if complementary_mode == "true" else False
    pamela.mergeMode = True if merge_mode == "true" else False
    pamela.maxSplitRecursionDepth = 1
    event_types = pamela.event_types_filter
    pamela.search_rules(event_types, selected_pattern_ids, target_pattern_description, max_rule_ante_length, min_rule_ante_support)
    pamela.save()
    return Response.get(True)


@app.route('/get-model', methods=['GET','POST'])
@cross_origin()
def get_model():
    session_key = request.args.get('session-key')
    session['session_key'] = session_key
    pamela: PatternMiningManager = PatternMiningManager.load()
    body = request.get_json()
    event_type = body["event-type"]
    object_types = body["object-types"]
    resp = pamela.get_model_response(event_type, object_types)
    return resp

@app.route('/get-rules', methods=['GET','POST'])
@cross_origin()
def get_rules():
    raise NotImplementedError()


if __name__ == '__main__':
    app.run(debug=False)

