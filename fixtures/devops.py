import pytest
from common import commonFunction
from step import devops_steps
import sys
sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from fixtures.platform import create_ws


@pytest.fixture
def create_devops(create_ws):
    dev_name = 'test-dev' + str(commonFunction.get_random())
    devops_steps.step_create_devops(create_ws, dev_name)  # 创建一个devops工程
    response = devops_steps.step_get_devopinfo(create_ws, dev_name)
    devops_name_new = response.json()['items'][0]['metadata']['name']
    yield devops_name_new
    # 删除devops工程
    devops_steps.step_delete_devops(create_ws, devops_name_new)

