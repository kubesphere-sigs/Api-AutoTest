import json

import allure
import requests

from common.getConfig import get_apiserver
from common.getHeader import get_header, get_header_for_patch

env_url = get_apiserver()


@allure.step('创建ippool')
def step_create_ippool(ippool_name, ip, mask=31, description='', blockSize=32, cluster_name=''):
    if cluster_name == '':
        url = env_url + '/apis/network.kubesphere.io/v1alpha1/ippools'
    else:
        url = env_url + '/apis/clusters/' + cluster_name + '/network.kubesphere.io/v1alpha1/ippools'
    data = {"apiVersion": "network.kubesphere.io/v1alpha1",
            "kind": "IPPool",
            "metadata": {"name": ippool_name,
                         "annotations": {
                             "kubesphere.io/description": description,
                             "kubesphere.io/creator": "admin"
                         }},
            "spec": {"type": "calico",
                     "cidr": ip + '/' + str(mask),
                     "name": ippool_name,
                     "disabled": False,
                     "ipipMode": "Always",
                     "vxlanMode": "Never",
                     "blockSize": blockSize}}
    response = requests.post(url=url, data=json.dumps(data), headers=get_header())
    return response


@allure.step('更新ippool信息')
def step_update_ippool(id, ippool_name, spec, description='', alias='', cluster_name=''):
    if cluster_name == '':
        url = env_url + '/apis/network.kubesphere.io/v1alpha1/ippools/' + ippool_name
    else:
        url = env_url + '/apis/clusters/' + cluster_name + '/network.kubesphere.io/v1alpha1/ippools/' + ippool_name
    data = {"metadata": {"name": ippool_name,
                         "labels": {"ippool.network.kubesphere.io/id": id,
                                    "ippool.network.kubesphere.io/name": ippool_name,
                                    "ippool.network.kubesphere.io/type": "calico"},
                         "annotations": {"kubesphere.io/creator": "admin",
                                         "kubesphere.io/description": description,
                                         "kubesphere.io/alias-name": alias},
                         "finalizers": ["finalizers.network.kubesphere.io/ippool"]},
            "spec": spec}
    response = requests.patch(url=url, data=json.dumps(data), headers=get_header_for_patch())
    return response


@allure.step('删除ippool')
def step_delete_ippool(ippool_name, cluster_name=''):
    if cluster_name == '':
        url = env_url + '/apis/network.kubesphere.io/v1alpha1/ippools/' + ippool_name
    else:
        url = env_url + '/apis/clusters/' + cluster_name + '/network.kubesphere.io/v1alpha1/ippools/' + ippool_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('按名称精确查询ippool')
def step_search_by_name(ippool_name, cluster_name=''):
    if cluster_name == '':
        url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/ippools?name=' + ippool_name + '&sortBy=createTime'
    else:
        url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/ippools?name=' + ippool_name + '&sortBy=createTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('给ippool分配企业空间')
def step_assign_ws(ippool_name, ws_name, cluster_name=''):
    if cluster_name == '':
        url = env_url + '/apis/network.kubesphere.io/v1alpha1/ippools/' + ippool_name
    else:
        url = env_url + '/apis/clusters/' + cluster_name + '/network.kubesphere.io/v1alpha1/ippools/' + ippool_name
    data = {"metadata": {"labels": {"kubesphere.io/workspace": ws_name,
                                    "ippool.network.kubesphere.io/default": None}}
            }
    response = requests.patch(url=url, data=json.dumps(data), headers=get_header_for_patch())
    return response


@allure.step('获取使用ippool的企业空间数量')
def step_get_used_ws_number(ippool_name, cluster_name=''):
    if cluster_name == '':
        url = env_url + '/apis/network.kubesphere.io/v1alpha1/ippools/' + ippool_name
    else:
        url = env_url + '/apis/clusters/' + cluster_name + '/network.kubesphere.io/v1alpha1/ippools/' + ippool_name
    r = requests.get(url=url, headers=get_header())
    # 获取企业空间数量
    try:
        ws_count = len(r.json()['status']['workspaces'])
    except:
        ws_count = 0
    return ws_count


@allure.step('获取企业空间使用的ippool数量')
def step_get_ws_ippool_number(ippool_name, ws_name, cluster_name=''):
    if cluster_name == '':
        url = env_url + '/apis/network.kubesphere.io/v1alpha1/ippools/' + ippool_name
    else:
        url = env_url + '/apis/clusters/' + cluster_name + '/network.kubesphere.io/v1alpha1/ippools/' + ippool_name
    r = requests.get(url=url, headers=get_header())
    if 'workspaces' in r.json()['status']:
        num = r.json()['status']['workspaces'][ws_name]['allocations']
    else:
        num = 0
    return num


@allure.step('查询使用该ippool的所有的容器组')
def step_get_job(ippool_name, cluster_name=''):
    if cluster_name == '':
        url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/pods?limit=6&labelSelector=ippool.network.kubesphere.io%2Fname%3D' \
              + ippool_name + '&sortBy=startTime'
    else:
        url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/pods?limit=6&labelSelector=ippool.network.kubesphere.io%2Fname%3D' \
              + ippool_name + '&sortBy=startTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询使用该ippool的指定容器组')
def step_search_pod(pod_name, ippool_name, cluster_name=''):
    if cluster_name == '':
        url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/pods?limit=6&labelSelector=ippool.network.kubesphere.io%2Fname%3D' \
              + ippool_name + '&name=' + pod_name + '&sortBy=startTime'
    else:
        url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/pods?limit=6&labelSelector=ippool.network.kubesphere.io%2Fname%3D' \
              + ippool_name + '&name=' + pod_name + '&sortBy=startTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在单集群项目创建使用ippool的工作负载')
def step_create_deploy_use_ip_pool(ippool_name, deploy_name, container_name, pro_name):
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


@allure.step('在多集群环境的项目创建使用ippool的工作负载')
def step_create_deploy_use_ip_pool_multi(ippool_name, deploy_name, container_name, pro_name, cluster_name):
    ippool_name = '[\"' + ippool_name + '\"]'
    base_url = env_url + '/apis/clusters/' + cluster_name + '/apps/v1/namespaces/' + pro_name + '/deployments'
    url = base_url + '?dryRun=All'
    data = {"apiVersion": "apps/v1", "kind": "Deployment",
            "metadata": {"namespace": pro_name,
                         "labels": {"app": deploy_name}, "name": deploy_name,
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"replicas": 1, "selector": {"matchLabels": {"app": deploy_name}}, "template": {
                "metadata": {"labels": {"app": deploy_name}, "annotations": {"kubesphere.io/imagepullsecrets": "{}",
                                                                             "cni.projectcalico.org/ipv4pools": ippool_name,
                                                                             "kubesphere.io/creator": "admin"}},
                "spec": {"containers": [{"name": container_name, "imagePullPolicy": "IfNotPresent",
                                         "ports": [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80}],
                                         "image": "nginx"}], "serviceAccount": "default",
                         "terminationGracePeriodSeconds": 30, "initContainers": [], "volumes": [],
                         "imagePullSecrets": None}}, "strategy": {"type": "RollingUpdate",
                                                                  "rollingUpdate": {"maxUnavailable": "25%",
                                                                                    "maxSurge": "25%"}}}}
    requests.post(url=url, data=json.dumps(data), headers=get_header())
    response = requests.post(url=base_url, data=json.dumps(data), headers=get_header())
    return response


@allure.step('禁用IPPool')
def step_disable_ippool(ippool_name, cluster_name=''):
    if cluster_name == '':
        url = env_url + '/apis/network.kubesphere.io/v1alpha1/ippools/' + ippool_name
    else:
        url = env_url + '/apis/clusters/' + cluster_name + '/network.kubesphere.io/v1alpha1/ippools/' + ippool_name
    data = {"spec": {"disabled": True}}
    response = requests.patch(url=url, data=json.dumps(data), headers=get_header_for_patch())
    return response


@allure.step('启用IPPool')
def step_enable_ippool(ippool_name, cluster_name=''):
    if cluster_name == '':
        url = env_url + '/apis/network.kubesphere.io/v1alpha1/ippools/' + ippool_name
    else:
        url = env_url + '/apis/clusters/' + cluster_name + '/network.kubesphere.io/v1alpha1/ippools/' + ippool_name
    data = {"spec": {"disabled": False}}
    response = requests.patch(url=url, data=json.dumps(data), headers=get_header_for_patch())
    return response


@allure.step('迁移ippool')
def step_migrate_ippool(old_ippool, new_ippool, cluster_name=''):
    if cluster_name == '':
        url = env_url + '/kapis/network.kubesphere.io/v1alpha2/ippool/migrate?oldippool=' + old_ippool + '&newippool=' + new_ippool
    else:
        url = env_url + '/kapis/clusters/' + cluster_name + '/network.kubesphere.io/v1alpha2/ippool/migrate?oldippool=' + old_ippool + '&newippool=' + new_ippool
    data = {}
    response = requests.post(url=url, data=json.dumps(data), headers=get_header_for_patch())
    return response


@allure.step('创建网络策略')
def step_create_network_policy(pro_name, network_name, cluster_name=''):
    if cluster_name == '':
        url = env_url + '/apis/networking.k8s.io/v1/namespaces/' + pro_name + '/networkpolicies'
    else:
        url = env_url + '/kapis/clusters/' + cluster_name + '/networking.k8s.io/v1/namespaces/' + pro_name + '/networkpolicies'
    data = {"kind": "NetworkPolicy", "apiVersion": "networking.k8s.io/v1",
            "metadata": {"name": network_name, "namespace": pro_name,
                         "annotations": {"kubesphere.io/creator": "admin"}}, "spec": {"podSelector": {}, "ingress": [
            {"from": [{"namespaceSelector": {"matchLabels": {"kubesphere.io/namespace": "pro"}}}]}],
                                                                                      "policyTypes": ["Ingress"]}}
    response = requests.post(url=url, data=json.dumps(data), headers=get_header())
    return response


@allure.step('删除网络策略')
def step_delete_network_policy(pro_name, network_name, cluster_name=''):
    if cluster_name == '':
        url = env_url + '/apis/networking.k8s.io/v1/namespaces/' + pro_name + '/networkpolicies/' + network_name
    else:
        url = env_url + '/kapis/clusters/' + cluster_name + '/networking.k8s.io/v1/namespaces/' + pro_name + '/networkpolicies/' + network_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('查询网络策略')
def step_search_network_policy(pro_name, network_name, cluster_name=''):
    if cluster_name == '':
        url_base = '/kapis/resources.kubesphere.io/v1alpha3/'
    else:
        url_base = '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/'
    # 如果pro_name和network_name为空，则查询所有的网络策略
    if pro_name == '' and network_name == '':
        url = env_url + url_base + 'networkpolicies?sortBy=createTime&limit=10'
    # 如果pro_name为空，network_name不为空，则查询network_name的网络策略
    elif pro_name == '' and network_name != '':
        url = env_url + url_base + 'networkpolicies?name=' + network_name + '&sortBy=createTime&limit=10'
    # 如果pro_name不为空，network_name为空，则查询pro_name的网络策略
    elif pro_name != '' and network_name == '':
        url = env_url + url_base + 'namespaces/' + pro_name + '/networkpolicies?sortBy=createTime&limit=10'
    # 如果pro_name和network_name都不为空，则查询pro_name下的network_name的网络策略
    else:
        url = env_url + url_base + 'namespaces/' + pro_name + '/networkpolicies?name=' + network_name + '&sortBy=createTime&limit=10'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('修改网络策略')
def step_update_network_policy(pro_name, network_name, alias, description, cluster_name=''):
    if cluster_name == '':
        url = env_url + '/apis/networking.k8s.io/v1/namespaces/' + pro_name + '/networkpolicies/' + network_name
    else:
        url = env_url + '/kapis/clusters/' + cluster_name + '/networking.k8s.io/v1/namespaces/' + pro_name + '/networkpolicies/' + network_name
    data = {"metadata": {"name": network_name, "namespace": pro_name,
                         "annotations": {"kubesphere.io/alias-name": alias, "kubesphere.io/description": description}},
            "spec": {"podSelector": {}, "ingress": [
                {"from": [{"namespaceSelector": {"matchLabels": {"kubesphere.io/namespace": "pro"}}}]}],
                     "policyTypes": ["Ingress"]}}
    response = requests.patch(url=url, data=json.dumps(data), headers=get_header_for_patch())
    return response


@allure.step('查看网络策略的详情信息')
def step_get_network_policy_detail(pro_name, network_name, cluster_name=''):
    if cluster_name == '':
        url = env_url + '/apis/networking.k8s.io/v1/namespaces/' + pro_name + '/networkpolicies/' + network_name
    else:
        url = env_url + '/kapis/clusters/' + cluster_name + '/networking.k8s.io/v1/namespaces/' + pro_name + '/networkpolicies/' + network_name
    response = requests.get(url=url, headers=get_header())
    return response
