import requests
import allure
import sys

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from common.getHeader import get_header
from common.getConfig import get_apiserver

env_url = get_apiserver()


@allure.step('获取可观测中心显示的集群名称')
def step_get_cluster_name():
    """
    获取可观测中心显示集群信息
    :return:
    """
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/clusters?limit=-1&sortBy=createTime&page=1'
    response = requests.get(url, headers=get_header())
    counts = response.json()['totalItems']
    cluster_name = []
    for i in range(counts):
        cluster_name.append(response.json()['items'][i]['metadata']['name'])
    return cluster_name
