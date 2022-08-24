import json

import allure
import requests
from common.getConfig import get_apiserver
from common.getHeader import get_header, get_header_for_patch

env_url = get_apiserver()


@allure.step('创建ippool')
def step_create_ippool(ippool_name, cidr, description):
    url = env_url + '/apis/network.kubesphere.io/v1alpha1/ippools'
    data = {"apiVersion": "network.kubesphere.io/v1alpha1",
            "kind": "IPPool",
            "metadata": {
                "annotations": {
                    "kubesphere.io/description": description,
                    "kubesphere.io/creator": "admin"},
                "name": ippool_name
            },
            "spec": {"type": "calico", "cidr": cidr}}
    response = requests.post(url=url, data=json.dumps(data), headers=get_header())
    return response


@allure.step('删除ippool')
def step_delete_ippool(ippool_name):
    url = env_url + '/apis/network.kubesphere.io/v1alpha1/ippools/' + ippool_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('按名称精确查询ippool')
def step_search_by_name(ippool_name):
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/ippools?name=' + ippool_name + '&sortBy=createTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('给ippool分配企业空间')
def step_assign_ws(ippool_name, ws_name):
    url = env_url + '/apis/network.kubesphere.io/v1alpha1/ippools/' + ippool_name
    data = {"metadata": {"labels": {"kubesphere.io/workspace": ws_name,
                                    "ippool.network.kubesphere.io/default": None}}
            }
    response = requests.patch(url=url, data=json.dumps(data), headers=get_header_for_patch())
    return response


@allure.step('获取使用ippool的企业空间数量')
def step_get_used_ws_number(ippool_name):
    url1 = env_url + '/apis/network.kubesphere.io/v1alpha1/ippools/' + ippool_name
    r = requests.get(url=url1, headers=get_header())
    num = 0
    if 'workspaces' in r.json()['status']:
        ws = r.json()['status']['workspaces']
        for i in ws:
            num = num + 1
    return num


@allure.step('获取企业空间使用的ippool数量')
def step_get_ws_ippool_number(ippool_name, ws_name):
    url = env_url + '/apis/network.kubesphere.io/v1alpha1/ippools/' + ippool_name
    r = requests.get(url=url, headers=get_header())
    if 'workspaces' in r.json()['status']:
        num = r.json()['status']['workspaces'][ws_name]['allocations']
    else:
        num = 0
    return num


@allure.step('查询所有的容器组')
def step_get_job(ippool_name):
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/pods?limit=6&labelSelector=ippool.network.kubesphere.io%2Fname%3D' \
          + ippool_name + '&sortBy=startTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询容器组')
def step_search_pod(pod_name, ippool_name):
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/pods?limit=6&labelSelector=ippool.network.kubesphere.io%2Fname%3D' \
          + ippool_name + '&name=' + pod_name + '&sortBy=startTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('创建工作负载')
def step_create_deploy(ippool_name, deploy_name, container_name, pro_name):
    ippool_name = '[\"' + ippool_name + '\"]'
    url = env_url + '/apis/apps/v1/namespaces/' + pro_name + '/deployments?dryRun=All'
    url_new = env_url + '/apis/apps/v1/namespaces/' + pro_name + '/deployments'
    data = {"apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"namespace": pro_name,
                         "labels": {"app": deploy_name},
                         "name": deploy_name,
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"replicas": 1,
                     "selector": {"matchLabels": {"app": deploy_name}},
                     "template": {"metadata": {"labels": {"app": deploy_name},
                                               "annotations": {"cni.projectcalico.org/ipv4pools": ippool_name}},
                                  "spec": {"containers": [{"name": container_name,
                                                           "imagePullPolicy": "IfNotPresent",
                                                           "image": "nginx",
                                                           "ports": [{"name": "tcp-80", "protocol": "TCP",
                                                                      "containerPort": 80}]}],
                                           "serviceAccount": "default",
                                           "initContainers": [],
                                           "volumes": [],
                                           "imagePullSecrets": None}},
                     "strategy": {"type": "RollingUpdate",
                                  "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}
                                  }
                     }
            }
    requests.post(url=url, data=json.dumps(data), headers=get_header())
    r_new = requests.post(url=url_new, data=json.dumps(data), headers=get_header())
    return r_new
