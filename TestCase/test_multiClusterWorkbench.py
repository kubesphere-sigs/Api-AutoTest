# -- coding: utf-8 --
import pytest
import allure
import sys
from common import commonFunction
from datetime import datetime
from step import platform_steps, multi_workspace_steps
import time

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用


@allure.feature('多集群环境工作台')
@pytest.mark.skipif(commonFunction.check_multi_cluster() is False, reason='未开启多集群功能')
@pytest.mark.skipif(commonFunction.check_multi_cluster() is False, reason='单集群环境下不执行')
class TestWorkbench(object):
    # 如果为单集群环境，则不会collect该class的所有用例。 __test__ = False
    __test__ = commonFunction.check_multi_cluster()

    @allure.story('平台信息')
    @allure.title('查询平台的集群数量')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_count(self):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 获取180分钟戳
        before_timestamp = commonFunction.get_before_timestamp(datetime.now(), 180)
        # 查询工作台的基本信息
        response = platform_steps.step_get_base_info(before_timestamp, now_timestamp, '600', '20')
        # 获取平台的集群数量
        cluster_count = response.json()['results'][0]['data']['result'][0]['value'][1]
        # 验证集群数量大于1
        assert int(cluster_count) >= 1

    @allure.story('平台信息')
    @allure.title('查询平台的企业空间数量')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_ws_count(self):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 获取180分钟戳
        before_timestamp = commonFunction.get_before_timestamp(datetime.now(), 180)
        # 查询工作台的基本信息
        response = platform_steps.step_get_base_info(before_timestamp, now_timestamp, '600', '20')
        # 获取平台的workspace数量
        ws_count = response.json()['results'][1]['data']['result'][0]['value'][1]
        # 查询集群的企业空间信息，并获取企业空间数量
        r = multi_workspace_steps.step_get_ws_info('')
        ws_count_actual = r.json()['totalItems']
        # 验证企业空间数量正确
        assert int(ws_count) == ws_count_actual

    @allure.story('平台信息')
    @allure.title('查询平台的用户数量')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_user_count(self):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 获取180分钟戳
        before_timestamp = commonFunction.get_before_timestamp(datetime.now(), 180)
        # 查询工作台的基本信息
        response = platform_steps.step_get_base_info(before_timestamp, now_timestamp, '600', '20')
        # 获取平台的用户数量
        user_count = response.json()['results'][2]['data']['result'][0]['value'][1]
        # 查询集群的用户信息，并获取用户数量
        r = platform_steps.step_get_user_info('')
        user_count_actual = r.json()['totalItems']
        # 验证用户数量正确
        assert int(user_count) == user_count_actual

    @allure.story('平台信息')
    @allure.title('查询平台的应用模版数量')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_template_count(self):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 获取180分钟戳
        before_timestamp = commonFunction.get_before_timestamp(datetime.now(), 180)
        # 查询工作台的基本信息
        response = platform_steps.step_get_base_info(before_timestamp, now_timestamp, '600', '20')
        # 获取平台的应用模版数量
        try:
            template_count = response.json()['results'][3]['data']['result'][0]['value'][1]
            # 查询集群的应用模版信息，并获取用户数量
            r = platform_steps.step_get_app_info()
            template_count_actual = r.json()['total_count']
            # 验证用户数量正确
            assert int(template_count) == template_count_actual
        except IndexError as e:
            print(e)
            print('集群未开启openpitrix')

    @allure.story('工具箱')
    @allure.title('获取集群的kubeconfig信息')
    def test_get_kubeconfig(self):
        # 获取集群的kubeconfig信息
        response = platform_steps.step_get_kubeconfig()
        # 验证获取信息成功
        assert response.status_code == 200