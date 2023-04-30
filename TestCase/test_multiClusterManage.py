# -- coding: utf-8 --
import pytest
import allure
import sys
import time
import random
from datetime import datetime
from common import commonFunction
from step import multi_cluster_steps, project_steps, multi_workspace_steps, platform_steps, cluster_steps

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用


@allure.feature('多集群环境集群管理')
@pytest.mark.skipif(commonFunction.check_multi_cluster() is False, reason='未开启多集群功能')
@pytest.mark.skipif(commonFunction.check_multi_cluster() is False, reason='单集群环境下不执行')
class TestCluster(object):
    # 如果为单集群环境，则不会collect该class的所有用例。 __test__ = False
    __test__ = commonFunction.check_multi_cluster()

    cluster_names = []
    cluster_host_name = ''
    cluster_any_name = ''

    def setup_class(self):
        # 获取所有集群的名称
        self.cluster_names = multi_cluster_steps.step_get_cluster_name()
        # 获取host集群的名称
        self.cluster_host_name = multi_cluster_steps.step_get_host_cluster_name()
        # 获取多集群环境的集群名称
        response = multi_cluster_steps.step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        i = random.randint(0, cluster_count - 1)
        # 获取某个集群的名称
        self.cluster_any_name = response.json()['items'][i]['metadata']['name']

    @allure.story("概览")
    @allure.title('查看每个集群的版本信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_version(self):
        # 查询集群的版本信息
        for name in self.cluster_names:
            r = multi_cluster_steps.step_get_cluster_version(name)
            # 获取版本号
            cluster_version = r.json()['gitVersion']
            # 验证版本号获取成功
            assert cluster_version

    @allure.story("概览")
    @allure.title('查看每个集群的clusterrole信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_roles(self):
        for cluster_name in self.cluster_names:
            # 查询每个集群的clusterrole信息
            response = multi_cluster_steps.step_get_cluster_roles(cluster_name)
            count = response.json()['totalItems']
            name_1 = response.json()['items'][0]['metadata']['name']
            name_2 = response.json()['items'][1]['metadata']['name']
            # 验证查询成功
            assert count == 2
            assert name_1 == 'cluster-viewer'
            assert name_2 == 'cluster-admin'

    @allure.story("概览")
    @allure.title('查看每个集群指定的clusterrole信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_roles_by_name(self):
        condition = 'name=cluster'
        for cluster_name in self.cluster_names:
            # 查询每个集群的clusterrole信息
            response = multi_cluster_steps.step_get_cluster_roles(cluster_name, condition)
            count = response.json()['totalItems']
            name_1 = response.json()['items'][0]['metadata']['name']
            name_2 = response.json()['items'][1]['metadata']['name']
            # 验证查询成功
            assert count == 2
            assert name_1 == 'cluster-viewer'
            assert name_2 == 'cluster-admin'

    @allure.story("概览")
    @allure.title('查看每个集群的namespaces信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_namespaces(self):
        for cluster_name in self.cluster_names:
            # 查询每个集群的namespaces信息
            r = multi_cluster_steps.step_get_cluster_namespace(cluster_name)
            # 获取namespace数量
            namespaces_count = r.json()['totalItems']
            # 验证namespaces数量大于0
            assert namespaces_count > 0

    @allure.story("概览")
    @allure.title('查看每个集群的component信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_component(self):
        for cluster_name in self.cluster_names:
            # 查询每个集群的component信息
            r = multi_cluster_steps.step_get_cluster_components(cluster_name)
            # 验证组件数量大于0
            assert len(r.json()) > 0

    @allure.story("概览")
    @allure.title('查看每个集群的监控metrics')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_monitoring_metrics(self):
        for cluster_name in self.cluster_names:
            # 查询每个集群的监控metrics
            r = multi_cluster_steps.step_get_cluster_monitoring_metrics(cluster_name)
            # 获取监控的metrics数量
            metrics_count = len(r.json()['results'])
            # 验证监控的metrics数量为8
            assert metrics_count == 8

    @allure.story("概览")
    @allure.title('查看每个集群的apiserver监控metrics')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_apiserver_monitoring_metrics(self):
        for cluster_name in self.cluster_names:
            # 查询每个集群的apiserver监控metrics
            r = multi_cluster_steps.step_get_cluster_apiserver_monitoring_metrics(cluster_name)
            # 获取apiserver监控metrics数量
            count = len(r.json()['results'])
            # 验证apiserver监控metrics的数量为2
            assert count == 2

    @allure.story("概览")
    @allure.title('查看每个集群的调度器信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_scheduler(self):
        for cluster_name in self.cluster_names:
            # 查询每个集群的调度器信息
            r = multi_cluster_steps.step_get_cluster_scheduler(cluster_name)
            # 获取metric_name
            metric_name = r.json()['results'][0]['metric_name']
            # 验证metric_name为 scheduler_schedule_attempts
            assert metric_name == 'scheduler_schedule_attempts'

    @allure.story("节点")
    @allure.title('为每个集群的某个节点设置污点')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_set_taints(self):
        for cluster_name in self.cluster_names:
            # 污点信息
            taints = [{"key": "tester", "value": "wx", "effect": "NoSchedule"}]
            # 获取节点列表中第一个节点的名称
            res = multi_cluster_steps.step_get_nodes(cluster_name)
            node_name = res.json()['items'][0]['metadata']['name']
            # 为节点设置污点
            multi_cluster_steps.step_ste_taints(cluster_name, node_name, taints)
            # 获取节点的污点信息
            r = multi_cluster_steps.step_get_node_detail_info(cluster_name, node_name)
            taints_actual = r.json()['spec']['taints']
            # 验证污点设置成功
            with pytest.assume:
                assert taints == taints_actual
            # 清空设置的污点
            multi_cluster_steps.step_ste_taints(cluster_name=cluster_name, node_name=node_name, taints=[])

    @allure.story("节点")
    @allure.title('为每个集群的某个节点添加标签')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_add_labels(self):
        for cluster_name in self.cluster_names:
            # 获取节点列表中第一个节点的名称
            res = multi_cluster_steps.step_get_nodes(cluster_name)
            node_name = res.json()['items'][0]['metadata']['name']
            # 获取节点的标签信息
            re = multi_cluster_steps.step_get_node_detail_info(cluster_name, node_name)
            labels_old = re.json()['metadata']['labels']  # 用于删除添加的标签
            labels = re.json()['metadata']['labels']  # 用于添加标签
            # 添加标签的内容
            labels['tester/label'] = 'wxx'
            # 添加标签
            multi_cluster_steps.step_add_labels_for_node(cluster_name, node_name, labels)
            # 获取编辑后节点的标签信息
            r = multi_cluster_steps.step_get_node_detail_info(cluster_name, node_name)
            labels_actual = r.json()['metadata']['labels']
            # 验证标签添加成功
            with pytest.assume:
                assert labels == labels_actual
            # 删除添加的标签
            labels_old['tester/label'] = None
            multi_cluster_steps.step_add_labels_for_node(cluster_name, node_name, labels_old)

    @allure.story('节点')
    @allure.title('设置每个集群的某个节点为停止调度, 然后设置为启用调度')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_set_uncordon_node(self):
        for cluster_name in self.cluster_names:
            # 获取节点列表中第一个节点的名称
            res = multi_cluster_steps.step_get_nodes(cluster_name)
            node_name = res.json()['items'][0]['metadata']['name']
            # 设置节点为停止调度
            multi_cluster_steps.step_cordon_node(cluster_name, node_name, True)
            # 获取节点的调度状态
            r = multi_cluster_steps.step_get_node_detail_info(cluster_name, node_name)
            cordon_status = r.json()['spec']['unschedulable']
            # 验证节点调度状态为停止调度
            with pytest.assume:
                assert cordon_status == True
            # 设置节点为启用调度
            multi_cluster_steps.step_cordon_node(cluster_name, node_name, False)

    @allure.story('节点')
    @allure.title('查看每个集群的某个节点的pod信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_pods(self):
        for cluster_name in self.cluster_names:
            # 获取节点列表中第一个节点的名称
            re = multi_cluster_steps.step_get_nodes(cluster_name)
            node_name = re.json()['items'][0]['metadata']['name']
            # 查看节点的pod信息
            r = multi_cluster_steps.step_get_pod_of_node(cluster_name, node_name)
            # 验证pod信息查询成功
            assert r.status_code == 200

    @allure.story('节点')
    @allure.title('查看每个集群的某个节点的event信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_events(self):
        for cluster_name in self.cluster_names:
            # 获取节点列表中第一个节点的名称
            re = multi_cluster_steps.step_get_nodes(cluster_name)
            node_name = re.json()['items'][0]['metadata']['name']
            # 查看节点的event信息
            r = multi_cluster_steps.step_get_event_of_node(cluster_name, node_name)
            # 获取资源类型
            kind = r.json()['kind']
            # 验证event信息查询成功
            assert kind == 'EventList'

    @allure.story('节点')
    @allure.title('查看每个集群的某个节点的监控信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_monitoring(self):
        for cluster_name in self.cluster_names:
            # 获取节点列表中第一个节点的名称
            re = multi_cluster_steps.step_get_nodes(cluster_name)
            node_name = re.json()['items'][0]['metadata']['name']
            # 获取当前时间的10位时间戳
            now_time = datetime.now()
            now_timestamp = str(datetime.timestamp(now_time))[0:10]
            # 获取10分钟之前的戳
            before_timestamp = commonFunction.get_before_timestamp(now_time, 10)
            # 查看最近十分钟的监控信息
            r = multi_cluster_steps.step_get_metrics_of_node(cluster_name=cluster_name, node_name=node_name,
                                                             start_time=before_timestamp,
                                                             end_time=now_timestamp,
                                                             step='60s', times='10')
            # 获取查询到的数据的结果类型
            result_type = r.json()['results'][0]['data']['resultType']
            # 验证查询到的数据的结果类型
            assert result_type == 'matrix'

    @allure.story('节点')
    @allure.title('查看某个集群的某个节点的状态信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_status(self):
        # 获取节点列表中第一个节点的名称
        re = multi_cluster_steps.step_get_nodes(self.cluster_any_name)
        node_name = re.json()['items'][0]['metadata']['name']
        # 获取当前时间的10位时间戳
        now_time = datetime.now()
        now_timestamp = str(datetime.timestamp(now_time))[0:10]
        # 获取20分钟之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp(now_time, 20)
        # 查看节点的状态信息
        r = multi_cluster_steps.step_get_status_of_node(cluster_name=self.cluster_any_name, node_name=node_name,
                                                        start_time=before_timestamp,
                                                        end_time=now_timestamp, step='180s', times='20')
        # 获取查询结果中的节点信息
        node = r.json()['results'][0]['data']['result'][0]['metric']['node']
        # 验证查询结果正确
        assert node == node_name

    @allure.story('节点')
    @allure.title('在某个集群中查询节点中不存在的pod')
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_non_existent_pod(self):
        # 获取节点列表中第一个节点的名称
        res = multi_cluster_steps.step_get_nodes(self.cluster_any_name)
        node_name = res.json()['items'][0]['metadata']['name']
        # 查询不存在的pod
        pod_name = 'non-existent'
        re = multi_cluster_steps.step_query_pod(self.cluster_any_name, node_name, pod_name)
        # 获取查询结果
        total_items = re.json()['totalItems']
        # 验证查询结果
        assert total_items == 0

    @allure.story('节点')
    @allure.title('按名称在某个集群中精确查询节点中存在的pod')
    @allure.severity(allure.severity_level.NORMAL)
    def test_precise_query_existent_pod(self):
        # 获取节点列表中第一个节点的名称
        res = multi_cluster_steps.step_get_nodes(self.cluster_any_name)
        node_name = res.json()['items'][0]['metadata']['name']
        # 获取节点的任意一个pod的名称
        re = multi_cluster_steps.step_get_pod_of_node(self.cluster_any_name, node_name)
        pod_name = re.json()['items'][0]['metadata']['name']
        # 按名称精确查询存在的pod
        r = multi_cluster_steps.step_query_pod(self.cluster_any_name, node_name, pod_name)
        # 获取查询到的pod名称
        name_actual = r.json()['items'][0]['metadata']['name']
        # 验证查询结果
        assert name_actual == pod_name

    @allure.story('节点')
    @allure.title('按名称在某个集群模糊查询节点中存在的pod')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_query_existent_pod(self):
        # 获取节点列表中第一个节点的名称
        res = multi_cluster_steps.step_get_nodes(self.cluster_any_name)
        node_name = res.json()['items'][0]['metadata']['name']
        # 获取节点的任意一个pod的名称
        re = multi_cluster_steps.step_get_pod_of_node(self.cluster_any_name, node_name)
        pod_name = re.json()['items'][0]['metadata']['name']
        # 按名称模糊查询存在的pod
        pod_fuzzy_name = pod_name[2:]
        r = multi_cluster_steps.step_query_pod(self.cluster_any_name, node_name, pod_fuzzy_name)
        # 获取查询到的pod名称
        name_actual = r.json()['items'][0]['metadata']['name']
        # 验证查询结果
        assert name_actual == pod_name

    @allure.story('边缘节点')
    @allure.title('在某个集群中查看边缘节点列表')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skipif(commonFunction.get_components_status_of_cluster('whizard') is False, reason='集群已未开启边缘节点功能')
    def test_get_edge_nodes(self):
        # 查看边缘节点列表
        re = multi_cluster_steps.step_get_edge_nodes(self.cluster_any_name)
        # 获取查询结果
        count = re.json()['totalItems']
        # 验证查询结果
        assert count >= 0

    @allure.story('边缘节点')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skipif(commonFunction.get_components_status_of_cluster('whizard') is False, reason='集群已未开启边缘节点功能')
    @pytest.mark.parametrize('ip, title, status_code',
                             [('10.10.10', '添加边缘节点时，校验ip地址格式-不符合格式的ip地址', '400'),
                              ('10.10.10.10', '添加边缘节点时，校验ip地址格式-符合格式的ip地址', '200')])
    def test_add_edge_node_with_invalid_ip(self, ip, title, status_code):
        # 添加边缘节点
        node_name = 'edge-node'
        re = multi_cluster_steps.step_check_internal_ip(self.cluster_any_name, node_name, ip)
        assert re.json()['code'] == int(status_code)

    @allure.story('边缘节点')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skipif(commonFunction.get_components_status_of_cluster('whizard') is False, reason='集群已未开启边缘节点功能')
    @pytest.mark.parametrize('add_default_taint, title, result',
                             [('true', '获取边缘节点配置命令-添加默认污点', True),
                              ('false', '获取边缘节点配置命令-不添加默认污点', False)])
    def test_get_edge_node_config_command(self, title, add_default_taint, result):
        # 添加边缘节点
        node_name = 'edge-node'
        ip = '10.10.10.10'
        re = multi_cluster_steps.step_get_edge_node_config_command(self.cluster_any_name, node_name, ip,
                                                                   add_default_taint)
        result_new = 'with-edge-taint' in re.json()['data']
        assert result_new == result

    @allure.story('项目')
    @allure.title('按名称在某个集群精确查询集群中不存在的系统项目')
    @allure.severity(allure.severity_level.NORMAL)
    def test_precise_non_existent_system_project(self):
        project_name = 'non-existent-project'
        # 查询指定的集群的系统项目
        re = multi_cluster_steps.step_query_system_project(self.cluster_any_name, project_name)
        # 获取查询结果
        items = re.json()['items']
        # 验证查询结果为空
        assert items == []

    @allure.story('项目')
    @allure.title('按名称在某个集群精确查询集群中存在的系统项目')
    @allure.severity(allure.severity_level.NORMAL)
    def test_precise_query_existent_system_project(self):
        # 获取集群任意系统项目的名称
        re = multi_cluster_steps.step_query_system_project(self.cluster_any_name, '')
        project_name = re.json()['items'][0]['metadata']['name']
        # 按名称精确查询系统项目
        r = multi_cluster_steps.step_query_system_project(self.cluster_any_name, project_name)
        # 获取查询结果
        project_name_actual = r.json()['items'][0]['metadata']['name']
        # 验证查询结果
        assert project_name_actual == project_name

    @allure.story('项目')
    @allure.title('按名称在某个集群模糊查询集群中存在的系统项目')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_query_existent_system_project(self):
        # 获取集群任意系统项目的名称
        re = multi_cluster_steps.step_query_system_project(self.cluster_any_name, '')
        project_name = re.json()['items'][0]['metadata']['name']
        # 按名称精确查询系统项目
        fuzzy_project_name = project_name[2:]
        r = multi_cluster_steps.step_query_system_project(self.cluster_any_name, fuzzy_project_name)
        # 获取查询结果
        project_name_actual = r.json()['items'][0]['metadata']['name']
        # 验证查询结果
        assert project_name_actual == project_name

    @allure.story('项目')
    @allure.title('查询某个集群中所有系统项目的详情信息,并验证其状态为活跃')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_check_system_project_state(self):
        # 获取集群中系统项目的数量
        re = multi_cluster_steps.step_query_system_project(self.cluster_any_name, '')
        project_count = re.json()['totalItems']
        # 获取集群系统项目的名称
        for j in range(0, project_count):
            project_name = re.json()['items'][j]['metadata']['name']
            # 查询项目的详细信息
            r = multi_cluster_steps.step_get_project_detail(self.cluster_any_name, project_name)
            # 获取项目的状态
            status = r.json()['status']['phase']
            # 验证项目运行状态为活跃
            assert status == 'Active'

    @allure.story('项目')
    @allure.title('查询某个集群中所有系统项目的配额信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_one_system_project_quota(self):
        # 获取集群中系统项目的数量
        re = multi_cluster_steps.step_query_system_project(self.cluster_any_name, '')
        project_count = re.json()['totalItems']
        for j in range(0, project_count):
            # 获取集群所有系统项目的名称
            project_name = re.json()['items'][j]['metadata']['name']
            # 查询项目的配额信息
            r = multi_cluster_steps.step_get_project_quota(self.cluster_any_name, project_name)
            # 获取项目的配额信息
            used = r.json()['data']['used']
            # 验证项目配额信息获取成功
            assert 'count/pods' in used

    @allure.story('项目')
    @allure.title('查询某个集群中所有系统项目的LimitRanges信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_one_system_project_detail(self):
        # 获取集群中系统项目的数量
        re = multi_cluster_steps.step_query_system_project(self.cluster_any_name, '')
        project_count = re.json()['totalItems']
        for j in range(0, project_count):
            # 获取集群系统项目的名称
            project_name = re.json()['items'][j]['metadata']['name']
            # 查询项目的LimitRanges
            r = multi_cluster_steps.step_get_project_limit_ranges(self.cluster_any_name, project_name)
            # 获取请求资源的kind
            kind = r.json()['kind']
            # 验证请求资源的kind为LimitRangeList
            assert kind == 'LimitRangeList'

    @allure.story('项目')
    @allure.title('查询某个集群中任一系统项目的工作负载信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_system_project_workload(self):
        # 获取集群中系统项目的数量
        res = multi_cluster_steps.step_query_system_project(self.cluster_any_name, '')
        project_count = res.json()['totalItems']
        j = random.randint(0, project_count - 1)
        # 获取集群任意系统项目的名称
        re = multi_cluster_steps.step_query_system_project(self.cluster_any_name, '')
        project_name = re.json()['items'][j]['metadata']['name']
        # 查询项目的工作负载信息
        r = multi_cluster_steps.step_get_project_workload(self.cluster_any_name, project_name)
        # 获取接口的响应数据
        data = r.json()['data']
        # 验证接口响应数据正确
        data_except = ['daemonsets', 'deployments', 'jobs', 'persistentvolumeclaims', 'statefulsets']
        assert data_except[random.randint(0, 4)] in data

    @allure.story('项目')
    @allure.title('查看某个集群中所有系统项目的pod运行情况')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_check_system_project_pods(self):
        res = multi_cluster_steps.step_query_system_project(self.cluster_any_name, '')
        project_count = res.json()['totalItems']
        # 获取集群中所有系统项目的名称
        for j in range(0, project_count):
            project_name = res.json()['items'][j]['metadata']['name']
            # 查询项目的pods信息
            r = multi_cluster_steps.step_get_pods_of_project(cluster_name=self.cluster_any_name,
                                                             project_name=project_name)
            # 获取pod的数量
            pod_count = r.json()['totalItems']
            # 获取所有pod的状态
            for k in range(0, pod_count):
                state = r.json()['items'][k]['status']['phase']
                # 获取pod的名称
                pod_name = r.json()['items'][k]['metadata']['name']
                if state not in ['Running', 'Succeeded']:
                    print(
                        '集群：' + self.cluster_any_name + ' 项目：' + project_name + ' 容器组：' + pod_name + ' 状态不正常')
                else:
                    # 验证pod的运行状态
                    assert state in ['Running', 'Succeeded']

    @allure.story('项目')
    @allure.title('在某个集群中使用名称精确查询项目中存在的pod')
    @allure.severity(allure.severity_level.NORMAL)
    def test_precise_query_existent_pod_of_project(self):
        # 用于存放pod的名称
        pod_names = []
        # 获取集群中任一系统项目的名称
        res = multi_cluster_steps.step_query_system_project(self.cluster_any_name, '')
        project_count = res.json()['totalItems']
        j = random.randint(0, project_count - 1)
        project_name = res.json()['items'][j]['metadata']['name']
        # 查询项目的所有的pod信息
        re = multi_cluster_steps.step_get_pods_of_project(cluster_name=self.cluster_any_name, project_name=project_name)
        # 获取pod的数量
        pod_count = re.json()['totalItems']
        # 获取项目所有的pod的名称
        if pod_count > 0:
            for k in range(0, pod_count):
                name = re.json()['items'][k]['metadata']['name']
                pod_names.append(name)
            # 使用pod的名称，精确查询存在的pod
            r = multi_cluster_steps.step_get_pods_of_project(self.cluster_any_name, project_name,
                                                             'name=' + pod_names[0])
            # 获取查询结果中pod名称
            pod_name_actual = r.json()['items'][0]['metadata']['name']
            # 验证查询结果正确
            assert pod_name_actual == pod_names[0]
        else:
            print('项目：' + project_name + ' 不存在pod')

    @allure.story('项目')
    @allure.title('在某个集群中使用名称模糊查询项目中存在的pod')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_query_existent_pod_of_project(self):
        # 用于存放pod的名称
        pod_names = []
        # 获取集群中任一系统项目的名称
        res = multi_cluster_steps.step_query_system_project(self.cluster_any_name, '')
        project_count = res.json()['totalItems']
        j = random.randint(0, project_count - 1)
        project_name = res.json()['items'][j]['metadata']['name']
        # 查询项目的所有的pod信息
        re = multi_cluster_steps.step_get_pods_of_project(cluster_name=self.cluster_any_name, project_name=project_name)
        # 获取pod的数量
        pod_count = re.json()['totalItems']
        # 获取项目所有的pod的名称
        if pod_count > 0:
            for k in range(0, pod_count):
                name = re.json()['items'][k]['metadata']['name']
                pod_names.append(name)
            # 使用pod的名称，精确查询存在的pod
            r = multi_cluster_steps.step_get_pods_of_project(self.cluster_any_name, project_name,
                                                             'name=' + pod_names[0][2:])
            # 获取查询结果中pod名称
            pod_name_actual = r.json()['items'][0]['metadata']['name']
            # 验证查询结果正确
            assert pod_name_actual == pod_names[0]
        else:
            print('项目：' + project_name + ' 不存在pod')

    @allure.story('项目')
    @allure.title('在某个集群中使用名称查询项目中不存在的pod')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_query_existent_pod_of_project(self):
        # 获取集群中任一系统项目的名称
        re = multi_cluster_steps.step_query_system_project(self.cluster_any_name, '')
        project_name = re.json()['items'][3]['metadata']['name']
        # 使用pod的名称，模糊查询存在的pod
        pod_name = 'test' + str(commonFunction.get_random())
        r = multi_cluster_steps.step_get_pods_of_project(self.cluster_any_name, project_name, 'name=' + pod_name)
        # 获取查询结果中的pod数量
        pod_count = r.json()['totalItems']
        # 验证查询结果正确
        assert pod_count == 0

    @allure.story('项目')
    @allure.title('在某个集群中创建用户项目，并验证项目创建成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_user_system(self):
        project_name = 'user-project' + str(commonFunction.get_random())
        alias_name = 'test'
        description = 'create user-system'
        # 创建用户项目
        multi_cluster_steps.step_create_user_project(self.cluster_any_name, project_name, alias_name, description)
        # 查询创建的项目，并获取其运行状态
        r = multi_cluster_steps.step_get_user_system(self.cluster_any_name, project_name)
        state = r.json()['status']['phase']
        # 验证项目的状态为active
        with pytest.assume:
            assert state == 'Active'
        # 删除创建的项目
        multi_cluster_steps.step_delete_user_system(self.cluster_any_name, project_name)

    @allure.story('项目')
    @allure.title('在每个集群删除用户项目，并验证删除成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_user_system(self):
        status = ''
        project_name = 'user-project' + str(commonFunction.get_random())
        alias_name = 'test'
        description = 'create user-system'
        # 创建用户项目
        multi_cluster_steps.step_create_user_project(self.cluster_any_name, project_name, alias_name, description)
        # 删除用户项目
        re = multi_cluster_steps.step_delete_user_system(self.cluster_any_name, project_name)
        # 获取删除项目的状态
        state = re.json()['status']['phase']
        # 验证删除项目的状态为Terminating
        with pytest.assume:
            assert state == 'Terminating'
        # 等待项目删除成功
        i = 0
        while i < 60:
            # 查询被删除的项目并获取查询结果
            r = multi_cluster_steps.step_get_user_system(self.cluster_any_name, project_name)
            status = r.json()['status']
            if status == {'phase': 'Terminating'}:
                time.sleep(1)
                i += 1
            else:
                break
        # 验证项目删除成功
        assert status == 'Failure'

    @allure.story('应用负载')
    @allure.title('在某个集群查看集群所有的deployments，并验证其运行正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_check_deployments_of_cluster(self):
        # 查询集群所有的deployments
        re = multi_cluster_steps.step_get_resource_of_cluster(self.cluster_any_name, 'deployments')
        # 获取集群deployments的数量
        count = re.json()['totalItems']
        # 获取集群所有的系统项目名称
        system_ns = project_steps.step_get_system_project(self.cluster_any_name)
        # 获取集群所有的deployments的状态
        for j in range(0, count):
            # 获取每个deployment的namespace
            ns = re.json()['items'][j]['metadata']['namespace']
            if ns in system_ns:
                state = re.json()['items'][j]['status']['conditions'][0]['status']
                # 验证deployment的状态为True
                assert state == 'True'
            else:
                break

    @allure.story('应用负载')
    @allure.title('查看某个集群所有的deployments的Revision Records')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_check_deployments_revision_records(self):
        # 查询集群所有的deployments
        re = multi_cluster_steps.step_get_resource_of_cluster(self.cluster_any_name, 'deployments')
        # 获取集群deployments的数量
        count = re.json()['totalItems']
        # 获取集群所有的deployments的labels
        for j in range(0, count):
            label_selector = ''
            project_name = re.json()['items'][j]['metadata']['namespace']
            labels = re.json()['items'][j]['spec']['selector']['matchLabels']
            # 将labels的key和value拼接为label_selector
            keys = list(labels.keys())
            values = list(labels.values())
            for k in range(0, len(keys)):
                label_selector += keys[k] + '=' + values[k] + ','
            # 去掉最后的逗号
            label_selector = label_selector[:-1]
            # 查看deployments的revision records信息
            r = multi_cluster_steps.step_get_deployment_revision_records(project_name, label_selector)
            # 获取请求的资源类型
            kind = r.json()['kind']
            # 验证请求的资源类型为ReplicaSetList
            assert kind == 'ReplicaSetList'

    @allure.story('应用负载')
    @allure.title('查看某个集群所有的statefulSets，并验证其运行正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_check_statefulsets_of_cluster(self):
        # 查询集群所有的statefulSets
        re = multi_cluster_steps.step_get_resource_of_cluster(self.cluster_any_name, 'statefulsets')
        # 获取集群所有的系统项目名称
        system_ns = project_steps.step_get_system_project(self.cluster_any_name)
        # 获取集群statefulSets的数量
        count = re.json()['totalItems']
        # 获取集群所有的statefulSets的副本数和ready的副本数
        for j in range(0, count):
            # 获取每个statefulSets的namespace
            ns = re.json()['items'][j]['metadata']['namespace']
            if ns in system_ns:
                replica = re.json()['items'][j]['status']['replicas']
                ready_replicas = re.json()['items'][j]['status']['readyReplicas']
                # 验证每个statefulSets的ready的副本数=副本数
                assert replica == ready_replicas
            else:
                break

    @allure.story('应用负载')
    @allure.title('查看某个集群所有的daemonSets，并验证其运行正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_check_daemonsets_of_cluster(self):
        # 查询集群所有的daemonSets
        re = multi_cluster_steps.step_get_resource_of_cluster(self.cluster_any_name, 'daemonsets')
        # 获取集群daemonSets的数量
        count = re.json()['totalItems']
        # 获取集群所有的daemonSets的current_number_scheduled和desired_number_scheduled
        for j in range(0, count):
            current_number_scheduled = re.json()['items'][j]['status']['currentNumberScheduled']
            desired_number_scheduled = re.json()['items'][j]['status']['desiredNumberScheduled']
            # 验证每个daemonSets的current_number_scheduled=desired_number_scheduled
            assert current_number_scheduled == desired_number_scheduled

    @allure.story('应用负载')
    @allure.title('查看某个集群所有的daemonSets的详情信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_check_daemonsets_detail_of_cluster(self):
        # 查询集群所有的daemonSets
        re = multi_cluster_steps.step_get_resource_of_cluster(self.cluster_any_name, 'daemonsets')
        # 获取集群daemonSets的数量
        count = re.json()['totalItems']
        # 获取集群中所有的daemonSets的名称和所在的项目名称
        for j in range(0, count):
            resource_name = re.json()['items'][j]['metadata']['name']
            project_name = re.json()['items'][j]['metadata']['namespace']
            # 查询daemonSets的详细信息
            r = multi_cluster_steps.step_get_app_workload_detail(self.cluster_any_name, project_name, 'daemonsets',
                                                                 resource_name)
            # 验证信息查询成功
            assert r.json()['kind'] == 'DaemonSet'

    @allure.story('应用负载')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('type, title',
                             [('statefulsets', '查看某个集群所有的statefulSets的Revision Records'),
                              ('daemonsets', '查看某个集群所有的daemonSets的Revision Records')])
    def test_check_app_workload_revision_records(self, type, title):
        # 查询集群所有的daemonSets
        label_selector = ''
        res = multi_cluster_steps.step_get_resource_of_cluster(cluster_name=self.cluster_any_name, resource_type=type)
        # 获取集群daemonSets的数量
        count = res.json()['totalItems']
        # 获取所有的daemonSets的label、project_name和daemonSets的名称
        for j in range(0, count):
            labels = res.json()['items'][j]['metadata']['labels']
            # 将labels的key和value拼接为label_selector
            keys = list(labels.keys())
            values = list(labels.values())
            for k in range(0, len(keys)):
                label_selector = ''
                label_selector += keys[k] + '=' + values[k] + ','
            # 去掉最后的逗号
            label_selector = label_selector[:-1]
            # 获取daemonSets的名称和所在的项目名称
            project_name = res.json()['items'][j]['metadata']['namespace']
            # 查看daemonSets的revision Records 信息
            r = multi_cluster_steps.step_get_app_workload_revision_records(self.cluster_any_name, project_name,
                                                                           label_selector)
            # 获取请求的资源类型
            kind = r.json()['kind']
            # 验证请求的资源类型为ControllerRevisionList
            assert kind == 'ControllerRevisionList'

    @allure.story('应用负载')
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title('{title}')
    @pytest.mark.parametrize('type, title',
                             [('deployments', '查看某个集群所有的deployments的Monitoring'),
                              ('statefulsets', '查看某个集群所有的statefulSets的Monitoring'),
                              ('daemonsets', '查看某个集群所有的daemonSets的Monitoring'),
                              ('pods', '查看某个集群所有pod的Monitoring'),
                              ('services', '查看某个集群所有service的Monitoring')])
    def test_check_app_workload_monitoring(self, type, title):
        # 查询集群所有的对应类型的资源
        re = multi_cluster_steps.step_get_resource_of_cluster(self.cluster_any_name, type)
        # 获取集群daemonSets的数量
        count = re.json()['totalItems']
        # 获取任一对应类型资源的project_name和资源的名称
        if count > 0:
            j = random.randint(0, count - 1)
            project_name = re.json()['items'][j]['metadata']['namespace']
            resource_name = re.json()['items'][j]['metadata']['name']
            # 查看监控信息
            r = multi_cluster_steps.step_get_app_workload_monitoring(self.cluster_any_name, project_name, type,
                                                                     resource_name)
            # 获取请求结果中监控数据的类型
            result_type = r.json()['results'][0]['data']['resultType']
            # 验证请求结果中监控数据的类型为vector
            assert result_type == 'vector'
        else:
            print('无' + type)

    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('story, type, title',
                             [('应用负载', 'deployments', '查看每个集群所有的deployments的event'),
                              ('应用负载', 'statefulsets', '查看每个集群所有的statefulSets的event'),
                              ('应用负载', 'daemonsets', '查看每个集群所有的daemonSets的event'),
                              ('应用负载', 'pods', '查看每个集群所有pod的event'),
                              ('应用负载', 'services', '查看每个集群所有service的event'),
                              ('存储', 'persistentvolumeclaims', '查看每个集群所有pvc的event')
                              ])
    def test_check_app_workload_event(self, story, type, title):
        allure.dynamic.story(story)
        # 获取多集群环境的集群信息
        response = multi_cluster_steps.step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询集群所有的资源
            re = multi_cluster_steps.step_get_resource_of_cluster(cluster_name, type)
            # 获取集群某一资源的数量
            count = re.json()['totalItems']
            # 获取某一资源任意的project_name,资源的名称和uid
            if count > 0:
                j = random.randint(0, count - 1)
                project_name = re.json()['items'][j]['metadata']['namespace']
                resource_name = re.json()['items'][j]['metadata']['name']
                resource_uid = response.json()['items'][i]['metadata']['uid']
                # 查询daemonSets的event信息
                r = multi_cluster_steps.step_get_resource_event(cluster_name, project_name, type, resource_name,
                                                                resource_uid)
                # 获取请求结果的类型
                kind = r.json()['kind']
                # 验证请求结果的类型为EventList
                assert kind == 'EventList'
            else:
                print('无' + type)

    @allure.story('应用负载')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('type, title',
                             [('deployments', '在某个集群按名称精确查询存在的deployments'),
                              ('statefulsets', '在某个集群按名称精确查询存在的statefulSets'),
                              ('daemonsets', '在某个集群按名称精确查询存在的daemonSets'),
                              ('pods', '在某个集群按名称模糊查询存在的pod'),
                              ('services', '在某个按名称模糊查询存在的service')])
    def test_precise_query_app_workload_by_name(self, type, title):
        # 获取集群中存在的资源的名称
        re = multi_cluster_steps.step_get_resource_of_cluster(self.cluster_any_name, type)
        # 获取第一个资源的名称
        name = re.json()['items'][0]['metadata']['name']
        r = multi_cluster_steps.step_get_resource_of_cluster(self.cluster_any_name, type, 'name=' + name)
        # 获取查询结果的名称
        name_actual = r.json()['items'][0]['metadata']['name']
        # 验证查询结果正确
        assert name == name_actual

    @allure.story('应用负载')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('type, title',
                             [('deployments', '在某个集群按名称模糊查询存在的deployments'),
                              ('statefulsets', '在某个集群按名称模糊查询存在的statefulSets'),
                              ('daemonsets', '在某个集群按名称模糊查询存在的daemonSets'),
                              ('pods', '在某个集群按名称模糊查询存在的pod'),
                              ('services', '在某个集群按名称模糊查询存在的service')
                              ])
    def test_fuzzy_query_app_workload_by_name(self, type, title):
        # 获取集群中存在的资源的名称
        re = multi_cluster_steps.step_get_resource_of_cluster(self.cluster_any_name, type)
        count = re.json()['totalItems']
        if count > 0:
            # 获取第任一资源的名称
            i = random.randint(0, count - 1)
            name = re.json()['items'][i]['metadata']['name']
            r = multi_cluster_steps.step_get_resource_of_cluster(self.cluster_any_name, type, 'name=' + name[1:])
            # 获取查询结果的名称
            name_actual = r.json()['items'][0]['metadata']['name']
            # 验证查询结果正确
            assert name in name_actual
        else:
            print('无' + type)

    @allure.story('应用负载')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('type, title',
                             [('deployments', '在某个集群按状态查询存在的deployments'),
                              ('statefulsets', '在某个集群按状态查询存在的statefulSets'),
                              ('daemonsets', '在某个集群按状态查询存在的daemonSets')])
    def test_query_app_workload_by_status(self, type, title):
        # 查询状态为running的资源
        r = multi_cluster_steps.step_get_resource_of_cluster(self.cluster_any_name, type, 'status=running')
        # 获取资源的数量
        count = r.json()['totalItems']
        # 获取资源的ready_replicas和replicas
        for j in range(0, count):
            if type == 'daemonsets':
                ready_replicas = r.json()['items'][j]['status']['numberReady']
                replicas = r.json()['items'][j]['status']['numberAvailable']
            else:
                ready_replicas = r.json()['items'][j]['status']['readyReplicas']
                replicas = r.json()['items'][j]['status']['replicas']
            # 验证ready_replicas=replicas，从而判断资源的状态为running
            assert ready_replicas == replicas

    @allure.story('应用负载')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('type, title',
                             [('deployments', '在某个集群按状态和名称查询存在的deployments'),
                              ('statefulsets', '在某个集群按状态和名称查询存在的statefulSets'),
                              ('daemonsets', '在某个集群按状态和名称查询存在的daemonSets')])
    def test_query_app_workload_by_status_and_name(self, type, title):
        # 查询集群中所有的资源
        re = multi_cluster_steps.step_get_resource_of_cluster(self.cluster_any_name, type)
        # 获取资源的数量
        count = re.json()['totalItems']
        if count > 0:
            running_resource = []
            try:
                for j in range(0, count):
                    if type == 'daemonsets':
                        ready_replicas = re.json()['items'][j]['status']['numberReady']
                        replicas = re.json()['items'][j]['status']['numberAvailable']
                    else:
                        ready_replicas = re.json()['items'][j]['status']['readyReplicas']
                        replicas = re.json()['items'][j]['status']['replicas']
                    # 判断资源状态为运行中
                    if ready_replicas == replicas:
                        running_resource.append(re.json()['items'][j]['metadata']['name'])
                # 使用名称和状态查询资源
                for name in running_resource:
                    r = multi_cluster_steps.step_get_resource_of_cluster(self.cluster_any_name, type, 'name=' + name,
                                                                         'status=running')
                    # 获取查询结果中的name
                    name_actual = r.json()['items'][0]['metadata']['name']
                    # 验证查询的结果正确
                    assert name == name_actual
            except Exception as e:
                print(e)
        else:
            print('无' + type)

    @allure.story('应用负载')
    @allure.title('获取每个集群所有的容器组，并验证其数量与从项目管理中获取的数量一致')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_pods_of_cluster(self):
        # 获取集群的容器组的数量
        res = multi_cluster_steps.step_get_pods_of_cluster(self.cluster_any_name)
        count = res.json()['totalItems']
        # 从项目管理处获取所有项目的名称
        project_name = []
        re = multi_cluster_steps.step_get_project_of_cluster(self.cluster_any_name)
        project_count = re.json()['totalItems']
        for j in range(0, project_count):
            name = re.json()['items'][j]['metadata']['name']
            project_name.append(name)
        # 获取每个项目的pod数量,并将其加和
        pod_counts = 0
        for project in project_name:
            r = multi_cluster_steps.step_get_pods_of_project(self.cluster_any_name, project)
            pod_count = r.json()['totalItems']
            pod_counts += pod_count
        # 验证集群的容器数量等于每个项目的容器数之和
        assert count == pod_counts

    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('story, type, title',
                             [('配置中心', 'secrets', '在某个集群按名称精确查询存在的密钥'),
                              ('配置中心', 'configmaps', '在某个集群按名称精确查询存在的配置'),
                              ('配置中心', 'serviceaccounts', '在某个集群按名称精确查询存在的服务账号'),
                              ('CRDs', 'customresourcedefinitions', '在某个集群按名称精确查询存在的CRD'),
                              ('存储', 'persistentvolumeclaims', '在某个集群按名称精确查询存在的存储卷'),
                              ('存储', 'storageclasses', '在某个集群按名称精确查询存在的存储类型')
                              ])
    def test_precise_query_resource_by_name(self, story, type, title):
        allure.dynamic.story(story)
        # 获取集群中存在的任一资源的名称
        re = multi_cluster_steps.step_get_resource_of_cluster(cluster_name=self.cluster_any_name, resource_type=type)
        count = re.json()['totalItems']
        name = re.json()['items'][random.randint(0, count - 1)]['metadata']['name']
        # 按名称精确查询存在的资源
        r = multi_cluster_steps.step_get_resource_of_cluster(self.cluster_any_name, type, 'name=' + name)
        name_actual = r.json()['items'][0]['metadata']['name']
        # 验证查询结果正确
        assert name in name_actual

    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('story, type, title',
                             [('配置中心', 'secrets', '在某个集群按名称模糊查询存在的密钥'),
                              ('配置中心', 'configmaps', '在某个集群按名称模糊查询存在的配置'),
                              ('配置中心', 'serviceaccounts', '在某个集群按名称模糊查询存在的服务账号'),
                              ('CRDs', 'customresourcedefinitions', '在某个集群按名称模糊查询存在的CRD'),
                              ('存储', 'persistentvolumeclaims', '在某个集群按名称模糊查询存在的存储卷'),
                              ('存储', 'storageclasses', '在某个集群按名称模糊查询存在的存储类型')
                              ])
    def test_fuzzy_query_resource_by_name(self, story, type, title):
        allure.dynamic.story(story)
        # 查看集群中的某一种资源
        re = multi_cluster_steps.step_get_resource_of_cluster(self.cluster_any_name, resource_type=type)
        # 获取集群中某一种资源的数量
        count = re.json()['totalItems']
        # 获取集群中存在的任一资源的名称
        name = re.json()['items'][random.randint(0, count - 1)]['metadata']['name']
        fuzzy_name = name[1:]
        # 按名称精确查询存在的资源
        r = multi_cluster_steps.step_get_resource_of_cluster(self.cluster_any_name, type, 'name=' + fuzzy_name)
        # 获取结果数量
        count_actual = r.json()['totalItems']
        # 获取结果中的名称
        name_actual = []
        for i in range(0, count_actual):
            name_actual.append(r.json()['items'][i]['metadata']['name'])
        # 验证查询结果正确
        assert name in name_actual

    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('story, type, title',
                             [('配置中心', 'secrets', '在某个集群按项目查询存在的密钥'),
                              ('配置中心', 'configmaps', '在某个集群按项目查询存在的配置'),
                              ('配置中心', 'serviceaccounts', '在某个集群按项目查询存在的服务账号'),
                              ('存储', 'persistentvolumeclaims', '在某个集群按项目查询存在的存储卷')
                              ])
    def test_query_configuration_by_project(self, story, type, title):
        allure.dynamic.story(story)
        # 查询项目为kube-system的所有资源
        r = multi_cluster_steps.step_get_resource_of_cluster_by_project(cluster_name=self.cluster_any_name, type=type,
                                                                        project_name='kubesphere-system')
        # 获取资源数量
        count = r.json()['totalItems']
        # 遍历所有资源，验证资源的项目为kubesphere-system
        for j in range(0, count):
            project = r.json()['items'][j]['metadata']['namespace']
            assert project == 'kubesphere-system'

    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('story, type, title',
                             [('配置中心', 'secrets', '在某个集群按项目和名称查询存在的密钥'),
                              ('配置中心', 'configmaps', '在某个集群按项目和名称查询存在的配置'),
                              ('配置中心', 'serviceaccounts', '在某个集群按项目和名称查询存在的服务账号'),
                              ('存储', 'persistentvolumeclaims', '在某个集群按项目和名称查询存在的存储卷')
                              ])
    def test_query_configuration_by_project_and_name(self, story, type, title):
        allure.dynamic.story(story)
        # 查询项目为kube-system的所有资源
        if type == 'persistentvolumeclaims':
            re = multi_cluster_steps.step_get_resource_of_cluster_by_project(cluster_name=self.cluster_any_name,
                                                                             type=type,
                                                                             project_name='kubesphere-monitoring-system')
            # 获取任一资源的名称
            name = re.json()['items'][0]['metadata']['name']
            # 按项目和名称查询资源
            r = multi_cluster_steps.step_get_resource_of_cluster_by_project(self.cluster_any_name, type,
                                                                            'kubesphere-monitoring-system',
                                                                            'name=' + name)
            # 在查询结果中获取资源名称
            name_actual = r.json()['items'][0]['metadata']['name']
        else:
            re = multi_cluster_steps.step_get_resource_of_cluster_by_project(cluster_name=self.cluster_any_name,
                                                                             type=type,
                                                                             project_name='kubesphere-system')
            # 获取资源数量
            count = re.json()['totalItems']
            # 获取任一资源的名称
            name = re.json()['items'][random.randint(0, count - 1)]['metadata']['name']
            # 按项目和名称查询资源
            r = multi_cluster_steps.step_get_resource_of_cluster_by_project(self.cluster_any_name, type,
                                                                            'kubesphere-system',
                                                                            'name=' + name)
            # 在查询结果中获取资源名称
            name_actual = r.json()['items'][0]['metadata']['name']
        # 验证查询结果正确
        assert name in name_actual

    @allure.story('CRDs')
    @allure.title('在某个集群查询任一CRD的详情信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_crd_detail(self):
        # 查询集群中的crd
        re = multi_cluster_steps.step_get_resource_of_cluster(cluster_name=self.cluster_any_name,
                                                              resource_type='customresourcedefinitions')
        # 获取crd的数量
        count = re.json()['totalItems']
        # 获取crd的名称
        j = random.randint(0, count - 1)
        name = re.json()['items'][j]['metadata']['name']
        # 查询CRD的详情信息
        r = multi_cluster_steps.step_get_crd_detail(self.cluster_any_name, name)
        # 获取查询结果中的kind
        kind = r.json()['kind']
        # 验证查询结果正确
        assert kind == 'CustomResourceDefinition'

    @allure.story('CRDs')
    @allure.title('在某个集群查询任一CRD的FederatedGroupList')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_crd_federated_group_list(self):
        # 查询集群中的crd
        res = multi_cluster_steps.step_get_resource_of_cluster(cluster_name=self.cluster_any_name,
                                                               resource_type='customresourcedefinitions')
        # 获取crd的数量
        count = res.json()['totalItems']
        # 获取任一crd的group和kind
        j = random.randint(0, count - 1)
        # 获取crd的名称
        name = res.json()['items'][j]['metadata']['name']
        # 获取crd的group,version和kind
        re = multi_cluster_steps.step_get_crd_detail(self.cluster_any_name, name)
        group = re.json()['spec']['group']
        version = re.json()['spec']['versions'][0]['name']
        kind = res.json()['items'][j]['spec']['names']['kind']
        # 查询crd的FederatedGroupList信息
        r = multi_cluster_steps.step_get_crd_federated_group_list(self.cluster_any_name, group, version, kind.lower())
        # 验证查询结果正确
        assert r.status_code == 200

    @allure.story('存储')
    @allure.title('在某个集群按状态查询存储卷，并验证查询结果正确')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_pvc_by_status(self):
        # 查询状态为bound的存储卷
        r = multi_cluster_steps.step_get_resource_of_cluster(self.cluster_any_name, 'persistentvolumeclaims',
                                                             'status=bound')
        # 获取存储卷数量
        count = r.json()['totalItems']
        # 获取并验证所有存储卷的状态为Bound
        for j in range(0, count):
            status = r.json()['items'][j]['status']['phase']
            assert status == 'Bound'

    @allure.story('存储')
    @allure.title('在某个集群查询每一个存储卷的详情信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_pvc_detail(self):
        # 查询集群的存储卷
        re = multi_cluster_steps.step_get_resource_of_cluster(self.cluster_any_name, 'persistentvolumeclaims')
        # 获取存储卷的数量
        count = re.json()['totalItems']
        if count > 0:
            # 获取任一存储卷的名称和所在namespace
            j = random.randint(0, count)
            name = re.json()['items'][j]['metadata']['name']
            namespace = re.json()['items'][j]['metadata']['namespace']
            # 查询存储卷的详情信息
            r = multi_cluster_steps.step_get_pvc_detail(self.cluster_any_name, namespace, name)
            # 获取查询结果的kind
            kind = r.json()['kind']
            # 验证查询结果正确
            assert kind == 'PersistentVolumeClaim'
        else:
            print('无存储卷')

    @allure.story('存储')
    @allure.title('在某个集群查询每一个存储卷的监控信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_pvc_metrics(self):
        # 查询集群存在的存储卷信息
        re = multi_cluster_steps.step_get_resource_of_cluster(self.cluster_any_name, 'persistentvolumeclaims')
        # 获取存储卷的数量
        count = re.json()['totalItems']
        # 获取所有存储卷的名称和所在namespace
        for j in range(0, count):
            name = re.json()['items'][j]['metadata']['name']
            namespace = re.json()['items'][j]['metadata']['namespace']
            # 获取当前时间的10位时间戳
            now_time = datetime.now()
            now_timestamp = str(datetime.timestamp(now_time))[0:10]
            # 获取60分钟之前的时间时间戳
            before_timestamp = commonFunction.get_before_timestamp(now_time, 60)
            # 查询每个pvc最近1个小时的监控信息
            r = multi_cluster_steps.step_get_metrics_of_pvc(self.cluster_any_name, namespace, name, before_timestamp,
                                                            now_timestamp, '60s', '60')
            # 获取查询到的数据的结果类型
            result_type = r.json()['results'][0]['data']['resultType']
            # 验证查询到的数据的结果类型
            assert result_type == 'matrix'

    @allure.story('存储')
    @allure.title('在某个集群查询每一个存储卷的pod信息')
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_pvc_pods(self):
        # 查询集群存在的存储卷信息
        re = multi_cluster_steps.step_get_resource_of_cluster(self.cluster_any_name, 'persistentvolumeclaims')
        # 获取存储卷的数量
        count = re.json()['totalItems']
        # 获取所有存储卷的名称和所在namespace
        for j in range(0, count):
            name = re.json()['items'][j]['metadata']['name']
            namespace = re.json()['items'][j]['metadata']['namespace']
            # 查询存储卷的pod信息
            r = multi_cluster_steps.step_get_pods_of_project(self.cluster_any_name, namespace, 'pvcName=' + name)
            # 获取pod的数量
            count_pod = r.json()['totalItems']
            if count_pod > 0:
                # 获取所有pod的运行状态
                for k in range(0, count_pod):
                    status = r.json()['items'][k]['status']['phase']
                    # 验证pod状态获取成功
                    assert status
            else:
                print('存储卷：' + name + '未绑定pod')

    @allure.story('存储')
    @allure.title('在某个集群查看所有存储卷的快照信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_pvc_snapshot(self):
        # 查询集群存在的存储卷信息
        re = multi_cluster_steps.step_get_resource_of_cluster(self.cluster_any_name, 'persistentvolumeclaims')
        # 获取存储卷的数量
        count = re.json()['totalItems']
        # 获取所有存储卷的名称和所在namespace
        for j in range(0, count):
            name = re.json()['items'][j]['metadata']['name']
            namespace = re.json()['items'][j]['metadata']['namespace']
            # 查询每个pvc的快照信息
            r = multi_cluster_steps.step_get_resource_of_cluster_by_project(self.cluster_any_name, 'volumesnapshots',
                                                                            namespace,
                                                                            'persistentVolumeClaimName=' + name)
            # 验证查询成功
            assert r.status_code == 200

    @allure.story('存储')
    @allure.title('在某个集群查询存储类型的详细信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_storage_class_detail(self):
        # 查询集群存在的存储类型
        re = multi_cluster_steps.step_get_resource_of_cluster(self.cluster_any_name, 'storageclasses')
        # 获取存储类型的数量
        count = re.json()['totalItems']
        # 获取所有的存储类型的名称
        for j in range(0, count):
            name = re.json()['items'][j]['metadata']['name']
            # 查询每个存储类型的详情信息
            r = multi_cluster_steps.step_get_storage_class_detail(self.cluster_any_name, name)
            # 获取详情信息中的kind
            kind = r.json()['kind']
            # 验证查询结果正确
            assert kind == 'StorageClass'

    @allure.story('存储')
    @allure.title('在某个集群将存储类型设置为默认的存储类型')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_set_default_storage_class(self):
        # 查询集群存在的存储类型
        re = multi_cluster_steps.step_get_resource_of_cluster(self.cluster_any_name, 'storageclasses')
        # 获取存储类型的数量
        count = re.json()['totalItems']
        # 获取任一存储类型的名称
        name = re.json()['items'][random.randint(0, count - 1)]['metadata']['name']
        # 将任一存储类型设置为非默认存储类型
        r = multi_cluster_steps.step_set_default_storage_class(self.cluster_any_name, name, 'false')
        # 获取请求结果中的storageclass.kubernetes.io/is-default-class
        result = r.json()['metadata']['annotations']['storageclass.kubernetes.io/is-default-class']
        # 验证结果为false
        with pytest.assume:
            assert result == 'false'
        # 将任一存储类型设置为默认存储类型
        r = multi_cluster_steps.step_set_default_storage_class(self.cluster_any_name, name, 'true')
        # 获取请求结果中的storageclass.kubernetes.io/is-default-class
        result = r.json()['metadata']['annotations']['storageclass.kubernetes.io/is-default-class']
        # 验证结果为true
        assert result == 'true'

    @allure.story('监控告警/集群状态')
    @allure.title('在某个集群查看组件的运行状态并验证组件均健康运行')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_component_health(self):
        # 获取组件的健康状况
        r = multi_cluster_steps.step_get_component_health(self.cluster_any_name)
        # 获取组件的数量
        component_count = len(r.json()['kubesphereStatus'])
        for j in range(0, component_count):
            # 获取每个组件的total_backends
            total_backends = r.json()['kubesphereStatus'][j]['totalBackends']
            # 获取每个组件的healthyBackends
            healthy_backends = r.json()['kubesphereStatus'][j]['healthyBackends']
            # 获取组件的名称
            component_name = r.json()['kubesphereStatus'][j]['name']
            # 验证 total_backends=healthy_backends
            if total_backends != healthy_backends:
                print('组件：' + component_name + ' 运行不正常')
                # 校验失败仍能继续运行
                with pytest.assume:
                    assert total_backends == healthy_backends

    @allure.story('监控告警/集群状态')
    @allure.title('在某个集群查看节点的运行状态并验证节点均健康运行')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_node_health(self):
        # 查询节点的健康状况
        r = multi_cluster_steps.step_get_component_health(self.cluster_any_name)
        # 获取集群的total_nodes
        total_nodes = r.json()['nodeStatus']['totalNodes']
        # 获取集群的healthyNodes
        healthy_nodes = r.json()['nodeStatus']['healthyNodes']
        # 验证total_nodes = healthy_nodes
        assert total_nodes == healthy_nodes

    @allure.story('监控告警/集群状态')
    @allure.title('查看某个集群的监控信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_metrics(self):
        # 获取当前时间的10位时间戳
        now_time = datetime.now()
        now_timestamp = str(datetime.timestamp(now_time))[0:10]
        # 获取210分钟之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp(now_time, 210)
        # 查询集群的最近210分钟的监控信息
        re = multi_cluster_steps.step_get_metrics_of_cluster(self.cluster_any_name, before_timestamp, now_timestamp,
                                                             '300s',
                                                             '100')
        # 获取查询结果的数据类型
        for j in range(0, 10):
            try:
                result_type = re.json()['results'][j]['data']['resultType']
                # 验证数据类型为matrix
                assert result_type == 'matrix'
            except Exception as e:
                print(e)

    @allure.story('监控告警/集群状态')
    @allure.title('查看某个集群的apiserver的监控信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_apiserver_metrics(self):
        # 获取当前时间的10位时间戳
        now_time = datetime.now()
        now_timestamp = str(datetime.timestamp(now_time))[0:10]
        # 获取240分钟之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp(now_time, 240)
        # 查询集群的最近240分钟的监控信息
        r = multi_cluster_steps.step_get_metrics_of_apiserver(self.cluster_any_name, before_timestamp, now_timestamp,
                                                              '300s',
                                                              '100')
        # 获取查询结果的数据类型
        for j in range(0, 3):
            try:
                result_type = r.json()['results'][j]['data']['resultType']
                # 验证数据类型为matrix
                assert result_type == 'matrix'
            except Exception as e:
                print(e)

    @allure.story('监控告警/集群状态')
    @allure.title('查看某个集群的schedule的监控信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_schedule_metrics(self):
        # 获取当前时间的10位时间戳
        now_time = datetime.now()
        now_timestamp = str(datetime.timestamp(now_time))[0:10]
        # 获取240分钟之前的时间
        before_timestamp = commonFunction.get_before_timestamp(now_time, 240)
        # 查询集群的最近240分钟的监控信息
        r = multi_cluster_steps.step_get_metrics_of_scheduler(self.cluster_any_name, before_timestamp, now_timestamp,
                                                              '300s',
                                                              '100')
        # 获取查询结果的数据类型
        for j in range(0, 2):
            try:
                result_type = r.json()['results'][j]['data']['resultType']
                # 验证数据类型为matrix
                assert result_type == 'matrix'
            except Exception as e:
                print(e)

    @allure.story('监控告警/应用资源')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('sort, title',
                             [('node_load1', '在某个集群通过Sort by Load Average查看Node Usage Ranking'),
                              ('node_cpu_utilisation', '在某个集群通Sort by CPU查看Node Usage Ranking'),
                              ('node_memory_utilisation', '在某个集群通Sort by Memory查看Node Usage Ranking'),
                              ('node_disk_size_utilisation', '在某个集群通Sort by Local Storage查看Node Usage Ranking'),
                              ('node_disk_inode_utilisation',
                               '在某个集群通Sort by inode Utilization查看Node Usage Ranking'),
                              ('node_pod_utilisation', '在某个集群通Sort by Pod Utilization查看Node Usage Ranking')
                              ])
    def test_get_node_usage_rank(self, sort, title):
        # 查询Node Usage Ranking
        r = multi_cluster_steps.step_get_node_usage_rank(self.cluster_any_name, sort)
        # 获取结果中的数据类型
        for j in range(0, 15):
            try:
                result_type = r.json()['results'][j]['data']['resultType']
                # 验证数据类型为vector
                assert result_type == 'vector'
            except Exception as e:
                print(e)

    @allure.story('监控告警/应用资源')
    @allure.title('查看某个集群资源使用情况')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_resource_usage(self):
        # 获取当前时间的10位时间戳
        now_time = datetime.now()
        now_timestamp = str(datetime.timestamp(now_time))[0:10]
        # 获取1440分钟之前的时间
        before_timestamp = commonFunction.get_before_timestamp(now_time, 1440)
        # 查询最近一天的集群应用资源使用情况
        r = multi_cluster_steps.step_get_resource_usage_of_cluster(self.cluster_any_name, before_timestamp,
                                                                   now_timestamp,
                                                                   '3600s', '24')
        # 获取结果中的数据类型
        for j in range(0, 3):
            try:
                result_type = r.json()['results'][j]['data']['resultType']
                # 验证数据类型为matrix
                assert result_type == 'matrix'
            except Exception as e:
                print(e)

    @allure.story('监控告警/应用资源')
    @allure.title('查看某个集群应用资源用量')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_app_usage(self):
        # 获取当前时间的10位时间戳
        now_time = datetime.now()
        now_timestamp = str(datetime.timestamp(now_time))[0:10]
        # 获取1440分钟之前的时间
        before_timestamp = commonFunction.get_before_timestamp(now_time, 1440)
        # 查询最近一天的集群应用资源使用情况
        r = multi_cluster_steps.step_get_app_usage_of_cluster(self.cluster_any_name, before_timestamp, now_timestamp,
                                                              '3600s', '24')
        # 获取结果中的数据类型
        for j in range(0, 8):
            try:
                result_type = r.json()['results'][j]['data']['resultType']
                # 验证数据类型为matrix
                assert result_type == 'matrix'
            except Exception as e:
                print(e)

    @allure.story('监控告警/应有资源')
    @allure.title('查看某个集群项目变化趋势')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_app_usage(self):
        # 获取当前时间的10位时间戳
        now_time = datetime.now()
        now_timestamp = str(datetime.timestamp(now_time))[0:10]
        # 获取1440分钟之前的时间
        before_timestamp = commonFunction.get_before_timestamp(now_time, 1440)
        # 查询最近一天的集群项目变化趋势
        r = multi_cluster_steps.step_get_project_trend_of_cluster(self.cluster_any_name, before_timestamp,
                                                                  now_timestamp,
                                                                  '3600s', '24')
        # 获取结果中的数据类型
        result_type = r.json()['results'][0]['data']['resultType']
        # 验证数据类型为matrix
        assert result_type == 'matrix'

    @allure.story('集群设置/基本信息')
    @allure.title('查看集群基本信息')
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_information(self):
        # 查看host集群的基本信息
        response = multi_cluster_steps.step_get_information(self.cluster_host_name)
        # 获取指标
        metric_name_1 = response.json()['results'][0]['metric_name']
        metric_name_2 = response.json()['results'][1]['metric_name']
        metric_name_3 = response.json()['results'][2]['metric_name']
        metric_name_4 = response.json()['results'][3]['metric_name']
        # 验证指标名称
        metric_name = ['cluster_node_total', 'cluster_disk_size_capacity', 'cluster_memory_total', 'cluster_cpu_total']
        assert metric_name_1 in metric_name
        assert metric_name_2 in metric_name
        assert metric_name_3 in metric_name
        assert metric_name_4 in metric_name

    @allure.story('集群设置/基本信息')
    @allure.title('编辑集群基本信息')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_information(self):
        # 编辑host集群的基本信息
        group = 'production'
        description = 'test'
        provider = 'QingCloud Kubernetes Engine'
        multi_cluster_steps.step_edit_information(self.cluster_host_name, group, description, provider)
        # 查看集群基本信息
        response = multi_cluster_steps.step_get_base_information(self.cluster_host_name)
        group_actual = response.json()['metadata']['labels']['cluster.kubesphere.io/group']
        description_actual = response.json()['metadata']['annotations']['kubesphere.io/description']
        provider_actual = response.json()['spec']['provider']
        # 验证编辑成功
        assert group == group_actual
        assert description == description_actual
        assert provider == provider_actual

    @allure.story('集群设置/集群可见性')
    @allure.title('创建企业空间并验证其集群可见性')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_visibility(self):
        # 创建企业空间，并设置其所在集群为单个集群
        ws_name = 'test-ws' + str(commonFunction.get_random())
        # 获取集群名称
        clusters = multi_workspace_steps.step_get_cluster_name()
        multi_workspace_steps.step_create_multi_ws(ws_name, clusters[0])
        time.sleep(5)
        # 查看集群可见性
        response = multi_cluster_steps.step_get_cluster_visibility(clusters[0])
        # 获取所有已授权的企业空间名称
        ws_names = []
        count = response.json()['totalItems']
        for i in range(0, count):
            name = response.json()['items'][i]['metadata']['name']
            ws_names.append(name)
        # 验证集群可见性
        with pytest.assume:
            assert ws_name in ws_names
        # 删除创建的企业空间
        multi_workspace_steps.step_delete_workspace(ws_name)

    @allure.story('集群设置/集群可见性')
    @allure.title('编辑集群可见性/取消企业空间授权')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_unauthorized_cluster_visibility(self):
        # 创建企业空间，其所在集群为host集群
        ws_name = 'test-ws' + str(commonFunction.get_random())
        cluster_name = self.cluster_host_name
        multi_workspace_steps.step_create_multi_ws(ws_name, cluster_name)
        # # 取消企业空间在host集群的授权
        multi_cluster_steps.step_unauthorized_cluster_visibility(self.cluster_host_name, ws_name)
        time.sleep(3)
        # 查看集群可见性
        response = multi_cluster_steps.step_get_cluster_visibility(self.cluster_host_name)
        # 获取所有的企业空间名称
        ws_names = []
        count = response.json()['totalItems']
        for i in range(0, count):
            name = response.json()['items'][i]['metadata']['name']
            ws_names.append(name)
        # 验证授权取消成功
        with pytest.assume:
            assert ws_name not in ws_names
        # 删除创建的企业空间
        multi_workspace_steps.step_delete_workspace(ws_name)

    @allure.story('集群设置/集群可见性')
    @allure.title('编辑集群可见性/添加企业空间在集群的授权')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_authorized_cluster_visibility(self):
        # 创建企业空间，不添加集群
        ws_name = 'test-ws' + str(commonFunction.get_random())
        cluster_name = []
        multi_workspace_steps.step_create_multi_ws(ws_name, cluster_name)
        # 添加企业空间在host集群的授权
        multi_cluster_steps.step_authorized_cluster_visibility(self.cluster_host_name, ws_name)
        # 查看集群可见性
        time.sleep(5)
        response = multi_cluster_steps.step_get_cluster_visibility(self.cluster_host_name)
        # 获取所有授权的企业空间名称
        ws_names = []
        count = response.json()['totalItems']
        for i in range(0, count):
            name = response.json()['items'][i]['metadata']['name']
            ws_names.append(name)
        # 验证授权成功
        with pytest.assume:
            assert ws_name in ws_names
        # 删除创建的企业空间
        multi_workspace_steps.step_delete_workspace(ws_name)

    @allure.story('集群设置/集群成员')
    @allure.title('查询集群默认成员')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_member_by_name(self):
        # 查询集群所有成员
        response = multi_cluster_steps.step_get_cluster_member(self.cluster_host_name, 'name=admin')
        # 获取集群成员的数量和名称
        count = response.json()['totalItems']
        # 验证查询成功
        assert count == 1

    @allure.story('集群设置/集群成员')
    @allure.title('邀请集群成员/移出集群成员')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_invite_cluster_member(self):
        # 创建平台用户
        user_name = 'user' + str(commonFunction.get_random())
        role = 'platform-regular'
        email = 'test' + str(commonFunction.get_random()) + '@qq.com'
        password = 'P@88w0rd'
        platform_steps.step_create_user(user_name, role, email, password)
        # 遍历所有集群
        for cluster_name in self.cluster_names:
            # 邀请用户到集群成员
            multi_cluster_steps.step_invite_cluster_member(cluster_name, user_name, 'cluster-viewer')
            # 查询集群成员
            response = multi_cluster_steps.step_get_cluster_member(cluster_name, 'name=' + user_name)
            # 验证集群成员邀请成功
            name = response.json()['items'][0]['metadata']['name']
            with pytest.assume:
                assert name == user_name
            # 将用户从集群成员中移出
            multi_cluster_steps.step_remove_cluster_member(cluster_name, user_name)
            # 查询集群成员，验证移出成功
            re = multi_cluster_steps.step_get_cluster_member(cluster_name, 'name=' + user_name)
            count = re.json()['totalItems']
            with pytest.assume:
                assert count == 0
        # 删除创建的用户
        platform_steps.step_delete_user(user_name)

    @allure.story('集群设置/集群角色')
    @allure.title('查看默认的集群角色')
    @allure.severity(allure.severity_level.NORMAL)
    def test_get__cluster_role(self):
        # 遍历所有集群
        for cluster_name in self.cluster_names:
            # 查看集群角色
            response = multi_cluster_steps.step_get_cluster_role(cluster_name)
            count = response.json()['totalItems']
            # 验证角色数量
            assert count == 2
            name_1 = response.json()['items'][0]['metadata']['name']
            name_2 = response.json()['items'][1]['metadata']['name']
            # 验证角色名称
            assert name_1 == 'cluster-viewer'
            assert name_2 == 'cluster-admin'

    @allure.story('集群设置/网关设置')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('type, title',
                             [('NodePort', '开启集群网关并设置类型为NodePort'),
                              ('LoadBalancer', '开启集群网关并设置类型为LoadBalancer')
                              ])
    def test_open_cluster_gateway(self, type, title):
        # 遍历所有集群
        for cluster_name in self.cluster_names:
            # 开启集群网关
            multi_cluster_steps.step_open_cluster_gateway(cluster_name, type)
            # 查看集群网关，并验证网关类型
            response = multi_cluster_steps.step_get_cluster_gateway(cluster_name)
            gateway_type = response.json()[0]['spec']['service']['type']
            with pytest.assume:
                assert gateway_type == type
            # 关闭集群网关
            multi_cluster_steps.step_delete_cluster_gateway(cluster_name)
            time.sleep(10)

    @allure.story('集群设置/网关设置')
    @allure.title('修改网关信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_edit_cluster_gateway(self):
        # 开启集群网关
        response = multi_cluster_steps.step_open_cluster_gateway(self.cluster_any_name, type='NodePort')
        # 并获取获取uid和resource_version
        uid = response.json()['metadata']['uid']
        resource_version = response.json()['metadata']['resourceVersion']
        # 编辑集群config信息
        config = {"4": "5"}
        status = 'true'
        multi_cluster_steps.step_edit_cluster_gateway(self.cluster_any_name, uid, resource_version, config, status)
        # 查看集群网关，并获取config信息
        re = multi_cluster_steps.step_get_cluster_gateway(self.cluster_any_name)
        config_actual = re.json()[0]['spec']['controller']['config']
        status_actual = re.json()[0]['spec']['deployment']['annotations']['servicemesh.kubesphere.io/enabled']
        # 验证config信息编辑成功
        with pytest.assume:
            assert config_actual == config
        # 验证集群网关的链路追踪的状态
        with pytest.assume:
            assert status_actual == status
        # 关闭集群网关
        multi_cluster_steps.step_delete_cluster_gateway(self.cluster_any_name)
        time.sleep(10)

    @allure.story('集群设置/网关设置')
    @allure.title('在网管设置中查询项目网关')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_project_gateway(self):
        # 开启集群网关
        multi_cluster_steps.step_open_cluster_gateway(self.cluster_any_name, type='LoadBalancer')
        # 查询项目网关
        response = multi_cluster_steps.step_get_project_gateway(self.cluster_any_name,
                                                                'kubesphere-router-kubesphere-system')
        gateway_name = response.json()['items'][0]['metadata']['name']
        # 验证查询结果
        with pytest.assume:
            assert gateway_name == 'kubesphere-router-kubesphere-system'
        # 关闭集群网关
        multi_cluster_steps.step_delete_cluster_gateway(self.cluster_any_name)


if __name__ == "__main__":
    pytest.main(['-rs', 'testMultiClusterManager.py'])  # -s参数是为了显示用例的打印信息 r 显示跳过的原因。 -q参数只显示结果，不显示过程
