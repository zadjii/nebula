"""
This is a small tool to parse the message_blueprints file and
  generate appropriate code in a bunch of languages.
"""
import os
import shutil
import string

from datetime import datetime

"""Argument types"""
INT = 0
STRING = 1
FLOAT = 2
BLOB = 3
BOOL = 4
MANUAL = 5  # indicates that this field can't be generated manually


class Argument(object):
    def __init__(self):
        self.name = None
        self.type = None
        self.size = None


# def parse_arg(arg_string):
#     # print '9 {}'.format(arg_string)
#     parts = string.split(arg_string, ':')
#     # print '10 {}'.format(parts)
#     arg = Argument()
#     arg._name = parts[-1]
#     arg._type = None
#     if len(parts) > 1:
#         arg._type = parts[0]
#     arg._size = None  # todo
#     # print '11 {}'.format(arg.__dict__)
#     return arg


class AbstractMessage(object):
    def __init__(self):
        self.code = None
        self.CAPS = None
        self.class_name = None
        self._arglist = []

    def add_arg(self, arg_string):
        # print '9 {}'.format(arg_string)
        parts = string.split(arg_string, ':')
        # print '10 {}'.format(parts)
        arg = Argument()
        arg.name = parts[-1]
        arg.type = None
        if len(parts) > 1:
            typestring = parts[0]
            if typestring.lower() == 'int':
                arg.type = INT
            elif typestring.lower() == 'float':
                arg.type = FLOAT
            elif typestring.lower() == 'string':
                arg.type = STRING
            elif typestring.lower() == 'blob':
                arg.type = BLOB
            elif typestring.lower() == 'bool':
                arg.type = BOOL
            else:  # typestring.lower() == 'todo':
                arg.type = MANUAL
            # arg.type = parts[0]
        arg.size = None  # todo
        # print '11 {}'.format(arg.__dict__)
        # return arg
        self._arglist.append(arg)

    def get_args(self):
        return self._arglist


def generate_message(parts):
    msg = AbstractMessage()
    msg.code = int(parts[0])
    msg.CAPS = parts[1]
    msg.class_name = create_classname_from_caps(msg.CAPS)
    for arg in parts[2:]:
        # arg_obj = parse_arg(arg)
        # msg._arglist.append(arg_obj)
        msg.add_arg(arg)
    # print '7 {}'.format(msg.__dict__)
    print '7.5 {}={}'.format(
        msg.class_name, [arg.__dict__ for arg in msg.get_args()])
    return msg


def open_file(path):
    f = open(path, 'r')
    return f


def get_lines(file_data):
    lines = []
    line = file_data.readline()
    while line is not None and len(line) > 0:
        # print '5 {}'.format(line)
        lines.append(line)
        line = file_data.readline()
    return lines


def remove_comments(line):
    parts = string.split(line, '#', 1)
    # print '6 ({})->({})'.format(line, parts)
    if len(parts) >= 1:
        return parts[0]
    else:
        return ''


def create_classname_from_caps(caps_name):
    camel_case = string.capwords(caps_name, '_')
    no_underscore = string.replace(camel_case, '_', '')
    class_name = no_underscore + 'Message'
    return class_name


def split_commas(line):
    return string.split(line, ',')


def strip_whitespace(parts):
    new_parts = []
    for part in parts:
        part2 = string.strip(part)
        new_parts.append(part2)
    return new_parts


def parse_lines(lines):
    # print '4 {}'.format(lines)
    messages = []
    for line in lines:
        line = remove_comments(line)
        if len(line) <= 0:
            continue
        # print '1 "{}"'.format(line)
        parts = split_commas(line)
        parts = strip_whitespace(parts)
        if len(parts) <= 1:
            continue
        # print '2 {}'.format(parts)
        msg = generate_message(parts)
        if msg is not None:
            messages.append(msg)
    return messages


def make_msgcodes_py(messages):
    handle = open('./out/msg_codes.py', mode='w')
    handle.write('# last generated {}\n'.format(datetime.utcnow()))
    for message in messages:
        handle.write('{} = {}\n'.format(message.CAPS, message.code))
    handle.close()
    print 'wrote msg_codes.py'


def make_messages_init_py(messages):
    handle = open('./out/messages/__init__.py', mode='w')
    handle.write('# last generated {}\n'.format(datetime.utcnow()))
    handle.write('from messages.BaseMessage import BaseMessage\n')
    for message in messages:
        handle.write('from messages.{0} import {0}\n'.format(message.class_name))
    handle.write('\n')
    handle.close()
    print 'wrote __init__.py'


def make_messages_dir():
    if not os.path.exists('./out/messages'):
        os.mkdir('./out/messages')
    # else todo shit we need to clear this dir out, and that always sucks


def make_message_deserializer(messages):
    handle = open('./out/messages/MessageDeserializer.py', mode='w')
    handle.write('# last generated {}\n'.format(datetime.utcnow()))
    handle.write('import json\n')
    handle.write('from msg_codes import *\n')
    handle.write('from messages import *\n')
    handle.write('from common_util import *\n')
    handle.write('_decoder_table = {\n')
    msg0 = messages[0]
    handle.write('    {}: {}.deserialize # {}\n'.format(msg0.CAPS, msg0.class_name, msg0.code))
    for msg in messages[1:]:
        handle.write('    , {}: {}.deserialize # {}\n'.format(msg.CAPS, msg.class_name, msg.code))
    handle.write('}\n')
    handle.write("""

class MessageDeserializer(object):
    @staticmethod
    def decode_msg(json_string):
        _log = get_mylog()
        _log.debug('->decoding "{}"'.format(json_string))
        json_dict = json.loads(json_string)
        if 'type' not in json_dict.keys():
            raise
        msg_type = json_dict['type']
        return _decoder_table[msg_type](json_dict)
""")
    handle.close()
    print 'wrote MessageDeserializer.py'


MANUAL_CLASSES = 0


def make_message_class_py(msg):
    handle = open('./out/messages/{}.py'.format(msg.class_name), mode='w')
    handle.write('# last generated {}\n'.format(datetime.utcnow()))
    handle.write('from messages import BaseMessage\n')
    handle.write('from msg_codes import {0} as {0}\n'.format(msg.CAPS))
    handle.write('__author__ = \'Mike\'\n')
    handle.write('\n\n')
    handle.write('class {}(BaseMessage):\n'.format(msg.class_name))

    handle.write('    def __init__(self')
    for arg in msg.get_args():
        if arg.type == MANUAL:
            handle.write(', {}=~~~TODO FIXME ~~~'.format(arg.name))
        else:
            handle.write(', {}=None'.format(arg.name))
    handle.write('):\n')

    handle.write('        super({}, self).__init__()\n'.format(msg.class_name))

    handle.write('        self.type = {}\n'.format(msg.CAPS))
    for arg in msg.get_args():
        if arg.type == MANUAL:
            handle.write('        self.{} = ~~~TODO FIXME~~~\n'.format(arg.name))
            print '!!!!!!!! IMPORTANT NOTE: {} has an arg ({}) that must be ' \
                  'filled manually !!!!!!'.format(msg.class_name, arg.name)
            global MANUAL_CLASSES
            MANUAL_CLASSES += 1
        else:
            handle.write('        self.{0} = {0}\n'.format(arg.name))

    handle.write('\n')
    handle.write('    @staticmethod\n')
    handle.write('    def deserialize(json_dict):\n')
    handle.write('        msg = {}()\n'.format(msg.class_name))
    for arg in msg.get_args():
        handle.write('        msg.{0} = json_dict[\'{0}\']\n'.format(arg.name))
    handle.write('        return msg\n')
    handle.write('\n')

    handle.close()
    print 'wrote {}.py'.format(msg.class_name)


def generate_python(messages):
    if not os.path.exists('./out'):
        os.mkdir('./out')
    # make msgcodes.py
    make_msgcodes_py(messages)

    # make messages/ directory
    make_messages_dir()

    # make messages/__init__.py
    make_messages_init_py(messages)

    # copy BaseMessage.py to messages dir
    shutil.copyfile('./BaseMessage.py', './out/messages/BaseMessage.py')
    print 'copied BaseMessage.py'
    # copy util.py to messages dir
    shutil.copyfile('./util.py', './out/messages/util.py')
    print 'copied util.py'

    # make message classes
    for msg in messages:
        make_message_class_py(msg)

    # make message deserializer
    make_message_deserializer(messages)


def make_messages_js(messages):
    handle = open('./out/js/messages.js', mode='w')
    handle.write('// last generated {}\n'.format(datetime.utcnow()))
    for msg in messages:
        handle.write('const {} = {};\n'.format(msg.CAPS, msg.code))
    # make message classes
    for msg in messages:
        handle.write('function {}('.format(msg.class_name))
        handle.write(', '.join([arg.name for arg in msg.get_args()]))
        # for arg in msg.get_args():
        #     handle.write(arg.name + ', ')
        handle.write('){\n')
        handle.write('    return {\n')
        # handle.write('        "{0}": {0}\n'.format(msg.get_args()[0]))
        handle.write('        "{}": {}\n'.format('type', msg.CAPS))
        for arg in msg.get_args():
            handle.write('        , "{0}": {0}'.format(arg.name))
            if arg.type == MANUAL:
                handle.write(' ~~~~ // FIXME TODO')
            handle.write('\n')
        handle.write('    };\n}\n')
    handle.close()
    print 'wrote messages.js'


def generate_javascript(messages):
    if not os.path.exists('./out/js'):
        os.mkdir('./out/js')
    # make messages.js
    make_messages_js(messages)


def generatecode(messages):
    generate_python(messages)
    generate_javascript(messages)


def main():
    blueprint_file = open_file(path='message_blueprints')
    lines = get_lines(blueprint_file)
    messages = parse_lines(lines)
    messages = sorted(messages, key=lambda item: item.code)
    print '8 {}'.format([msg.__dict__ for msg in messages])
    generatecode(messages)
    print '3 all done'
    global MANUAL_CLASSES
    if MANUAL_CLASSES > 0:
        print 'there are {} instances that must be updated manually'\
            .format(MANUAL_CLASSES)

if __name__ == '__main__':
    main()
