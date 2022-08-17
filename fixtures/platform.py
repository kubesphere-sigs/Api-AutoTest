import pytest
import time
from common import commonFunction
from datetime import datetime
from step import platform_steps, workspace_steps


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
    # 使用新创建的角色创建用户
    platform_steps.step_create_user(user_name, create_role)
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