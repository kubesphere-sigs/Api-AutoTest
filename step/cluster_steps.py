import requests
import allure
import sys

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from config import config
from common.getHeader import get_header


@allure.step('获取集群的名称')
def step_get_cluster_name():
    clusters = []
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/clusters'
    response = requests.get(url=url, headers=get_header())
    for i in range(response.json()['totalItems']):
        clusters.append(response.json()['items'][i]['metadata']['name'])
    return clusters


@allure.step('查询容器的日志')
def step_get_container_log(pod_name, container_name, start_time, end_time):
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/logs?operation=query&log_query=&pods=' + pod_name + \
                '&sort=desc&containers=' + container_name + '&from=0&size=100' \
                '&start_time=' + start_time + '&end_time=' + end_time
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('获取集群的节点信息')
def step_get_node_info():
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/nodes?' \
                       'sortBy=createTime&labelSelector=%21node-role.kubernetes.io%2Fedge'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询节点的pod信息')
def step_get_pod_info(node_name):
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/pods?' \
                       'labelSelector=&nodeName=' + node_name + '&sortBy=startTime'
    response = requests.get(url=url, headers=get_header())
    return response