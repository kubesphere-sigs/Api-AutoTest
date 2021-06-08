import requests
import pytest
import json
import allure
import sys
from config import config
from common.getData import DoexcleByPandas
from common.getHeader import get_header
from common.getHeader import get_header_for_patch
from common import commonFunction
import time
import datetime
import random

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用


@allure.step('获取集群的节点列表信息')
def step_get_nodes():
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/nodes'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('为节点设置污点')
def step_ste_taints(node_name, taints):
    url = config.url + '/api/v1/nodes/' + node_name
    data = {"spec": {"taints": taints}}
    response = requests.patch(url=url, headers=get_header_for_patch(), data=json.dumps(data))
    return response


@allure.step('查看节点的详细信息')
def step_get_node_detail_info(node_name):
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/nodes/' + node_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('往节点中添加标签')
def step_add_labels_for_node(node_name, labels):
    url = config.url + '/api/v1/nodes/' + node_name
    data = {"metadata": {"labels": labels}}
    response = requests.patch(url=url, headers=get_header_for_patch(), data=json.dumps(data))
    return response


@allure.step('节点停止/启用调度')
def step_cordon_node(node_name, cordon):
    url = config.url + '/api/v1/nodes/' + node_name
    data = {"spec": {"unschedulable": cordon}}
    response = requests.patch(url=url, headers=get_header_for_patch(), data=json.dumps(data))
    return response


@allure.step('查看节点的pod信息')
def step_get_pod_of_node(node_name):
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/pods?nodeName=' + node_name + '&sortBy=startTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询指定的pod')
def step_query_pod(node_name, pod_name):
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/pods?nodeName=' + node_name + '&name=' + pod_name + '&sortBy=startTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看节点的event信息')
def step_get_event_of_node(node_name):
    url = config.url + '/api/v1/events?fieldSelector=involvedObject.name%3D' + node_name + '%2CinvolvedObject.kind%3DNode'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看节点的监控信息')
def step_get_metrics_of_node(node_name, start_time, end_time, step, times):
    url = config.url + '/kapis/monitoring.kubesphere.io/v1alpha3/nodes?start=' + start_time + '&end=' + end_time + \
          '&step=' + step + '&times=' + times + '&resources_filter=' + node_name + \
          '%24&metrics_filter=node_cpu_utilisation%7Cnode_load1%7Cnode_load5%7Cnode_load15%7Cnode_memory_utilisation' \
          '%7Cnode_disk_size_utilisation%7Cnode_disk_inode_utilisation%7Cnode_disk_inode_usage%7Cnode_disk_inode_total' \
          '%7Cnode_disk_read_iops%7Cnode_disk_write_iops%7Cnode_disk_read_throughput%7Cnode_disk_write_throughput' \
          '%7Cnode_net_bytes_transmitted%7Cnode_net_bytes_received%24 '
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看节点的状态信息')
def step_get_status_of_node(node_name, start_time, end_time, step, times):
    url = config.url + '/kapis/monitoring.kubesphere.io/v1alpha3/nodes?start=' + start_time + '&end=' + end_time + \
          '&step=' + step + '&times=' + times + '&resources_filter=' + node_name + \
          '%24&metrics_filter=node_cpu_utilisation%7Cnode_memory_utilisation%7Cnode_disk_size_utilisation' \
          '%7Cnode_pod_utilisation%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群指定的系统项目')
def step_query_system_project(project_name):
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces?name=' + project_name + \
          '&sortBy=createTime&labelSelector=kubesphere.io%2Fworkspace%3Dsystem-workspace'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询指定项目的详细信息')
def step_get_project_detail(project_name):
    url = config.url + '/api/v1/namespaces/' + project_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询指定项目的配额信息')
def step_get_project_quota(project_name):
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha2/namespaces/' + project_name + '/quotas'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询指定项目的LimitRanges')
def step_get_project_limit_ranges(project_name):
    url = config.url + '/api/v1/namespaces/' + project_name + '/limitranges'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询指定项目的工作负载信息')
def step_get_project_workload(project_name):
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha2/namespaces/' + project_name + '/abnormalworkloads'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询指定项目的pod信息')
def step_query_project_pods(project_name, pod_name):
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' \
          + project_name + '/pods?name=' + pod_name + '&sortBy=startTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('创建用户项目')
def step_create_user_project(project_name, alias_name, description):
    url = config.url + '/api/v1/namespaces'
    data = {"apiVersion": "v1", "kind": "Namespace", "metadata": {"name": project_name,
                                                                  "annotations": {
                                                                      "kubesphere.io/alias-name": alias_name,
                                                                      "kubesphere.io/description": description,
                                                                      "kubesphere.io/creator": "admin"},
                                                                  "labels": {}}}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('查询指定的用户项目')
def step_get_user_system(project_name):
    url = config.url + '/api/v1/namespaces/' + project_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('删除用户项目')
def step_delete_user_system(project_name):
    url = config.url + '/api/v1/namespaces/' + project_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.feature('集群管理')
class TestCluster(object):
    # 从文件中读取用例信息
    parametrize = DoexcleByPandas().get_data_for_pytest(filename='../data/data.xlsx', sheet_name='cluster')

    @allure.title('{title}')  # 设置用例标题
    # 将用例信息以参数化的方式传入测试方法
    @pytest.mark.parametrize('id,url,params,data, story, title,method,severity,condition,except_result', parametrize)
    def test_cluster(self, id, url, params, data, story, title, method, severity, condition, except_result):

        '''
        :param id: 用例编号
        :param url: 用例请求的URL地址
        :param data: 用例使用的请求数据
        :param title: 用例标题
        :param method: 用例的请求方式
        :param severity: 用例优先级
        :param condition: 用例的校验条件
        :param except_result: 用例的预期结果
        '''

        allure.dynamic.story(story)  # 动态生成模块
        allure.dynamic.severity(severity)  # 动态生成用例等级

        # test开头的测试函数
        if params != '':
            url = config.url + url + '?' + params
        else:
            url = config.url + url
        print(url)
        if method == 'get':
            # 测试get方法
            r = requests.get(url, headers=get_header())

        elif method == 'post':
            # 测试post方法
            data = eval(data)
            r = requests.post(url, headers=get_header(), data=json.dumps(data))

        elif method == 'put':
            # 测试put方法
            data = eval(data)
            r = requests.put(url, headers=get_header(), data=json.dumps(data))

        elif method == 'delete':
            # 测试delete方法
            r = requests.delete(url, headers=get_header())

        # 将校验条件和预期结果参数化
        if condition != '':
            condition_new = eval(condition)  # 将字符串转化为表达式
            if isinstance(condition_new, str):
                # 判断表达式的结果是否为字符串，如果为字符串格式，则去掉其首尾的空格
                assert condition_new.strip() == except_result
            else:
                assert condition_new == except_result
            # 将用例中的内容打印在报告中
        print(
            '用例编号: ' + str(id) + '\n'
                                 '用例请求的URL地址: ' + str(url) + '\n'
                                                             '用例使用的请求数据: ' + str(data) + '\n'
                                                                                         '用例模块: ' + story + '\n'
                                                                                                            '用例标题: ' + title + '\n'
                                                                                                                               '用例的请求方式: ' + method + '\n '
                                                                                                                                                      '用例优先级: ' + severity + '\n'
                                                                                                                                                                             '用例的校验条件: ' + str(
                condition) + '\n'
                             '用例的实际结果: ' + str(condition_new) + '\n'
                                                                '用例的预期结果: ' + str(except_result)
        )

    @allure.story("节点")
    @allure.title('为节点设置污点')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_set_taints(self):
        # 污点信息
        taints = [{"key": "tester", "value": "wx", "effect": "NoSchedule"}]
        # 获取节点列表中第一个节点的名称
        response = step_get_nodes()
        node_name = response.json()['items'][0]['metadata']['name']
        # 为节点设置污点
        step_ste_taints(node_name, taints)
        # 获取节点的污点信息
        r = step_get_node_detail_info(node_name)
        taints_actual = r.json()['spec']['taints']
        # 验证污点设置成功
        assert taints == taints_actual
        # 清空设置的污点
        step_ste_taints(node_name=node_name, taints=[])

    @allure.story("节点")
    @allure.title('为节点添加标签')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_add_labels(self):
        # 获取节点列表中第一个节点的名称
        response = step_get_nodes()
        node_name = response.json()['items'][0]['metadata']['name']
        # 获取节点的标签信息
        re = step_get_node_detail_info(node_name)
        labels_old = re.json()['metadata']['labels']  # 用于删除添加的标签
        labels = re.json()['metadata']['labels']  # 用于添加标签
        # 添加标签的内容
        labels['tester/label'] = 'wxx'
        # 添加标签
        step_add_labels_for_node(node_name, labels)
        # 获取编辑后节点的标签信息
        r = step_get_node_detail_info(node_name)
        labels_actual = r.json()['metadata']['labels']
        # 验证标签添加成功
        assert labels == labels_actual
        # 删除添加的标签
        labels_old['tester/label'] = None
        step_add_labels_for_node(node_name, labels_old)

    @allure.story('节点')
    @allure.title('设置节点为停止调度, 然后设置为启用调度')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_set_uncordon_node(self):
        # 获取节点列表中第一个节点的名称
        response = step_get_nodes()
        node_name = response.json()['items'][0]['metadata']['name']
        # 设置节点为停止调度
        step_cordon_node(node_name, True)
        # 获取节点的调度状态
        response = step_get_node_detail_info(node_name)
        cordon_status = response.json()['spec']['unschedulable']
        # 验证节点调度状态为停止调度
        assert cordon_status == True
        # 设置节点为启用调度
        step_cordon_node(node_name, False)

    @allure.story('节点')
    @allure.title('查看节点的pod信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_pods(self):
        # 获取节点列表中第一个节点的名称
        response = step_get_nodes()
        node_name = response.json()['items'][0]['metadata']['name']
        # 查看节点的pod信息
        response = step_get_pod_of_node(node_name)
        # 验证pod信息查询成功
        assert response.status_code == 200

    @allure.story('节点')
    @allure.title('查看节点的event信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_events(self):
        # 获取节点列表中第一个节点的名称
        response = step_get_nodes()
        node_name = response.json()['items'][0]['metadata']['name']
        # 查看节点的event信息
        response = step_get_event_of_node(node_name)
        # 获取资源类型
        kind = response.json()['kind']
        # 验证event信息查询成功
        assert kind == 'EventList'

    @allure.story('节点')
    @allure.title('查看节点的监控信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_events(self):
        # 获取节点列表中第一个节点的名称
        response = step_get_nodes()
        node_name = response.json()['items'][0]['metadata']['name']
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 获取10分钟之前的时间
        now = datetime.datetime.now()
        now_reduce_10 = now - datetime.timedelta(minutes=10)
        # 转换成时间数组
        timeArray = time.strptime(str(now_reduce_10)[0:19], "%Y-%m-%d %H:%M:%S")
        # 转换成时间戳
        before_timestamp = str(time.mktime(timeArray))[0:10]
        # 查看最近十分钟的监控信息
        r = step_get_metrics_of_node(node_name=node_name, start_time=before_timestamp, end_time=now_timestamp,
                                     step='60s', times='10')
        # 获取查询到的数据的结果类型
        resultType = r.json()['results'][0]['data']['resultType']
        # 验证查询到的数据的结果类型
        assert resultType == 'matrix'

    @allure.story('节点')
    @allure.title('查看节点的状态信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_status(self):
        # 获取节点列表中第一个节点的名称
        response = step_get_nodes()
        node_name = response.json()['items'][0]['metadata']['name']
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 获取20分钟之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp(20)
        # 查看节点的状态信息
        response = step_get_status_of_node(node_name=node_name, start_time=before_timestamp, end_time=now_timestamp,
                                           step='180s', times='20')
        # 获取查询结果中的节点信息
        node = response.json()['results'][0]['data']['result'][0]['metric']['node']
        # 验证查询结果正确
        assert node == node_name

    @allure.story('节点')
    @allure.title('查询节点中不存在的pod')
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_non_existent_pod(self):
        # 获取节点列表中第一个节点的名称
        response = step_get_nodes()
        node_name = response.json()['items'][0]['metadata']['name']
        # 查询不存在的pod
        pod_name = 'non-existent'
        re = step_query_pod(node_name, pod_name)
        # 获取查询结果
        totalItems = re.json()['totalItems']
        # 验证查询结果
        assert totalItems == 0

    @allure.story('节点')
    @allure.title('按名称精确查询节点中存在的pod')
    @allure.severity(allure.severity_level.NORMAL)
    def test_precise_query_existent_pod(self):
        # 获取节点列表中第一个节点的名称
        response = step_get_nodes()
        node_name = response.json()['items'][0]['metadata']['name']
        # 获取节点的任意一个pod的名称
        re = step_get_pod_of_node(node_name)
        pod_name = re.json()['items'][0]['metadata']['name']
        # 按名称精确查询存在的pod
        re = step_query_pod(node_name, pod_name)
        # 获取查询到的pod名称
        name_actual = re.json()['items'][0]['metadata']['name']
        # 验证查询结果
        assert name_actual == pod_name

    @allure.story('节点')
    @allure.title('按名称模糊查询节点中存在的pod')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_query_existent_pod(self):
        # 获取节点列表中第一个节点的名称
        response = step_get_nodes()
        node_name = response.json()['items'][0]['metadata']['name']
        # 获取节点的任意一个pod的名称
        re = step_get_pod_of_node(node_name)
        pod_name = re.json()['items'][0]['metadata']['name']
        # 按名称模糊查询存在的pod
        pod_fuzzy_name = pod_name[2:]
        re = step_query_pod(node_name, pod_fuzzy_name)
        # 获取查询到的pod名称
        name_actual = re.json()['items'][0]['metadata']['name']
        # 验证查询结果
        assert name_actual == pod_name

    @allure.story('项目管理')
    @allure.title('按名称精确查询集群中不存在的系统项目')
    @allure.severity(allure.severity_level.NORMAL)
    def test_precise_non_existent_system_project(self):
        project_name = 'non-existent-project'
        # 查询指定的集群的系统项目
        response = step_query_system_project(project_name)
        # 获取查询结果
        items = response.json()['items']
        # 验证查询结果为空
        assert items == []

    @allure.story('项目管理')
    @allure.title('按名称精确查询集群中存在的系统项目')
    @allure.severity(allure.severity_level.NORMAL)
    def test_precise_query_existent_system_project(self):
        # 获取集群任意系统项目的名称
        response = step_query_system_project('')
        project_name = response.json()['items'][0]['metadata']['name']
        # 按名称精确查询系统项目
        re = step_query_system_project(project_name)
        # 获取查询结果
        project_name_actual = re.json()['items'][0]['metadata']['name']
        # 验证查询结果
        assert project_name_actual == project_name

    @allure.story('项目管理')
    @allure.title('按名称模糊查询集群中存在的系统项目')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_query_existent_system_project(self):
        # 获取集群任意系统项目的名称
        response = step_query_system_project('')
        project_name = response.json()['items'][0]['metadata']['name']
        # 按名称精确查询系统项目
        fuzzy_project_name = project_name[2:]
        re = step_query_system_project(fuzzy_project_name)
        # 获取查询结果
        project_name_actual = re.json()['items'][0]['metadata']['name']
        # 验证查询结果
        assert project_name_actual == project_name

    @allure.story('项目管理')
    @allure.title('查询集群中所有系统项目的详情信息,并验证其状态为活跃')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_check_system_project_state(self):
        # 获取集群中系统项目的数量
        response = step_query_system_project('')
        project_count = response.json()['totalItems']
        # 获取集群任意系统项目的名称
        for i in range(0, project_count):
            project_name = response.json()['items'][i]['metadata']['name']
            # 查询项目的详细信息
            r = step_get_project_detail(project_name)
            # 获取项目的状态
            status = r.json()['status']['phase']
            # 验证项目运行状态为活跃
            assert status == 'Active'

    @allure.story('项目管理')
    @allure.title('查询集群中所有系统项目的配额信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_one_system_project_quota(self):
        # 获取集群中系统项目的数量
        response = step_query_system_project('')
        project_count = response.json()['totalItems']
        for i in range(0, project_count):
            # 获取集群任意系统项目的名称
            project_name = response.json()['items'][i]['metadata']['name']
            # 查询项目的配额信息
            r = step_get_project_quota(project_name)
            # 获取项目的配额信息
            used = r.json()['data']['used']
            # 验证项目配额信息获取成功
            assert 'count/pods' in used

    @allure.story('项目管理')
    @allure.title('查询集群中所有系统项目的LimitRanges信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_one_system_project_detail(self):
        # 获取集群中系统项目的数量
        response = step_query_system_project('')
        project_count = response.json()['totalItems']
        for i in range(0, project_count):
            # 获取集群任意系统项目的名称
            project_name = response.json()['items'][i]['metadata']['name']
            # 查询项目的LimitRanges
            r = step_get_project_limit_ranges(project_name)
            # 获取请求资源的kind
            kind = r.json()['kind']
            # 验证请求资源的kind为LimitRangeList
            assert kind == 'LimitRangeList'

    @allure.story('项目管理')
    @allure.title('查询集群中所有系统项目的工作负载信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_one_system_project_workload(self):
        # 获取集群中系统项目的数量
        response = step_query_system_project('')
        project_count = response.json()['totalItems']
        for i in range(0, project_count):
            # 获取集群任意系统项目的名称
            response = step_query_system_project('')
            project_name = response.json()['items'][i]['metadata']['name']
            # 查询项目的工作负载信息
            response = step_get_project_workload(project_name)
            # 获取接口的响应数据
            data = response.json()['data']
            # 验证接口响应数据正确
            data_except = ['daemonsets', 'deployments', 'jobs', 'persistentvolumeclaims', 'statefulsets']
            assert data_except[random.randint(0, 4)] in data

    @allure.story('项目管理')
    @allure.title('验证集群中所有系统项目的pod运行正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_check_one_system_project_pods(self):
        # 获取集群中系统项目的数量
        response = step_query_system_project('')
        project_count = response.json()['totalItems']
        # 获取集群中所有系统项目的名称
        for i in range(0, project_count):
            project_name = response.json()['items'][i]['metadata']['name']
            # 查询项目的pods信息
            r = step_query_project_pods(project_name=project_name, pod_name='')
            # 获取pod的数量
            pod_count = r.json()['totalItems']
            # 获取所有pod的状态
            status = []
            for j in range(0, pod_count):
                state = r.json()['items'][j]['status']['phase']
                # 验证pod的运行状态
                assert state in ['Running', 'Succeeded']
                status.append(state)

    @allure.story('项目管理')
    @allure.title('使用名称精确查询项目中存在的pod')
    @allure.severity(allure.severity_level.NORMAL)
    def test_precise_query_existent_pod(self):
        # 用于存放pod的名称
        pod_names = []
        # 获取集群中任一系统项目的名称
        response = step_query_system_project('')
        project_name = response.json()['items'][0]['metadata']['name']
        # 查询项目的所有的pod信息
        re = step_query_project_pods(project_name=project_name, pod_name='')
        # 获取pod的数量
        pod_count = re.json()['totalItems']
        # 获取项目的pod的名称
        for i in range(0, pod_count):
            name = re.json()['items'][i]['metadata']['name']
            pod_names.append(name)
        # 使用pod的名称，精确查询存在的pod
        r = step_query_project_pods(project_name=project_name, pod_name=pod_names[0])
        # 获取查询结果中pod名称
        pod_name_actual = r.json()['items'][0]['metadata']['name']
        # 验证查询结果正确
        assert pod_name_actual == pod_names[0]

    @allure.story('项目管理')
    @allure.title('使用名称模糊查询项目中存在的pod')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_query_existent_pod(self):
        # 用于存放pod的名称
        pod_names = []
        # 获取集群中任一系统项目的名称
        response = step_query_system_project('')
        project_name = response.json()['items'][0]['metadata']['name']
        # 查询项目的所有的pod信息
        re = step_query_project_pods(project_name=project_name, pod_name='')
        # 获取pod的数量
        pod_count = re.json()['totalItems']
        # 获取项目的pod的名称
        for i in range(0, pod_count):
            name = re.json()['items'][i]['metadata']['name']
            pod_names.append(name)
        # 使用pod的名称，模糊查询存在的pod
        r = step_query_project_pods(project_name=project_name, pod_name=pod_names[0][2:])
        # 获取查询结果中pod名称
        pod_name_actual = r.json()['items'][0]['metadata']['name']
        # 验证查询结果正确
        assert pod_name_actual == pod_names[0]

    @allure.story('项目管理')
    @allure.title('使用名称查询项目中不存在的pod')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_query_existent_pod(self):
        # 获取集群中任一系统项目的名称
        response = step_query_system_project('')
        project_name = response.json()['items'][0]['metadata']['name']
        # 使用pod的名称，模糊查询存在的pod
        pod_name = 'test' + str(commonFunction.get_random())
        r = step_query_project_pods(project_name=project_name, pod_name=pod_name)
        # 获取查询结果中的pod数量
        pod_count = r.json()['totalItems']
        # 验证查询结果正确
        assert pod_count == 0

    @allure.story('项目管理')
    @allure.title('创建用户项目，并验证项目创建成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_user_system(self):
        project_name = 'user-project' + str(commonFunction.get_random())
        alias_name = 'test'
        description = 'create user-system'
        # 创建用户项目
        step_create_user_project(project_name, alias_name, description)
        # 查询创建的项目，并获取其运行状态
        r = step_get_user_system(project_name)
        state = r.json()['status']['phase']
        # 验证项目的状态为active
        assert state == 'Active'
        # 删除创建的项目
        step_delete_user_system(project_name)

    @allure.story('项目管理')
    @allure.title('删除用户项目，并验证删除成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_user_system(self):
        project_name = 'user-project' + str(commonFunction.get_random())
        alias_name = 'test'
        description = 'create user-system'
        # 创建用户项目
        step_create_user_project(project_name, alias_name, description)
        # 删除用户项目
        response = step_delete_user_system(project_name)
        # 获取删除项目的状态
        state = response.json()['status']['phase']
        # 验证删除项目的状态为Terminating
        assert state == 'Terminating'
        # 等待项目删除成功
        i = 0
        while i < 60:
            # 查询被删除的项目并获取查询结果
            r = step_get_user_system(project_name)
            status = r.json()['status']
            if status == {'phase': 'Terminating'}:
                time.sleep(1)
                i += 1
            else:
                break
        # 验证项目删除成功
        assert status == 'Failure'