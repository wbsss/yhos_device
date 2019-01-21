#!/usr/bin/env python
# encoding: utf-8
from bottle import Bottle, run, request, response, get, post ,static_file
from HTMLParser import HTMLParser
app = Bottle()
import json
from collections import OrderedDict
import comm
import os
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
# 初始化
@app.hook('before_request')
def validate():
    response.headers['Access-Control-Allow-Origin'] = '*'
#返回信息
def response_json(code, msg='success', data=[]):
    return '{"errcode":%d,"errmsg":"%s","data":%s}' % (code, msg, json.dumps(data))
@app.route('/get_hd', method='GET')
def get_hd():
    res = comm.get_hd()
    return json.loads(res)
# 添加raid ----初始化（type无备份0,有备份1）
@app.route('/add_raid/<type:path>/disk/<disk:path>/mkfs/<mkfs>', method='GET')
def add_raid(type,mkfs,disk):
    disk_num = disk.count(' /') + 1
    res = comm.add_raid(type,mkfs,disk_num,disk)
    if(res != True):
        return response_json(-1,res)
    return response_json(0,'success')
#删除raid---恢复初始状态（会删除所有数据）
@app.route('/del_raid/<raid_name:path>', method='GET')
def del_raid(raid_name):
    print(raid_name)
    res = comm.del_raid(raid_name)
    if(res != True):
        return response_json(-1,res)
    return response_json(0)
#获取raid信息
@app.route('/get_raid', method='GET')
def get_raid():
    res = comm.get_raid()
    return json.loads(res)
#获取存储空间信息
@app.route('/get_df', method='GET')
def get_df():
    res = comm.get_df()
    return json.loads(res)
#获取文件夹和信息
@app.route('/get_file_foder/<path:path>', method='GET')
def get_file_foder(path):
    res = comm.get_file_foder(path)
    return json.loads(res)
#新建文件夹
@app.route('/add_file_foder/<path:path>', method='GET')
def add_file_foder(path):
    if '/volume' not in path:
        return response_json(-1, 'error')
    res = comm.add_file_foder(path)
    if (res != True):
        return response_json(-1, res)
    return response_json(0)
# 删除文件夹或文件
@app.route('/del_file_foder/<path:path>/name/<name>', method='GET')
def del_file_foder(path,name):
    name = name.replace(' ','\ ')
    if '/volume' in path:
        res = comm.del_file_foder(path,name)
    else:
        return response_json(-1, 'error')
    if (res != True):
        return response_json(-1, res)
    return response_json(0)
#复制文件夹或文件
@app.route('/cp_file_foder/<cover>/source/<sourcedir:path>/dest/<destdir:path>/name/<name>', method='GET')
def cp_file_foder(cover,sourcedir,destdir,name):
    if ('/volume' not in sourcedir) or ('/volume' not in destdir):
        return response_json(-1, 'error')
    res = comm.cp_file_foder(cover,sourcedir,destdir,name)
    if (res != True):
        return response_json(-1, res)
    return response_json(0)
#移动文件夹或文件
@app.route('/mv_file_foder/<cover>/source/<sourcedir:path>/dest/<destdir:path>/name/<name>', method='GET')
def mv_file_foder(cover,sourcedir,destdir,name):
    if ('/volume' not in sourcedir) or ('/volume' not in destdir):
        return response_json(-1, 'error')
    res = comm.mv_file_foder(cover,sourcedir,destdir,name)
    if (res != True):
        return response_json(-1, res)
    return response_json(0)
# 重命名
@app.route('/rename/<path:path>/name/<name>', method='GET')
def rename(path,name):
    if ('/volume' not in path) or (' ' not in name):
        return response_json(-1, 'error')
    res = comm.rename(path,name)
    if (res != True):
        return response_json(-1, res)
    return response_json(0)
# 退出
@app.route('/logout', method='GET')
def logout():
    session = request.environ.get('beaker.session')
    session['uid'] = None
    session.save()
    return response_json(0, 'success')
@app.route('/login/<name>/<pwd>', method='GET')
def login(name,pwd):
    res = comm.check_user(name, pwd)
    if (res != True):
        return response_json(-1, res)
    return response_json(0, 'success')
# 上传文件
@app.route('/upload', method='POST')
def upload():
    uploadfile = request.files.get('file')  # 获取上传的文件
    path   = request.forms.get('path')
    if 'volume' not in path:
        return response_json(-1, 'error')
    name = uploadfile.raw_filename
    # 文件名格式转换
    name = HTMLParser().unescape(name)
    uploadfile.save("%s/%s"%(path,name), overwrite=True)  # overwrite参数是指覆盖同名文件
    return response_json(0, 'success')
# 下载文件
@app.route('/download/<filename:path>',method='GET')
def download(filename):
    download_path = '/'
    # 判断文件是否存在
    is_file = os.path.isfile('%s' %(filename))
    if not is_file:
        return response_json(-1, '该文件不存在！')
    # file = static_file(filename, root=download_path,download=True)#强制下载
    file = static_file(filename, root=download_path)
    return file
# storj
@app.route('/get_storj', method='GET')
def get_storj():
    res = comm.get_storj()
    if (res == False):
        return response_json(-1, 'error')
    return json.loads(res,object_pairs_hook=OrderedDict)
@app.route('/create_storj_node/<purse_addr>/<storage:path>/port/<port>/<size>', method='GET')
def create_storj_node(purse_addr,storage,port,size):
    res = comm.create_storj_node(purse_addr,storage,port,size)
    if (res != True):
        return response_json(-1, res)
    return response_json(0, 'success')
@app.route('/stop_storj_node/<id>', method='GET')
def stop_storj_node(id):
    res = comm.stop_storj_node(id)
    if (res != True):
        return response_json(-1, res)
    return response_json(0, 'success')
@app.route('/restart_storj_node/<id>', method='GET')
def restart_storj_node(id):
    res = comm.restart_storj_node(id)
    if (res != True):
        return response_json(-1, res)
    return response_json(0, 'success')
@app.route('/destroy_storj_node/<id>', method='GET')
def destroy_storj_node(id):
    res = comm.destroy_storj_node(id)
    if (res != True):
        return response_json(-1, res)
    return response_json(0, 'success')

@app.route('/check', method='GET')

def check():
    return response_json(0,'success')


def web_server_start_localhost(param):
    try:
        run(app, host='0.0.0.0', port='4000', debug=False, server='gevent')
    except Exception as e:
        print(e)
    pass