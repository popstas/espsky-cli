#!/usr/bin/env python

import argparse
import base64
import ConfigParser
from Crypto.Cipher import AES
import json
import hashlib
import os
import StringIO
import sys
import paho.mqtt.client as mqtt

parser = argparse.ArgumentParser(description='espsky-cli')
parser.add_argument('command', help='Command')
parser.add_argument('file_path', help='File path to upload', nargs='?', default=False)
parser.add_argument('-t', '--token', help='ESPSky device token', required=True)


args = parser.parse_args()


def _pad(s):
    return s + (16 - len(s) % 16) * chr(0)


def device_token_hash():
    sha512 = hashlib.sha512(args.token)
    token_hash = base64.b64encode(sha512.digest()).translate(None, ''.join(['=', '/', '+']))
    return token_hash


def mqtt_connect():
    client = mqtt.Client()
    if args.mqtt_user and args.mqtt_password:
        client.username_pw_set(args.mqtt_user, args.mqtt_password)
    client.connect(args.mqtt_host, 1883, 60)
    return client


def mqtt_command(mqttc, command, command_args, body=''):
    command_args['command'] = command
    # print command_args
    json_raw = json.dumps(command_args)
    json_raw_aligned = _pad(json_raw)
    key = args.token[0:16]
    iv = 16 * '\x00'
    cipher = AES.new(key, AES.MODE_CBC, iv)
    json_enc = cipher.encrypt(json_raw_aligned)
    mqttc.publish('/%s/system/command' % device_token_hash(), bytearray(json_enc))
    return False


def restart():
    mqttc = mqtt_connect()
    mqtt_command(mqttc, 'system/node/restart', {})


def main():
    config_path = os.getcwd() + '/config'
    if os.path.isfile(config_path):
        config_raw = '[espsky]\n' + open(config_path, 'r').read()
        config_fp = StringIO.StringIO(config_raw)
        config = ConfigParser.RawConfigParser()
        config.readfp(config_fp)
        args.mqtt_host = config.get('espsky', 'mqtt_host')
        args.mqtt_user = config.get('espsky', 'mqtt_user')
        args.mqtt_password = config.get('espsky', 'mqtt_password')

    if not args.mqtt_host:
        print('host not defined')
        sys.exit(1)

    elif args.command == 'restart':
        restart()
    else:
        print 'Command not found'
        sys.exit(1)


main()
