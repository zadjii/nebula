from models import Session
from host.util import set_mylog_name, mylog, ResultAndData, ERROR


def get_user_from_session(db, session_id):
    rd = ERROR()
    sess_obj = db.session.query(Session).filter_by(uuid=session_id).first()
    if sess_obj is None:
        rd = ERROR('No session exists on remote for sid:{}'.format(session_id))
    else:
        user = sess_obj.user
        if user is None:
            rd = ERROR('No user exists on remote\'s session, sid:{}'.format(session_id))
        else:
            rd = ResultAndData(True, user)
    return rd