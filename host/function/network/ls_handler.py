from host import get_db, Cloud
from host.util import mylog
from msg_codes import send_generic_error_and_close, make_list_files_response, \
    send_msg

__author__ = 'Mike'


def list_files_handler(connection, address, msg_obj):
    session_id = msg_obj['sid']
    cloudname = msg_obj['cname']
    rel_path = msg_obj['fpath']
    db = get_db()
    # todo match session to session object
    # todo validate that the conn.ip == session ip
    cloud = db.session.query(Cloud).filter_by(name=cloudname).first()
    if cloud is None:
        send_generic_error_and_close(connection)  # todo send maeiningful error
        mylog('sid[{}] requested {}, I was alerted, but I don\'t have it'
              .format(session_id, cloudname))
    full_path = cloud.translate_relative_path(rel_path)
    response = make_list_files_response(cloudname, rel_path, full_path)
    send_msg(response, connection)