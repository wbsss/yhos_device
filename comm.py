#!/usr/bin/env python
# encoding: utf-8
import subprocess
import json
import re
import os
from bottle import response

#添加raid
def add_raid(type,mkfs,disk_num,disk):
    # 先删除
    del_raid('/dev/md0')
    if disk_num == 1:
        type = 'basic'
    # 取消挂载=>删除分区>创建新分区
    partition_name_arr = ''
    disk_arr = disk.split()
    for n,dsk in enumerate(disk_arr):
        cmd ="fdisk -l 2>/dev/null |grep %s|awk 'NR>1{print $1}'" %(dsk)
        print("cmd",cmd)
        p= execution(cmd)
        str = p.stdout.read()
        arr = str.split()
        l = len(arr)
        for i, str in enumerate(arr):
            cmd = "umount %s"%(str)
            print("cmd",cmd)
            p = execution(cmd)
            cmd = "echo 'd\n%s\nw' |sudo fdisk %s" % (str[-1:], str[:-1])
            if(i==l-1):
                cmd = "echo 'd\nw' |sudo fdisk %s" % (str[:-1])
            print("cmd",cmd)
            p = execution(cmd)
            partition_name = p.stdout.read()
            if partition_name == None:
                return '磁盘%s新建分区失败，无法继续创建raid' %(dsk)
        #创建新分区
        partition_name = add_partition(dsk)
        if n == 0:
            partition_name_arr += partition_name
        else:
            partition_name_arr += " %s" % (partition_name)
    print partition_name_arr
    #创建raid
    raid_num = getraid_num_max()
    print ("raid_num",raid_num)
    if (raid_num == '\n'):
        raid_num =0
    else:
        raid_num =int(raid_num)+1
    cmd = "echo 'y' |sudo mdadm -C /dev/md%s -a yes -l %s -n %s %s" %(raid_num,type,disk_num,partition_name_arr)
    if (type == 'basic'):
        cmd = "echo 'y' |sudo mdadm -C /dev/md%s -a yes -l %s -n %s -f %s" % (raid_num,'1', disk_num, partition_name_arr)
    print("cmd",cmd)
    p = execution(cmd)
    str = p.stdout.read()
    if(p.returncode != 0):
        return str
    # 格式化
    cmd = "mkfs.%s /dev/md%s" % (mkfs, raid_num)
    print("cmd", cmd)
    p = execution(cmd)
    cmd = "ls / |grep volume* | awk -F '' '$0=$NF' | sudo awk 'NR==1{max=$1;next}{max=max>$1?max:$1}END{print max}'"
    print("cmd", cmd)
    p = execution(cmd)
    num = p.stdout.read()[:-1]
    print(num)
    if not num:
        num = 1
    else:
        num = int(num)
        num += 1
    cmd = "mkdir /volume%s" % (num)
    print("cmd", cmd)
    p = execution(cmd)
    cmd = "mount /dev/md%s /volume%s" % (raid_num, num)
    print("cmd", cmd)
    p = execution(cmd)
    if (p.returncode != 0):
        return p.stdout.read()
    return True
# 删除raid
def del_raid(raid_name):
    # 取消挂载->删除文件夹
    cmd = "df |grep %s | awk '{print $NF}'" % (raid_name)
    print("cmd", cmd)
    p = execution(cmd)
    mount = p.stdout.read()[:-1]
    if mount:
        cmd = "umount %s" % (mount)
        print("cmd", cmd)
        p = execution(cmd)
        if p.returncode != 0:
            return False
        cmd = "rm -rf %s" % (mount)
        print("cmd", cmd)
        p = execution(cmd)
    #删除raid
    # 获取组成raid的分区
    cmd = "cat /proc/mdstat|sudo grep %s" %(raid_name.split('/')[2])
    print("cmd",cmd)
    p = execution(cmd)
    if p.returncode == 0:
        str = p.stdout.read()[:-1]
        print ("str",str)
        arr = str.split()
        print ("arr", arr)
        cmd = "mdadm -S %s" % (raid_name)
        print("cmd",cmd)
        p = execution(cmd)
        if p.returncode == 0:
            for i,dev in enumerate(arr):
                if i>3:
                    cmd = "mdadm --zero-superblock %s" %("/dev/%s"%(re.sub(u"\\[.*?]", "", dev)))
                    print("cmd",cmd)
                    p = execution(cmd)
        else:
            return p.stdout.read()
        cmd = "sh -c 'mdadm --detail --scan --verbose > /etc/mdadm.conf'"
        print("cmd", cmd)
        p = execution(cmd)
    else:
        return p.stdout.read()
    return True
#获取全部raid信息
def get_raid():
    cmd = "cat /proc/mdstat |sudo  grep 'md'|sudo awk '{print $1}'"
    print("cmd",cmd)
    p = execution(cmd)
    raid_arr = p.stdout.read()[:-1].split()
    resp = ''
    for i,raid in enumerate(raid_arr):
        res = ''
        #type
        cmd = "cat /proc/mdstat |sudo  grep '%s'" %(raid)
        print("cmd",cmd)
        p = execution(cmd)
        type = p.stdout.read()[:-1].split()[3]
        #disk
        raid_name = "/dev/%s" %(raid)
        res += '"raid_name":"Raid Group %s"' % (int(raid_name[-1:])+1)
        res += ',"raid_path":"%s"' % (raid_name)

        cmd = "mdadm -D %s |sudo grep '/dev/sd'|sudo awk '{print $NF}'" %(raid_name)
        print("cmd",cmd)
        p = execution(cmd)
        disk_arr = ''
        # 记录disk_arr长度，当为1时，设置type为basic
        t =0
        for k,line in enumerate(p.stdout.readlines()):
            t+=1
            line = line[:-1]
            if k == 0:
                disk_arr += '"%s"'%(line)
            else:
                disk_arr += ',"%s"' % (line)
        res += ',"disk_arr":[%s]' % (disk_arr)
        if t==1:
            res += ',"type":"basic"'
        else:
            res += ',"type":"%s"' % (type)
        cmd = "pvs %s" %(raid_name)
        print("cmd",cmd)
        p = execution(cmd)
        if p.returncode == 0:
            # pvs --->size,free_size,raid_name
            vg = p.stdout.read().split()[7]
            cmd = "vgdisplay %s |sudo  grep 'VG Size\|Alloc PE / Size\|Free  PE / Size'" % (vg)
            print("cmd", cmd)
            p = execution(cmd)
            for j,line in enumerate(p.stdout.readlines()):
                line = line[:-1].split("       ")
                if j == 0:
                    res += ',"size":"%s"' % (line[2].strip().strip('<'))
                if j == 1:
                    res += ',"used_size":"%s"' % (line[1].split('/')[1].strip().strip('<'))
                if j == 2:
                    res += ',"free_size":"%s"' % (line[1].split('/')[1].strip().strip('<'))
        else:
            cmd = "mdadm -D %s |grep 'Array Size'" %(raid_name)
            print("cmd", cmd)
            p = execution(cmd)
            str = re.findall(r'[(](.*?)[)]', p.stdout.read())[0].split()
            size = "%s %s" %(str[0],str[1])
            res += ',"size":"%s"' % (size)
            cmd = "df |grep '%s'" %(raid_name)
            print("cmd", cmd)
            p = execution(cmd)
            if p.stdout.read():
                res += ',"used_size":"%s"' % (size)
                res += ',"free_size":"%s"' % ("0")
            else:
                res += ',"used_size":"%s"' % ("0")
                res += ',"free_size":"%s"' % (size)
        if i == 0:
            resp += '{%s}' % (res)
        else:
            resp += ',{%s}' % (res)
    return '{"errcode":%d,"errmsg":"%s","data":[%s]}' % (0, 'success', resp)
#获取存储空间信息
def get_df():
    cmd = "df -TH |sudo  grep /volume"
    print("cmd",cmd)
    p = execution(cmd)
    str = ''
    for i,line in enumerate(p.stdout.readlines()):
        line_arr = line[:-1].split()
        of_raid = "Raid Group %s" % (int(line_arr[0][-1:]) + 1)
        raid_group = line_arr[0]
        df_name = "存储空间%s"%(line_arr[6][-1:])
        # {"partition_name": "['/dev/mapper/vg2-volume_2', '20G', '45M', '19G', '1%', '/volume2']"}
        if i==0:
            str +='{"name":"%s","path":"%s","mount": "%s","size":"%s","used":"%s","free":"%s","percent":"%s","mkfs":"%s","of_raid":"%s","of_raid_name":"%s"}' %(df_name,line_arr[0],line_arr[6],line_arr[2],line_arr[3],line_arr[4],line_arr[5],line_arr[1],raid_group,of_raid)
        else:
            str += ',{"name":"%s","path":"%s","mount": "%s","size":"%s","used":"%s","free":"%s","percent":"%s","mkfs":"%s","of_raid":"%s","of_raid_name":"%s"}' % (df_name,line_arr[0],line_arr[6], line_arr[2], line_arr[3], line_arr[4], line_arr[5],line_arr[1],raid_group,of_raid)
    return '{"errcode":%d,"errmsg":"%s","data":[%s]}' % (0, 'success', str)
#获取文件或文件夹
def get_file_foder(path):
    path = path.replace(' ','')
    cmd ="ls %s -lQ --time-style \"+%%Y/%%m/%%d %%H:%%M:%%S\"" %(path)
    print("cmd",cmd)
    p = execution(cmd)
    if p.returncode != 0:
        return False
    str = ''
    # ['-rwxrwxrwx.', '1', 'root', 'root', '8', '2018/10/13', '18:01:01', 'a.txt']
    for i,line in enumerate(p.stdout.readlines()):
        if i>0:
            arr =  line[:-1].split()
            # 解决空格问题
            p1 = re.compile(r'[\"](.*?)[\"]', re.S)
            filename = re.findall(p1, line)[0]
            if(1 == i):
                str += '{"foder_name":"%s","permission":"%s","count":"%s","user":"%s","group":"%s","size":"%s","data_day":"%s","data_time":"%s"}' % (filename,arr[0],arr[1],arr[2],arr[3],arr[4],arr[5],arr[6])
            else:
                str += ',{"foder_name":"%s","permission":"%s","count":"%s","user":"%s","group":"%s","size":"%s","data_day":"%s","data_time":"%s"}' % (filename,arr[0],arr[1],arr[2],arr[3],arr[4],arr[5],arr[6])
    if path[-1:] != '/':
        path = "%s/" %(path)
    return '{"errcode":%d,"errmsg":"%s","data":[{"path":"%s","foders":[%s]}]}' % (0, 'success', path,str)
#新建文件夹
def add_file_foder(path):
    cmd = "mkdir %s" %(path)
    print("cmd",cmd)
    p = execution(cmd)
    if p.returncode != 0:
        return False
    # 给权限
    cmd = "chmod -R 0777 %s" % (path)
    print("cmd",cmd)
    p = execution(cmd)
    return True
#复制文件夹或文件
def cp_file_foder(cover,sourcedir,destdir,name):
    if (sourcedir[-1:] != '/'):
        sourcedir = '%s/' % (sourcedir)
    if ',' in name:
        cmd = "echo '%s' | cp -ir %s{%s} %s" % (cover, sourcedir, name, destdir)
    else:
        cmd = "echo '%s' | cp -ir %s%s %s" % (cover, sourcedir, name, destdir)
    print("cmd",cmd)
    p = execution(cmd)
    if p.returncode != 0:
        return False
    return True
#移动文件夹或文件
def mv_file_foder(cover,sourcedir,destdir,name):
    if (sourcedir[-1:] != '/'):
        sourcedir = '%s/' % (sourcedir)
    if ',' in name:
        cmd = "echo '%s' | mv %s{%s} %s" % (cover,sourcedir,name,destdir)
    else:
        cmd = "echo '%s' | mv %s%s %s" % (cover, sourcedir, name, destdir)
    print("cmd",cmd)
    p = execution(cmd)
    if p.returncode != 0:
        return False
    return True
#删除文件夹或文件
def del_file_foder(path,name):
    if(path[-1:] != '/'):
        path = '%s/' %(path)
    if ',' in name:
        cmd = "rm -rf %s{%s}" % (path, name)
    else:
        cmd = "rm -rf %s%s" % (path,name)
    print("cmd",cmd)
    p = execution(cmd)
    if p.returncode != 0:
        return p.stdout.read()
    return True
# 重命名文件
def rename(path,name):
    if (path[-1:] != '/'):
        path = '%s/' % (path)
    name = name.split()
    cmd = "mv %s%s %s%s" %(path,name[0],path,name[1])
    print("cmd", cmd)
    p = execution(cmd)
    if p.returncode != 0:
        return False
    return True
# 获取硬盘信息
def get_hd():
    cmd = "df |sudo grep '/boot'|sudo awk '{print $1}'"
    print("cmd", cmd)
    p = execution(cmd)
    boot = p.stdout.read()[:-2]
    cmd = "parted -l 2> /dev/null |sudo grep 'Disk /dev/sd' |sudo cut -f2 -d' '|sudo cut -f1 -d':'"
    print("cmd",cmd)
    p = execution(cmd)
    k = 0
    resp = ''
    hdds = p.stdout.readlines()
    for line in hdds:
        hd= line[:-1]
        j = 0
        res = ''
        state = False
        # 去除已经初始化的硬盘
        cmd = "cat /proc/mdstat |sudo  grep 'md'|sudo awk '{print $1}'"
        print("cmd", cmd)
        p = execution(cmd)
        raid_arr = p.stdout.read()[:-1].split()
        ini_hdd = []
        for i, raid in enumerate(raid_arr):
            raid_name = "/dev/%s" % (raid)
            cmd = "mdadm -D %s |sudo grep '/dev/sd'|sudo awk '{print $NF}'" % (raid_name)
            print("cmd", cmd)
            p = execution(cmd)
            ini_hdd += p.stdout.read().split()
        for str in (ini_hdd):
            if hd in str:
                state = True
                break
        if hd != boot:
            # hd = /dev/sda
            cmd = "smartctl -a %s |sudo grep 'Model Family\|Device Model\|Serial Number\|Firmware Version\|User Capacity\|SMART support is\|Power_On_Hours\| Reallocated_Sector_Ct\|Temperature_Celsius'" %(hd)
            print("cmd", cmd)
            p = execution(cmd)
            for i,str in enumerate(p.stdout.readlines()):
                if i<7:
                    data = str.split(':')
                    if i != 5:
                        if j ==0:
                            res += '"%s":"%s"' %(data[0],data[1][:-1].lstrip())
                        else:
                            res += ',"%s":"%s"' % (data[0], data[1][:-1].lstrip())
                else:
                    data = str.split()
                    res += ',"%s":"%s"' % (data[1], data[9])
                j = None
            if k == 0:
                resp +='{"is_ini":"%s","HD":"%s",%s}' %(state,hd,res)
                k = None
            else:
                resp += ',{"is_ini":"%s","HD":"%s",%s}' %(state,hd,res)
        pass
    return '{"errcode":%d,"errmsg":"%s","data":[%s]}' %(0,'success',resp)
# 判断用户名和密码
def check_user(name,pwd):
    cmd = "echo '%s' 2>/dev/null |su - %s" %(pwd,name)
    print("cmd", cmd)
    p = execution(cmd)
    print p.stdout.read()
    if p.returncode != 0:
        return False
    return True
# 获取网络信息
def get_network():
    cmd = "ip addr"
    print("cmd", cmd)
    p = execution(cmd)
    print p.stdout.read()
    return None
# -------------Storj API --------------------#
#创建节点
def create_storj_node(purse_addr,storage,port,size):
    cmd = "echo 'wq' | storjshare-create --storj %s --storage %s  --outfile %s/config.json  --manualforwarding true  --logdir %s --rpcport %s --size %s " %(purse_addr,storage,storage,storage,port,size)
    print("cmd:", cmd)
    path = os.path.exists(storage)
    if not path:
        return False
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.wait()
    print("-----code-------", p.returncode)
    if p.returncode != 0:
        return False
    cmd = "storjshare start --config %s/config.json" % (storage)
    print("cmd:", cmd)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.wait()
    print("-----code-------", p.returncode)
    if p.returncode != 0:
        return False
    return True
# 获取storj信息
def get_storj():
    cmd = "storjshare status | sed \"s,\x1B\[[0-9;]*[a-zA-Z],,g\""
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.wait()
    print("-----code-------", p.returncode)
    if p.returncode != 0:
        return False
    arr = p.stdout.readlines()
    str = ''
    for i,line in enumerate(arr):
        if i>3 and (i%3== 1):
            # print(arr[i].split('│')[1])
            Location = arr[i + 1].split('│')[1].strip()
            NodeID = arr[i].split('│')[1].strip()
            Uptime = arr[i].split('│')[3].strip()
            Status = arr[i].split('│')[2].strip()
            Restarts = arr[i].split('│')[4].strip()
            Peers = arr[i].split('│')[5].strip()
            Allocs = "%s(%s)" %(arr[i].split('│')[6].strip(),arr[i+1].split('│')[6].strip())
            Delta = arr[i].split('│')[7].strip()
            Port = "%s%s" %(arr[i].split('│')[8].strip(),arr[i+1].split('│')[8].strip())
            Shared = "%s%s" %(arr[i].split('│')[9].strip(),arr[i+1].split('│')[9].strip())
            Bridges = arr[i].split('│')[10].strip()
            if i == 4:
                str += '{"NodeID":"%s","Location":"%s","Status":"%s","Uptime":"%s","Restarts":"%s","Peers":"%s","Allocs":"%s","Delta":"%s","Port":"%s","Shared":"%s","Bridges":"%s"}' \
                    %(NodeID,Location,Status,Uptime,Restarts,Peers,Allocs,Delta,Port,Shared,Bridges)
            else:
                str += ',{"NodeID":"%s","Location":"%s","Status":"%s","Uptime":"%s","Restarts":"%s","Peers":"%s","Allocs":"%s","Delta":"%s","Port":"%s","Shared":"%s","Bridges":"%s"}' \
                      % (NodeID, Location, Status, Uptime, Restarts, Peers, Allocs, Delta, Port, Shared, Bridges)
    res = '{"errcode":%d,"errmsg":"%s","data":[%s]}' % (0, 'success', str)
    return res
#停止指定节点
def stop_storj_node(id):
    cmd = "storjshare stop --nodeid %s" %(id)
    print("cmd:", cmd)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.wait()
    print("-----code-------", p.returncode)
    if p.returncode !=0:
        return False
    return True
# 重启指定节点
def restart_storj_node(id):
    cmd = "storjshare restart --nodeid %s" %(id)
    print("cmd:", cmd)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.wait()
    print("-----code-------", p.returncode)
    if p.returncode !=0:
        return False
    return True
# 结束指定节点
def destroy_storj_node(id):
    cmd = "storjshare destroy --nodeid %s" %(id)
    print("cmd:", cmd)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.wait()
    print("-----code-------", p.returncode)
    if p.returncode !=0:
        return False
    return True
#----------------工具函数----------------
def response_json(code, msg='success', data=None):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return '{"errcode":%d,"errmsg":"%s","data":%s}' % (code, msg, json.dumps(data))
# 获取最大raid下标
def getraid_num_max():
    cmd = "cat /proc/mdstat |sudo  grep 'md' |sudo awk '{print substr($1,3,1)}'|sudo awk 'NR==1{max=$1;next}{max=max>$1?max:$1}END{print max}'"
    print("cmd",cmd)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.wait()
    str = ''
    for line in p.stdout.readlines():
        str +=line
    if(p.returncode != 0):
        return str
    return str
#新建分区
def add_partition(disk_name):
    cmd = "echo 'pq' |sudo fdisk %s 2>/dev/null|sudo  grep 'dev/sda' |sudo awk 'NR>1{print $1}'" %(disk_name)
    print("cmd", cmd)
    p = execution(cmd)
    list = p.stdout.read().split()
    cmd = "echo 'n\np\n\n\n\np\nq' |sudo fdisk %s 2>/dev/null|sudo  grep '%s' |sudo awk 'NR>1{print $1}'" %(disk_name,disk_name)
    print("cmd", cmd)
    p = execution(cmd)
    list1 = p.stdout.read().split()
    for li in list:
        list1.remove(li)
    if list1:
        pat_name = list1[0]
    else:
        pat_name = None
    cmd = "echo 'n\np\n\n\n\np\nt\nfd\nw' |sudo  fdisk %s" %(disk_name)
    print("cmd",cmd)
    p =execution(cmd)
    if (p.returncode > 1):
        return p.returncode
    return pat_name
#h获取某个存储空间下的共享文件夹
def get_share(lvm_name):
    # cmd = "df |sudo  grep '%s' |sudo awk '{print $NF}'" %(lvm_name)
    # print("cmd",cmd)
    # p = execution(cmd)
    # lvname = p.stdout.read()[:-1]
    if lvm_name == '\n' or lvm_name == '':
        return None
    cmd = "grep -nr '%s'  /etc/samba/smb.conf |sudo  awk -F ':' '{print $1}'" %(lvm_name)
    print("cmd",cmd)
    p = execution(cmd)
    list = []
    for line in p.stdout.readlines():
        if line == '':
            return  None
        else:
            line = int(line)
        cmd = "sed -n '%dp' /etc/samba/smb.conf|sudo cut -d '[' -f2|sudo cut -d ']' -f1" % (line - 1)
        print("cmd",cmd)
        p = execution(cmd)
        list.append(p.stdout.read()[:-1])
    return list
#执行命令 cmd = "cat /proc/mdstat|grep md0"
def execution(cmd):
    cmd = 'sudo %s' %(cmd)
    print cmd
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.wait()
    print("-----code-------", p.returncode)
    return p
# print add_lvm("/dev/md0","ext4","10G")
# print del_lvm("/dev/mapper/vg1-volume_1")
# print del_share("aaa")
# print add_share("volume1","ccc")
# print get_file_foder("ccc","/")
# print add_file_foder("0","ccc","/vvv")
# print del_file_foder("0","ccc","/a.txt")
# print set_nfs_cfg("/volume1/aaa 192.168.1.0/24(rw,sync,all_squash)")
# print get_share("/dev/mapper/vg2-volume_1")
# print get_all_share()
# print get_all_service()
# print get_user()
# print get_hd()
# print add_partition("/dev/sda")
# print get_raid()
# print get_raid_hd()
# print add_raid(1,2,"/dev/sda /dev/sdb")
# print del_raid("/dev/md0")
# print mv_file_foder('n','/volume1/vvv','/volume2/')
# print get_user_quota('wubs')
# print create_storj_node("0x608fc99b0492Aaf373E55eA8e418fC0f2Bd77572","/storjData/node2","4012","3GB")
# print stop_storj_node("89f2a5f6a47d48e65b8a22d2e808a8d65b38945b")
# print restart_storj_node("89f2a5f6a47d48e65b8a22d2e808a8d65b38945b")
# print destroy_storj_node("89f2a5f6a47d48e65b8a22d2e808a8d65b38945b")