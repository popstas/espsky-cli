#!/usr/bin/env python

import argparse
import base64
import ConfigParser
from Crypto.Cipher import AES
import json
import hashlib
import os
import requests
import StringIO
import sys
import paho.mqtt.client as mqtt
import time

parser = argparse.ArgumentParser(description='espsky-cli')
parser.add_argument('command', help='Command')
parser.add_argument('file_path', help='File path to upload', nargs='?', default=False)
parser.add_argument('-n', '--filename', help='Filename, default from file url', nargs='?')
parser.add_argument('-t', '--token', help='ESPSky device token', required=True)


args = parser.parse_args()
mqtt_answer = False


def _pad(s):
    return s + (16 - len(s) % 16) * chr(0)


def device_token_hash():
    sha512 = hashlib.sha512(args.token)
    token_hash = base64.b64encode(sha512.digest()).translate(None, ''.join(['=', '/', '+']))
    return token_hash


def content_signature(content):
    return base64.b64encode(hashlib.sha512(content).digest())


def mqtt_on_connect(client, userdata, rc):
    client.subscribe('/%s/system/response' % device_token_hash(), 0)


def mqtt_on_message(mqttc, userdata, message):
    global mqtt_answer
    json_raw = decode_message(str(message.payload))
    mqtt_answer = json.loads(json_raw)
    # mqttc.loop_stop()
    # print 'Received message:' + json_raw
    # print mqtt_answer


def mqtt_connect():
    client = mqtt.Client()
    client.on_connect = mqtt_on_connect
    client.on_message = mqtt_on_message
    if args.mqtt_user and args.mqtt_password:
        client.username_pw_set(args.mqtt_user, args.mqtt_password)

    client.connect(args.mqtt_host, 1883, 60)
    return client


def encode_message(content):
    aligned = _pad(content)
    key = args.token[0:16]
    iv = 16 * '\x00'
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.encrypt(aligned)


def decode_message(content):
    key = args.token[0:16]
    iv = 16 * '\x00'
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.decrypt(content).split(b'\0', 1)[0]


def mqtt_wait_for(mqttc, response, timeout=5):
    global mqtt_answer
    mqtt_answer = False
    time_start = time.time()
    waiting = True
    mqttc.loop_start()

    while waiting:
        if time.time() - time_start > timeout:
            waiting = False
        if mqtt_answer and mqtt_answer['response'] == response:
            waiting = False

    return mqtt_answer


def mqtt_command(mqttc, command, command_args, body=''):
    json_obj = {'command': command, 'args': command_args}
    json_raw = json.dumps(json_obj)
    mqttc.publish('/%s/system/command' % device_token_hash(), bytearray(encode_message(json_raw)))
    answer = mqtt_wait_for(mqttc, 'system/file/download/complete')
    if answer and answer['result']:
        print 'file download success'
    else:
        print 'file download failed'


def download(file_url):
    r = requests.get(file_url)
    file_content = r.text
    file_signature = content_signature(file_content)
    filename = os.path.basename(file_url)
    if args.filename:
        filename = args.filename

    mqttc = mqtt_connect()
    command_args = {'name': filename, 'url': file_url, 'signature': file_signature}

    mqtt_command(mqttc, 'system/file/download', command_args, file_content)


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

    elif args.command == 'download':
        download(args.file_path)
    elif args.command == 'restart':
        restart()
    else:
        print 'Command not found'
        sys.exit(1)


main()
