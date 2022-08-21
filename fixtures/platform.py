import pytest
import time
from common import commonFunction
from datetime import datetime
from step import platform_steps, workspace_steps, app_steps, cluster_steps


@pytest.fixture()
def create_role():
    authority = '["role-template-view-basic"]'
    role_name = 'role' + str(commonFunction.get_random())
    # 创建角色
    platform_steps.step_create_role(role_name, authority)
    yield role_name
    # 删除角色
    platform_steps.step_delete_role(role_name)


@pytest.fixture()
def create_user(create_role):
    user_name = 'user' + str(commonFunction.get_random())
    email = 'qq' + str(commonFunction.get_random()) + '@qq.com'
    password = 'P@88w0rd'
    # 使用新创建的角色创建用户
    platform_steps.step_create_user(user_name, create_role, email, password)
    yield user_name
    # 删除用户
    platform_steps.step_delete_user(user_name)


@pytest.fixture
def create_ws():
    ws_name = 'test-ws' + str(commonFunction.get_random())
    # 创建企业空间
    workspace_steps.step_create_workspace(ws_name)
    time.sleep(1)
    yield ws_name
    # 删除企业空间
    workspace_steps.step_delete_workspace(ws_name)


@pytest.fixture
def workbench_info():
    # 获取当前时间的10位时间戳
    now_time = datetime.now()
    now_timestamp = str(datetime.timestamp(now_time))[0:10]
    # 获取180分钟戳
    before_timestamp = commonFunction.get_before_timestamp(now_time, 180)
    # 查询工作台的基本信息
    response = platform_steps.step_get_base_info(before_timestamp, now_timestamp, '600', '20')
    return response


@pytest.fixture
def create_category():
    category_name = 'category' + str(commonFunction.get_random())
    response = app_steps.step_create_category(category_name)
    time.sleep(3)
    # 获取创建分类的category_id
    category_id = response.json()['category_id']
    yield category_id
    # 删除分类
    app_steps.step_delete_category(category_id)


@pytest.fixture
def node_name():
    # 获取节点列表中第一个节点的名称
    response = cluster_steps.step_get_nodes()
    node_name = response.json()['items'][0]['metadata']['name']
    return node_name