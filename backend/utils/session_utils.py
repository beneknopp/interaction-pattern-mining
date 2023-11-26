import os

from flask import session

RUNTIME_RESOURCE_FOLDER = os.path.join(os.getcwd(), "runtime_resources")
ALLOWED_EXTENSIONS = {'sqlite', 'xml'}


def get_file_extension(filename):
    return filename.rsplit('.', 1)[1].lower()

def allowed_file(filename):
    return filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def make_session():
    key_path = os.path.join(RUNTIME_RESOURCE_FOLDER, "running_session_key")
    with open(key_path) as rf:
        session_key = str(int(rf.read()) + 1)
    with open(key_path, "w") as wf:
        wf.write(session_key)
    session['session_key'] = session_key
    session_path = get_session_path()
    os.mkdir(session_path)
    return session_key, session_path


def get_session_path():
    session_key = session.get('session_key', None)
    return os.path.join(
        RUNTIME_RESOURCE_FOLDER,
        session_key
    )
