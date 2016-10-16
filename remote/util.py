from models.Session import Session
from common_util import *
from remote.models.Cloud import Cloud


def get_user_from_session(db, session_id):
    rd = Error()
    sess_obj = db.session.query(Session).filter_by(uuid=session_id).first()
    if sess_obj is None:
        rd = Error('No session exists on remote for sid:{}'.format(session_id))
    else:
        user = sess_obj.user
        if user is None:
            rd = Error('No user exists on remote\'s session, sid:{}'.format(session_id))
        else:
            rd = ResultAndData(True, user)
    return rd


def get_cloud_by_name(db, uname, cname):
    # return [cloud for cloud in db.session.query(Cloud).filter_by(name=cname)
    #         if cloud.owner_name() == uname]
    # Hosts don't know about owner names yet, todo:15
    return db.session.query(Cloud).filter_by(name=cname).first()


def validate_session_id(db, session_id):
    # type: (SimpleDB, Any) -> ResultAndData

    sess_obj = db.session.query(Session).filter_by(uuid=session_id).first()
    if sess_obj is None:
        msg = 'There is no session of uuid={}'.format(session_id)
        return Error(msg)
    if sess_obj.has_timed_out():
        msg = 'Session timed out uuid={}'.format(session_id)
        return Error(msg)
    return Success(sess_obj)