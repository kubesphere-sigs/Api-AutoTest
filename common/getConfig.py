import yaml
import sys
import os

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

# 获取yaml文件路径
yamlPath = '../config/config_new.yaml'
yamlPath_1 = 'config/config_new.yaml'


def get_apiserver():
    # open方法打开直接读出来
    if os.path.exists(yamlPath):
        f = open(yamlPath, 'r', encoding='utf-8')
    else:
        f = open(yamlPath_1, 'r', encoding='utf-8')
    cfg = f.read()

    d = yaml.safe_load(cfg)  # 用load方法转字典
    url = d['env']['url']
    if 'http://' in url:
        return url
    elif 'https://' in url:
        return url
    else:
        url = 'http://' + url
    return url
