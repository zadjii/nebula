import json
from messages import *
from messages.MessageDeserializer import MessageDeserializer
__author__ = 'zadjii'

def test_single_message(msg_obj):
    print 'dict={}'.format(msg_obj.__dict__)
    msg_json = msg_obj.serialize()
    print 'json={}'.format(msg_json)
    copy_msg = MessageDeserializer.decode_msg(msg_json)
    print '{}=?{}'.format(msg_obj.__dict__, copy_msg.__dict__)
    if msg_obj.__dict__ != copy_msg.__dict__:
        raise


def test_msgs():
    print '#' * 80
    print '# Running test_msgs to see json of various message types '
    print '# THIS IS THE OBJECT TESTER'
    print '#' * 80

    print '_____ Testing BaseMessge _____'
    base = BaseMessage()
    base.type = 22
    print base.__dict__
    print base.serialize()
    json_blob = '{"type":23}'
    base2 = BaseMessage.deserialize(json.loads(json_blob))
    print base2.__dict__

    base3 = MessageDeserializer.decode_msg(json_blob)
    print base3
    print base3.__dict__

    # print '_____ Making NEW_HOST_MSG[0] json _____'

    print '_____ Testing NewHostMessage _____'
    msg_obj = NewHostMessage(port=23456)
    test_single_message(msg_obj)

    print '_____ Testing AssignHostIDMessage _____'
    msg_obj = AssignHostIDMessage(22, 'TODOkey', 'TODOcert')
    test_single_message(msg_obj)


if __name__ == '__main__':
    test_msgs()