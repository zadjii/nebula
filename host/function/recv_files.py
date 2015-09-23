from datetime import datetime
import os
from host import get_db, FileNode
from host.util import mylog
from msg_codes import recv_msg

__author__ = 'Mike'


def recv_file_tree(msg, cloud, socket_conn, db):
    while msg['fsize'] is not None:
        recv_file_transfer(msg, cloud, socket_conn, db)
        msg = recv_msg(socket_conn)


def recv_file_transfer(msg, cloud, socket_conn, db):
    msg_file_isdir = msg['isdir']
    msg_file_size = msg['fsize']
    msg_rel_path = msg['fpath']
    mylog('[{}] is recv\'ing <{}>'.format(cloud.my_id_from_remote, msg_rel_path))
    full_path = os.path.join(cloud.root_directory, msg_rel_path)
    if msg_file_isdir :
        if not os.path.exists(full_path):
            os.mkdir(full_path)
            print 'Created directory {}'.format(full_path)
    else:  # is normal file
        data_buffer = ''  # fixme i'm using a string to buffer this?? LOL
        total_read = 0
        while total_read < msg_file_size:
            new_data = socket_conn.recv(min(1024, (msg_file_size - total_read)))
            nbytes = len(new_data)
            # print 'read ({},{})'.format(new_data, nbytes)
            if total_read is None or new_data is None:
                print 'I know I should have broke AND I JUST DIDN\'T ANYWAYS'
                break
            total_read += nbytes
            data_buffer += new_data
            # print '<{}>read:{}B, total:{}B, expected total:{}B'.format(
            #     msg_rel_path, nbytes, total_read, msg_file_size
            # )
        # print 'complete file data \'{}\''.format(data_buffer)
        file_handle = open(full_path, mode='wb')
        done = False
        total_written = 0
        while not done:
            nbytes_written = file_handle.write(data_buffer[total_written:])
            if nbytes_written is None:
                break
            total_written += nbytes_written
            done = total_written <= 0
        file_handle.close()
        mylog('[{}]I think I wrote the file to {}'.format(cloud.my_id_from_remote, full_path))
    updated_node = cloud.create_or_update_node(msg_rel_path, msg, db)
    if updated_node is not None:
        old_modified_on = updated_node.last_modified
        updated_node.last_modified = datetime.utcfromtimestamp(os.path.getmtime(full_path))
        mylog('update mtime {}=>{}'.format(old_modified_on, updated_node.last_modified))
        db.session.commit()
    new_num_nodes = db.session.query(FileNode).count()
    mylog('RFT:total file nodes:'.format(new_num_nodes))
