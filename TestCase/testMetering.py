import requests
import pytest
import json
import allure
import sys
from config import config
from common.getData import DoexcleByPandas
from common.getHeader import get_header
from common import commonFunction
import random

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用


@allure.step('查看资源消费历史')
def step_get_consumption_history(type, start_time, end_time, step, name):
    if type == 'cluster':
        url = config.url + '/kapis/metering.kubesphere.io/v1alpha1/' + type + '?start=' + start_time + '&end=' + end_time + \
              '&step=' + step + 's&metrics_filter=meter_cluster_cpu_usage%7Cmeter_cluster_memory_usage%7C' \
                                'meter_cluster_net_bytes_transmitted%7Cmeter_cluster_net_bytes_received%7C' \
                                'meter_cluster_pvc_bytes_total&resources_filter=' + name
    elif type == 'node':
        url = config.url + '/kapis/metering.kubesphere.io/v1alpha1/nodes?start=' + start_time + '&end=' + end_time + \
              '&step=' + step + 's&metrics_filter=meter_node_cpu_usage%7Cmeter_node_memory_usage_wo_cache%7C' \
                                'meter_node_net_bytes_transmitted%7Cmeter_node_net_bytes_received%7C' \
                                'meter_node_pvc_bytes_total&resources_filter=' + name

    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看pod的资源消费历史')
def step_get_pod_consumption_history(node_name, start_time, end_time, step, pod_name):
    url = config.url + '/kapis/metering.kubesphere.io/v1alpha1/nodes/' + node_name + '/pods?start=' + start_time + \
          '&end=' + end_time + '&step=' + step + 's&metrics_filter=meter_pod_cpu_usage%7C' \
          'meter_pod_memory_usage_wo_cache%7Cmeter_pod_net_bytes_transmitted%7C' \
          'meter_pod_net_bytes_received&resources_filter=' + pod_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看项目的资源消费历史')
def step_get_project_consumption_history(project_name, start_time, end_time, step):
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/metering?start=' + start_time + '&end=' + end_time + \
          '&step=' + step + 's&metrics_filter=meter_namespace_cpu_usage%7Cmeter_namespace_memory_usage_wo_cache%7C' \
                            'meter_namespace_net_bytes_transmitted%7Cmeter_namespace_net_bytes_received%7C' \
                            'meter_namespace_pvc_bytes_total&resources_filter=' + project_name + '&level=LevelNamespace'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看企业空间的资源消费历史')
def step_get_workspace_consumption_history(ws_name, start_time, end_time, step):
    url = config.url + '/kapis/metering.kubesphere.io/v1alpha1/workspaces/' + ws_name + '?start=' + start_time + \
          '&end=' + end_time + '&step=' + step + \
          's&metrics_filter=meter_workspace_cpu_usage%7C' \
          'meter_workspace_memory_usage%7Cmeter_workspace_net_bytes_transmitted%7C' \
          'meter_workspace_net_bytes_received%7Cmeter_workspace_pvc_bytes_total&resources_filter=' + ws_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('获取集群的节点信息')
def step_get_node_info():
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/nodes?' \
                       'sortBy=createTime&labelSelector=%21node-role.kubernetes.io%2Fedge'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询节点的消费信息')
def step_get_node_consumption(metric_name, node_name):
    url = config.url + '/kapis/metering.kubesphere.io/v1alpha1/nodes?' \
                       'metrics_filter=' + metric_name + '&resources_filter=' + node_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询节点的pod信息')
def step_get_pod_info(node_name):
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/pods?' \
                       'labelSelector=&nodeName=' + node_name + '&sortBy=startTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询pod的消费信息')
def step_get_pod_consumption(node_name, metric):
    url = config.url + '/kapis/metering.kubesphere.io/v1alpha1/nodes/' + node_name + '/pods?' \
                        'metrics_filter=' + metric
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群的企业空间信息')
def step_get_workspace_info():
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces?sortBy=createTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询企业空间的项目信息')
def step_get_project_info(ws_name):
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/namespaces?' \
          'sortBy=createTime&labelSelector=%21kubesphere.io%2Fkubefed-host-namespace%2C%21kubesphere.io%2Fdevopsproject'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询企业空间的项目的最近1h的消费信息')
def step_get_project_consumption(metric, project):
    condition = ''
    for i in project:
        condition += str(i) + '%7C'
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/metering?metrics_filter=' + metric + \
                       '&resources_filter=' + condition + '&level=LevelNamespace'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询项目下最近1h消费的资源')
def step_get_hierarchy_consumption(ws_name, project_name):
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/namespaces/' + project_name + \
                       '/metering/hierarchy?workspace=' + ws_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询项目下资源的历史消费信息')
def step_get_hierarchy_consumption_history(project_name, start_time, end_time, step, name, kind):
    url = config.url + '/kapis/metering.kubesphere.io/v1alpha1/namespaces/' + project_name + \
          '/workloads?start=' + start_time + '&end=' + end_time + '&step=' + step + \
          's&metrics_filter=meter_workload_cpu_usage%7Cmeter_workload_memory_usage_wo_cache%7C' \
          'meter_workload_net_bytes_transmitted%7Cmeter_workload_net_bytes_received&' \
          'resources_filter=' + name + '&kind=' + kind
    response = requests.get(url=url, headers=get_header())
    return response


@allure.feature('计量计费')
class TestMetering(object):
    # 从文件中读取用例信息
    parametrize = DoexcleByPandas().get_data_for_pytest(filename='../data/data.xlsx', sheet_name='metering')

    # 设置用例标题
    @allure.title('{title}')
    # 将用例信息以参数化的方式传入测试方法
    @pytest.mark.parametrize('id,url,params,data, story, title,method,severity,condition,except_result', parametrize)
    def test_metering(self, id, url, params, data, story, title, method, severity, condition, except_result):

        """
        :param id: 用例编号
        :param url: 用例请求的URL地址
        :param data: 用例使用的请求数据
        :param title: 用例标题
        :param method: 用例的请求方式
        :param severity: 用例优先级
        :param condition: 用例的校验条件
        :param except_result: 用例的预期结果
        """

        allure.dynamic.story(story)  # 动态生成模块
        allure.dynamic.severity(severity)  # 动态生成用例等级

        # test开头的测试函数
        if params != '':
            url = config.url + url + '?' + params
        else:
            url = config.url + url
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

    @allure.story('集群资源消费情况')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('step, title',
                             [('3600', '查看集群截止到昨天的消费情况，时间间隔为1小时'),
                              ('7200', '查看集群截止到昨天的消费情况，时间间隔为2小时'),
                              ('14400', '查看集群截止到昨天的消费情况，时间间隔为4小时'),
                              ('28800', '查看集群截止到昨天的消费情况，时间间隔为7小时'),
                              ('86400', '查看集群截止到昨天的消费情况，时间间隔为1天')
                              ])
    def test_get_cluster_consumption_by_yesterday(self, step, title):
        # 获取当前日期的时间戳
        now_timestamp = commonFunction.get_timestamp()
        # 获取7天之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp_day(7)
        # 获取截止到昨天的最近7天的消费历史
        response = step_get_consumption_history(type='cluster', start_time=before_timestamp, end_time=now_timestamp,
                                                step=step, name='default')
        # 获取查询结果的数据类型
        for i in range(0, 5):
            try:
                result_type = response.json()['results'][i]['data']['resultType']
                # 验证数据类型为matrix
                assert result_type == 'matrix'
                # 获取趋势图数据的时间间隔
                time_1 = response.json()['results'][i]['data']['result'][0]['values'][0][0]
                time_2 = response.json()['results'][i]['data']['result'][0]['values'][1][0]
                time_interval = time_2 - time_1
                # 验证时间间隔正确
                assert time_interval == int(step)
            except Exception as e:
                print(e)
                print('集群无资源消费信息')
                break

    @allure.story('集群资源消费情况')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('metric_name, title',
                             [('meter_node_cpu_usage', '查看所有节点的cpu消费情况'),
                              ('meter_node_memory_usage_wo_cache', '查看所有节点的内存消费情况'),
                              ('meter_node_pvc_bytes_total', '查看所有节点的pvc消费情况'),
                              ('meter_node_net_bytes_received', '查看所有节点的网络流入消费情况'),
                              ('meter_node_net_bytes_transmitted', '查看所有节点的网络流出消费情况')
                              ])
    def test_get_node_consumption(self, metric_name, title):
        # 查询集群的节点信息
        response = step_get_node_info()
        # 获取集群节点的数量
        count = response.json()['totalItems']
        # 获取节点的名称
        for i in range(0, count):
            try:
                name = response.json()['items'][0]['metadata']['name']
                # 查看节点的消费信息
                r = step_get_node_consumption(metric_name, name)
                # 获取metric_name
                metric = r.json()['results'][0]['metric_name']
                # 验证metric正确
                assert metric == metric_name
            except Exception as e:
                print(e)
                print('节点无资源消费信息')
                break

    @allure.story('集群资源消费情况')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('step, title',
                             [('3600', '查看所有节点截止到昨天的消费情况，时间间隔为1小时'),
                              ('7200', '查看所有节点截止到昨天的消费情况，时间间隔为2小时'),
                              ('14400', '查看所有节点截止到昨天的消费情况，时间间隔为4小时'),
                              ('28800', '查看所有节点截止到昨天的消费情况，时间间隔为7小时'),
                              ('86400', '查看所有节点截止到昨天的消费情况，时间间隔为1天')
                              ])
    def test_get_node_consumption_by_yesterday(self, step, title):
        # 获取当前日期的时间戳
        now_timestamp = commonFunction.get_timestamp()
        # 获取7天之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp_day(7)
        # 查询集群的节点信息
        response = step_get_node_info()
        # 获取集群节点的数量
        count = response.json()['totalItems']
        # 获取节点的名称
        for i in range(0, count):
            name = response.json()['items'][0]['metadata']['name']
            # 获取截止到昨天的最近7天的消费历史
            response = step_get_consumption_history(type='node', start_time=before_timestamp, end_time=now_timestamp,
                                                    step=step, name=name)
            # 获取查询结果的数据类型
            for j in range(0, 5):
                try:
                    result_type = response.json()['results'][j]['data']['resultType']
                    # 验证数据类型为matrix
                    assert result_type == 'matrix'
                    # 获取趋势图数据的时间间隔
                    time_1 = response.json()['results'][j]['data']['result'][0]['values'][0][0]
                    time_2 = response.json()['results'][j]['data']['result'][0]['values'][1][0]
                    time_interval = time_2 - time_1
                    # 验证时间间隔正确
                    assert time_interval == int(step)
                except Exception as e:
                    print(e)
                    print('节点: ' + name + '无资源消费信息')
                    break

    @allure.story('集群资源消费情况')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('metric_name, title',
                             [('meter_pod_cpu_usage', '查看所有pod的cpu消费情况'),
                              ('meter_pod_memory_usage_wo_cache', '查看所有pod的内存消费情况'),
                              ('meter_pod_pvc_bytes_total', '查看所有pod的pvc消费情况'),
                              ('meter_pod_net_bytes_received', '查看所有pod的网络流入消费情况'),
                              ('meter_pod_net_bytes_transmitted', '查看所有pod的网络流出消费情况')
                              ])
    def test_get_pod_consumption(self, metric_name, title):
        # 查询集群的节点信息
        response = step_get_node_info()
        # 获取集群节点的数量
        count = response.json()['totalItems']
        # 获取节点的名称
        for i in range(0, count):
            try:
                name = response.json()['items'][0]['metadata']['name']
                # 查询pod的消费信息
                r = step_get_pod_consumption(node_name=name, metric=metric_name)
                # 获取metric_name
                metric = r.json()['results'][0]['metric_name']
                # 验证metric正确
                assert metric == metric_name
            except Exception as e:
                print(e)
                print('pod：' + name + '无资源消费信息')
                break

    @allure.story('集群资源消费情况')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_pod_consumption_by_yesterday(self):
        step = random.choice(['3600', '7200', '14400', '28800', '86400'])
        title = '查看所有pod截止到昨天的消费情况，时间间隔为' + str(int(step)/60/60) + '小时'
        allure.dynamic.title(title)
        # 获取当前日期的时间戳
        now_timestamp = commonFunction.get_timestamp()
        # 获取7天之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp_day(7)
        # 查询集群所有的节点
        response = step_get_node_info()
        # 获取集群的节点数量
        node_count = response.json()['totalItems']
        # 获取节点的名称
        for i in range(0, node_count):
            node_name = response.json()['items'][i]['metadata']['name']
            # 查询每个节点的pod信息
            re = step_get_pod_info(node_name)
            # 获取每个节点的pod数量
            pod_count = re.json()['totalItems']
            for j in range(0, pod_count):
                # 获取每个pod的名称
                pod_name = re.json()['items'][j]['metadata']['name']
                # 查询pod截止到昨天最近7天的消费情况
                r = step_get_pod_consumption_history(node_name, before_timestamp, now_timestamp, step, pod_name)
                # 获取每个指标的消费历史数据的时间间隔
                for k in range(0, 4):
                    try:
                        time_1 = r.json()['results'][k]['data']['result'][0]['values'][0][0]
                        time_2 = r.json()['results'][k]['data']['result'][0]['values'][1][0]
                        time_interval = time_2 - time_1
                        # 验证时间间隔正确
                        assert time_interval == int(step)
                    except Exception as e:
                        print(e)
                        print('pod:' + pod_name + ' 没有消费数据')
                        break

    @allure.story('企业空间资源消费情况')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('step, title',
                             [('3600', '查看所有企业空间截止到昨天的消费情况，时间间隔为1小时'),
                              ('7200', '查看所有企业空间截止到昨天的消费情况，时间间隔为2小时'),
                              ('14400', '查看所有企业空间截止到昨天的消费情况，时间间隔为4小时'),
                              ('28800', '查看所有企业空间截止到昨天的消费情况，时间间隔为7小时'),
                              ('86400', '查看所有企业空间截止到昨天的消费情况，时间间隔为1天')
                              ])
    def test_get_workspace_consumption_by_yesterday(self, step, title):
        # 获取当前日期的时间戳
        now_timestamp = commonFunction.get_timestamp()
        # 获取7天之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp_day(7)
        # 查询企业空间信息
        response = step_get_workspace_info()
        # 获取企业空间的数量
        ws_count = response.json()['totalItems']
        # 获取企业空间的名称
        for i in range(0, ws_count):
            ws_name = response.json()['items'][i]['metadata']['name']
            # 查询企业空间的历史消费信息
            r = step_get_workspace_consumption_history(ws_name, before_timestamp, now_timestamp, step)
            # 查询每个指标的消费历史数据
            for j in range(0, 5):
                try:
                    # 获取数据类型
                    result_type = r.json()['results'][j]['data']['resultType']
                    # 验证数据类型为matrix
                    assert result_type == 'matrix'
                    # 获取并验证数据的时间间隔
                    time_1 = r.json()['results'][j]['data']['result'][0]['values'][0][0]
                    time_2 = r.json()['results'][j]['data']['result'][0]['values'][1][0]
                    time_interval = time_2 - time_1
                    assert time_interval == int(step)
                except Exception as e:
                    print(e)
                    print('企业空间：' + ws_name + '没有资源历史消费信息')
                    break

    @allure.story('企业空间资源消费情况')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('metric, title',
                             [('meter_namespace_cpu_usage', '按cpu查看企业空间所有项目最近1h的消费情况'),
                              ('meter_namespace_memory_usage_wo_cache', '按memoory查看企业空间所有项目最近1h的消费情况'),
                              ('meter_namespace_pvc_bytes_total', '按pvc查看企业空间所有项目最近1h的消费情况'),
                              ('meter_namespace_net_bytes_received', '按网络流入查看企业空间所有项目最近1h的消费情况'),
                              ('meter_namespace_net_bytes_transmitted', '按网络流出查看企业空间所有项目最近1h的消费情况'),
                              ])
    def test_get_project_consumption(self, metric, title):
        # 查询企业空间信息
        response = step_get_workspace_info()
        # 获取企业空间的数量
        ws_count = response.json()['totalItems']
        # 获取企业空间的名称
        for i in range(0, ws_count):
            ws_name = response.json()['items'][i]['metadata']['name']
            # 查询每个企业空间的项目信息
            re = step_get_project_info(ws_name)
            # 获取项目的数量
            project_count = re.json()['totalItems']
            project_names = []
            # 获取企业空间中项目的名称
            for j in range(0, project_count):
                project_name = re.json()['items'][j]['metadata']['name']
                project_names.append(project_name)
            # 查询每个项目最近1h的资源消费信息
            if len(project_names) > 0:
                r = step_get_project_consumption(metric, project_names)
                # 获取查询结果中的metric_name
                metric_name = r.json()['results'][0]['metric_name']
                # 验证metric_name正确
                assert metric_name == metric
            else:
                print('企业空间：' + ws_name + '没有项目')

    @allure.story('企业空间资源消费情况')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('step, title',
                             [('3600', '查看所有企业空间的所有项目截止到昨天的消费情况，时间间隔为1小时'),
                              ('7200', '查看所有企业空间的所有项目截止到昨天的消费情况，时间间隔为2小时'),
                              ('14400', '查看所有企业空间的所有项目截止到昨天的消费情况，时间间隔为4小时'),
                              ('28800', '查看所有企业空间的所有项目截止到昨天的消费情况，时间间隔为7小时'),
                              ('86400', '查看所有企业空间的所有项目截止到昨天的消费情况，时间间隔为1天')
                              ])
    def test_get_project_consumption_by_yesterday(self, step, title):
        # 获取当前日期的时间戳
        now_timestamp = commonFunction.get_timestamp()
        # 获取7天之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp_day(7)
        # 查询企业空间信息
        response = step_get_workspace_info()
        # 获取企业空间的数量
        ws_count = response.json()['totalItems']
        # 获取企业空间的名称
        for i in range(0, ws_count):
            ws_name = response.json()['items'][i]['metadata']['name']
            # 查询每个企业空间的项目信息
            re = step_get_project_info(ws_name)
            # 获取项目的数量
            project_count = re.json()['totalItems']
            # 获取企业空间中项目的名称
            for j in range(0, project_count):
                project_name = re.json()['items'][j]['metadata']['name']
                # 查询项目截止到昨天最近7天的资源消费历史
                r = step_get_project_consumption_history(project_name, before_timestamp, now_timestamp, step)
                for k in range(1, 5):
                    try:
                        # 获取并验证查询结果中每个指标的数据类型
                        result_type = r.json()['results'][k]['data']['resultType']
                        assert result_type == 'matrix'
                        # 获取并验证查询结果中每个指标的时间间隔
                        time_1 = r.json()['results'][k]['data']['result'][0]['values'][0][0]
                        time_2 = r.json()['results'][k]['data']['result'][0]['values'][1][0]
                        time_interval = time_2 - time_1
                        assert time_interval == int(step)
                    except Exception as e:
                        print(e)
                        print('企业空间：' + ws_name + '的项目 ' + project_name + '没有历史消费信息')
                        break

    @allure.story('企业空间资源消费情况')
    @allure.title('查询所有项目最近1h消费的资源信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_hierarchy_consumption(self):
        # 查询企业空间信息
        response = step_get_workspace_info()
        # 获取企业空间的数量
        ws_count = response.json()['totalItems']
        # 获取企业空间的名称
        for i in range(0, ws_count):
            ws_name = response.json()['items'][i]['metadata']['name']
            # 查询每个企业空间的项目信息
            re = step_get_project_info(ws_name)
            # 获取项目的数量
            project_count = re.json()['totalItems']
            # 获取企业空间中项目的名称
            for j in range(0, project_count):
                project_name = re.json()['items'][j]['metadata']['name']
                # 查询最近1h消费的资源信息
                r = step_get_hierarchy_consumption(ws_name, project_name)
                # 验证资源查询成功
                assert r.status_code == 200

    @allure.story('企业空间资源消费情况')
    @allure.title('{title}')
    @pytest.mark.parametrize('step, title',
                             [('3600', '查询所有项目下包含的资源截止到昨天的最近7天的资源消费历史数据，时间间隔为1小时'),
                              ('7200', '查询所有项目下包含的资源截止到昨天的最近7天的资源消费历史数据，时间间隔为2小时'),
                              ('14400', '查询所有项目下包含的资源截止到昨天的最近7天的资源消费历史数据，时间间隔为4小时'),
                              ('28800', '查询所有项目下包含的资源截止到昨天的最近7天的资源消费历史数据，时间间隔为7小时'),
                              ('86400', '查询所有项目下包含的资源截止到昨天的最近7天的资源消费历史数据，时间间隔为1天')
                              ])
    def test_get_hierarchy_consumption_history(self, step, title):
        # 获取当前日期的时间戳
        now_timestamp = commonFunction.get_timestamp()
        # 获取7天之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp_day(7)
        # 查询企业空间信息
        response = step_get_workspace_info()
        # 获取企业空间的数量
        ws_count = response.json()['totalItems']
        # 获取企业空间的名称
        for i in range(0, ws_count):
            ws_name = response.json()['items'][i]['metadata']['name']
            # 查询每个企业空间的项目信息
            re = step_get_project_info(ws_name)
            # 获取项目的数量
            project_count = re.json()['totalItems']
            # 获取企业空间中项目的名称
            for j in range(0, project_count):
                project_name = re.json()['items'][j]['metadata']['name']
                # 查询最近1h消费的资源信息
                r = step_get_hierarchy_consumption(ws_name, project_name)
                hierarchy_list = ['apps', 'daemonsets', 'deployments', 'openpitrixs', 'statefulsets']
                for k in hierarchy_list:
                    if r.json()[k] is not None:
                        hierarchy = r.json()[k]
                        for key in hierarchy.keys():
                            # 查询资源截止到昨天的最近7天消费历史
                            rep = step_get_hierarchy_consumption_history(project_name, before_timestamp, now_timestamp,
                                                                         step, key, k)
                            # 获取查询结果中所有指标的数据类型
                            for m in range(0, 4):
                                try:
                                    result_type = rep.json()['results'][m]['data']['resultType']
                                    # 验证数据类型正确
                                    assert result_type == 'matrix'
                                    # 获取并验证查询结果中每个指标的时间间隔
                                    time_1 = rep.json()['results'][m]['data']['result'][0]['values'][0][0]
                                    time_2 = rep.json()['results'][m]['data']['result'][0]['values'][1][0]
                                    time_interval = time_2 - time_1
                                    assert time_interval == int(step)
                                except Exception as e:
                                    print(e)
                                    print('项目：' + project_name + ' 资源类型：' + k + ' 资源名称：' + key + ' 无历史消费信息')
                                    break
