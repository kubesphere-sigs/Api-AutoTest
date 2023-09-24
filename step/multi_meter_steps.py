import requests
import allure
import sys
from common.getHeader import get_header
from common.getConfig import get_apiserver

env_url = get_apiserver()
sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用


@allure.step('获取集群信息')
def step_get_cluster():
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/clusters'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看资源消费历史')
def step_get_consumption_history(cluster_name, type, start_time, end_time, step, name):
    if type == 'cluster':
        url = env_url + '/kapis/clusters/' + cluster_name + '/metering.kubesphere.io/v1alpha1/' + type + \
              '?start=' + start_time + '&end=' + end_time + \
              '&step=' + step + 's&metrics_filter=meter_cluster_cpu_usage%7Cmeter_cluster_memory_usage%7C' \
                                'meter_cluster_net_bytes_transmitted%7Cmeter_cluster_net_bytes_received%7C' \
                                'meter_cluster_pvc_bytes_total&resources_filter=' + cluster_name
    elif type == 'node':
        url = env_url + '/kapis/clusters/' + cluster_name + '/metering.kubesphere.io/v1alpha1/nodes?' \
                                                               'start=' + start_time + '&end=' + end_time + \
              '&step=' + step + 's&metrics_filter=meter_node_cpu_usage%7Cmeter_node_memory_usage_wo_cache%7C' \
                                'meter_node_net_bytes_transmitted%7Cmeter_node_net_bytes_received%7C' \
                                'meter_node_pvc_bytes_total&resources_filter=' + name

    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看资源消费历史')
def step_get_node_consumption_history(cluster_name, start_time, end_time, step, name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/metering.kubesphere.io/v1alpha1/nodes?' \
                                                               'start=' + start_time + '&end=' + end_time + \
              '&step=' + step + 's&metrics_filter=meter_node_cpu_usage%7Cmeter_node_memory_usage_wo_cache%7C' \
                                'meter_node_net_bytes_transmitted%7Cmeter_node_net_bytes_received%7C' \
                                'meter_node_pvc_bytes_total&resources_filter=' + name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看集群资源消费历史')
def step_get_cluster_consumption_history(cluster_name, type, start_time, end_time, step):
    url = env_url + '/kapis/clusters/' + cluster_name + '/metering.kubesphere.io/v1alpha1/' + type + \
          '?start=' + start_time + '&end=' + end_time + \
          '&step=' + step + 's&metrics_filter=meter_cluster_cpu_usage%7Cmeter_cluster_memory_usage%7C' \
                            'meter_cluster_net_bytes_transmitted%7Cmeter_cluster_net_bytes_received%7C' \
                            'meter_cluster_pvc_bytes_total&resources_filter=' + cluster_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看pod的资源消费历史')
def step_get_pod_consumption_history(cluster_name, node_name, start_time, end_time, step, pod_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/metering.kubesphere.io/v1alpha1/nodes/' + \
          node_name + '/pods?start=' + start_time + \
          '&end=' + end_time + '&step=' + step + 's&metrics_filter=meter_pod_cpu_usage%7C' \
          'meter_pod_memory_usage_wo_cache%7Cmeter_pod_net_bytes_transmitted%7C' \
          'meter_pod_net_bytes_received&resources_filter=' + pod_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看项目的资源消费历史')
def step_get_project_consumption_history(cluster_name, project_name, start_time, end_time, step):
    url = env_url + '/kapis/clusters/' + cluster_name + '/tenant.kubesphere.io/v1alpha2/metering?start=' + \
          start_time + '&end=' + end_time + \
          '&step=' + step + 's&metrics_filter=meter_namespace_cpu_usage%7Cmeter_namespace_memory_usage_wo_cache%7C' \
                            'meter_namespace_net_bytes_transmitted%7Cmeter_namespace_net_bytes_received%7C' \
                            'meter_namespace_pvc_bytes_total&resources_filter=' + project_name + '&level=LevelNamespace'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看企业空间的资源消费历史')
def step_get_workspace_consumption_history(cluster_name, ws_name, start_time, end_time, step):
    url = env_url + '/kapis/clusters/' + cluster_name + '/metering.kubesphere.io/v1alpha1/workspaces/' + \
          ws_name + '?start=' + start_time + \
          '&end=' + end_time + '&step=' + step + \
          's&metrics_filter=meter_workspace_cpu_usage%7C' \
          'meter_workspace_memory_usage%7Cmeter_workspace_net_bytes_transmitted%7C' \
          'meter_workspace_net_bytes_received%7Cmeter_workspace_pvc_bytes_total&resources_filter=' + ws_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('获取集群的节点信息')
def step_get_node_info(cluster_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/nodes?' \
                       'sortBy=createTime&labelSelector=%21node-role.kubernetes.io%2Fedge'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询节点的消费信息')
def step_get_node_consumption(metric_name, node_name):
    url = env_url + '/kapis/metering.kubesphere.io/v1alpha1/nodes?' \
                       'metrics_filter=' + metric_name + '&resources_filter=' + node_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询节点的pod信息')
def step_get_pod_info(cluster_name, node_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/pods?' \
                       'labelSelector=&nodeName=' + node_name + '&sortBy=startTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询pod的消费信息')
def step_get_pod_consumption(cluster_name, node_name, metric):
    url = env_url + '/kapis/clusters/' + cluster_name + '/metering.kubesphere.io/v1alpha1/nodes/' + node_name + \
                       '/pods?metrics_filter=' + metric
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群的企业空间信息')
def step_get_workspace_info():
    url = env_url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces?sortBy=createTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询企业空间的项目信息')
def step_get_project_info(cluster_name, ws_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + \
          '/namespaces?labelSelector=kubefed.io%2Fmanaged%21%3Dtrue%2C%20kubesphere.io%2Fkubefed-host-namespace%21%3Dtrue&sortBy=createTime'
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
def step_get_hierarchy_consumption(cluster_name, ws_name, project_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/tenant.kubesphere.io/v1alpha2/namespaces/' + \
          project_name + \
                       '/metering/hierarchy?workspace=' + ws_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询项目下资源的历史消费信息')
def step_get_hierarchy_consumption_history(cluster_name, project_name, start_time, end_time, step, name, kind):
    url = env_url + '/kapis/clusters/' + cluster_name + '/metering.kubesphere.io/v1alpha1/namespaces/' + \
          project_name + \
          '/workloads?start=' + start_time + '&end=' + end_time + '&step=' + step + \
          's&metrics_filter=meter_workload_cpu_usage%7Cmeter_workload_memory_usage_wo_cache%7C' \
          'meter_workload_net_bytes_transmitted%7Cmeter_workload_net_bytes_received&' \
          'resources_filter=' + name + '&kind=' + kind
    response = requests.get(url=url, headers=get_header())
    return response