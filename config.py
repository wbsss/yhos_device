#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 2017年1月19日

@author: Jarvis
'''
import logging

class mqttConfig:
    host = 'localhost'
    port = 1883
    user = 'zlt000001'
    password = '484848'
    api_url = 'http://127.0.0.1:18083/api/clients'
    api_client_param = 'client_key'

class databaseConfig:
    provider = 'mysql'
    host = '119.23.18.15'
    port = 3306
    user = 'zltuser'
    password = 'm75WezYsQQ33FdXP'
    db = 'zlt'

class memcacheConfig:
    host = 'localhost'
    port = 11211

class redisConfig:
    host = 'localhost'
    port = 6379

class jpushConfig:
    appkey = '8708d22a2777844638baeb96'
    secret = '3210845bf60d52e2171e7718'
    production = True

class langConfig:
    dir = 'lang'

class webConfig:
    host = '0.0.0.0'
    port = 4001
    logfile = 'web.log'

class defaultConfig:
    device_host = '119.23.18.15'
    device_port = 1883
    device_heartbeat = 120
    device_server_id = '000001'
    device_interval = 90
    device_udinterval = 90
    device_mode = 1
    device_config = 0

class voiceConfig:
    #upload_url = 'http://app.imerit.cn:8000/tp/index.php/upload/upload?token=4d01072c0156eb26848160a4ba7b5fb1'
    upload_url = 'http://app.imerit.cn:8000/tp/index.php/upload/upload?token=9ae6bacb71e827112fa8fa638a6817a2'

class friendMatchConfig:
    timeout = 15

class logConfig:
    file = 'server.log'
    format = '%(asctime)s %(filename)s:%(lineno)d %(levelname)s %(message)s'
    level = logging.INFO
id = '000001'
local_addr = 'localhost'
pub_addr = 'localhost'
mqtt = mqttConfig()
database = databaseConfig()
memcache = memcacheConfig()
redis = redisConfig()
jpush = jpushConfig()
lang = langConfig()
web = webConfig()
default = defaultConfig()
voice = voiceConfig()
friend_match = friendMatchConfig()
log = logConfig()
