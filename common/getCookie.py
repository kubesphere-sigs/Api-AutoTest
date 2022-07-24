import yaml
import sys

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用


def get_token():
    # yaml文件路径
    yamlPath = '../config/token.yaml'
    yamlPath_1 = 'config/config_new.yaml'

    with open(yamlPath, 'r', encoding='utf-8') as f:
        result = yaml.load(f.read(), Loader=yaml.FullLoader)
    token = result["token"]
    return token