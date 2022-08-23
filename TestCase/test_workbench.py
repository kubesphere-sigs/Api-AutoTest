# -- coding: utf-8 --
import pytest
import allure
import sys
from common import commonFunction
from step import platform_steps
from fixtures.platform import workbench_info
sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用


@allure.feature('工作台')
@pytest.mark.skipif(commonFunction.check_multi_cluster() is True, reason='多集群环境下不执行')
class TestWorkbench(object):
    if commonFunction.check_multi_cluster() is True:
        # 如果为单集群环境，则不会collect该class的所有用例。 __test__ = False
        __test__ = False
    else:
        __test__ = True

    @allure.story('平台信息')
    @allure.title('查询平台的集群数量')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_count(self, workbench_info):
        # 获取平台的集群数量
        cluster_count = workbench_info.json()['results'][0]['data']['result'][0]['value'][1]
        # 验证集群数量正确
        assert cluster_count == str(1)

    @allure.story('平台信息')
    @allure.title('查询平台的企业空间数量')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_ws_count(self, workbench_info):
        # 获取平台的workspace数量
        ws_count = workbench_info.json()['results'][1]['data']['result'][0]['value'][1]
        # 查询集群的企业空间信息，并获取企业空间数量
        r = platform_steps.step_get_ws_info()
        ws_count_actual = r.json()['totalItems']
        # 验证企业空间数量正确
        assert int(ws_count) == ws_count_actual

    @allure.story('平台信息')
    @allure.title('查询平台的用户数量')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_user_count(self, workbench_info):
        # 获取平台的用户数量
        user_count = workbench_info.json()['results'][2]['data']['result'][0]['value'][1]
        # 查询集群的用户信息，并获取用户数量
        r = platform_steps.step_get_user_info('')
        user_count_actual = r.json()['totalItems']
        # 验证用户数量正确
        assert int(user_count) == user_count_actual

    @allure.story('平台信息')
    @allure.title('查询平台的应用模版数量')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_template_count(self, workbench_info):
        # 获取平台的应用模版数量
        try:
            template_count = workbench_info.json()['results'][3]['data']['result'][0]['value'][1]
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
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_kubeconfig(self):
        # 获取集群的kubeconfig信息
        response = platform_steps.step_get_kubeconfig()
        # 验证获取信息成功
        assert response.status_code == 200
