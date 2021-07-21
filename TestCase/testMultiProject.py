import requests
import pytest
import json
import allure
import sys
import time

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from config import config
from common.getData import DoexcleByPandas
from common.getHeader import get_header, get_header_for_patch
from common import commonFunction
import string


@allure.step('验证任务状态为完成,并返回任务的uid')
def step_get_job_status(project_name, job_name):
    """
    :param project_name: 项目名称
    :param job_name: 任务名称
    :return: 任务的uid
    """
    # 验证任务状态为完成，等待60s
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + \
          '/jobs?name=' + job_name + '&sortBy=updateTime&limit=10'
    i = 0
    while i < 60:
        r2 = requests.get(url=url, headers=get_header())
        # 捕获异常，不对异常作处理
        try:
            if r2.json()['items'][0]['status']['succeeded'] == 4:
                # print('任务从创建到运行完成耗时:' + str(i) + '秒')
                break
        except KeyError:
            time.sleep(1)
            i = i + 1
    assert r2.json()['items'][0]['status']['conditions'][0]['type'] == 'Complete'
    return r2.json()['items'][0]['metadata']['uid']


@allure.step('验证任务状态为运行中,并返回任务的uid')
def step_get_job_status_run(project_name, job_name):
    """
    :param project_name: 项目名称
    :param job_name: 任务名称
    :return: 任务的uid
    """
    # 验证任务状态为运行中
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + \
          '/jobs?name=' + job_name + '&sortBy=updateTime&limit=10'
    r2 = requests.get(url=url, headers=get_header())
    print(r2.json()['items'])
    # 捕获异常，不对异常作处理
    try:
        assert r2.json()['items'][0]['active'] == 2
        return r2.json()['items'][0]['metadata']['uid']
    except KeyError:
        pass


@allure.step('查询指定任务，并返回结果')
def step_get_assign_job(project_name, way, condition):
    """
    :param way: 查询方式 [name,status]
    :param condition: 查询条件
    :param project_name: 项目名称
    :return: 查询到的任务数量
    """
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + '/jobs?' + way + '=' + condition + '&sortBy=updateTime&limit=10'
    r = requests.get(url=url, headers=get_header())
    return r.json()['totalItems']


@allure.step('删除指定任务，并返回删除结果')
def step_delete_job(project_name, job_name):
    """
    :param project_name: 项目名称
    :param job_name: 任务名称
    :return: 删除结果
    """
    url = config.url + '/apis/batch/v1/namespaces/' + project_name + '/jobs/' + job_name
    data = {"kind": "DeleteOptions",
            "apiVersion": "v1",
            "propagationPolicy": "Background"}
    r = requests.delete(url=url, headers=get_header(), data=json.dumps(data))
    # 返回删除结果
    return r.json()['status']


@allure.step('查看任务的容器组名称信息,并获取第一个容器名称')
def step_get_job_pods(project_name, uid):
    """
    :param project_name: 项目名称
    :param uid: 容器的uid
    :return: 第一个容器的名称
    """
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + \
          '/pods?limit=10&ownerKind=Job&labelSelector=controller-uid%3D' + uid + '&sortBy=startTime'
    r = requests.get(url=url, headers=get_header())
    return r.json()['items'][0]['metadata']['name']


@allure.step('获取容器组的日志，并验证任务运行结果')
def step_get_pods_log(project_name, pod_name, job_name):
    """
    :param project_name: 项目名称
    :param pod_name: 容器名称
    :param job_name: 任务名称
    """
    container_name = 'container-' + job_name
    url = config.url + '/api/v1/namespaces/' + project_name + '/pods/' + pod_name + '/log?container=' + container_name + '&tailLines=1000&timestamps=true&follow=false'
    r = requests.get(url=url, headers=get_header())

    print(r.text)
    assert '3.1415926' in r.text


@allure.step('在多集群项目创建deployment')
def step_create_deploy(cluster_name, project_name, work_name, container_name, image, replicas, ports, volumemount,
                       volume_info, strategy):
    """
    :param cluster_name:
    :param strategy: 策略信息
    :param ports: 容器的端口信息
    :param volumemount: 绑定存储卷的设置
    :return: 接口响应对象
    :param replicas: 副本数
    :return: 接口对象
    :param volume_info: 绑定的存储卷信息
    :param project_name: 项目名称
    :param work_name: 工作负载名称
    :param container_name: 容器名称
    :param image: 镜像名称
    """
    url1 = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federateddeployments'
    url2 = url1 + '?dryRun=All'

    data = {"apiVersion": "types.kubefed.io/v1beta1", "kind": "FederatedDeployment",
            "metadata": {"namespace": project_name,
                         "name": work_name,
                         "labels": {"app": work_name},
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"placement": {"clusters": [{"name": cluster_name}]},
                     "template": {"metadata": {"namespace": project_name, "labels": {"app": work_name}},
                                  "spec": {"replicas": replicas,
                                           "selector": {"matchLabels": {"app": work_name}},
                                           "template": {"metadata": {"labels": {"app": work_name}},
                                                        "spec": {
                                                            "containers": [
                                                                {"name": container_name,
                                                                 "imagePullPolicy": "IfNotPresent",
                                                                 "image": image,
                                                                 "ports": ports,
                                                                 "volumeMounts": volumemount
                                                                 }],
                                                            "serviceAccount": "default",
                                                            "affinity": {},
                                                            "initContainers": [],
                                                            "volumes": volume_info,
                                                            "imagePullSecrets": None
                                                        }},
                                           "strategy": strategy}},
                     "overrides": [{"clusterName": cluster_name, "clusterOverrides": []}]}}

    requests.post(url=url2, headers=get_header(), data=json.dumps(data))
    response = requests.post(url=url1, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('在多集群项目创建statefulsets')
def step_create_stateful(cluster_name, project_name, work_name, container_name, image, replicas, ports, service_ports,
                         volumemount, volume_info, service_name):
    url1 = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedstatefulsets?dryRun=All'
    url3 = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedstatefulsets'
    url2 = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedservices?dryRun=All'
    url4 = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedservices'
    data1 = {"apiVersion": "types.kubefed.io/v1beta1",
             "kind": "FederatedStatefulSet",
             "metadata": {"namespace": project_name,
                          "name": work_name,
                          "labels": {"app": work_name},
                          "annotations": {"kubesphere.io/creator": "admin"}},
             "spec": {"placement": {"clusters": [{"name": cluster_name}]},
                      "template": {"metadata": {"namespace": project_name, "labels": {"app": work_name}},
                                   "spec": {"replicas": replicas, "selector": {"matchLabels": {"app": work_name}},
                                            "template": {
                                                "metadata": {"labels": {"app": work_name},
                                                             "annotations": {
                                                                 "logging.kubesphere.io/logsidecar-config": "{}"}},
                                                "spec": {"containers": [
                                                    {"name": container_name, "imagePullPolicy": "IfNotPresent",
                                                     "image": image, "ports": ports,
                                                     "volumeMounts": volumemount}],
                                                    "serviceAccount": "default", "affinity": {}, "initContainers": [],
                                                    "volumes": volume_info,
                                                    "imagePullSecrets": None}},
                                            "updateStrategy": {"type": "RollingUpdate",
                                                               "rollingUpdate": {
                                                                   "partition": 0}},
                                            "serviceName": service_name}},
                      "overrides": [{"clusterName": cluster_name, "clusterOverrides": []}]}}

    data2 = {"apiVersion": "types.kubefed.io/v1beta1",
             "kind": "FederatedService",
             "metadata": {"namespace": project_name, "name": work_name,
                          "annotations": {"kubesphere.io/alias-name": "test",
                                          "kubesphere.io/serviceType": "statefulservice",
                                          "kubesphere.io/creator": "admin"},
                          "labels": {"app": work_name}},
             "spec": {"placement":
                          {"clusters": [{"name": cluster_name}]},
                      "template": {"metadata": {"namespace": project_name, "labels": {}},
                                   "spec": {"sessionAffinity": "None",
                                            "selector": {"app": work_name},
                                            "ports": service_ports,
                                            "clusterIP": "None"}},
                      "overrides": [{"clusterName": cluster_name, "clusterOverrides": []}]}}

    requests.post(url=url1, headers=get_header(), data=json.dumps(data1))
    requests.post(url=url2, headers=get_header(), data=json.dumps(data2))
    requests.post(url=url3, headers=get_header(), data=json.dumps(data1))
    response = requests.post(url=url4, headers=get_header(), data=json.dumps(data2))
    return response


@allure.step('在多集群环境创建无状态服务')
def step_create_service(cluster_name, project_name, service_name, port):
    url1 = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedservices?dryRun=All'
    url2 = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedservices'

    data = {"apiVersion": "types.kubefed.io/v1beta1",
            "kind": "FederatedService",
            "metadata": {"namespace": project_name,
                         "annotations": {
                             "kubesphere.io/serviceType": "statelessservice",
                             "kubesphere.io/workloadName": service_name + "-v1",
                             "kubesphere.io/workloadModule": "deployments",
                             "kubesphere.io/creator": "admin"},
                         "labels": {
                             "app": service_name},
                         "name": service_name},
            "spec": {"placement": {"clusters": [{"name": cluster_name}]}, "template": {
                "metadata": {"namespace": project_name, "labels": {"version": "v1", "app": service_name}},
                "spec": {"sessionAffinity": "None", "selector": {"app": service_name},
                         "template": {"metadata": {"labels": {"version": "v1", "app": service_name}}},
                         "ports": port}},
                     "overrides": [{"clusterName": cluster_name, "clusterOverrides": []}]}}
    requests.post(url=url1, headers=get_header(), data=json.dumps(data))
    response = requests.post(url=url2, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('在多集群项目创建路由')
def step_create_route(cluster_name, project_name, ingress_name, host, service_info):
    url1 = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedingresses?dryRun=All'
    url2 = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedingresses'
    data = {"apiVersion": "types.kubefed.io/v1beta1",
            "kind": "FederatedIngress",
            "metadata": {"namespace": project_name, "name": ingress_name,
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"placement": {"clusters": [{"name": cluster_name}]},
                     "template": {"metadata": {"namespace": project_name, "labels": {}},
                                  "spec": {"rules": [
                                      {"clusters": [cluster_name], "protocol": "http", "host": host,
                                       "http": {"paths": [
                                           {"path": "/", "backend": service_info
                                            }]}}],
                                      "tls": []}},
                     "overrides": [{"clusterName": cluster_name, "clusterOverrides": [{"path": "/spec/rules", "value": [
                         {"clusters": [cluster_name], "protocol": "http", "host": host,
                          "http": {"paths": [
                              {"path": "/", "backend": service_info}]}}]},
                                                                                      {"path": "/spec/tls",
                                                                                       "value": []}]}]}}

    requests.post(url=url1, headers=get_header(), data=json.dumps(data))
    response = requests.post(url=url2, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('在多集群项目设置网关')
def step_create_gateway(cluster_name, project_name, type, annotations):
    url = config.url + '/kapis/clusters/' + cluster_name + \
          '/resources.kubesphere.io/v1alpha2/namespaces/' + project_name + '/router'
    data = {"type": type, "annotations": annotations}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('编辑多集群项目的网关')
def step_edit_gateway(cluster_name, project_name, type, annotations):
    url = config.url + '/kapis/clusters/' + cluster_name + \
          '/resources.kubesphere.io/v1alpha2/namespaces/' + project_name + '/router'
    data = {"type": type, "annotations": annotations}
    response = requests.put(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('在多集群项目删除网关')
def step_delete_gateway(cluster_name, project_name):
    url = config.url + '/kapis/clusters/' + cluster_name + \
          '/resources.kubesphere.io/v1alpha2/namespaces/' + project_name + '/router'
    data = {}
    response = requests.delete(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('查看多集群项目网关')
def step_get_gateway(cluster_name, project_name):
    url = config.url + '/kapis/clusters/' + cluster_name + \
          '/resources.kubesphere.io/v1alpha2/namespaces/' + project_name + '/router'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在多集群项目删除service')
def step_delete_service(project_name, service_name):
    url = config.url + '/api/v1/namespaces/' + project_name + '/services/' + service_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('修改多集群项目工作负载副本数')
def step_modify_work_replicas(cluster_name, project_name, type, work_name, replicas):
    """
    :param project_name: 项目名称
    :param work_name: 工作负载名称
    :param replicas: 副本数
    """
    url1 = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federated' + type + '/' + work_name
    url2 = config.url + '/apis/clusters/host/apps/v1/namespaces/' + project_name + '/' + type + '/' + work_name
    data1 = {
        "spec": {"overrides": [{"clusterName": cluster_name,
                                "clusterOverrides": [{"path": "/spec/replicas", "value": replicas}]
                                }
                               ]
                 }
    }
    data2 = {"spec": {"replicas": replicas}}
    requests.patch(url=url1, headers=get_header_for_patch(), data=json.dumps(data1))
    response = requests.patch(url=url2, headers=get_header_for_patch(), data=json.dumps(data2))
    return response


@allure.step('获取多集群项目的工作负载中所有的容器组的运行情况')
def step_get_work_pod_info(cluster_name, project_name, work_name):
    status = []
    url = config.url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/namespaces/' + \
          project_name + '/pods?ownerKind=ReplicaSet&labelSelector=app%3D' + work_name

    r = requests.get(url=url, headers=get_header())
    return r


@allure.step('在多集群环境获取指定的工作负载')
def step_get_workload(cluster_name, project_name, type, condition):
    """

    :param project_name: 项目名称
    :param type: 负载类型
    :param condition: 查询条件  如：name=test
    :return:
    """
    url = config.url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/namespaces/' \
          + project_name + '/' + type + '?' + condition
    print(url)
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('删除指定的工作负载')
def step_delete_workload(project_name, type, work_name):
    url = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federated' + type + '/' + work_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('在多集群环境创建存储卷')
def step_create_volume(cluster_name, project_name, volume_name):
    url = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedpersistentvolumeclaims'
    url2 = url + '?dryRun=All'

    data = {"apiVersion": "types.kubefed.io/v1beta1",
            "kind": "FederatedPersistentVolumeClaim",
            "metadata": {"namespace": project_name, "name": volume_name,
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"placement": {"clusters": [{"name": cluster_name}]},
                     "template": {"metadata": {"namespace": project_name, "labels": {}},
                                  "spec": {"accessModes": ["ReadWriteOnce"],
                                           "resources": {"requests": {"storage": "10Gi"}},
                                           "storageClassName": "local"}},
                     "overrides": [{"clusterName": cluster_name, "clusterOverrides": []}]}}

    requests.post(url=url2, headers=get_header(), data=json.dumps(data))
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('删除多集群项目的存储卷')
def step_delete_volume(project_name, volume_name):
    url = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + \
          '/federatedpersistentvolumeclaims/' + volume_name
    # 删除存储卷
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('查询指定的存储卷')
def step_get_volume(project_name, volume_name):
    url1 = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + \
           '/persistentvolumeclaims?name=' + volume_name + '&sortBy=createTime&limit=10'
    response = requests.get(url=url1, headers=get_header())
    return response


@allure.step('获取多集群项目存储卷状态')
def step_get_volume_status(cluster_name, project_name, volume_name):
    url = config.url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/namespaces/' \
          + project_name + '/persistentvolumeclaims?names=' + volume_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('创建sa')
def step_create_sa(project_name, sa_name):
    url = config.url + '/api/v1/namespaces/' + project_name + '/serviceaccounts'
    data = {"apiVersion": "v1", "kind": "ServiceAccount",
            "metadata": {"namespace": project_name, "labels": {}, "name": sa_name,
                         "annotations": {"kubesphere.io/creator": "admin"}}}
    requests.post(url=url, headers=get_header(), data=json.dumps(data))


@allure.step('查询指定sa并返回密钥名称')
def step_get_sa(project_name, sa_name):
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + '/serviceaccounts?name=' + sa_name + '&sortBy=createTime&limit=10'
    r = requests.get(url=url, headers=get_header())
    if r.json()['totalItems'] > 0:
        return r.json()['items'][0]['secrets'][0]['name']
    else:
        return r.json()['totalItems']


@allure.step('查询项目的角色信息')
def step_get_role(project_name, role_name):
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + project_name + '/roles?name=' + role_name + '&annotation=kubesphere.io%2Fcreator'
    response = requests.get(url, headers=get_header())
    return response


@allure.step('创建角色')
def step_create_role(project_name, role_name):
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + project_name + '/roles'
    data = {"apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "Role",
            "metadata": {"namespace": project_name,
                         "name": role_name,
                         "annotations": {"iam.kubesphere.io/aggregation-roles": "[\"role-template-view-basic\"]",
                                         "kubesphere.io/creator": "admin"}
                         },
            "rules": []}
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('查询指定角色的信息')
def step_get_project_role(project_name, rloe_name):
    """
    :param project_name: 项目名称
    :param rloe_name: 项目角色名称
    :return:
    """
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + project_name + '/roles?name=' + rloe_name
    response = requests.get(url, headers=get_header())
    return response


@allure.step('修改角色信息')
def step_edit_project_role(project_name, role_name, resourceversion, annotations):
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + project_name + '/roles/' + role_name
    data = {"metadata": {"name": role_name,
                         "namespace": project_name,
                         "resourceVersion": resourceversion,
                         "annotations": annotations
                         }
            }
    response = requests.patch(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('删除角色')
def step_project_delete_role(project_name, role_name):
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + project_name + '/roles/' + role_name
    response = requests.delete(url, headers=get_header())
    return response


@allure.step('查看指定用户')
def step_get_project_user(project_name, user_name):
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + project_name + '/members?name=' + user_name
    response = requests.get(url, headers=get_header())
    return response


@allure.step('查看指定sa详情信息')
def step_get_sa_detail(project_name, sa_name):
    url = config.url + '/api/v1/namespaces/' + project_name + '/serviceaccounts/' + sa_name
    r = requests.get(url=url, headers=get_header())


@allure.step('查看指定密钥并返回密钥类型')
def step_get_secret(project_name, secret_name):
    url = config.url + '/api/v1/namespaces/' + project_name + '/secrets/' + secret_name
    r = requests.get(url=url, headers=get_header())
    return r.json()['type']


@allure.step('删除指定sa')
def step_delete_sa(project_name, sa_name):
    url = config.url + '/api/v1/namespaces/' + project_name + '/serviceaccounts/' + sa_name
    r = requests.delete(url=url, headers=get_header())


@allure.step('删除存储卷快照')
def step_delete_volume_snapshot(project_name, snapshot_name):
    url = config.url + '/apis/snapshot.storage.k8s.io/v1beta1/namespaces/' + project_name + \
          '/volumesnapshots/' + snapshot_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('查询指定的存储卷快照')
def step_get_volume_snapshot(project_name, snapshot_name):
    url1 = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + \
           '/volumesnapshots?name=' + snapshot_name + '&sortBy=createTime&limit=10'
    response = requests.get(url=url1, headers=get_header())
    return response


@allure.step('查询指定的多集群项目')
def step_get_project(ws_name, project_name):
    url1 = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + \
           '/federatednamespaces?name=' + project_name
    response = requests.get(url=url1, headers=get_header())
    return response


@allure.step('编辑多集群项目')
def step_edit_project(cluster_name, ws_name, project_name, alias_name, description):
    url = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + \
          '/federatednamespaces/' + project_name

    data = {"metadata": {"name": project_name, "namespace": project_name,
                         "labels": {"kubesphere.io/workspace": ws_name},
                         "annotations": {"kubesphere.io/alias-name": alias_name,
                                         "kubesphere.io/creator": "admin",
                                         "kubesphere.io/description": description},
                         "finalizers": ["kubefed.io/sync-controller"]},
            "spec": {"template": {"spec": {}},
                     "placement": {"clusters": [{"name": cluster_name}]}, "overrides": [
                    {"clusterName": cluster_name, "clusterOverrides": [
                        {"path": "/metadata/annotations", "value": {"kubesphere.io/creator": "admin"}}]}]}}
    response = requests.patch(url=url, headers=get_header_for_patch(), data=json.dumps(data))
    return response


@allure.step('在多集群项目获取项目配额的resourceVersion')
def step_get_project_quota_version(cluster_name, project_name):
    url = config.url + '/api/clusters/' + cluster_name + '/v1/namespaces/' + project_name + \
          '/resourcequotas/' + project_name
    response = requests.get(url=url, headers=get_header())
    try:
        if response.json():
            return response.json()['metadata']['resourceVersion']
        else:
            return None
    except Exception as e:
        print(e)


@allure.step('在多集群项目编辑项目配额')
def step_edit_project_quota(cluster_name, project_name, hard, resource_version):
    url_put = config.url + '/api/clusters/' + cluster_name + '/v1/namespaces/' + project_name + \
              '/resourcequotas/' + project_name
    url_post = config.url + '/api/clusters/' + cluster_name + '/v1/namespaces/' + project_name + '/resourcequotas'

    data_post = {"apiVersion": "v1",
                 "kind": "ResourceQuota",
                 "metadata": {
                     "name": project_name,
                     "namespace": project_name,
                     "cluster": cluster_name,
                     "annotations": {"kubesphere.io/creator": "admin"}}, "spec": {
            "hard": hard}}

    data_put = {"apiVersion": "v1",
                "kind": "ResourceQuota",
                "metadata": {
                    "name": project_name,
                    "namespace": project_name,
                    "cluster": cluster_name,
                    "resourceVersion": resource_version},
                "spec": {
                    "hard": hard}}

    if resource_version is None:
        response = requests.post(url=url_post, headers=get_header(), data=json.dumps(data_post))
    else:
        response = requests.put(url=url_put, headers=get_header(), data=json.dumps(data_put))
    return response


@allure.step('在多集群项目查询项目配额')
def step_get_project_quota(cluster_name, project_name):
    url = config.url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha2/namespaces/' + \
          project_name + '/quotas'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('获取容器默认资源请求')
def step_get_container_quota(project_name, ws_name):
    url = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + \
          '/federatedlimitranges?workspace=' + ws_name
    try:
        response = requests.get(url=url, headers=get_header())
        return response
    except Exception as e:
        print(e)


@allure.step('在多集群项目编辑容器资源默认请求')
def step_edit_container_quota(cluster_name, project_name, resource_version, limit, request):
    url_post = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedlimitranges'
    url_put = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + \
              '/federatedlimitranges/' + project_name

    data_post = {"apiVersion": "types.kubefed.io/v1beta1",
                 "kind": "FederatedLimitRange",
                 "metadata": {"name": project_name,
                              "annotations": {"kubesphere.io/creator": "admin"}},
                 "spec": {"placement": {"clusters": [{"name": cluster_name}]},
                          "template": {"metadata": {}, "spec": {
                              "limits": [
                                  {"default": limit,
                                   "defaultRequest": request,
                                   "type": "Container"}
                              ]}},
                          "overrides": [{"clusterName": cluster_name, "clusterOverrides": []}]}}

    data_put = {"apiVersion": "types.kubefed.io/v1beta1",
                "kind": "FederatedLimitRange",
                "metadata": {"annotations": {"kubesphere.io/creator": "admin"},
                             "finalizers": ["kubefed.io/sync-controller"],
                             "name": project_name,
                             "namespace": project_name,
                             "resourceVersion": resource_version},
                "spec": {"overrides": [{"clusterName": cluster_name,
                                        "clusterOverrides": []}],
                         "placement": {"clusters": [{"name": cluster_name}]},
                         "template": {"metadata": {}, "spec": {
                             "limits": [{"defaultRequest": request,
                                         "type": "Container",
                                         "default": limit}]
                         }}}}
    if resource_version is None:
        response = requests.post(url=url_post, headers=get_header(), data=json.dumps(data_post))
    else:
        response = requests.put(url=url_put, headers=get_header(), data=json.dumps(data_put))
    return response


@allure.step('删除指定的项目')
def step_delete_project(ws_name, project_name):
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/namespaces/' + project_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('创建系统用户')
def step_create_user(user_name):
    """
    :param user_name: 系统用户的名称
    """
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/users'
    data = {"apiVersion": "iam.kubesphere.io/v1alpha2",
            "kind": "User",
            "metadata": {"name": user_name,
                         "annotations": {"kubesphere.io/creator": "admin"}
                         },
            "spec": {"email": "stevewen@yunify.com",
                     "password": "P@88w0rd"}
            }
    requests.post(url, headers=get_header(), data=json.dumps(data))


@allure.step('获取集群的名称')
def step_get_cluster_name():
    clusters = []
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/clusters'
    response = requests.get(url=url, headers=get_header())
    for i in range(response.json()['totalItems']):
        clusters.append(response.json()['items'][i]['metadata']['name'])
    return clusters


@allure.step('创建多集群企业空间')
def step_create_multi_ws(ws_name, alias_name, description, cluster_names):
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces'
    clusters = []
    if isinstance(cluster_names, str):
        clusters.append({'name': cluster_names})
    else:
        for cluster_name in cluster_names:
            clusters.append({'name': cluster_name})
    data = {"apiVersion": "tenant.kubesphere.io/v1alpha2",
            "kind": "WorkspaceTemplate",
            "metadata":
                {"name": ws_name,
                 "annotations": {
                     "kubesphere.io/alias-name": alias_name,
                     "kubesphere.io/description": description,
                     "kubesphere.io/creator": "admin"}
                 },
            "spec": {"template": {"spec": {"manager": "admin"}},
                     "placement": {"clusters": clusters}}}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('在多集群环境查询企业空间')
def step_get_ws_info(ws_name):
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces?name=' + ws_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('创建多集群项目')
def step_create_multi_project(ws_name, project_name, clusters):
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/namespaces'
    url1 = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatednamespaces?dryRun=All'
    url2 = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatednamespaces'
    cluster_actual = []
    overrides = []
    if isinstance(clusters, str):
        cluster_actual.append({"name": clusters})
        overrides.append({"clusterName": clusters,
                          "clusterOverrides": [
                              {"path": "/metadata/annotations",
                               "value": {"kubesphere.io/creator": "admin"}}]})

    else:
        for cluster in clusters:
            cluster_actual.append({"name": cluster})
            overrides.append({"clusterName": cluster,
                              "clusterOverrides": [
                                  {"path": "/metadata/annotations",
                                   "value": {"kubesphere.io/creator": "admin"}}]})
    data = {"apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": project_name,
                "labels": {
                    "kubesphere.io/workspace": ws_name,
                    "kubesphere.io/kubefed-host-namespace": "true",
                    "kubefed.io/managed": "false"
                },
                "annotations": {"kubesphere.io/creator": "admin"}}, "spec": {}}

    data1 = {"apiVersion": "types.kubefed.io/v1beta1",
             "kind": "FederatedNamespace",
             "metadata": {
                 "name": project_name, "namespace": project_name,
                 "labels": {"kubesphere.io/workspace": ws_name},
                 "annotations": {"kubesphere.io/creator": "admin"}},
             "spec": {"placement":
                          {"clusters": cluster_actual},
                      "template": {"metadata": {"labels": {"kubesphere.io/workspace": ws_name}}},
                      "overrides": overrides}}
    requests.post(url=url, headers=get_header(), data=json.dumps(data))
    requests.post(url=url1, headers=get_header(), data=json.dumps(data1))
    requests.post(url=url2, headers=get_header(), data=json.dumps(data1))


@allure.step('获取环境中所有的多集群项目的名称和部署集群')
def step_get_multi_project_all():
    multi_projects = []
    response = step_get_ws_info('')
    ws_count = response.json()['totalItems']
    for k in range(0, ws_count):
        # 获取每个企业空间的名称
        ws_name = response.json()['items'][k]['metadata']['name']
        if ws_name != 'system-workspace':
            # 查询环境中存在的所有多集群项目
            r = step_get_project(ws_name, '')
            project_count = r.json()['totalItems']
            for i in range(0, project_count):
                project_info = []
                project_name = r.json()['items'][i]['metadata']['name']
                project_info.append(project_name)
                overrides = r.json()['items'][i]['spec']['overrides']
                override_count = len(overrides)
                for j in range(0, override_count):
                    cluster_name = overrides[j]['clusterName']
                    project_info.append(cluster_name)
                project_info.append(ws_name)
                multi_projects.append(project_info)

    return multi_projects


@allure.step('获取环境中所有的多集群项目的名称')
def step_get_multi_projects_name():
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/federatednamespaces?sortBy=createTime'
    response = requests.get(url=url, headers=get_header())
    multi_project_name = []
    for i in range(0, response.json()['totalItems']):
        multi_project_name.append(response.json()['items'][i]['metadata']['name'])
    return multi_project_name


@allure.step('按名称删除项目')
def step_delete_project_by_name(project_name):
    url = config.url + '/api/v1/namespaces/' + project_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('在多集群项目创建默认密钥')
def step_create_secret_default(cluster_name, project_name, secret_name, key, value):
    url = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedsecrets'
    url1 = url + '?dryRun=All'
    data = {"apiVersion": "types.kubefed.io/v1beta1",
            "kind": "FederatedSecret",
            "metadata": {"namespace": project_name,
                         "name": secret_name,
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"placement": {"clusters": [{"name": cluster_name}]},
                     "template": {"metadata":
                                      {"namespace": project_name, "labels": {}},
                                  "type": "Opaque",
                                  "spec": {"template": {"metadata": {"labels": {}}}},
                                  "data": {key: value}},
                     "overrides": [{"clusterName": cluster_name, "clusterOverrides": []}
                                   ]}}

    requests.post(url=url1, headers=get_header(), data=json.dumps(data))
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('在多集群项目创建TLS类型密钥')
def step_create_secret_tls(cluster_name, project_name, secret_name, credential, key):
    url = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedsecrets'
    url1 = url + '?dryRun=All'
    data = {"apiVersion": "types.kubefed.io/v1beta1",
            "kind": "FederatedSecret",
            "metadata": {"namespace": project_name,
                         "name": secret_name,
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"placement": {"clusters": [{"name": cluster_name}]},
                     "template": {"metadata":
                                      {"namespace": project_name, "labels": {}},
                                  "type": "kubernetes.io/tls",
                                  "spec": {"template": {"metadata": {"labels": {}}}},
                                  "data": {"tls.crt": credential, "tls.key": key}},
                     "overrides": [{"clusterName": cluster_name, "clusterOverrides": []}
                                   ]}}
    requests.post(url=url1, headers=get_header(), data=json.dumps(data))
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('在多集群项目查询密钥')
def step_get_secret(project_name, secret_name):
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + \
          '/federatedsecrets?name=' + secret_name + '&sortBy=createTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在多集群项目查询配置')
def step_get_config_map(project_name, config_name):
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + \
          '/federatedconfigmaps?name=' + config_name + '&sortBy=createTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在多集群项目创建镜像仓库类型密钥')
def step_create_secret_image(cluster_name, project_name, secret_name):
    url = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedsecrets'
    url1 = url + '?dryRun=All'
    data = {"apiVersion": "types.kubefed.io/v1beta1",
            "kind": "FederatedSecret",
            "metadata": {"namespace": project_name,
                         "name": secret_name,
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"placement": {"clusters": [{"name": cluster_name}]},
                     "template": {"metadata": {"namespace": project_name, "labels": {}},
                                  "type": "kubernetes.io/dockerconfigjson",
                                  "spec": {"template": {"metadata": {"labels": {}}}},
                                  "data": {
                                      ".dockerconfigjson": "eyJhdXRocyI6eyJodHRwczovL3NzIjp7InVzZXJuYW1lIjoic2FzYSIs"
                                                           "InBhc3N3b3JkIjoic2FzYSIsImVtYWlsIjoiIiwiYXV0aCI6ImMyRnpZ"
                                                           "VHB6WVhOaCJ9fX0="}},
                     "overrides": [{"clusterName": cluster_name, "clusterOverrides": []}]}}

    requests.post(url=url1, headers=get_header(), data=json.dumps(data))
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('在多集群项目创建账户密码密钥')
def step_create_secret_account(cluster_name, project_name, secret_name, username, password):
    url = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedsecrets'
    url1 = url + '?dryRun=All'
    data = {"apiVersion": "types.kubefed.io/v1beta1",
            "kind": "FederatedSecret",
            "metadata": {"namespace": project_name,
                         "name": secret_name,
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"placement": {"clusters": [{"name": cluster_name}]},
                     "template": {"metadata":
                                      {"namespace": project_name, "labels": {}},
                                  "type": "kubernetes.io/basic-auth",
                                  "spec": {"template": {"metadata": {"labels": {}}}},
                                  "data": {"password": password, "username": username}},
                     "overrides": [{"clusterName": cluster_name, "clusterOverrides": []}
                                   ]}}

    requests.post(url=url1, headers=get_header(), data=json.dumps(data))
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('在多集群项目删除密钥')
def step_delete_secret(project_name, secret_name):
    url = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedsecrets/' + secret_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('在多集群项目删除配置')
def step_delete_config_map(project_name, config_name):
    url = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + \
                       '/federatedconfigmaps/' + config_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('在多集群项目创建配置')
def step_create_config_map(cluster_name, project_name, config_name, key, value):
    url = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedconfigmaps'
    url1 = url + '?dryRun=All'
    data = {"apiVersion": "types.kubefed.io/v1beta1",
            "kind": "FederatedConfigMap",
            "metadata": {
                "namespace": project_name,
                "name": config_name,
                "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"placement": {"clusters": [{"name": cluster_name}]},
                     "template": {"metadata": {"namespace": project_name, "labels": {}},
                                  "spec": {"template": {"metadata": {"labels": {}}}},
                                  "data": {value: key}},
                     "overrides": [{"clusterName": cluster_name, "clusterOverrides": []}]}}
    requests.post(url=url1, headers=get_header(), data=json.dumps(data))
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('在多集群环境设置落盘日志收集功能')
def step_set_disk_log_collection(project_name, set):
    url = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + \
                       '/federatednamespaces/' + project_name
    data = {"metadata":
                {"labels":
                     {"logging.kubesphere.io/logsidecar-injection": set}},
            "spec":
                {"template":
                     {"metadata":
                          {"labels":
                               {"logging.kubesphere.io/logsidecar-injection": set}}}}}
    response = requests.patch(url=url, headers=get_header_for_patch(), data=json.dumps(data))
    return response


@allure.step('在多集群环境查询落盘日志收集功能')
def step_check_disk_log_collection(project_name):
    url = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + \
                       '/federatednamespaces/' + project_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在多集群环境查询项目的监控信息')
def step_get_project_metrics(cluster_name, project_name, start_time, end_time, step, times):
    url = config.url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/namespaces/' + \
          project_name + '?namespace=' + project_name + '&start=' + start_time + '&end=' + end_time + \
          '&step=' + step + '&times=' + times + '&metrics_filter=namespace_pod_count%7C' \
          'namespace_deployment_count%7Cnamespace_statefulset_count%7C' \
          'namespace_daemonset_count%7Cnamespace_job_count%7Cnamespace_cronjob_count%7Cnamespace_pvc_count%7C' \
          'namespace_service_count%7Cnamespace_secret_count%7Cnamespace_configmap_count%7C' \
          'namespace_ingresses_extensions_count%7Cnamespace_s2ibuilder_count%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在多集群环境查询项目的abnormalworkloads')
def step_get_project_abnormalworkloads(cluster_name, project_name):
    url = config.url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha2/namespaces/' + \
          project_name + '/abnormalworkloads'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在多集群环境查询项目的federatedlimitranges')
def step_get_project_federatedlimitranges(project_name):
    url = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedlimitranges'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在多集群环境查询项目的workloads')
def step_get_project_workloads(cluster_name, project_name):
    url = config.url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/namespaces/' + \
          project_name+ '/workloads?type=rank&metrics_filter=workload_cpu_usage%7Cworkload_memory_usage_wo_cache%7C' \
                        'workload_net_bytes_transmitted%7Cworkload_net_bytes_received%7Creplica&page=1&limit=10' \
                        '&sort_type=desc&sort_metric=workload_cpu_usage'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.feature('多集群项目管理')
@pytest.mark.skipif(commonFunction.check_multi_cluster() is False, reason='未开启多集群功能')
@pytest.mark.skipif(commonFunction.check_multi_cluster() is False, reason='单集群环境下不执行')
class TestProject(object):
    volume_name = 'testvolume'  # 存储卷名称，在创建、删除存储卷和创建存储卷快照时使用,excle中的用例也用到了这个存储卷
    snapshot_name = 'testshot'  # 存储卷快照的名称,在创建和删除存储卷快照时使用，在excle中的用例也用到了这个快照
    user_name = 'user-for-test-project'  # 系统用户名称
    ws_name = 'ws-for-test-project'  # 企业空间名称,不可修改，从excle中获取的测试用例中用到了这个企业空间
    alias_name = '我是别名'
    description = '我是描述'
    project_name = 'test-project'  # 项目名称，从excle中获取的测试用例中用到了这个项目名称
    ws_role_name = ws_name + '-viewer'  # 企业空间角色名称
    project_role_name = 'test-project-role'  # 项目角色名称
    job_name = 'demo-job'  # 任务名称,在创建和删除任务时使用
    work_name = 'workload-demo'  # 工作负载名称，在创建、编辑、删除工作负载时使用

    # 所有用例执行之前执行该方法
    def setup_class(self):
        step_create_user(self.user_name)  # 创建一个用户
        # 获取集群名称
        clusters = step_get_cluster_name()
        # 创建一个多集群企业空间（包含所有的集群）
        step_create_multi_ws(self.ws_name + str(commonFunction.get_random()), self.alias_name, self.description,
                             clusters)
        # 创建若干个多集群企业空间（只部署在单个集群）
        for i in range(len(clusters)):
            step_create_multi_ws(self.ws_name + str(commonFunction.get_random()), self.alias_name,
                                 self.description, clusters[i])
        # 在每个企业空间创建多集群项目,且将其部署在所有和单个集群上
        response = step_get_ws_info('')
        ws_count = response.json()['totalItems']
        for k in range(0, ws_count):
            # 获取每个企业空间的名称
            ws_name = response.json()['items'][k]['metadata']['name']
            # 获取企业空间的集群信息
            if ws_name != 'system-workspace':
                clusters_name = []
                re = step_get_ws_info(ws_name)
                clusters = re.json()['items'][0]['spec']['placement']['clusters']
                for i in range(0, len(clusters)):
                    clusters_name.append(clusters[i]['name'])
                if len(clusters_name) > 1:
                    # 创建多集群项目,但是项目部署在单个集群上
                    for j in range(0, len(clusters_name)):
                        multi_project_name = 'multi-pro' + str(commonFunction.get_random())
                        step_create_multi_project(ws_name, multi_project_name, clusters_name[j])
                else:
                    multi_project_name = 'multi-pro' + str(commonFunction.get_random())
                    step_create_multi_project(ws_name, multi_project_name, clusters_name)

    # 所有用例执行完之后执行该方法
    def teardown_class(self):
        # 获取环境中所有的多集群项目
        multi_project_name = step_get_multi_projects_name()
        for multi_project in multi_project_name:
            if 'multi-pro' in multi_project:
                # 删除创建的多集群项目
                step_delete_project_by_name(multi_project)
        time.sleep(5)
        # 获取环境中所有的企业空间
        response = step_get_ws_info('')
        ws_count = response.json()['totalItems']
        for k in range(0, ws_count):
            # 获取每个企业空间的名称
            ws_name = response.json()['items'][k]['metadata']['name']
            # 获取企业空间的集群信息
            if ws_name != 'system-workspace':
                commonFunction.delete_workspace(ws_name)  # 删除创建的工作空间

    @allure.story('存储管理-存储卷')
    @allure.title('在多集群项目创建存储卷，然后将存储卷绑定到新建的deployment上，最后验证资源和存储卷的状态正常')
    @allure.severity(allure.severity_level.BLOCKER)
    def test_create_volume_for_deployment(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            type_name = 'volume-type'  # 存储卷的类型
            work_name = 'workload' + str(commonFunction.get_random())  # 工作负载名称
            volume_name = 'volume-deploy' + str(commonFunction.get_random())  # 存储卷名称
            replicas = 1  # 副本数
            image = 'redis'  # 镜像名称
            container_name = 'container' + str(commonFunction.get_random())  # 容器名称
            condition = 'name=' + work_name  # 查询条件
            port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80}]  # 容器的端口信息
            volumeMounts = [{"name": type_name, "readOnly": False, "mountPath": "/data"}]  # 设置挂载哦的存储卷
            strategy_info = {"type": "RollingUpdate",
                             "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
            volume_info = [{"name": type_name, "persistentVolumeClaim": {"claimName": volume_name}}]  # 存储卷的信息
            # 创建存储卷
            step_create_volume(cluster_name=project_info[1], project_name=project_info[0], volume_name=volume_name)
            # 创建资源并将存储卷绑定到资源
            step_create_deploy(cluster_name=project_info[1], project_name=project_info[0], work_name=work_name,
                               image=image, replicas=replicas, container_name=container_name,
                               volume_info=volume_info, ports=port,
                               volumemount=volumeMounts, strategy=strategy_info)
            time.sleep(10)  # 等待资源创建成功
            # 获取工作负载的状态
            response = step_get_workload(cluster_name=project_info[1], project_name=project_info[0],
                                         type='deployments', condition=condition)
            try:
                readyReplicas = response.json()['items'][0]['status']['readyReplicas']
            except Exception as e:
                print(e)
                # 删除工作负载
                step_delete_workload(project_name=project_info[0], type='deployments', work_name=work_name)
                # 删除存储卷
                step_delete_volume(project_info[0], volume_name)
                pytest.xfail('工作负载创建失败，标记为xfail')
                break
            # 验证资源的所有副本已就绪
            assert readyReplicas == replicas
            # 获取存储卷状态
            re = step_get_volume_status(cluster_name=project_info[1], project_name=project_info[0],
                                        volume_name=volume_name)
            status = re.json()['items'][0]['status']['phase']
            # 验证存储卷状态正常
            assert status == 'Bound'
            # 删除工作负载
            step_delete_workload(project_name=project_info[0], type='deployments', work_name=work_name)
            # 删除存储卷
            step_delete_volume(project_info[0], volume_name)

    @allure.story('存储管理-存储卷')
    @allure.title('在多集群项目创建存储卷，然后将存储卷绑定到新建的statefulsets上，最后验证资源和存储卷的状态正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_volume_for_statefulsets(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            volume_name = 'volume-stateful' + str(commonFunction.get_random())  # 存储卷的名称
            type_name = 'volume-type'  # 存储卷的类型
            work_name = 'stateful' + str(commonFunction.get_random())  # 工作负载的名称
            service_name = 'service' + volume_name  # 服务名称
            replicas = 2  # 副本数
            image = 'nginx'  # 镜像名称
            container_name = 'container-stateful' + str(commonFunction.get_random())  # 容器名称
            condition = 'name=' + work_name  # 查询条件
            port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]
            service_port = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]
            volumemounts = [{"name": type_name, "readOnly": False, "mountPath": "/data"}]
            volume_info = [{"name": type_name, "persistentVolumeClaim": {"claimName": volume_name}}]  # 存储卷的信息
            # 创建存储卷
            step_create_volume(cluster_name=project_info[1], project_name=project_info[0], volume_name=volume_name)
            # 创建资源并将存储卷绑定到资源
            step_create_stateful(cluster_name=project_info[1], project_name=project_info[0], work_name=work_name,
                                 container_name=container_name, image=image, replicas=replicas,
                                 ports=port, service_ports=service_port,
                                 volumemount=volumemounts, volume_info=volume_info, service_name=service_name)

            # 验证资源创建成功
            time.sleep(10)  # 等待资源创建成功
            # 获取工作负载的状态
            response = step_get_workload(cluster_name=project_info[1], project_name=project_info[0],
                                         type='statefulsets', condition=condition)
            try:
                readyReplicas = response.json()['items'][0]['status']['readyReplicas']
            except Exception as e:
                print(e)
                # 删除工作负载
                step_delete_workload(project_name=project_info[0], type='deployments', work_name=work_name)
                # 删除存储卷
                step_delete_volume(project_info[0], volume_name)
                pytest.xfail('工作负载创建失败，标记为xfail')
                break
            # 验证资源的所有副本已就绪
            assert readyReplicas == replicas
            # 获取存储卷状态
            response = step_get_volume_status(cluster_name=project_info[1], project_name=project_info[0],
                                              volume_name=volume_name)
            status = response.json()['items'][0]['status']['phase']
            # 验证存储卷状态正常
            assert status == 'Bound'
            # 删除工作负载
            step_delete_workload(project_name=project_info[0], type='deployments', work_name=work_name)
            # 删除存储卷
            step_delete_volume(project_info[0], volume_name)

    @allure.story('存储管理-存储卷')
    @allure.title('在多集群项目创建存储卷，然后将存储卷绑定到新建的service上，最后验证资源和存储卷的状态正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_volume_for_service(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            volume_name = 'volume-service' + str(commonFunction.get_random())  # 存储卷的名称
            type_name = 'volume-type'  # 存储卷的类型
            service_name = 'service' + str(commonFunction.get_random())  # 工作负载的名称
            image = 'redis'  # 镜像名称
            container_name = 'container-daemon' + str(commonFunction.get_random())  # 容器名称
            condition = 'name=' + service_name  # 查询条件
            port_service = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]  # service的端口信息
            port_deploy = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80}]  # 容器的端口信息
            volumeMounts = [{"name": type_name, "readOnly": False, "mountPath": "/data"}]  # 设置挂载哦的存储卷
            volume_info = [{"name": type_name, "persistentVolumeClaim": {"claimName": volume_name}}]  # 存储卷的信息
            strategy_info = {"type": "RollingUpdate",
                             "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
            replicas = 2  # 副本数
            # 创建存储卷
            step_create_volume(cluster_name=project_info[1], project_name=project_info[0], volume_name=volume_name)
            # 创建service
            step_create_service(cluster_name=project_info[1], project_name=project_info[0],
                                service_name=service_name, port=port_service)
            # 创建service绑定的deployment
            step_create_deploy(cluster_name=project_info[1], project_name=project_info[0],
                               work_name=service_name, container_name=container_name,
                               ports=port_deploy, volumemount=volumeMounts, image=image, replicas=replicas,
                               volume_info=volume_info, strategy=strategy_info)
            # 验证service创建成功
            response = step_get_workload(cluster_name=project_info[1], project_name=project_info[0],
                                         type='services', condition=condition)
            try:
                name = response.json()['items'][0]['metadata']['name']
            except Exception as e:
                print(e)
                # 删除service
                step_delete_workload(project_name=project_info[0], type='services', work_name=service_name)
                # 删除deployment
                step_delete_workload(project_name=project_info[0], type='deployments', work_name=service_name)
                # 删除存储卷
                step_delete_volume(project_info[0], volume_name)
                pytest.xfail('服务创建失败，标记为xfail')
                break
            assert name == service_name
            # 验证deploy创建成功
            time.sleep(3)
            re = step_get_workload(cluster_name=project_info[1], project_name=project_info[0],
                                   type='deployments', condition=condition)
            # 获取并验证deployment的名称正确
            try:
                name = re.json()['items'][0]['metadata']['name']
            except Exception as e:
                print(e)
                # 删除service
                step_delete_workload(project_name=project_info[0], type='services', work_name=service_name)
                # 删除deployment
                step_delete_workload(project_name=project_info[0], type='deployments', work_name=service_name)
                # 删除存储卷
                step_delete_volume(project_info[0], volume_name)
                pytest.xfail('deploymenet创建失败，标记为xfail')
                break
            assert name == service_name
            # 获取存储卷状态
            response = step_get_volume_status(cluster_name=project_info[1], project_name=project_info[0],
                                              volume_name=volume_name)
            status = response.json()['items'][0]['status']['phase']
            # 验证存储卷状态正常
            assert status == 'Bound'
            # 删除service
            step_delete_workload(project_name=project_info[0], type='services', work_name=service_name)
            # 删除deployment
            step_delete_workload(project_name=project_info[0], type='deployments', work_name=service_name)
            # 删除存储卷
            step_delete_volume(project_info[0], volume_name)

    @allure.story('应用负载-工作负载')
    @allure.title('在多集群项目创建未绑定存储卷的deployment，并验证运行成功')
    @allure.severity(allure.severity_level.BLOCKER)
    def test_create_deployment(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            workload_name = 'workload' + str(commonFunction.get_random())  # 工作负载名称
            container_name = 'container' + str(commonFunction.get_random())  # 容器名称
            image = 'nginx'  # 镜像名称
            condition = 'name=' + workload_name  # 查询条件
            port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 81}]  # 容器的端口信息
            volumeMounts = []  # 设置挂载的存储卷
            strategy_info = {"type": "RollingUpdate",
                             "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
            replicas = 2  # 副本数
            volume_info = []
            # 创建工作负载
            step_create_deploy(cluster_name=project_info[1], project_name=project_info[0], work_name=workload_name,
                               container_name=container_name, ports=port, volumemount=volumeMounts,
                               image=image, replicas=replicas, volume_info=volume_info,
                               strategy=strategy_info)

            # 在工作负载列表中查询创建的工作负载，并验证其状态为运行中，最长等待时间60s
            i = 0
            while i < 60:
                response = step_get_workload(cluster_name=project_info[1], project_name=project_info[0],
                                             type='deployments', condition=condition)
                try:
                    status = response.json()['items'][0]['status']
                except Exception as e:
                    print(e)
                    # 删除deployment
                    step_delete_workload(project_name=project_info[0], type='deployments', work_name=workload_name)
                    pytest.xfail('deploymenet创建失败，标记为xfail')
                    break
                # 验证资源的所有副本已就绪
                if 'unavailableReplicas' not in status:
                    print('创建工作负载耗时:' + str(i) + 's')
                    break
                time.sleep(1)
                i = i + 1
            assert 'unavailableReplicas' not in status
            # 删除deployment
            re = step_delete_workload(project_name=project_info[0], type='deployments', work_name=workload_name)
            assert re.json()['status']['conditions'][0]['status'] == 'True'

    @allure.story('应用负载-工作负载')
    @allure.title('在多集群项目按名称查询存在的deployment')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_deployment_by_name(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            workload_name = 'workload' + str(commonFunction.get_random())  # 工作负载名称
            conndition = 'name=' + workload_name  # 查询条件
            container_name = 'container' + str(commonFunction.get_random())  # 容器名称
            image = 'nginx'  # 镜像名称
            port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 81}]  # 容器的端口信息
            volumeMounts = []  # 设置挂载哦的存储卷
            strategy_info = {"type": "RollingUpdate",
                             "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
            replicas = 2  # 副本数
            volume_info = []
            # 创建工作负载
            step_create_deploy(cluster_name=project_info[1], project_name=project_info[0], work_name=workload_name,
                               container_name=container_name, ports=port, volumemount=volumeMounts,
                               image=image, replicas=replicas, volume_info=volume_info,
                               strategy=strategy_info)
            time.sleep(3)
            # 按名称精确查询deployment
            response = step_get_workload(cluster_name=project_info[1], project_name=project_info[0],
                                         type='deployments', condition=conndition)
            # 获取并验证deployment的名称正确
            try:
                name = response.json()['items'][0]['metadata']['name']
            except Exception as e:
                print(e)
                # 删除deployment
                step_delete_workload(project_name=project_info[0], type='deployments', work_name=workload_name)
                pytest.xfail('deploymenet创建失败，标记为xfail')
                break
            assert name == workload_name
            # 删除deployment
            re = step_delete_workload(project_name=project_info[0], type='deployments', work_name=workload_name)
            assert re.json()['status']['conditions'][0]['status'] == 'True'

    @allure.story('应用负载-工作负载')
    @allure.title('在多集群项目创建未绑定存储卷的StatefulSets，并验证运行成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_statefulsets(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            workload_name = 'workload' + str(commonFunction.get_random())  # 工作负载名称
            container_name = 'container' + str(commonFunction.get_random())  # 容器名称
            image = 'nginx'  # 镜像名称
            replicas = 2  # 副本数
            condition = 'name=' + workload_name  # 查询条件
            volume_info = []
            port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]
            service_port = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]
            service_name = 'service' + workload_name
            volumemounts = []
            # 创建工作负载
            step_create_stateful(cluster_name=project_info[1], project_name=project_info[0], work_name=workload_name,
                                 container_name=container_name,
                                 image=image, replicas=replicas, volume_info=volume_info, ports=port,
                                 service_ports=service_port, volumemount=volumemounts, service_name=service_name)
            # 在工作负载列表中查询创建的工作负载，并验证其状态为运行中，最长等待时间60s
            time.sleep(5)
            i = 3
            while i < 60:
                response = step_get_workload(cluster_name=project_info[1], project_name=project_info[0],
                                             type='statefulsets', condition=condition)
                try:
                    readyReplicas = response.json()['items'][0]['status']['readyReplicas']
                except Exception as e:
                    print(e)
                    # 删除创建的工作负载
                    step_delete_workload(project_name=project_info[0], type='statefulsets',
                                         work_name=workload_name)
                    pytest.xfail('工作负载创建失败，标记为xfail')
                    break
                # 验证资源的所有副本已就绪
                if readyReplicas == replicas:
                    print('创建工作负载耗时:' + str(i) + 's')
                    break
                time.sleep(1)
                i = i + 1
            assert readyReplicas == replicas

            # 删除创建的工作负载
            step_delete_workload(project_name=project_info[0], type='services', work_name=workload_name)
            re = step_delete_workload(project_name=project_info[0], type='statefulsets', work_name=workload_name)
            assert re.json()['status']['conditions'][0]['status'] == 'True'

    @allure.story('应用负载-工作负载')
    @allure.title('在多集群项目按名称查询存在的StatefulSets')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_statefulstes_by_name(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            workload_name = 'workload' + str(commonFunction.get_random())  # 工作负载名称
            condition = 'name=' + workload_name
            type = 'statefulsets'
            container_name = 'container' + str(commonFunction.get_random())  # 容器名称
            image = 'nginx'  # 镜像名称
            replicas = 2  # 副本数
            volume_info = []
            port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]
            service_port = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]
            service_name = 'service' + workload_name
            volumemounts = []
            # 创建工作负载
            step_create_stateful(cluster_name=project_info[1], project_name=project_info[0], work_name=workload_name,
                                 container_name=container_name,
                                 image=image, replicas=replicas, volume_info=volume_info, ports=port,
                                 service_ports=service_port, volumemount=volumemounts, service_name=service_name)

            # 按名称精确查询statefulsets
            time.sleep(1)
            response = step_get_workload(cluster_name=project_info[1], project_name=project_info[0],
                                         type=type, condition=condition)
            # 获取并验证statefulsets的名称正确
            try:
                name = response.json()['items'][0]['metadata']['name']
            except Exception as e:
                print(e)
                # 删除创建的工作负载
                step_delete_workload(project_name=project_info[0], type=type,
                                     work_name=workload_name)
                pytest.xfail('工作负载创建失败，标记为xfail')
                break
            assert name == workload_name
            # 删除创建的statefulsets
            re = step_delete_workload(project_name=project_info[0], type=type, work_name=workload_name)
            assert re.json()['status']['conditions'][0]['status'] == 'True'

    @allure.story('应用负载-服务')
    @allure.title('创建未绑定存储卷的service，并验证运行成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_service(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            service_name = 'service' + str(commonFunction.get_random())  # 服务名称
            port_service = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]  # service的端口信息
            image = 'nginx'  # 镜像名称
            container_name = 'container' + str(commonFunction.get_random())  # 容器名称
            condition = 'name=' + service_name  # 查询deploy和service条件
            port_deploy = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]  # 容器的端口信息
            volumeMounts = []  # 设置挂载的存储卷
            strategy_info = {"type": "RollingUpdate",
                             "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
            replicas = 2  # 副本数
            volume_info = []
            # 创建service
            step_create_service(cluster_name=project_info[1], project_name=project_info[0],
                                service_name=service_name, port=port_service)
            # 创建service绑定的deployment
            step_create_deploy(cluster_name=project_info[1], project_name=project_info[0],
                               work_name=service_name, container_name=container_name,
                               ports=port_deploy, volumemount=volumeMounts, image=image, replicas=replicas,
                               volume_info=volume_info, strategy=strategy_info)
            # 验证service创建成功
            response = step_get_workload(cluster_name=project_info[1], project_name=project_info[0],
                                         type='services', condition=condition)
            try:
                name = response.json()['items'][0]['metadata']['name']
            except Exception as e:
                print(e)
                # 删除创建的工作负载
                step_delete_workload(project_name=project_info[0], type='services',
                                     work_name=service_name)
                pytest.xfail('服务创建失败，标记为xfail')
                break
            assert name == service_name
            # 验证deploy创建成功
            time.sleep(3)
            re = step_get_workload(cluster_name=project_info[1], project_name=project_info[0],
                                   type='deployments', condition=condition)
            # 获取并验证deployment的名称正确
            name = re.json()['items'][0]['metadata']['name']
            assert name == service_name
            # 删除service
            step_delete_workload(project_name=project_info[0], type='services', work_name=service_name)
            # 删除deployment
            step_delete_workload(project_name=project_info[0], type='deployments', work_name=service_name)

    @allure.story('应用负载-服务')
    @allure.title('在多集群项目删除service，并验证删除成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_service(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            service_name = 'service' + str(commonFunction.get_random())
            port_service = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]  # service的端口信息
            condition = 'name=' + service_name  # 查询service的条件
            # 创建service
            step_create_service(cluster_name=project_info[1], project_name=project_info[0],
                                service_name=service_name, port=port_service)
            # 验证service创建成功
            response = step_get_workload(cluster_name=project_info[1], project_name=project_info[0],
                                         type='services', condition=condition)
            try:
                name = response.json()['items'][0]['metadata']['name']
            except Exception as e:
                print(e)
                # 删除创建的工作负载
                step_delete_workload(project_name=project_info[0], type='services',
                                     work_name=service_name)
                pytest.xfail('服务创建失败，标记为xfail')
                break
            assert name == service_name
            # 删除service
            step_delete_workload(project_info[0], 'services', service_name)
            time.sleep(10)  # 等待删除成功
            # 验证service删除成功
            response = step_get_workload(cluster_name=project_info[1], project_name=project_info[0],
                                         type='services', condition=condition)
            count = response.json()['totalItems']
            assert count == 0

    @allure.story('应用负载-应用路由')
    @allure.title('在多集群项目为服务创建应用路由')
    def test_create_route(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 创建服务
            service_name = 'service' + str(commonFunction.get_random())  # 服务名称
            port_service = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]  # service的端口信息
            image = 'nginx'  # 镜像名称
            container_name = 'container' + str(commonFunction.get_random())  # 容器名称
            condition = 'name=' + service_name  # 查询deploy和service条件
            port_deploy = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]  # 容器的端口信息
            volumeMounts = []  # 设置挂载的存储卷
            strategy_info = {"type": "RollingUpdate",
                             "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
            replicas = 2  # 副本数
            volume_info = []
            # 创建service
            step_create_service(cluster_name=project_info[1], project_name=project_info[0],
                                service_name=service_name, port=port_service)
            # 创建service绑定的deployment
            step_create_deploy(cluster_name=project_info[1], project_name=project_info[0],
                               work_name=service_name, container_name=container_name,
                               ports=port_deploy, volumemount=volumeMounts, image=image, replicas=replicas,
                               volume_info=volume_info, strategy=strategy_info)
            # 验证service创建成功
            response = step_get_workload(cluster_name=project_info[1], project_name=project_info[0],
                                         type='services', condition=condition)
            try:
                name = response.json()['items'][0]['metadata']['name']
            except Exception as e:
                print(e)
                # 删除创建的工作负载
                step_delete_workload(project_name=project_info[0], type='services',
                                     work_name=service_name)
                pytest.xfail('服务创建失败，标记为xfail')
                break
            assert name == service_name
            # 验证deploy创建成功
            time.sleep(3)
            re = step_get_workload(cluster_name=project_info[1], project_name=project_info[0],
                                   type='deployments', condition=condition)
            # 获取并验证deployment的名称正确
            name = re.json()['items'][0]['metadata']['name']
            assert name == service_name
            # 为服务创建路由
            ingress_name = 'ingress' + str(commonFunction.get_random())
            host = 'www.test' + str(commonFunction.get_random()) + '.com'
            service_info = {"serviceName": service_name, "servicePort": 80}
            response = step_create_route(cluster_name=project_info[1], project_name=project_info[0],
                                         ingress_name=ingress_name, host=host,
                                         service_info=service_info)
            # 获取路由绑定的服务名称
            name = \
                response.json()['spec']['overrides'][0]['clusterOverrides'][0]['value'][0]['http']['paths'][0][
                    'backend'][
                    'serviceName']
            # 验证路由创建成功
            assert name == service_name

    @allure.story('项目设置-高级设置')
    @allure.title('在多集群项目设置网关-NodePort')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_gateway_nodeport(self):
        type = 'NodePort'  # 网关类型
        annotations = {"servicemesh.kubesphere.io/enabled": "false"}  # 网关的注释信息
        # 创建网关
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            step_create_gateway(cluster_name=project_info[1], project_name=project_info[0],
                                type=type, annotations=annotations)
            # 查询网关
            response = step_get_gateway(cluster_name=project_info[1], project_name=project_info[0])
            # 获取网关的类型
            gateway_type = response.json()['spec']['type']
            # 验证网关创建正确
            assert gateway_type == type
            # 验证网关创建成功
            assert response.status_code == 200
            # 删除网关
            step_delete_gateway(cluster_name=project_info[1], project_name=project_info[0])
            # 验证网关删除成功
            response = step_get_gateway(cluster_name=project_info[1], project_name=project_info[0])
            assert response.json()['message'] == 'service \"kubesphere-router-' + project_info[0] + '\" not found'

    @allure.story('项目设置-高级设置')
    @allure.title('在多集群项目设置网关-LoadBalancer')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_gateway_loadbalancer(self):
        type = 'LoadBalancer'  # 网关类型
        annotations = {"service.beta.kubernetes.io/qingcloud-load-balancer-eip-ids": "",
                       "service.beta.kubernetes.io/qingcloud-load-balancer-type": "0",
                       "servicemesh.kubesphere.io/enabled": "false"}  # 网关的注释信息
        # 创建网关
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            step_create_gateway(cluster_name=project_info[1], project_name=project_info[0],
                                type=type, annotations=annotations)
            # 查询网关
            response = step_get_gateway(cluster_name=project_info[1], project_name=project_info[0])
            # 获取网关的类型
            gateway_type = response.json()['spec']['type']
            # 验证网关创建正确
            assert gateway_type == type
            # 验证网关创建成功
            assert response.status_code == 200
            # # 删除网关
            step_delete_gateway(cluster_name=project_info[1], project_name=project_info[0])
            # 验证网关删除成功
            response = step_get_gateway(cluster_name=project_info[1], project_name=project_info[0])
            assert response.json()['message'] == 'service \"kubesphere-router-' + project_info[0] + '\" not found'

    @allure.story('项目设置-高级设置')
    @allure.title('在多集群项目编辑网关')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_edit_gateway(self):
        type = 'LoadBalancer'  # 网关类型
        type_new = 'NodePort'
        annotations = {"service.beta.kubernetes.io/qingcloud-load-balancer-eip-ids": "",
                       "service.beta.kubernetes.io/qingcloud-load-balancer-type": "0",
                       "servicemesh.kubesphere.io/enabled": "false"}  # 网关的注释信息

        annotations_new = {"servicemesh.kubesphere.io/enabled": "false"}  # 网关的注释信息

        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 创建网关
            step_create_gateway(cluster_name=project_info[1], project_name=project_info[0],
                                type=type, annotations=annotations)
            # 编辑网关
            step_edit_gateway(cluster_name=project_info[1], project_name=project_info[0],
                              type=type_new, annotations=annotations_new)
            # 查询网关
            response = step_get_gateway(cluster_name=project_info[1], project_name=project_info[0])
            # 获取网关的注释信息
            gateway_annotations = response.json()['metadata']['annotations']
            # 验证网关修改成功
            assert gateway_annotations == annotations_new
            # 删除网关
            step_delete_gateway(cluster_name=project_info[1], project_name=project_info[0])

    @allure.story('应用负载-工作负载')
    @allure.title('在多集群项目修改工作负载副本并验证运行正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_add_work_replica(self):
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            workload_name = 'workload' + str(commonFunction.get_random())  # 工作负载名称
            container_name = 'container' + str(commonFunction.get_random())  # 容器名称
            image = 'nginx'  # 镜像名称
            condition = 'name=' + workload_name  # 查询条件
            port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 81}]  # 容器的端口信息
            volumeMounts = []  # 设置挂载的存储卷
            strategy_info = {"type": "RollingUpdate",
                             "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
            replicas = 2  # 副本数
            volume_info = []
            # 创建工作负载
            step_create_deploy(cluster_name=project_info[1], project_name=project_info[0], work_name=workload_name,
                               container_name=container_name, ports=port, volumemount=volumeMounts,
                               image=image, replicas=replicas, volume_info=volume_info,
                               strategy=strategy_info)

            # 在工作负载列表中查询创建的工作负载，并验证其状态为运行中，最长等待时间60s
            i = 0
            while i < 60:
                response = step_get_workload(cluster_name=project_info[1], project_name=project_info[0],
                                             type='deployments', condition=condition)
                try:
                    status = response.json()['items'][0]['status']
                except Exception as e:
                    print(e)
                    # 删除deployment
                    step_delete_workload(project_name=project_info[0], type='deployments', work_name=workload_name)
                    pytest.xfail('deploymenet创建失败，标记为xfail')
                    break
                # 验证资源的所有副本已就绪
                if 'unavailableReplicas' not in status:
                    print('创建工作负载耗时:' + str(i) + 's')
                    break
                time.sleep(1)
                i = i + 1
            assert 'unavailableReplicas' not in status

            replicas_new = 3  # 副本数
            # 修改副本数
            step_modify_work_replicas(cluster_name=project_info[1], project_name=project_info[0], type='deployments',
                                      work_name=workload_name, replicas=replicas_new)
            # 获取工作负载中所有的容器组，并验证其运行正常，最长等待时间60s
            time.sleep(5)
            # 查询容器的信息
            re = step_get_work_pod_info(cluster_name=project_info[1], project_name=project_info[0],
                                        work_name=workload_name)
            pod_count = re.json()['totalItems']
            # 验证pod数量正确
            assert pod_count == replicas_new
            # 获取并验证所有的pod运行正常
            for j in range(pod_count):
                i = 0
                while i < 60:
                    r = step_get_work_pod_info(cluster_name=project_info[1], project_name=project_info[0],
                                               work_name=workload_name)
                    status = r.json()['items'][j]['status']['phase']
                    if status == 'Running':
                        break
                    else:
                        time.sleep(5)
                        i = i + 5
                assert status == 'Running'

    @allure.story('存储管理-存储卷')
    @allure.title('在多集群项目删除存在的存储卷，并验证删除成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_volume(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            volume_name = 'volume-stateful' + str(commonFunction.get_random())  # 存储卷的名称
            # 创建存储卷
            step_create_volume(cluster_name=project_info[1], project_name=project_info[0], volume_name=volume_name)
            # 删除存储卷
            step_delete_volume(project_info[0], volume_name)
            # 查询被删除的存储卷
            i = 0
            # 验证存储卷被删除，最长等待时间为30s
            while i < 30:
                response = step_get_volume(self.project_name, self.volume_name)
                # 存储卷快照的状态为布尔值，故先将结果转换我字符类型
                if response.json()['totalItems'] == 0:
                    print("删除存储卷耗时:" + str(i) + '秒')
                    break
                time.sleep(1)
                i = i + 1
            print("actual_result:r1.json()['totalItems'] = " + str(response.json()['totalItems']))
            print("expect_result: 0")
            # 验证存储卷成功
            assert response.json()['totalItems'] == 0

    @allure.story('项目设置-基本信息')
    @allure.title('编辑多集群项目信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_edit_project(self):
        alias_name = 'test-231313!#!G@#K!G#G!PG#'  # 别名信息
        description = '测试test123！@#'  # 描述信息
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 编辑项目信息
            response = step_edit_project(cluster_name=project_info[1], ws_name=project_info[2],
                                         project_name=project_info[0],
                                         alias_name=alias_name, description=description)
            # 验证编辑成功
            assert response.status_code == 200

    @allure.story('项目设置-项目配额')
    @allure.title('在多集群项目只设置项目配额-CPU')
    def test_edit_project_quota_cpu(self):
        # 配额信息
        hard = {"limits.cpu": "40",
                "requests.cpu": "40"
                }
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 获取项目配额的resource_version
            resource_version = step_get_project_quota_version(project_info[1], project_info[0])
            # 编辑配额信息
            step_edit_project_quota(project_info[1], project_info[0], hard, resource_version)
            # 获取修改后的配额信息
            response = step_get_project_quota(project_info[1], project_info[0])
            hard_actual = response.json()['data']['hard']
            # 验证配额修改成功
            assert hard_actual == hard

    @allure.story('项目设置-项目配额')
    @allure.title('在多集群项目设置项目配额-输入错误的cpu信息(包含字母)')
    def test_edit_project_quota_wrong_cpu(self):
        # 配额信息,错误的cpu信息
        hard = {"limits.cpu": "11www",
                "requests.cpu": "1www"
                }
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 获取项目配额的resource_version
            resource_version = step_get_project_quota_version(project_info[1], project_info[0])
            # 编辑配额信息
            r = step_edit_project_quota(project_info[1], project_info[0], hard, resource_version)
            # 获取编辑结果
            status = r.json()['status']
            # 验证编辑失败
            assert status == 'Failure'

    @allure.story('项目设置-项目配额')
    @allure.title('在多集群项目设置项目配额-输入错误的cpu信息(包含负数)')
    def test_edit_project_quota_wrong_cpu_1(self):
        # 配额信息,错误的cpu信息
        hard = {"limits.cpu": "-11",
                "requests.cpu": "1"
                }
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 获取项目配额的resource_version
            resource_version = step_get_project_quota_version(project_info[1], project_info[0])
            # 编辑配额信息
            r = step_edit_project_quota(project_info[1], project_info[0], hard, resource_version)
            # 获取编辑结果
            status = r.json()['status']
            # 验证编辑失败
            assert status == 'Failure'

    @allure.story('项目设置-项目配额')
    @allure.title('在多集群项目只设置项目配额-内存')
    def test_edit_project_quota_memory(self):
        # 配额信息
        hard = {"limits.memory": "1000Gi", "requests.memory": "1Gi"}
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 获取项目配额的resource_version
            resource_version = step_get_project_quota_version(project_info[1], project_info[0])
            # 编辑配额信息
            step_edit_project_quota(project_info[1], project_info[0], hard, resource_version)
            # 获取修改后的配额信息
            response = step_get_project_quota(project_info[1], project_info[0])
            hard_actual = response.json()['data']['hard']
            # 验证配额修改成功
            assert hard_actual == hard

    @allure.story('项目设置-项目配额')
    @allure.title('在多集群项目设置项目配额-输入错误的内存(包含非单位字母)')
    def test_edit_project_quota_wrong_memory_1(self):
        # 配额信息
        hard = {"limits.memory": "10Gi", "requests.memory": "1Giw"}
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 获取项目配额的resource_version
            resource_version = step_get_project_quota_version(project_info[1], project_info[0])
            # 编辑配额信息
            r = step_edit_project_quota(project_info[1], project_info[0], hard, resource_version)
            # 获取编辑结果
            status = r.json()['status']
            # 验证编辑失败
            assert status == 'Failure'

    @allure.story('项目设置-项目配额')
    @allure.title('在多集群项目设置项目配额-输入错误的内存(包含负数)')
    def test_edit_project_quota_wrong_memory_2(self):
        # 配额信息
        hard = {"limits.memory": "-10Gi", "requests.memory": "1Gi"}
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 获取项目配额的resource_version
            resource_version = step_get_project_quota_version(project_info[1], project_info[0])
            # 编辑配额信息
            r = step_edit_project_quota(project_info[1], project_info[0], hard, resource_version)
            # 获取编辑结果
            status = r.json()['status']
            # 验证编辑失败
            assert status == 'Failure'

    @allure.story('项目设置-项目配额')
    @allure.title('在多集群项目设置项目配额-CPU、内存')
    def test_edit_project_quota_cpu_memory(self):
        # 配额信息
        hard = {"limits.memory": "1000Gi", "requests.memory": "1Gi",
                "limits.cpu": "100", "requests.cpu": "100"}
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 获取项目配额的resource_version
            resource_version = step_get_project_quota_version(project_info[1], project_info[0])
            # 编辑配额信息
            step_edit_project_quota(project_info[1], project_info[0], hard, resource_version)
            # 获取修改后的配额信息
            response = step_get_project_quota(project_info[1], project_info[0])
            hard_actual = response.json()['data']['hard']
            # 验证配额修改成功
            assert hard_actual == hard

    @allure.story('项目设置-项目配额')
    @allure.title('在多集群项目只设置项目配额-资源配额')
    def test_edit_project_quota_resource(self):
        # 配额信息
        hard = {"count/pods": "100",
                "count/deployments.apps": "6",
                "count/statefulsets.apps": "6",
                "count/jobs.batch": "1",
                "count/services": "5",
                "persistentvolumeclaims": "6",
                "count/daemonsets.apps": "5",
                "count/cronjobs.batch": "4",
                "count/ingresses.extensions": "4",
                "count/secrets": "8",
                "count/configmaps": "7"}
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 获取项目配额的resource_version
            resource_version = step_get_project_quota_version(project_info[1], project_info[0])
            # 编辑配额信息
            step_edit_project_quota(project_info[1], project_info[0], hard, resource_version)
            # 获取修改后的配额信息
            response = step_get_project_quota(project_info[1], project_info[0])
            hard_actual = response.json()['data']['hard']
            # 验证配额修改成功
            assert hard_actual == hard

    @allure.story('项目设置-项目配额')
    @allure.title('在多集群项目只设置项目配额-输入错误的资源配额信息(包含字母)')
    def test_edit_project_quota_wrong_resource(self):
        # 配额信息
        hard = {"count/pods": "100q",
                "count/deployments.apps": "6",
                "count/statefulsets.apps": "6",
                "count/jobs.batch": "1",
                "count/services": "5",
                "persistentvolumeclaims": "6",
                "count/daemonsets.apps": "5",
                "count/cronjobs.batch": "4",
                "count/ingresses.extensions": "4",
                "count/secrets": "8",
                "count/configmaps": "7"}
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 获取项目配额的resource_version
            resource_version = step_get_project_quota_version(project_info[1], project_info[0])
            # 编辑配额信息
            r = step_edit_project_quota(project_info[1], project_info[0], hard, resource_version)
            # 获取编辑结果
            status = r.json()['status']
            # 验证编辑失败
            assert status == 'Failure'

    @allure.story('项目设置-项目配额')
    @allure.title('在多集群项目只设置项目配额-输入错误的资源配额信息(包含负数)')
    def test_edit_project_quota_wrong_resource_1(self):
        # 配额信息
        hard = {"count/pods": "-100",
                "count/deployments.apps": "6",
                "count/statefulsets.apps": "6",
                "count/jobs.batch": "1",
                "count/services": "5",
                "persistentvolumeclaims": "6",
                "count/daemonsets.apps": "5",
                "count/cronjobs.batch": "4",
                "count/ingresses.extensions": "4",
                "count/secrets": "8",
                "count/configmaps": "7"}
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 获取项目配额的resource_version
            resource_version = step_get_project_quota_version(project_info[1], project_info[0])
            # 编辑配额信息
            r = step_edit_project_quota(project_info[1], project_info[0], hard, resource_version)
            # 获取编辑结果
            status = r.json()['status']
            # 验证编辑失败
            assert status == 'Failure'

    @allure.story('项目设置-项目配额')
    @allure.title('在多集群下项目设置项目配额-cpu、memory、资源配额')
    def test_edit_project_quota(self):
        # 配额信息
        hard = {"count/configmaps": "7",
                "count/cronjobs.batch": "4",
                "count/daemonsets.apps": "5",
                "count/deployments.apps": "6",
                "count/ingresses.extensions": "4",
                "count/jobs.batch": "1",
                "count/pods": "100",
                "count/secrets": "8",
                "count/services": "5",
                "count/statefulsets.apps": "6",
                "persistentvolumeclaims": "6",
                "limits.cpu": "200", "limits.memory": "1000Gi",
                "requests.cpu": "200", "requests.memory": "3Gi"}
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 获取项目配额的resource_version
            resource_version = step_get_project_quota_version(project_info[1], project_info[0])
            # 编辑配额信息
            step_edit_project_quota(project_info[1], project_info[0], hard, resource_version)
            # 获取修改后的配额信息
            response = step_get_project_quota(project_info[1], project_info[0])
            hard_actual = response.json()['data']['hard']
            # 验证配额修改成功
            assert hard_actual == hard

    @allure.story('项目设置-资源默认请求')
    @allure.title('在多集群项目只设置资源默认请求-cpu')
    def test_edit_container_quota_cpu(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 获取资源默认请求
            response = step_get_container_quota(project_info[0], project_info[2])
            resource_version = None
            try:
                if response.json()['items'][0]['metadata']['resourceVersion']:
                    resource_version = response.json()['items'][0]['metadata']['resourceVersion']
                else:
                    resource_version = None
            except Exception as e:
                print(e)
            # 编辑资源默认请求
            limit = {"cpu": "16"}
            request = {"cpu": "2"}
            step_edit_container_quota(project_info[1], project_info[0], resource_version, limit, request)
            # 查询编辑结果
            response = step_get_container_quota(project_info[0], project_info[2])
            limit_actual = response.json()['items'][0]['spec']['template']['spec']['limits'][0]['default']
            request_actual = response.json()['items'][0]['spec']['template']['spec']['limits'][0]['defaultRequest']
            # 验证编辑成功
            assert limit == limit_actual
            assert request == request_actual

    @allure.story('项目设置-资源默认请求')
    @allure.title('在多集群项目只设置资源默认请求-输入错误的cpu信息(包含字母)')
    # 接口未做限制
    def wx_test_edit_container_quota_wrong_cpu(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 获取资源默认请求
            response = step_get_container_quota(project_info[0], project_info[2])
            resource_version = None
            try:
                if response.json()['items'][0]['metadata']['resourceVersion']:
                    resource_version = response.json()['items'][0]['metadata']['resourceVersion']
                else:
                    resource_version = None
            except Exception as e:
                print(e)
            # 编辑资源默认请求
            limit = {"cpu": "16aa"}
            request = {"cpu": "2"}
            r = step_edit_container_quota(project_info[1], project_info[0], resource_version, limit, request)
            # 获取编辑结果
            status = r.json()['status']
            # 验证编辑失败
            assert status == 'Failure'

    @allure.story('项目设置-资源默认请求')
    @allure.title('只设置资源默认请求-输入错误的cpu信息(包含负数)')
    # 接口未做限制
    def wx_test_edit_container_quota_wrong_cpu_1(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 获取资源默认请求
            response = step_get_container_quota(project_info[0], project_info[2])
            resource_version = None
            try:
                if response.json()['items'][0]['metadata']['resourceVersion']:
                    resource_version = response.json()['items'][0]['metadata']['resourceVersion']
                else:
                    resource_version = None
            except Exception as e:
                print(e)
            # 编辑资源默认请求
            limit = {"cpu": "-16"}
            request = {"cpu": "-2"}
            r = step_edit_container_quota(project_info[1], project_info[0], resource_version, limit, request)
            # 获取编辑结果
            status = r.json()['status']
            # 验证编辑失败
            assert status == 'Failure'

    @allure.story('项目设置-资源默认请求')
    @allure.title('只设置资源默认请求-内存')
    def test_edit_container_quota_memory(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 获取资源默认请求
            response = step_get_container_quota(project_info[0], project_info[2])
            resource_version = None
            try:
                if response.json()['items'][0]['metadata']['resourceVersion']:
                    resource_version = response.json()['items'][0]['metadata']['resourceVersion']
                else:
                    resource_version = None
            except Exception as e:
                print(e)
            # 编辑资源默认请求
            limit = {"memory": "1000Mi"}
            request = {"memory": "1Mi"}
            step_edit_container_quota(project_info[1], project_info[0], resource_version, limit, request)
            # 查询编辑结果
            response = step_get_container_quota(project_info[0], project_info[2])
            limit_actual = response.json()['items'][0]['spec']['template']['spec']['limits'][0]['default']
            request_actual = response.json()['items'][0]['spec']['template']['spec']['limits'][0]['defaultRequest']
            # 验证编辑成功
            assert limit == limit_actual
            assert request == request_actual

    @allure.story('项目设置-资源默认请求')
    @allure.title('只设置资源默认请求-输入错误的内存信息(包含非单位字母)')
    # 接口未做限制
    def wx_test_edit_container_quota_wrong_memory(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 获取资源默认请求
            response = step_get_container_quota(project_info[0], project_info[2])
            resource_version = None
            try:
                if response.json()['items'][0]['metadata']['resourceVersion']:
                    resource_version = response.json()['items'][0]['metadata']['resourceVersion']
                else:
                    resource_version = None
            except Exception as e:
                print(e)
            # 编辑资源默认请求
            limit = {"memory": "1000aMi"}
            request = {"memory": "1Mi"}
            r = step_edit_container_quota(project_info[1], project_info[0], resource_version, limit, request)
        # 获取编辑结果
        status = r.json()['status']
        # 验证编辑失败
        assert status == 'Failure'

    @allure.story('项目设置-资源默认请求')
    @allure.title('只设置资源默认请求-输入错误的内存信息(包含负数)')
    # 接口未做限制
    def wx_test_edit_container_quota_wrong_memory_1(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 获取资源默认请求
            response = step_get_container_quota(project_info[0], project_info[2])
            resource_version = None
            try:
                if response.json()['items'][0]['metadata']['resourceVersion']:
                    resource_version = response.json()['items'][0]['metadata']['resourceVersion']
                else:
                    resource_version = None
            except Exception as e:
                print(e)
            # 编辑资源默认请求
            limit = {"memory": "1000aMi"}
            request = {"memory": "1Mi"}
            r = step_edit_container_quota(project_info[1], project_info[0], resource_version, limit, request)
        # 获取编辑结果
        status = r.json()['status']
        # 验证编辑失败
        assert status == 'Failure'

    @allure.story('项目设置-资源默认请求')
    @allure.title('在多集群项目只设置资源默认请求-内存、cpu')
    def test_edit_container_quota_memory_1(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 获取资源默认请求
            response = step_get_container_quota(project_info[0], project_info[2])
            resource_version = None
            try:
                if response.json()['items'][0]['metadata']['resourceVersion']:
                    resource_version = response.json()['items'][0]['metadata']['resourceVersion']
                else:
                    resource_version = None
            except Exception as e:
                print(e)
            # 编辑资源默认请求
            limit = {"cpu": "15", "memory": "1000Mi"}
            request = {"cpu": "2", "memory": "1Mi"}
            step_edit_container_quota(project_info[1], project_info[0], resource_version, limit, request)
            # 查询编辑结果
            response = step_get_container_quota(project_info[0], project_info[2])
            limit_actual = response.json()['items'][0]['spec']['template']['spec']['limits'][0]['default']
            request_actual = response.json()['items'][0]['spec']['template']['spec']['limits'][0]['defaultRequest']
            # 验证编辑成功
            assert limit == limit_actual
            assert request == request_actual

    @allure.story('配置中心-密钥')
    @allure.title('在多集群项目创建默认类型的密钥')
    def test_create_secret_default(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 在多集群项目创建默认类型的密钥
            secret_name = 'secret' + str(commonFunction.get_random())
            step_create_secret_default(cluster_name=project_info[1], project_name=project_info[0],
                                       secret_name=secret_name, key='wx', value='dGVzdA==')
            # 查询创建的密钥
            response = step_get_secret(project_name=project_info[0], secret_name=secret_name)
            try:
                # 获取密钥的数量和状态
                secret_count = response.json()['totalItems']
                secret_status = response.json()['items'][0]['status']['conditions'][0]['status']
            except Exception as e:
                pytest.xfail('密钥创建失败，标记为xfail')
                print(e)
                break
            # 验证查询到的密钥数量和密钥的状态正确
            assert secret_count == 1
            assert secret_status == 'True'
            # 删除创建的密钥
            step_delete_secret(project_name=project_info[0], secret_name=secret_name)

    @allure.story('配置中心-密钥')
    @allure.title('在多集群项目创建TLS类型的密钥')
    def test_create_secret_tls(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 在多集群项目创建默认类型的密钥
            secret_name = 'secret' + str(commonFunction.get_random())
            step_create_secret_tls(cluster_name=project_info[1], project_name=project_info[0],
                                   secret_name=secret_name, credential='d3g=', key='dGVzdA==')
            # 查询创建的密钥
            response = step_get_secret(project_name=project_info[0], secret_name=secret_name)
            # 获取密钥的数量和状态
            try:
                secret_count = response.json()['totalItems']
                secret_status = response.json()['items'][0]['status']['conditions'][0]['status']
            except Exception as e:
                pytest.xfail('密钥创建失败，标记为xfail')
                print(e)
                break
            # 验证查询到的密钥数量和密钥的状态正确
            assert secret_count == 1
            assert secret_status == 'True'
            # 删除创建的密钥
            step_delete_secret(project_name=project_info[0], secret_name=secret_name)

    @allure.story('配置中心-密钥')
    @allure.title('在多集群项目创建image类型的密钥')
    def test_create_secret_image(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 在多集群项目创建默认类型的密钥
            secret_name = 'secret' + str(commonFunction.get_random())
            step_create_secret_image(cluster_name=project_info[1], project_name=project_info[0],
                                     secret_name=secret_name)
            # 查询创建的密钥
            response = step_get_secret(project_name=project_info[0], secret_name=secret_name)
            # 获取密钥的数量和状态
            try:
                secret_count = response.json()['totalItems']
                secret_status = response.json()['items'][0]['status']['conditions'][0]['status']
            except Exception as e:
                pytest.xfail('密钥创建失败，标记为xfail')
                print(e)
                break
            # 验证查询到的密钥数量和密钥的状态正确
            assert secret_count == 1
            assert secret_status == 'True'
            # 删除创建的密钥
            step_delete_secret(project_name=project_info[0], secret_name=secret_name)

    @allure.story('配置中心-密钥')
    @allure.title('在多集群项目创建账号密码类型的密钥')
    def test_create_secret_account(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 在多集群项目创建默认类型的密钥
            secret_name = 'secret' + str(commonFunction.get_random())
            step_create_secret_account(cluster_name=project_info[1], project_name=project_info[0],
                                       secret_name=secret_name, username='d3g=', password='dGVzdA==')
            # 查询创建的密钥
            response = step_get_secret(project_name=project_info[0], secret_name=secret_name)
            # 获取密钥的数量和状态
            try:
                secret_count = response.json()['totalItems']
                secret_status = response.json()['items'][0]['status']['conditions'][0]['status']
            except Exception as e:
                pytest.xfail('密钥创建失败，标记为xfail')
                print(e)
                break
            # 验证查询到的密钥数量和密钥的状态正确
            assert secret_count == 1
            assert secret_status == 'True'
            # 删除创建的密钥
            step_delete_secret(project_name=project_info[0], secret_name=secret_name)

    @allure.story('配置中心-密钥')
    @allure.title('在多集群项目创建配置')
    def test_create_config_map(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            config_name = 'config-map' + str(commonFunction.get_random())
            # 在每个多集群项目创建配置
            step_create_config_map(cluster_name=project_info[1], project_name=project_info[0],
                                   config_name=config_name, key='wx', value='test')
            # 查询创建的配置
            response = step_get_config_map(project_name=project_info[0], config_name=config_name)
            # 获取配置的数量和状态
            try:
                secret_count = response.json()['totalItems']
                secret_status = response.json()['items'][0]['status']['conditions'][0]['status']
            except Exception as e:
                pytest.xfail('密钥创建失败，标记为xfail')
                print(e)
                break
            # 验证查询到的配置数量和密钥的状态正确
            assert secret_count == 1
            assert secret_status == 'True'
            # 删除创建的配置
            step_delete_config_map(project_name=project_info[0], config_name=config_name)

    @allure.story('项目设置-高级设置')
    @allure.title('落盘日志收集-开启')
    @pytest.mark.skipif(commonFunction.get_components_status_of_cluster('logging') is False, reason='集群未开启logging功能')
    def test_disk_log_collection_open(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 开启落盘日志收集功能
            step_set_disk_log_collection(project_name=project_info[0], set='enabled')
            # 查看落盘日志收集功能
            response = step_check_disk_log_collection(project_name=project_info[0])
            # 获取功能状态
            status = response.json()['metadata']['labels']['logging.kubesphere.io/logsidecar-injection']
            # 验证功能开启成功
            assert status == 'enabled'

    @allure.story('项目设置-高级设置')
    @allure.title('落盘日志收集-关闭')
    @pytest.mark.skipif(commonFunction.get_components_status_of_cluster('logging') is False, reason='集群未开启logging功能')
    def test_disk_log_collection_close(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 关闭落盘日志收集功能
            step_set_disk_log_collection(project_name=project_info[0], set='disabled')
            # 查看落盘日志收集功能
            response = step_check_disk_log_collection(project_name=project_info[0])
            # 获取功能状态
            status = response.json()['metadata']['labels']['logging.kubesphere.io/logsidecar-injection']
            # 验证功能开启成功
            assert status == 'disabled'

    @allure.story('概览')
    @allure.title('查询多集群项目的监控信息')
    def test_get_project_metrics(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 获取当前时间的10位时间戳
            now_timestamp = str(time.time())[0:10]
            # 获取720分钟之前的戳
            before_timestamp = commonFunction.get_before_timestamp(720)
            # 查询每个项目最近12h的监控信息
            response = step_get_project_metrics(cluster_name=project_info[1], project_name=project_info[0],
                                                start_time=before_timestamp, end_time=now_timestamp,
                                                step='4320s', times=str(10))
            # 获取结果中的数据类型
            type = response.json()['results'][0]['data']['resultType']
            # 验证数据类型正确
            assert type == 'matrix'

    @allure.story('概览')
    @allure.title('查询多集群项目的abnormalworkloads')
    def test_get_project_abnormalworkloads(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 查询多集群项目的abnormalworkloads
            response =step_get_project_abnormalworkloads(cluster_name=project_info[1], project_name=project_info[0])
            # 验证查询成功
            assert 'persistentvolumeclaims' in response.json()['data']

    @allure.story('概览')
    @allure.title('查询多集群项目的federatedlimitranges')
    def test_get_project_federatedlimitranges(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            # 查询多集群项目的federatedlimitranges
            response = step_get_project_federatedlimitranges(project_name=project_info[0])
            # 获取查询结果中的kind
            kind = response.json()['kind']
            # 验证kind正确
            assert kind == 'FederatedLimitRangeList'
            
    @allure.story('概览')
    @allure.title('查询多集群项目的workloads')
    def test_get_project_workloads(self):
        # 获取环境中所有的多集群项目
        multi_projects = step_get_multi_project_all()
        for project_info in multi_projects:
            response = step_get_project_workloads(cluster_name=project_info[1], project_name=project_info[0])
            # 验证查询成功
            assert response.json()['total_item'] >= 0


if __name__ == "__main__":
    pytest.main(['-s', 'testProject.py'])  # -s参数是为了显示用例的打印信息。 -q参数只显示结果，不显示过程
