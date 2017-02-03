from datetime import datetime
from host.util import mylog
from msg_codes import send_generic_error_and_close

__author__ = 'Mike'


# def handle_client_session_alert(connection, address, msg_obj):
#     db = get_db()
#     # cloudname = msg_obj.cname
#     session_id = msg_obj.sid
#     user_id = msg_obj.uid
#     client_ip = msg_obj.ip
#     mylog('creating new session for (uid,sid,ip)={}'.format((user_id, session_id, client_ip)))
#     # cloud = db.session.query(Cloud).filter_by(name=cloudname).first()
#     # if cloud is None:
#     #     send_generic_error_and_close(connection)  # todo send maeiningful error
#     #     mylog('user[{}] requested {}, I was alerted, but I don\'t have it'
#     #           .format(user_id))
#     #     return
#     new_sess = Session(
#         user_id=user_id
#         , uuid=session_id
#         , created_on=datetime.utcnow()
#         , last_refresh=datetime.utcnow()
#         , client_ip=client_ip
#     )
#     db.session.add(new_sess)
#     # new_sess.cloud_id = cloud.id
#     # new_sess.user_id = user_id
#     # new_sess.uuid = session_id
#     # new_sess.created_on = datetime.utcnow()
#     # new_sess.last_refresh = new_sess.created_on
#     # new_sess.client_ip = client_ip
#     mylog('session_obj = {}'.format(new_sess.__dict__))
#     # cloud.sessions.append(new_sess)
#     db.session.commit()


