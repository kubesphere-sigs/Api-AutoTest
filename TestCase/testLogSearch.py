import requests
import pytest
import allure
import sys
from config import config
from common.getHeader import get_header
from common import commonFunction
import time

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用


@allure.step('查询集群的日志总量')
def step_get_log(start_time, end_time):
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/logs?operation=statistics&start_time=' + start_time + \
                       '&end_time=' + end_time
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群日志总数的变化趋势')
def step_get_logs_trend(start_time, end_time, interval):
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/logs?operation=histogram&interval=' + interval + \
                       's&start_time=' + start_time + '&end_time=' + end_time
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('按不同条件查询集群日志总数的变化趋势')
def step_get_logs_trend_by_search(search_rule, end_time):
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/logs?operation=histogram&interval=1d&' + search_rule + '&end_time=' + end_time
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('按关键字查询日志的详情信息')
def step_get_logs_by_keyword(keyword, end_time):
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/logs?operation=query&log_query=' + keyword + \
                       '&pods=&containers=&from=0&size=50&interval=1d&end_time=' + end_time
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('按项目查询日志的详情信息')
def step_get_logs_by_project(query_rule, project_name, end_time):
    if query_rule == 'Exact Query':
        condition = 'namespaces'
    elif query_rule == 'Fuzzy Query':
        condition = 'namespace_query'
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/logs?operation=query&log_query=&pods=&containers=' \
                       '&from=0&size=50&' + condition + '=' + project_name + '&interval=1d&end_time=' + end_time
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('按工作负载查询日志的详情信息')
def step_get_logs_by_workload(query_rule, workload_name, end_time):
    if query_rule == 'Exact Query':
        condition = 'workloads'
    elif query_rule == 'Fuzzy Query':
        condition = 'workload_query'
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/logs?operation=query&log_query=&pods=&containers=' \
                       '&from=0&size=50&' + condition + '=' + workload_name + '&interval=1d&end_time=' + end_time
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('按容器组查询日志的详情信息')
def step_get_logs_by_pod(query_rule, pod_name, end_time):
    if query_rule == 'Exact Query':
        condition = 'pods'
    elif query_rule == 'Fuzzy Query':
        condition = 'pod_query'
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/logs?operation=query&log_query=&' + condition + '=' + pod_name + \
                       '&containers=&from=0&size=50&interval=1d&end_time=' + end_time
    print(url)
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('按容器查询日志的详情信息')
def step_get_logs_by_container(query_rule, container_name, end_time):
    if query_rule == 'Exact Query':
        condition = 'containers'
    elif query_rule == 'Fuzzy Query':
        condition = 'container_query'
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/logs?operation=query&log_query=&pods=' \
                       '&' + condition + '=' + container_name + '&from=0&size=50&interval=1d&end_time=' + end_time
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


@allure.step('查询项目的pod信息')
def step_get_pod_info_of_project(project_name):
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + '/pods?sortBy=startTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询容器的日志')
def step_get_container_log(pod_name, container_name, start_time, end_time):
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/logs?operation=query&log_query=&pods=' + pod_name + \
                '&sort=desc&containers=' + container_name + '&from=0&size=100' \
                '&start_time=' + start_time + '&end_time=' + end_time
    response = requests.get(url=url, headers=get_header())
    return response


@allure.feature('日志查询')
@pytest.mark.skipif(commonFunction.get_component_health_of_cluster('') is False, reason='')
@pytest.mark.skipif(commonFunction.get_components_status_of_cluster('logging') is False, reason='集群未开启logging功能')
class TestLogSearch(object):

    @allure.story('日志总量')
    @allure.title('查询当天的日志总量信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_total_logs(self):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 获取当前日期的时间戳
        day_timestamp = commonFunction.get_timestamp()
        # 查询当天的日志总量信息
        response = step_get_log(day_timestamp, now_timestamp)
        # 获取收集日志的容器数量
        pod_count = response.json()['statistics']['containers']
        # 获取收集到的日志数量
        log_counts = response.json()['statistics']['logs']
        # 验证日志数量大于0
        assert log_counts > 0
        # 验证容器数量大于0
        assert pod_count > 0

    @allure.story('日志总量')
    @allure.title('查询最近 12 小时日志总数变化趋势')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_logs_trend(self):
        # 时间间隔,单位是秒
        interval = '1800'
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 获取12小时之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp(720)
        # 查询最近 12 小时日志总数变化趋势
        response = step_get_logs_trend(before_timestamp, now_timestamp, interval)
        # 获取查询结果数据中的时间间隔
        time_1 = response.json()['histogram']['histograms'][0]['time']
        time_2 = response.json()['histogram']['histograms'][1]['time']
        time_interval = (time_2 - time_1)/1000  # 换算成秒
        # 验证时间间隔正确
        assert time_interval == int(interval)

    @allure.story('日志查询规则')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(('search_rule', 'title'),
                             [('namespaces=kubesphere', '按项目精确查询日志趋势'),
                              ('log_query=error', '按关键字查询日志趋势'),
                              ('workloads=ks', '按工作负载精确查询日志趋势'),
                              ('pods=ks', '按容器组精确查询日志趋势'),
                              ('containers=ks', '按容器精确查询日志趋势'),
                              ('namespace_query=kubesphere', '按项目精确查询日志趋势'),
                              ('workload_query=ks', '按工作负载精确查询日志趋势'),
                              ('pod_query=ks', '按容器组精确查询日志趋势'),
                              ('container_query=ks', '按容器精确查询日志趋势')
                              ])
    def test_get_logs_trend_by_search(self, search_rule, title):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 按不同条件查询日志
        response = step_get_logs_trend_by_search(search_rule, now_timestamp)
        # 获取查询结果中的总日志条数
        log_count = response.json()['histogram']['total']
        # 验证查询成功
        assert log_count >= 0

    @allure.story('日志查询规则')
    @allure.title('按关键字查询日志的详情信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_logs_by_keyword(self):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 按关键字查询日志详情信息
        response = step_get_logs_by_keyword('error', now_timestamp)
        # 获取查询到的日志数量
        logs_count = response.json()['query']['total']
        # 验证查询成功
        assert logs_count >= 0

    @allure.story('日志查询规则')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(('query_rule', 'title'),
                             [('Exact Query', '按项目精确查询日志的详情信息'),
                              ('Fuzzy Query', '按项目模糊查询日志的详情信息')
                              ])
    def test_get_logs_by_project(self, query_rule, title):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 按项目查询日志详情信息
        response = step_get_logs_by_project(query_rule, 'kube', now_timestamp)
        # 获取查询到的日志数量
        logs_count = response.json()['query']['total']
        # 验证查询成功
        assert logs_count >= 0

    @allure.story('日志查询规则')
    @allure.title('{title}')
    @pytest.mark.parametrize(('query_rule', 'title'),
                             [('Exact Query', '按工作负载精确查询日志的详情信息'),
                              ('Fuzzy Query', '按工作负载模糊查询日志的详情信息')
                              ])
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_logs_by_workload(self, query_rule, title):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 按工作负载查询日志详情信息
        response = step_get_logs_by_workload(query_rule, 'kube', now_timestamp)
        # 获取查询到的日志数量
        logs_count = response.json()['query']['total']
        # 验证查询成功
        assert logs_count >= 0

    @allure.story('日志查询规则')
    @allure.title('{title}')
    @pytest.mark.parametrize(('query_rule', 'title'),
                             [('Exact Query', '按容器组精确查询日志的详情信息'),
                              ('Fuzzy Query', '按容器组模糊查询日志的详情信息')
                              ])
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_logs_by_pod(self, query_rule, title):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 按容器组查询日志详情信息
        response = step_get_logs_by_pod(query_rule, 'kube', now_timestamp)
        # 获取查询到的日志数量
        logs_count = response.json()['query']['total']
        # 验证查询成功
        assert logs_count >= 0

    @allure.story('日志查询规则')
    @allure.title('{title}')
    @pytest.mark.parametrize(('query_rule', 'title'),
                             [('Exact Query', '按容器精确查询日志的详情信息'),
                              ('Fuzzy Query', '按容器模糊查询日志的详情信息')
                              ])
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_logs_by_container(self, query_rule, title):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 按容器查询日志详情信息
        response = step_get_logs_by_container(query_rule, 'kube', now_timestamp)
        # 获取查询到的日志数量
        logs_count = response.json()['query']['total']
        # 验证查询成功
        assert logs_count >= 0

    @allure.story('日志查询规则')
    @allure.title('查询所有容器的日志详情')
    def test_get_all_containers_log(self):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 获取7天前的时间的10位时间戳
        before_timestamp = commonFunction.get_before_timestamp(10080)
        # 查询企业空间信息
        response = step_get_workspace_info()
        # 获取企业空间的数量
        ws_count = response.json()['totalItems']
        # 获取企业空间的名称
        for i in range(0, ws_count):
            ws_name = response.json()['items'][i]['metadata']['name']
            # print(ws_name)
            # 查询每个企业空间的项目信息
            re = step_get_project_info(ws_name)
            # 获取项目的数量
            project_count = re.json()['totalItems']
            # 获取企业空间中项目的名称
            for j in range(0, project_count):
                project_name = re.json()['items'][j]['metadata']['name']
                # 获取项目的pod信息
                r = step_get_pod_info_of_project(project_name)
                # 获取项目的pod的数量
                pod_count = r.json()['totalItems']
                # 获取项目pod的名称
                for k in range(0, pod_count):
                    pod_name = r.json()['items'][k]['metadata']['name']
                    # 获取pod的容器名称
                    container = r.json()['items'][k]['spec']['containers']
                    for m in range(0, len(container)):
                        container_name = r.json()['items'][k]['spec']['containers'][m]['name']
                        # 查询容器的日志
                        r1 = step_get_container_log(pod_name, container_name, before_timestamp, now_timestamp)
                        # 获取容器的日志数量
                        logs_count = r1.json()['query']['total']
                        if logs_count == 0:
                            print('企业空间：' + ws_name + ' 项目：' + project_name + ' pod：' + pod_name + ' 容器：' + container_name + ' 最近7天没有日志')
                        # 验证日志查询成功
                        assert logs_count >= 0


