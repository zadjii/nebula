from common.SimpleDB import SimpleDB
from models.Session import Session
from common_util import *
from remote.models.Cloud import Cloud
from remote.models.User import User


def get_user_from_session(db, session_id):
    # rd = Error()
    # sess_obj = db.session.query(Session).filter_by(uuid=session_id).first()
    # if sess_obj is None:
    #     rd = Error('No session exists on remote for sid:{}'.format(session_id))
    # else:
    #     user = sess_obj.user
    #     if user is None:
    #         rd = Error('No user exists on remote\'s session, sid:{}'.format(session_id))
    #     else:
    #         rd = ResultAndData(True, user)
    # return rd
    rd = validate_session_id(db, session_id)
    if rd.success:
        sess_obj = rd.data
        rd = sess_obj.get_user()
    return rd


def get_user_by_name(db, username):
    # type: (SimpleDB, str) -> User
    # _log = get_mylog()
    query = db.session.query(User).filter(User.username.ilike(username))
    # _log.debug('{}'.format(query.all()))
    return query.first()


def get_cloud_by_name(db, uname, cname):
    # type: (SimpleDB, str, str) -> Cloud
    # return [cloud for cloud in db.session.query(Cloud).filter_by(name=cname)
    #         if cloud.owner_name() == uname]
    # Hosts don't know about owner names yet, todo:15
    # return db.session.query(Cloud).filter_by(name=cname).first()
    clouds = [cloud
              for cloud in db.session.query(Cloud).filter_by(name=cname).all()
              if cloud.uname().lower() == uname.lower()]
    if len(clouds) > 1:
        mylog('get_cloud_by_name error '
              '- There should be AT MOST one result'
              '\n\t Found {}'.format([cloud.full_name() for cloud in clouds]))
    return None if len(clouds) < 1 else clouds[0]


def validate_session_id(db, session_id):
    # type: (SimpleDB, Any) -> ResultAndData

    sess_obj = db.session.query(Session).filter_by(uuid=session_id).first()
    if sess_obj is None:
        msg = 'There is no session of uuid={}'.format(session_id)
        return Error(msg)
    if sess_obj.has_timed_out():
        msg = 'Session timed out uuid={}'.format(session_id)
        return Error(msg)
    sess_obj.refresh()
    db.session.commit()
    return Success(sess_obj)
