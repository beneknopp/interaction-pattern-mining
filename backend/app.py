import os

from flask import Flask, flash, request, send_from_directory, current_app
from flask_cors import cross_origin

from dtos.response import Response
from event_log_management.event_log_manager import EventLogManager
from pattern_mining.pattern_mining_manager import PatternMiningManager
from rest_utils.helpers import allowed_file, make_session

app = Flask(__name__)

@app.route('/')
@cross_origin()
def hello_world():
    return "Hello world!"

@app.route('/upload-ocel', methods=['GET', 'POST'])
@cross_origin()
def upload_ocel():
    # try:
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return Response.get(True)
    if file and allowed_file(file.filename):
        session_key, session_path = make_session()
        elmo = EventLogManager(session_key)
        elmo.enter_transmitted_file(file)
        elmo.initialize_log()
        pamela = PatternMiningManager(session_key, elmo.ocel)
        pamela.initialize()
        return {
            'object_types': pamela.object_types,
            'event_types': pamela.event_types,
            'event_type_attributes': pamela.event_type_attributes,
            'object_type_attributes': pamela.object_type_attributes,
            "event_types_object_types": pamela.event_types_object_types,
            'event_type_object_relations': pamela.event_type_object_relations,
            'event_type_object_to_object_relations': pamela.event_type_object_to_object_relations,
            'variabe_prefixes': pamela.variable_prefixes
        }
    return Response.get(False)

if __name__ == '__main__':
    app.run(debug=True)
