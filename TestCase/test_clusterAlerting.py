# -- coding: utf-8 --
import random
import time
import numpy
import pytest
import allure
import sys
from common import commonFunction
from step import cluster_steps

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用


@allure.feature('单集群告警')
@pytest.mark.skipif(commonFunction.get_components_status_of_cluster('alerting') is False,
                    reason='集群未开启alerting功能')
class TestClusterAlerting(object):
    if commonFunction.check_multi_cluster() is True:
        # 如果为多集群环境，则不会collect该class的所有用例。 __test__ = False
        __test__ = False
    else:
        __test__ = True

    @allure.story("监控告警/规则组")
    @allure.title('按名称查询内置的规则组')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_alert_policies_by_name(self):
        # 按名称查询规则组
        response = cluster_steps.step_get_alert_policies('builtin', 'name=kubesphere-system')
        # 获取规则组数量
        count = response.json()['totalItems']
        # 验证时数量为2
        assert count == 1

    @allure.story("监控告警/规则组")
    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('title, state, type',
                             [('按告警状态/未激活查询内置的规则组', 'inactive', 'builtin'),
                              ('按告警状态/待发送查询内置的规则组', 'pending', 'builtin'),
                              ('按告警状态/发送中查询内置的规则组', 'firing', 'builtin'),
                              ('按告警状态/已禁用查询内置的规则组', 'disabled', 'builtin'),
                              ('按告警状态/未激活查询自定义的规则组', 'inactive', ''),
                              ('按告警状态/待发送查询自定义的规则组', 'pending', ''),
                              ('按告警状态/发送中查询自定义的规则组', 'firing', ''),
                              ('按告警状态/已禁用查询自定义的规则组', 'disabled', '')
                              ])
    def test_get_alert_policies_by_state(self, title, state, type):
        # 按告警状态查询告警规则组
        response = cluster_steps.step_get_alert_policies(type, 'state=' + state)
        # 获取告警规则组的数量
        count = response.json()['totalItems']
        # 如果告警规则组数量大于0，便判断告警规则的状态
        if count > 0:
            # 获取第一个告警规则组的规则的状态
            state_count = response.json()['items'][0]['status']['rulesStats'][state]
            # 验证状态
            with pytest.assume:
                assert state_count > 0
        else:
            assert response.status_code == 200

    @allure.story("监控告警/规则组")
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('title, state, type', [
        ('按规则组状态/已启用查询内置的规则组', 'true', 'builtin'),
        ('按规则组状态/已禁用查询内置的规则组', 'false', 'builtin'),
        ('按规则组状态/已启用查询自定义的规则组', 'true', ''),
        ('按规则组状态/已禁用查询自定义的规则组', 'false', '')
    ])
    def test_get_alert_policies_by_status(self, title, state, type):
        # 按规则组状态查询规则组
        response = cluster_steps.step_get_alert_policies_by_state(type, state)
        with pytest.assume:
            assert response.status_code == 200

    @allure.story("监控告警/告警消息")
    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('title, condition, type',
                             [('查看所有内置规则组的告警消息', '', 'builtin'),
                              ('按告警状态/已触发查询内置规则组的告警消息', '&state=firing', 'builtin'),
                              ('按告警状态/验证中查询内置规则组的告警消息', '&state=pending', 'builtin'),
                              ('按告警级别/一般告警查询内置规则组的告警消息', '&label_filters=severity%3Dwarning', 'builtin'),
                              ('按告警级别/重要告警查询内置规则组的告警消息', '&label_filters=severity%3Derror', 'builtin'),
                              ('按告警级别/危险告警查询内置规则组的告警消息', '&label_filters=severity%3Dcritical', 'builtin'),
                              ('按告警级别(重要告警)、告警状态(已触发)查询内置规则组的告警消息',
                               '&state=firing&label_filters=severity%3Derror', 'builtin'),
                              ('按告警级别(重要告警)、告警状态(验证中)查询内置规则组的告警消息',
                               '&state=pending&label_filters=severity%3Derror', 'builtin'),
                              ('按告警级别(危险告警)、告警状态(已触发)查询内置规则组的告警消息',
                               '&state=firing&label_filters=severity%3Dcritical', 'builtin'),
                              ('按告警级别(危险告警)、告警状态(验证中)查询内置规则组的告警消息',
                               '&state=pending&label_filters=severity%3Dcritical', 'builtin'),
                              ('按告警级别(一般告警)、告警状态(已触发)查询内置规则组的告警消息',
                               '&state=firing&label_filters=severity%3Dwarninng', 'builtin'),
                              ('按告警级别(一般告警)、告警状态(验证中)查询内置规则组的告警消息',
                               '&state=pending&label_filters=severity%3Dwarning', 'builtin'),
                              ('查看所有自定义规则组的告警消息', '', ''),
                              ('按告警状态/已触发查询自定义规则组的告警消息', '&state=firing', ''),
                              ('按告警状态/验证中查询自定义规则组的告警消息', '&state=pending', ''),
                              ('按告警级别/一般告警查询自定义规则组的告警消息', '&label_filters=severity%3Dwarning',
                               ''),
                              ('按告警级别/重要告警查询自定义规则组的告警消息', '&label_filters=severity%3Derror',
                               ''),
                              ('按告警级别/危险告警查询自定义规则组的告警消息', '&label_filters=severity%3Dcritical',
                               ''),
                              ('按告警级别(重要告警)、告警状态(已触发)查询自定义规则组的告警消息',
                               '&state=firing&label_filters=severity%3Derror', ''),
                              ('按告警级别(重要告警)、告警状态(验证中)查询自定义规则组的告警消息',
                               '&state=pending&label_filters=severity%3Derror', ''),
                              ('按告警级别(危险告警)、告警状态(已触发)查询自定义规则组的告警消息',
                               '&state=firing&label_filters=severity%3Dcritical', ''),
                              ('按告警级别(危险告警)、告警状态(验证中)查询自定义规则组的告警消息',
                               '&state=pending&label_filters=severity%3Dcritical', ''),
                              ('按告警级别(一般告警)、告警状态(已触发)查询自定义规则组的告警消息',
                               '&state=firing&label_filters=severity%3Dwarninng', ''),
                              ('按告警级别(一般告警)、告警状态(验证中)查询自定义规则组的告警消息',
                               '&state=pending&label_filters=severity%3Dwarning', '')
                              ])
    def test_get_alert_message_by_condition(self, title, condition, type):
        # 查询告警消息
        response = cluster_steps.step_get_alert_message(type, condition)
        # 获取告警消息的数量
        count = response.json()['totalItems']
        # 验证数量>=0
        assert count >= 0

    @allure.story('监控告警/规则组')
    @allure.title('创建规则组（节点的cpu使用率大于0）')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_alert_policy(self):
        # 获取集群的节点名称
        response = cluster_steps.step_get_nodes()
        node_count = response.json()['totalItems']  # 节点数量
        node_names = []
        for i in range(0, node_count):
            node_names.append(response.json()['items'][i]['metadata']['name'])
        # 获取任意节点名称
        node_name = node_names[numpy.random.randint(0, node_count)]
        # 创建规则组（节点的cpu使用率大于0）
        alert_name = 'test-alert' + str(commonFunction.get_random())
        cluster_steps.step_create_alert_policy(alert_name, node_name)
        # 验证告警规则已触发
        if cluster_steps.step_check_group_rule_firing(alert_name):
            # 查看告警消息，并验证告警消息正确
            r = cluster_steps.step_get_alert_message('', '')
            message_count = r.json()['totalItems']
            policy_names = []
            for i in range(0, message_count):
                policy_names.append(r.json()['items'][i]['labels']['rule_group'])
            with pytest.assume:
                assert alert_name in policy_names
            # 删除创建的规则组
            cluster_steps.step_delete_alert_custom_policy(alert_name)
        else:
            pytest.xfail('规则组不存在状态为firing的规则')

    @allure.story('监控告警/规则组')
    @allure.title('修改规则组中的持续时间')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_edit_alert_custom_policy(self):
        # 获取集群的节点名称
        response = cluster_steps.step_get_nodes()
        node_count = response.json()['totalItems']  # 节点数量
        node_names = []
        for i in range(0, node_count):
            node_names.append(response.json()['items'][i]['metadata']['name'])
        # 获取任意节点名称
        node_name = node_names[random.randint(0, node_count - 1)]
        # 创建规则组（节点的cpu使用率大于0）
        group_name = 'test-alert' + str(commonFunction.get_random())
        cluster_steps.step_create_alert_policy(group_name, node_name)
        # 查询新建的自定义规则组，并获取其告警规则的role_id
        re = cluster_steps.step_get_alert_custom_policy(group_name)
        rule_id = re.json()['items'][0]['spec']['rules'][0]['labels']['rule_id']
        resource_version = re.json()['items'][0]['metadata']['resourceVersion']
        # 修改自定义策略的持续时间为5min
        cluster_steps.step_edit_alert_custom_policy(group_name, rule_id, node_name, resource_version)
        # 查看规则组的详情，并验证持续时间修改成功
        r = cluster_steps.step_get_alert_custom_policy_detail(group_name)
        duration = r.json()['spec']['rules'][0]['for']
        with pytest.assume:
            assert duration == '5m'
        # 删除规则组
        cluster_steps.step_delete_alert_custom_policy(group_name)


if __name__ == "__main__":
    pytest.main(['-s', 'test_clusterAlerting.py'])  # -s参数是为了显示用例的打印信息。 -q参数只显示结果，不显示过程
