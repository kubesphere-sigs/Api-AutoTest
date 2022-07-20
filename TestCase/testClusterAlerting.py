import pytest
import allure
import sys
from common import commonFunction
from step import cluster_steps


sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用


@allure.feature('单集群告警')
@pytest.mark.skipif(commonFunction.get_components_status_of_cluster('alerting') is False, reason='集群未开启alerting功能')
class TestClusterAlerting(object):

    @allure.story("监控告警/告警策略")
    @allure.title('按名称查询内置的告警策略')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_alert_policies_by_name(self):
        # 按名称查询告警策略
        response = cluster_steps.step_get_alert_policies('builtin/', 'name=KubeletServerCertificateExpiration')
        # 获取告警策略数量
        count = response.json()['total']
        # 验证时数量为2
        assert count == 2

    @allure.story("监控告警/告警策略")
    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('title, state, type',
                             [('按告警状态/未激活查询内置的告警策略', 'inactive', 'builtin/'),
                              ('按告警状态/待发送查询内置的告警策略', 'pending', 'builtin/'),
                              ('按告警状态/发送中查询内置的告警策略', 'firing', 'builtin/'),
                              ('按告警状态/未激活查询自定义的告警策略', 'inactive', ''),
                              ('按告警状态/待发送查询自定义的告警策略', 'pending', ''),
                              ('按告警状态/发送中查询自定义的告警策略', 'firing', '')
                              ])
    def test_get_alert_policies_by_state(self, title, state, type):
        # 按告警状态查询告警策略
        response = cluster_steps.step_get_alert_policies(type, 'state=' + state)
        # 获取告警策略的数量
        count = response.json()['total']
        # 如果告警策略数量大于0，便判断策略的状态
        if count > 0:
            # 获取第一个告警策略的状态
            state_actual = response.json()['items'][0]['state']
            # 验证状态
            assert state_actual == state
        else:
            assert response.status_code == 200

    @allure.story("监控告警/告警策略")
    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('title, level, type',
                             [('按告警级别/危险告警查询内置的告警策略', 'critical', 'builtin/'),
                              ('按告警级别/重要告警送查询内置的告警策略', 'error', 'builtin/'),
                              ('按告警级别/一般告警查询内置的告警策略', 'warning', 'builtin/'),
                              ('按告警级别/危险告警查询自定义的告警策略', 'critical', ''),
                              ('按告警级别/重要告警查询自定义的告警策略', 'error', ''),
                              ('按告警级别/一般告警查询自定义的告警策略', 'warning', '')
                              ])
    def test_get_alert_policies_by_level(self, title, level, type):
        pass
        # 按告警级别查询告警策略
        response = cluster_steps.step_get_alert_policies(type, 'label_filters=severity%3D' + level)
        # 获取告警策略的数量
        count = response.json()['total']
        # 如果告警策略数量大于0，便判断策略的状态
        if count > 0:
            # 获取第一个告警策略的状态
            state_actual = response.json()['items'][0]['labels']['severity']
            # 验证状态
            assert state_actual == level
        else:
            assert response.status_code == 200

    @allure.story("监控告警/告警策略")
    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('title, condition, type',
                             [('按告警级别、名称和告警状态查询内置的告警策略', 'name=kube&state=inactive&label_filters=severity%3Dcritical',
                               'builtin/'),
                              ('按告警级别、名称查询内置的告警策略', 'name=kube&label_filters=severity%3Dwarning', 'builtin/'),
                              ('按告警级别、告警状态查询内置的告警策略', 'state=inactive&label_filters=severity%3Derror', 'builtin/'),
                              ('按告警级别、名称和告警状态查询自定义的告警策略', 'name=kube&state=inactive&label_filters=severity%3Dcritical',
                               ''),
                              ('按告警级别、名称查询自定义的告警策略', 'name=kube&label_filters=severity%3Dwarning', ''),
                              ('按告警级别、告警状态查询自定义的告警策略', 'state=inactive&label_filters=severity%3Derror', ''),
                              ])
    def test_get_alert_policies_by_condition(self, title, condition, type):
        # 查询告警策略
        response = cluster_steps.step_get_alert_policies(type, condition)
        # 获取告警策略的数量
        count = response.json()['total']
        # 验证数量>=0
        assert count >= 0

    @allure.story("监控告警/告警消息")
    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('title, condition, type',
                             [('查看所有内置告警策略的告警消息', '', 'builtin/'),
                              ('按告警状态查询内置告警策略的告警消息', 'state=pending', 'builtin/'),
                              ('按告警级别查询内置告警策略的告警消息', 'label_filters=severity%3Dwarning', 'builtin/'),
                              ('按告警级别、告警状态查询内置告警策略的告警消息', 'state=inactive&label_filters=severity%3Derror', 'builtin/'),
                              ('查看所有自定义告警策略的告警消息', '', ''),
                              ('按告警状态查询自定义告警策略的告警消息', 'state=pending', ''),
                              ('按告警级别查询自定义告警策略的告警消息', 'label_filters=severity%3Dwarning', ''),
                              ('按告警级别、告警状态查询自定义告警策略的告警消息', 'state=inactive&label_filters=severity%3Derror', ''),
                              ])
    def test_get_alert_message_by_condition(self, title, condition, type):
        # 查询告警消息
        response = cluster_steps.step_get_alert_message(type, condition)
        # 获取告警消息的数量
        count = response.json()['total']
        # 验证数量>=0
        assert count >= 0