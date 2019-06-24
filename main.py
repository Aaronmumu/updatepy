#!/usr/bin/python3
# -*- coding: utf-8 -*-
import pymysql
import os
import os.path
import shutil
import time, datetime
import paramiko
import smtplib
from email.mime.text import MIMEText
import tabulate
from glob import glob

# 数据库更新
class db:
    def __init__(self, **param):
        self.ip = param.get('ip')
        self.port = param.get('port')
        self.user = param.get('user')
        self.db = param.get('db')
        self.pwd = param.get('pwd')
        pass

    def update(self):
        dbconn = pymysql.connect(self.ip, self.user, self.pwd, self.db, self.port)
        f = open("db.txt", "r")
        if dbconn:
            cursor = dbconn.cursor()
            while True:
                line = f.readline().strip('\n')  # 按行读取且处理掉换行符，效果:"\'\n'变为了''
                if line:
                    cursor.execute(line)
                    print(line)
                    dbconn.commit()
                else:
                    break
            cursor.execute("SELECT VERSION()")
            data = cursor.fetchone()
            print("Database version : %s " % data)
            dbconn.close()
        else:
            print("连接数据库失败")

# 项目源码更新
class project:
    def __init__(self):
        pass

    def update(self, sourceDir, targetDir, backupDir):
        print("更新代码部分")
        # 重命名文件夹
        shutil.move(targetDir, backupDir)
        # 复制整个目录(备份)
        shutil.copytree(sourceDir, targetDir)
        # 若需要文件过滤等处理
        # sourceDir = "source"
        # targetDir = "target-01"
        # self.copyFiles(sourceDir, targetDir)

    def copyFiles(self, sourceDir, targetDir):
        if sourceDir.find(".svn") > 0:
            return
        for file in os.listdir(sourceDir):
            sourceFile = os.path.join(sourceDir, file)
            targetFile = os.path.join(targetDir, file)
            if os.path.isfile(sourceFile):
                if not os.path.exists(targetDir):
                    os.makedirs(targetDir)
                if not os.path.exists(targetFile) or (
                        os.path.exists(targetFile) and (os.path.getsize(targetFile) != os.path.getsize(sourceFile))):
                    open(targetFile, "wb").write(open(sourceFile, "rb").read())
            if os.path.isdir(sourceFile):
                First_Directory = False
                self.copyFiles(sourceFile, targetFile)

    def removeFileInFirstDir(self, targetDir):
        for file in os.listdir(targetDir):
            targetFile = os.path.join(targetDir, file)
            if os.path.isfile(targetFile):
                os.remove(targetFile)

    def coverFiles(self, sourceDir, targetDir):
        for file in os.listdir(sourceDir):
            sourceFile = os.path.join(sourceDir, file)
            targetFile = os.path.join(targetDir, file)
            # cover the files
            if os.path.isfile(sourceFile):
                open(targetFile, "wb").write(open(sourceFile, "rb").read())

    def moveFileto(self, sourceDir, targetDir):
        shutil.copy(sourceDir, targetDir)

    def writeVersionInfo(self, targetDir):
        open(targetDir, "wb").write("Revison:")

# 获取时间
def getCurTime():
    nowTime = time.localtime()
    year = str(nowTime.tm_year)
    month = str(nowTime.tm_mon)
    day = str(nowTime.tm_mday)
    hour = str(nowTime.tm_hour)
    min = str(nowTime.tm_min)
    sec = str(nowTime.tm_sec)
    if len(month) < 2:
        month = '0' + month
    if len(day) < 2:
        day = '0' + day
    if len(hour) < 2:
        hour = '0' + hour
    if len(min) < 2:
        min = '0' + min
    if len(sec) < 2:
        sec = '0' + sec

    return (year + '_' + month + '_' + day + '_' + hour + '_' + min + '_' + sec)

#ssh
class shell:
    def __init__(self, **param):
        self.ip = param.get('ip')
        self.port = param.get('port')
        self.user = param.get('user')
        self.pwd = param.get('pwd')
        self.projects = param.get('projects')

    def __ftp__(self):
        transport = paramiko.Transport((self.ip, self.port))
        transport.connect(username=self.user, password=self.pwd)
        sftp = paramiko.SFTPClient.from_transport(transport)
        for project in self.projects:
            path = project['souce_path'] + '/' + project['package']
            old_path = glob(path)[0]
            npos = old_path.rfind('/')
            if npos == -1:
                npos = old_path.rfind('\\')
            package = old_path[npos + 1:]
            project['package'] = package
            topath = project['package_path'][0] + '/' + project['package']
            sftp.put(old_path, topath)  # 将aa.tar.gz
            print("成功将本地压缩包", old_path, "上传到服务器", topath)
        transport.close()

    def __create__(self):
        # 创建SSH对象
        self.ssh = paramiko.SSHClient()
        # 把要连接的机器添加到known_hosts文件中
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # 连接服务器
        self.ssh.connect(hostname=self.ip, port=self.port, username=self.user, password=self.pwd)

    def __exe__(self, cmd):
        cin, out, err = self.ssh.exec_command(cmd)
        res = out.read()
        if not res:
            res = err.read()
        return res

    def __close__(self):
        self.ssh.close()

    def __title_ip__(self):
        ip = 'ip:=' + self.ip
        title = ip.center(111, '*')
        return title

    def __ssh__(self):
        self.__create__()
        title = self.__title_ip__()

        outlist = []
        index = 0
        for project in self.projects:
            for x in project['package_path']:
                time = getCurTime();
                tmp_dir = 'unzip_' + getCurTime();
                project_dir = project['web_path'] + '/' + project['name']
                backup_dir = project['web_back_path'] + '/back_' + project['name'] + '_' + time
                update_package_dir = tmp_dir + '/' + project['name']

                # 操作命令
                cmd = 'cd ' + x + ';'
                cmd += 'mkdir ' + tmp_dir + ';'
                cmd += 'tar -zxvf ' + project['package'] + ' -C ' + tmp_dir + ';'
                # 备份
                cmd += 'mv ' + project_dir + ' ' + backup_dir + ';'
                # 替换更新
                cmd += 'mv ' + update_package_dir + ' ' + project_dir + ';'
                # 删除临时解压
                pass

                print(cmd)
                self.__exe__(cmd)

                templist = []
                templist.append('网站路径:' + project_dir)
                templist.append('备份路径:' + backup_dir)
                outlist.append(templist)
                index = index + 1

        self.__close__()
        return outlist, title

    def convert(self):
        self.__ftp__()
        return self.__ssh__()

if __name__ == '__main__':
    print("它机操作(h) 本机操作(l) or 退出(q) \n")
    flag = True
    while (flag):
        answer = input("操作:")
        if 'q' == answer:
            flag = False
        elif 'h' == answer:

            # dir = input("备份目录:")
            # # 文件移动 需要推送到它机服务器
            # sourceDir = 'source'
            # targetDir = 'target'#PHP运行环境根目录
            # backupDir = dir + 'backup_' + getCurTime()

            # mac = {
            #     shell(**{'ip': '192.168.3.45',  # ip
            #              'port': 22,  # 端口
            #              'user': 'root',  # 用户名
            #              'pwd': '123456',  # 密码
            #              'projects': [{
            #                  'package': 'mhash.tar.gz',  # 包
            #                  'souce_path': 'D:\www\pyth',  # 更新包的原始目录
            #                  'path': ['/datapy/package'],  # 上传包路径
            #                  'web_path': '/datapy/www',  # web目录路径
            #                  'web_back_path': '/datapy/back',  # web备份目录路径
            #              }]})
            # }

            name = 'mhash-0.9.9.9'
            package = 'mhash.tar.gz'
            souce_path = 'D:\www\pyth'

            iname = input("项目名(默认: %s):" % name)
            ipackage = input("更新包名(默认: %s):" % package)
            isouce_path = input("更新包目录(默认: %s):" % souce_path)

            if iname:
                name = iname
            if ipackage:
                package = ipackage
            if isouce_path:
                souce_path = isouce_path

            tar = souce_path + '\\' + package;

            if not os.path.exists(tar):
                print('%s文件不存在 ' % tar)
                exit(1)

            mac = {
                shell(**{'ip': '',  # ip
                         'port': 22,  # 端口
                         'user': 'user_00',  # 用户名
                         'pwd': '',  # 密码
                         'projects': [{
                             'name': name,  # 包
                             'package': package,  # 包
                             'souce_path': souce_path,  # 更新包的原始目录
                             'package_path': ['/datapy/package'],  # 上传包路径
                             'web_path': '/datapy/www',  # web目录路径
                             'web_back_path': '/datapy/back',  # web备份目录路径
                         }]})
            }

            headers = ['path', 'bin', 'size', 'source_time', 'modify_time', 'bnew']
            out = ''
            for x in mac:
                table, title = x.convert()
                # now_out = tabulate(table, headers, tablefmt='html', stralign="center") + '\n\n'
                # replace_out = now_out.replace("${title}", title)
                # replace_color = replace_out.replace('">false', 'color: red">false')
                # out += replace_color + '<br>'
                print(table, title)
            pass
        elif 'l' == answer:
            dir = input("备份目录:")
            # 更新数据库结构
            db = db(**{'ip': '',  # ip
                       'port': 3306,  # 端口
                       'user': 'dev',  # 用户名
                       'db': '',  # 数据库
                       'pwd': 'dev'  # 密码
                       })
            db.update()
            # 文件移动 本地或者更新到别的服务器
            sourceDir = 'source'
            targetDir = 'target'
            backupDir = dir + 'backup_' + getCurTime()

            project = project()
            project.update(sourceDir, targetDir, backupDir)
            pass
        else:
            print("not the correct command")
