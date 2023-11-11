import os

RUNTIME_RESOURCE_FOLDER = os.path.abspath('../runtime_resources')
ALLOWED_EXTENSIONS = {'sqlite'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def make_session():
    session_key_path = os.path.join(os.getcwd(), "rest_utils")
    session_key_path = os.path.join(session_key_path, "running_session_key")
    with open(session_key_path) as rf:
        session_key = str(int(rf.read()) + 1)
    with open(session_key_path, "w") as wf:
        wf.write(session_key)
    session_path = get_session_path(session_key)
    try:
        os.mkdir(session_path)
    except FileNotFoundError:
        os.mkdir(RUNTIME_RESOURCE_FOLDER)
        os.mkdir(session_path)
    return session_key, session_path

def get_session_path(session_key):
    return os.path.join(
        RUNTIME_RESOURCE_FOLDER,
        session_key
    )