import requests
import allure
import sys

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from common.getHeader import get_header
from common.getConfig import get_apiserver

env_url = get_apiserver()


@allure.step('查询集群的操作审计总量')
def step_get_audits(start_time, end_time, *cluster_name):
    if cluster_name:
        for i in cluster_name:
            path = '/kapis/clusters/' + str(i) + '/tenant.kubesphere.io/v1alpha2/auditing/events'
    else:
        path = '/kapis/tenant.kubesphere.io/v1alpha2/auditing/events'
    url = env_url + path + '?operation=statistics&start_time=' + start_time + '&end_time=' + end_time + '&interval=30m'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群操作审计总数的变化趋势')
def step_get_audits_trend(start_time, end_time, *cluster_name):
    if cluster_name:
        for i in cluster_name:
            path = '/kapis/clusters/' + str(i) + '/tenant.kubesphere.io/v1alpha2/auditing/events'
    else:
        path = '/kapis/tenant.kubesphere.io/v1alpha2/auditing/events'
    url = env_url + path + '?operation=histogram&start_time=' + start_time + '&end_time=' + end_time + '&interval=30m'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('按不同条件查询集群审计总数的变化趋势')
def step_get_audits_trend_by_search(search_rule, end_time, *cluster_name):
    if cluster_name:
        for i in cluster_name:
            path = '/kapis/clusters/' + str(i) + '/tenant.kubesphere.io/v1alpha2/auditing/events'
    else:
        path = '/kapis/tenant.kubesphere.io/v1alpha2/auditing/events'
    url = env_url + path + '?operation=histogram&start_time=0&end_time=' + end_time + '&interval=1d&' + search_rule
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('按时间范围查询集群审计总数的变化趋势')
def step_get_audits_trend_by_time(interval, start_time, end_time, *cluster_name):
    if cluster_name:
        for i in cluster_name:
            path = '/kapis/clusters/' + str(i) + '/tenant.kubesphere.io/v1alpha2/auditing/events'
    else:
        path = '/kapis/tenant.kubesphere.io/v1alpha2/auditing/events'
    url = env_url + path + '?operation=histogram&start_time=' + start_time + '&end_time=' + end_time + '&interval=' + interval
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('按不同条件查询审计的信息')
def step_get_audits_by_search(search_rule, end_time, *cluster_name):
    if cluster_name:
        for i in cluster_name:
            path = '/kapis/clusters/' + str(i) + '/tenant.kubesphere.io/v1alpha2/auditing/events'
    else:
        path = '/kapis/tenant.kubesphere.io/v1alpha2/auditing/events'
    url = env_url + path + '?operation=query&from=0&size=50&' + search_rule + '&start_time=0&end_time=' + end_time + '&interval=1d'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('按时间范围查询审计的详细信息')
def step_get_audits_by_time(interval, start_time, end_time, *cluster_name):
    if cluster_name:
        for i in cluster_name:
            path = '/kapis/clusters/' + str(i) + '/tenant.kubesphere.io/v1alpha2/auditing/events'
    else:
        path = '/kapis/tenant.kubesphere.io/v1alpha2/auditing/events'
    url = env_url + path + '?operation=query&from=0&size=50&' + '&start_time=' + start_time + '&end_time=' + end_time + '&interval=' + interval
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群的事件总量')
def step_get_event(start_time, end_time, *cluster_name):
    if cluster_name:
        for i in cluster_name:
            path = '/kapis/clusters/' + str(i) + '/tenant.kubesphere.io/v1alpha2/events'
    else:
        path = '/kapis/tenant.kubesphere.io/v1alpha2/events'
    url = env_url + path + '?operation=statistics&start_time=' + start_time + '&end_time=' + end_time
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群事件总数的变化趋势')
def step_get_events_trend(start_time, end_time, interval, *cluster_name):
    if cluster_name:
        for i in cluster_name:
            path = '/kapis/clusters/' + str(i) + '/tenant.kubesphere.io/v1alpha2/events'
    else:
        path = '/kapis/tenant.kubesphere.io/v1alpha2/events'
    url = env_url + path + '?operation=histogram&interval=' + interval + '&start_time=' + start_time + '&end_time=' + end_time
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('按不同条件查询集群事件总数的变化趋势')
def step_get_events_trend_by_search(search_rule, end_time, *cluster_name):
    if cluster_name:
        for i in cluster_name:
            path = '/kapis/clusters/' + str(i) + '/tenant.kubesphere.io/v1alpha2/events'
    else:
        path = '/kapis/tenant.kubesphere.io/v1alpha2/events'
    url = env_url + path + '?operation=histogram&start_time=0&end_time=' + end_time + '&interval=1d&' + search_rule
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('按不同条件查询事件的详情信息')
def step_get_events_by_search(search_rule, end_time, *cluster_name):
    if cluster_name:
        for i in cluster_name:
            path = '/kapis/clusters/' + str(i) + '/tenant.kubesphere.io/v1alpha2/events'
    else:
        path = '/kapis/tenant.kubesphere.io/v1alpha2/events'
    url = env_url + path + '?operation=query&from=0&size=50&' + search_rule + '&start_time=0&end_time=' + end_time + '&interval=1d'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('按时间范围查询事件的详情信息')
def step_get_events_by_time(interval, start_time, end_time, *cluster_name):
    if cluster_name:
        for i in cluster_name:
            path = '/kapis/clusters/' + str(i) + '/tenant.kubesphere.io/v1alpha2/events'
    else:
        path = '/kapis/tenant.kubesphere.io/v1alpha2/events'
    url = env_url + path + '?operation=query&from=0&size=50' + '&start_time=' + start_time + '&end_time=' + end_time + '&interval=' + interval
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群的日志总量')
def step_get_log(start_time, end_time, *cluster_name):
    if cluster_name:
        for i in cluster_name:
            path = '/kapis/clusters/' + str(i) + '/tenant.kubesphere.io/v1alpha2/logs'
    else:
        path = '/kapis/tenant.kubesphere.io/v1alpha2/logs'
    url = env_url + path + '?operation=statistics&start_time=' + start_time + '&end_time=' + end_time
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群日志总数的变化趋势')
def step_get_logs_trend(start_time, end_time, interval, *cluster_name):
    path = ''
    if cluster_name:
        for i in cluster_name:
            path = '/kapis/clusters/' + str(i) + '/tenant.kubesphere.io/v1alpha2/logs'
    else:
        path = '/kapis/tenant.kubesphere.io/v1alpha2/logs'
    url = env_url + path + '?operation=histogram&interval=' + interval + '&start_time=' + start_time + '&end_time=' + end_time
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('按不同条件查询集群日志总数的变化趋势')
def step_get_logs_trend_by_search(search_rule, end_time, *cluster_name):
    if cluster_name:
        for i in cluster_name:
            path = '/kapis/clusters/' + str(i) + '/tenant.kubesphere.io/v1alpha2/logs'
    else:
        path = '/kapis/tenant.kubesphere.io/v1alpha2/logs'
    url = env_url + path + '?operation=histogram&interval=1d&' + search_rule + '&end_time=' + end_time
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('按关键字查询日志的详情信息')
def step_get_logs_by_keyword(keyword, end_time, *cluster_name):
    if cluster_name:
        for i in cluster_name:
            path = '/kapis/clusters/' + str(i) + '/tenant.kubesphere.io/v1alpha2/logs'
    else:
        path = '/kapis/tenant.kubesphere.io/v1alpha2/logs'
    url = env_url + path + '?operation=query&log_query=' + keyword + '&pods=&containers=&from=0&size=50&interval=1d&end_time=' + end_time
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('按项目查询日志的详情信息')
def step_get_logs_by_project(query_rule, project_name, end_time, *cluster_name):
    if cluster_name:
        for i in cluster_name:
            path = '/kapis/clusters/' + str(i) + '/tenant.kubesphere.io/v1alpha2/logs'
    else:
        path = '/kapis/tenant.kubesphere.io/v1alpha2/logs'
    if query_rule == 'Exact Query':
        condition = 'namespaces'
    elif query_rule == 'Fuzzy Query':
        condition = 'namespace_query'
    url = env_url + path + '?operation=query&log_query=&pods=&containers=&from=0&size=50&' + condition + '=' + project_name + '&interval=1d&end_time=' + end_time
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('按工作负载查询日志的详情信息')
def step_get_logs_by_workload(query_rule, workload_name, end_time, *cluster_name):
    if cluster_name:
        for i in cluster_name:
            path = '/kapis/clusters/' + str(i) + '/tenant.kubesphere.io/v1alpha2/logs'
    else:
        path = '/kapis/tenant.kubesphere.io/v1alpha2/logs'
    if query_rule == 'Exact Query':
        condition = 'workloads'
    elif query_rule == 'Fuzzy Query':
        condition = 'workload_query'
    url = env_url + path + '?operation=query&log_query=&pods=&containers=' \
                       '&from=0&size=50&' + condition + '=' + workload_name + '&interval=1d&end_time=' + end_time
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('按容器组查询日志的详情信息')
def step_get_logs_by_pod(query_rule, pod_name, end_time, *cluster_name):
    if cluster_name:
        for i in cluster_name:
            path = '/kapis/clusters/' + str(i) + '/tenant.kubesphere.io/v1alpha2/logs'
    else:
        path = '/kapis/tenant.kubesphere.io/v1alpha2/logs'
    if query_rule == 'Exact Query':
        condition = 'pods'
    elif query_rule == 'Fuzzy Query':
        condition = 'pod_query'
    url = env_url + path + '?operation=query&log_query=&' + condition + '=' + pod_name + \
                       '&containers=&from=0&size=50&interval=1d&end_time=' + end_time
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('按时间范围查询日志的详情信息')
def step_get_logs_by_time(interval, start_time, end_time, *cluster_name):
    if cluster_name:
        for i in cluster_name:
            path = '/kapis/clusters/' + str(i) + '/tenant.kubesphere.io/v1alpha2/logs'
    else:
        path = '/kapis/tenant.kubesphere.io/v1alpha2/logs'
    url = env_url + path + '?operation=query&log_query=&pods=&containers=&from=0&size=50&interval=' + interval + '&start_time=' + start_time + '&end_time=' + end_time
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('按容器查询日志的详情信息')
def step_get_logs_by_container(query_rule, container_name, end_time, *cluster_name):
    if cluster_name:
        for i in cluster_name:
            path = '/kapis/clusters/' + str(i) + '/tenant.kubesphere.io/v1alpha2/logs'
    else:
        path = '/kapis/tenant.kubesphere.io/v1alpha2/logs'
    if query_rule == 'Exact Query':
        condition = 'containers'
    elif query_rule == 'Fuzzy Query':
        condition = 'container_query'
    url = env_url + path + '?operation=query&log_query=&pods=&' + condition + '=' + container_name + '&from=0&size=50&interval=1d&end_time=' + end_time
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看资源消费历史')
def step_get_consumption_history(type, start_time, end_time, step, name):
    if type == 'cluster':
        url = env_url + '/kapis/metering.kubesphere.io/v1alpha1/' + type + '?start=' + start_time + '&end=' + end_time + \
              '&step=' + step + 's&metrics_filter=meter_cluster_cpu_usage%7Cmeter_cluster_memory_usage%7C' \
                                'meter_cluster_net_bytes_transmitted%7Cmeter_cluster_net_bytes_received%7C' \
                                'meter_cluster_pvc_bytes_total&resources_filter=' + name
    elif type == 'node':
        url = env_url + '/kapis/metering.kubesphere.io/v1alpha1/nodes?start=' + start_time + '&end=' + end_time + \
              '&step=' + step + 's&metrics_filter=meter_node_cpu_usage%7Cmeter_node_memory_usage_wo_cache%7C' \
                                'meter_node_net_bytes_transmitted%7Cmeter_node_net_bytes_received%7C' \
                                'meter_node_pvc_bytes_total&resources_filter=' + name

    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看pod的资源消费历史')
def step_get_pod_consumption_history(node_name, start_time, end_time, step, pod_name):
    url = env_url + '/kapis/metering.kubesphere.io/v1alpha1/nodes/' + node_name + '/pods?start=' + start_time + \
          '&end=' + end_time + '&step=' + step + 's&metrics_filter=meter_pod_cpu_usage%7C' \
          'meter_pod_memory_usage_wo_cache%7Cmeter_pod_net_bytes_transmitted%7C' \
          'meter_pod_net_bytes_received&resources_filter=' + pod_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看项目的资源消费历史')
def step_get_project_consumption_history(project_name, start_time, end_time, step):
    url = env_url + '/kapis/tenant.kubesphere.io/v1alpha2/metering?start=' + start_time + '&end=' + end_time + \
          '&step=' + step + 's&metrics_filter=meter_namespace_cpu_usage%7Cmeter_namespace_memory_usage_wo_cache%7C' \
                            'meter_namespace_net_bytes_transmitted%7Cmeter_namespace_net_bytes_received%7C' \
                            'meter_namespace_pvc_bytes_total&resources_filter=' + project_name + '&level=LevelNamespace'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看企业空间的资源消费历史')
def step_get_workspace_consumption_history(ws_name, start_time, end_time, step):
    url = env_url + '/kapis/metering.kubesphere.io/v1alpha1/workspaces/' + ws_name + '?start=' + start_time + \
          '&end=' + end_time + '&step=' + step + \
          's&metrics_filter=meter_workspace_cpu_usage%7C' \
          'meter_workspace_memory_usage%7Cmeter_workspace_net_bytes_transmitted%7C' \
          'meter_workspace_net_bytes_received%7Cmeter_workspace_pvc_bytes_total&resources_filter=' + ws_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询节点的消费信息')
def step_get_node_consumption(metric_name, node_name):
    url = env_url + '/kapis/metering.kubesphere.io/v1alpha1/nodes?' \
                       'metrics_filter=' + metric_name + '&resources_filter=' + node_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询pod的消费信息')
def step_get_pod_consumption(node_name, metric):
    url = env_url + '/kapis/metering.kubesphere.io/v1alpha1/nodes/' + node_name + '/pods?' \
                        'metrics_filter=' + metric
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询企业空间的项目的最近1h的消费信息')
def step_get_project_consumption(metric, project):
    condition = ''
    for i in project:
        condition += str(i) + '%7C'
    url = env_url + '/kapis/tenant.kubesphere.io/v1alpha2/metering?metrics_filter=' + metric + \
                       '&resources_filter=' + condition + '&level=LevelNamespace'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询项目下最近1h消费的资源')
def step_get_hierarchy_consumption(ws_name, project_name):
    url = env_url + '/kapis/tenant.kubesphere.io/v1alpha2/namespaces/' + project_name + \
                       '/metering/hierarchy?workspace=' + ws_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询项目下资源的历史消费信息')
def step_get_hierarchy_consumption_history(project_name, start_time, end_time, step, name, kind):
    url = env_url + '/kapis/metering.kubesphere.io/v1alpha1/namespaces/' + project_name + \
          '/workloads?start=' + start_time + '&end=' + end_time + '&step=' + step + \
          's&metrics_filter=meter_workload_cpu_usage%7Cmeter_workload_memory_usage_wo_cache%7C' \
          'meter_workload_net_bytes_transmitted%7Cmeter_workload_net_bytes_received&' \
          'resources_filter=' + name + '&kind=' + kind
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('获取kubeconfig')
def step_get_kubeconfig():
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha2/users/admin/kubeconfig'
    response = requests.get(url=url, headers=get_header())
    return response.text