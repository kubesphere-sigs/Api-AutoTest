# -- coding: utf-8 --
import pytest
import allure
import sys
import time
import random
from common import commonFunction
from step import multi_cluster_steps

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用


@allure.feature('多集群告警')
@pytest.mark.skipif(commonFunction.get_components_status_of_cluster('alerting') is False, reason='集群未开启alerting功能')
@pytest.mark.skipif(commonFunction.get_components_status_of_cluster('whizard') is True, reason='集群已开启whizard功能')
class TestMultiClusterAlerting(object):
    # 如果为单集群环境，则不会collect该class的所有用例。 __test__ = False
    __test__ = commonFunction.check_multi_cluster()

    cluster_host_name = ''

    def setup_class(self):
        # 获取host集群的名称
        self.cluster_host_name = multi_cluster_steps.step_get_host_cluster_name()

    @allure.story("监控告警/告警消息")
    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('title, condition, type',
                             [('查看所有内置规则组的告警消息', '', 'builtin/'),
                              ('按告警状态查询内置规则组的告警消息', 'state=pending', 'builtin/'),
                              ('按告警级别查询内置规则组的告警消息', 'label_filters=severity%3Dwarning', 'builtin/'),
                              ('按告警级别、告警状态查询内置规则组的告警消息', 'state=inactive&label_filters=severity%3Derror', 'builtin/'),
                              ('查看所有自定义规则组的告警消息', '', ''),
                              ('按告警状态查询自定义规则组的告警消息', 'state=pending', ''),
                              ('按告警级别查询自定义规则组的告警消息', 'label_filters=severity%3Dwarning', ''),
                              ('按告警级别、告警状态查询自定义规则组的告警消息', 'state=inactive&label_filters=severity%3Derror', ''),
                              ])
    def test_get_alert_message_by_condition(self, title, condition, type):
        # 查询告警消息
        response = multi_cluster_steps.step_get_alert_message(self.cluster_host_name, type, condition)
        # 获取告警消息的数量
        count = response.json()['totalItems']
        # 验证数量>=0
        assert count >= 0

    @allure.story('监控告警/规则组')
    @allure.title('创建规则组（节点的cpu使用率大于0）')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_alert_policy(self):
        # 获取集群的节点名称
        response = multi_cluster_steps.step_get_nodes(self.cluster_host_name)
        node_count = response.json()['totalItems']  # 节点数量
        node_names = []
        for i in range(0, node_count):
            node_names.append(response.json()['items'][i]['metadata']['name'])
        # 获取任意节点名称
        node_name = node_names[random.randint(0, node_count - 1)]
        # 创建规则组（节点的cpu使用率大于0）
        alert_name = 'test-alert' + str(commonFunction.get_random())
        multi_cluster_steps.step_create_alert_policy(self.cluster_host_name, alert_name, node_name)
        # 等待180s后查看新建的规则组，并验证其状态为firing
        time.sleep(180)
        re = multi_cluster_steps.step_get_alert_custom_policy(self.cluster_host_name, alert_name)
        state = re.json()['items'][0]['status']['rulesStatus'][0]['state']
        with pytest.assume:
            assert state == 'firing'
        # 查看告警消息，并验证告警消息正确
        r = multi_cluster_steps.step_get_alert_message(self.cluster_host_name, '', 'label_filters=severity%3Dcritical')
        message_count = r.json()['totalItems']
        policy_names = []
        for i in range(0, message_count):
            policy_names.append(r.json()['items'][0]['labels']['rule_group'])
        with pytest.assume:
            assert alert_name in policy_names
        # 删除规则组
        multi_cluster_steps.step_delete_alert_custom_policy(self.cluster_host_name, alert_name)

    @allure.story('监控告警/规则组')
    @allure.title('修改规则组中的持续时间')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_alert_custom_policy(self):
        # 获取集群所有节点的名称
        response = multi_cluster_steps.step_get_nodes(self.cluster_host_name)
        node_count = response.json()['totalItems']  # 节点数量
        node_names = []
        for i in range(0, node_count):
            node_names.append(response.json()['items'][i]['metadata']['name'])
        # 获取任意节点名称
        node_name = node_names[random.randint(0, node_count - 1)]
        # 创建规则组（节点的cpu使用率大于0）
        alert_name = 'test-alert' + str(commonFunction.get_random())
        multi_cluster_steps.step_create_alert_policy(self.cluster_host_name, alert_name, node_name)
        # 查询新建的自定义告警规则组，并获取规则组的uid
        re = multi_cluster_steps.step_get_alert_custom_policy(self.cluster_host_name, alert_name)
        alert_id = re.json()['items'][0]['metadata']['uid']
        resource_version = re.json()['items'][0]['metadata']['resourceVersion']
        # 修改自定义策略的持续时间为5min
        multi_cluster_steps.step_edit_alert_custom_policy(self.cluster_host_name, alert_name, alert_id, resource_version, node_name)
        # 查看规则组的详情，并验证持续时间修改成功
        r = multi_cluster_steps.step_get_alert_custom_policy(self.cluster_host_name, alert_name)
        duration = r.json()['items'][0]['spec']['rules'][0]['for']
        assert duration == '5m'
        # 删除规则组
        multi_cluster_steps.step_delete_alert_custom_policy(self.cluster_host_name, alert_name)

    @allure.story("监控告警/规则组")
    @allure.title('按名称查询内置的规则组')
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_alert_policies_by_name(self):
        # 按名称查询规则组
        response = multi_cluster_steps.step_get_alert_policies(self.cluster_host_name, 'builtin', 'name=kubernetes-system-controller-manager')
        # 获取规则组数量
        count = response.json()['totalItems']
        # 验证时数量为1
        assert count == 1

    @allure.story("监控告警/规则组")
    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('title, state, type',
                             [('按告警状态/未激活查询内置的规则组', 'inactive', 'builtin'),
                              ('按告警状态/待发送查询内置的规则组', 'pending', 'builtin'),
                              ('按告警状态/发送中查询内置的规则组', 'firing', 'builtin'),
                              ('按告警状态/未激活查询自定义的规则组', 'inactive', ''),
                              ('按告警状态/待发送查询自定义的规则组', 'pending', ''),
                              ('按告警状态/发送中查询自定义的规则组', 'firing', '')
                              ])
    def test_get_alert_policies_by_state(self, title, state, type):
        # 按告警状态查询规则组
        response = multi_cluster_steps.step_get_alert_policies(self.cluster_host_name, type, 'state=' + state)
        # 获取规则组的数量
        count = response.json()['totalItems']
        # 如果规则组数量大于0，便判断策略的状态
        if count > 0:
            # 获取第一个告警规则相应状态的规则数量
            state_count = response.json()['items'][0]['status']['rulesStats'][state]
            # 验证状态
            assert state_count > 0
        else:
            assert response.status_code == 200

    @allure.story("监控告警/规则组")
    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('title, level, type',
                             [('按告警级别/危险告警查询内置的规则组', 'critical', 'builtin/'),
                              ('按告警级别/重要告警送查询内置的规则组', 'error', 'builtin/'),
                              ('按告警级别/一般告警查询内置的规则组', 'warning', 'builtin/'),
                              ('按告警级别/危险告警查询自定义的规则组', 'critical', ''),
                              ('按告警级别/重要告警查询自定义的规则组', 'error', ''),
                              ('按告警级别/一般告警查询自定义的规则组', 'warning', '')
                              ])
    def test_get_alert_policies_by_level(self, title, level, type):
        # 按告警级别查询规则组
        response = multi_cluster_steps.step_get_alert_policies(self.cluster_host_name, type, 'label_filters=severity%3D' + level)
        # 获取规则组的数量
        count = response.json()['totalItems']
        # 如果规则组数量大于0，便判断策略的状态
        if count > 0:
            # 获取第一个规则组的状态
            state_actual = response.json()['items'][0]['labels']['severity']
            # 验证状态
            assert state_actual == level
        else:
            assert response.status_code == 200

    @allure.story("监控告警/规则组")
    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('title, condition, type',
                             [('按告警级别、名称和告警状态查询内置的规则组', 'name=kube&state=inactive&label_filters=severity%3Dcritical',
                               'builtin/'),
                              ('按告警级别、名称查询内置的规则组', 'name=kube&label_filters=severity%3Dwarning', 'builtin/'),
                              ('按告警级别、告警状态查询内置的规则组', 'state=inactive&label_filters=severity%3Derror', 'builtin/'),
                              ('按告警级别、名称和告警状态查询自定义的规则组', 'name=kube&state=inactive&label_filters=severity%3Dcritical',
                               ''),
                              ('按告警级别、名称查询自定义的规则组', 'name=kube&label_filters=severity%3Dwarning', ''),
                              ('按告警级别、告警状态查询自定义的规则组', 'state=inactive&label_filters=severity%3Derror', ''),
                              ])
    def test_get_alert_policies_by_condition(self, title, condition, type):
        # 查询规则组
        response = multi_cluster_steps.step_get_alert_policies(self.cluster_host_name, type, condition)
        # 获取规则组的数量
        count = response.json()['totalItems']
        # 验证数量>=0
        assert count >= 0