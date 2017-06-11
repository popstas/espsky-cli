#!/usr/bin/env python

import argparse
import ConfigParser
import os
import StringIO
import sys

parser = argparse.ArgumentParser(description='espsky-cli')
parser.add_argument('command', help='Command')
parser.add_argument('file_path', help='File path to upload', nargs='?', default=False)
args = parser.parse_args()


def mqtt_command(command, command_args, body):
    return False


def upload(file_path, max_tries=3):
    with open(file_path, 'r') as f:
        file_content = f.read()

    filename = os.path.basename(file_path)
    file_length = len(file_content)

    success = False
    tries = 0

    command_args = {'filename': filename, 'length': file_length}

    while not success and tries < max_tries:
        success = mqtt_command('upload', command_args, file_content)
        tries += 1

    if not success:
        print 'Upload failed'
        sys.exit(1)

    print 'Upload finished' + (' (tries: %d)' % tries if tries > 1 else '')


def main():
    config_path = os.getcwd() + '/config'
    if os.path.isfile(config_path):
        config_raw = '[esksky]\n' + open(config_path, 'r').read()
        config_fp = StringIO.StringIO(config_raw)
        config = ConfigParser.RawConfigParser()
        config.readfp(config_fp)
        if not args.host:
            args.mqtt_host = config.get('esksky', 'mqtt_host')
            args.mqtt_user = config.get('esksky', 'mqtt_user')
            args.mqtt_password = config.get('esksky', 'mqtt_password')

    if not args.mqtt_host:
        print('host not defined')
        sys.exit(1)

    elif args.command == 'upload':
        upload(args.file_path)
    else:
        print 'Command not found'
        sys.exit(1)


main()
