from flask import Flask, flash, request, session
from flask_cors import cross_origin

from dtos.response import Response
from event_log_management.event_log_manager import EventLogManager
from pattern_mining.pattern_mining_manager import PatternMiningManager
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
            "event_types_object_types": pamela.event_types_object_types,
            'event_type_object_relations': pamela.event_type_object_relations,
            'event_type_object_to_object_relations': pamela.event_type_object_to_object_relations,
            'search_plans': pamela.get_search_plans(),
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

@app.route('/load-tables', methods=['GET'])
@cross_origin()
def load_tables():
    session_key = request.args.get('sessionKey')
    session['session_key'] = session_key
    pamela: PatternMiningManager = PatternMiningManager.load()
    event_types = pamela.event_types
    pamela.load_tables(event_types)
    pamela.save_base_table_evaluation()
    pamela.visualize_base_table_creation_eval()
    pamela.save()
    return Response.get(True)

@app.route('/search', methods=['GET'])
@cross_origin()
def search():
    session_key = request.args.get('sessionKey')
    session['session_key'] = session_key
    pamela: PatternMiningManager = PatternMiningManager.load()
    event_types = pamela.event_types
    pamela.search_models(event_types)
    pamela.save_evaluation()
    pamela.visualize_results()
    pamela.save()
    return Response.get(True)


if __name__ == '__main__':
    app.run(debug=True)

