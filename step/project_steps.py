import requests
import json
import allure
import sys
import time

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from config import config
from common.getHeader import get_header, get_header_for_patch
from step import workspace_steps


@allure.step('创建一个计算圆周率的任务')
def step_create_job(project_name, job_name):
    """
    :param project_name: 项目名称
    :param job_name: 任务名称
    """
    container_name = 'container-' + job_name
    url = config.url + '/apis/batch/v1/namespaces/' + project_name + '/jobs?dryRun=All'
    url1 = config.url + '/apis/batch/v1/namespaces/' + project_name + '/jobs'
    data = {"apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {"namespace": project_name,
                         "labels": {"app": job_name},
                         "name": job_name,
                         "annotations": {"kubesphere.io/alias-name": "计算任务",
                                         "kubesphere.io/description": "创建任务计算圆周率",
                                         "kubesphere.io/creator": "admin"}},
            "spec": {"template": {"metadata": {"labels": {"app": job_name}},
                                  "spec": {"containers": [{"name": container_name,
                                                           "imagePullPolicy": "IfNotPresent",
                                                           "image": "perl",
                                                           "command": ["perl", "-Mbignum=bpi", "-wle",
                                                                       "print bpi(2000)"]}],  # 输出π，2000位
                                           "restartPolicy": "OnFailure",
                                           "serviceAccount": "default",
                                           "initContainers": [],
                                           "volumes": []}},
                     "backoffLimit": 5, "completions": 4, "parallelism": 2, "activeDeadlineSeconds": 300}}

    requests.post(url=url, headers=get_header(), data=json.dumps(data))
    requests.post(url=url1, headers=get_header(), data=json.dumps(data))


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
            time.sleep(10)
            i = i + 10
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
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + '/jobs?' + way + '=' + \
          condition + '&sortBy=updateTime&limit=10'
    response = requests.get(url=url, headers=get_header())
    return response


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


@allure.step('创建deployment')
def step_create_deploy(project_name, work_name, container_name, image, replicas, ports, volumemount,
                       volume_info, strategy):
    """
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
    url1 = config.url + '/apis/apps/v1/namespaces/' + project_name + '/' + 'deployments?dryRun=All'
    url2 = config.url + '/apis/apps/v1/namespaces/' + project_name + '/deployments'

    data = {"apiVersion": "apps/v1", "kind": "Deployment",
            "metadata": {"namespace": project_name,
                         "labels": {"app": work_name},
                         "name": work_name,
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"replicas": replicas,
                     "selector": {"matchLabels": {"app": work_name}},
                     "template": {"metadata": {
                         "labels": {"app": work_name},
                         "annotations": {"logging.kubesphere.io/logsidecar-config": "{}"}},
                         "spec": {
                             "containers": [{
                                 "name": container_name,
                                 "imagePullPolicy": "IfNotPresent",
                                 "image": image,
                                 "ports": ports,
                                 "volumeMounts": volumemount
                             }],
                             "serviceAccount": "default",
                             "affinity": {},
                             "imagePullSecrets": None,
                             "initContainers": [],
                             "volumes": volume_info}},
                     "strategy": strategy
                     }}
    requests.post(url=url1, headers=get_header(), data=json.dumps(data))
    response = requests.post(url=url2, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('创建statefulsets')
def step_create_stateful(project_name, work_name, container_name, image, replicas, ports, service_ports, volumemount,
                         volume_info,
                         service_name):
    url1 = config.url + '/apis/apps/v1/namespaces/' + project_name + '/statefulsets?dryRun=All'
    url3 = config.url + '/apis/apps/v1/namespaces/' + project_name + '/statefulsets'
    url2 = config.url + '/api/v1/namespaces/' + project_name + '/services?dryRun=All'
    url4 = config.url + '/api/v1/namespaces/' + project_name + '/services'
    data1 = {"apiVersion": "apps/v1",
             "kind": "StatefulSet",
             "metadata": {
                 "namespace": project_name,
                 "labels": {"app": work_name},
                 "name": work_name,
                 "annotations": {"kubesphere.io/creator": "admin"}},
             "spec": {
                 "replicas": replicas,
                 "selector": {"matchLabels": {"app": work_name}},
                 "template": {
                     "metadata": {
                         "labels": {"app": work_name},
                         "annotations": {"logging.kubesphere.io/logsidecar-config": "{}"}},
                     "spec": {
                         "containers": [{
                             "name": container_name,
                             "imagePullPolicy": "IfNotPresent",
                             "image": image,
                             "ports": ports,
                             "volumeMounts": volumemount}],
                         "serviceAccount": "default",
                         "affinity": {},
                         "initContainers": [],
                         "volumes": volume_info,
                         "imagePullSecrets": None}},
                 "updateStrategy": {
                     "type": "RollingUpdate",
                     "rollingUpdate": {"partition": 0}},
                 "serviceName": service_name}}

    data2 = {"apiVersion": "v1",
             "kind": "Service",
             "metadata": {
                 "namespace": project_name,
                 "labels": {"app": work_name},
                 "name": service_name,
                 "annotations": {"kubesphere.io/alias-name": work_name,
                                 "kubesphere.io/serviceType": "statefulservice",
                                 "kubesphere.io/creator": "admin"}},
             "spec": {"sessionAffinity": "None",
                      "selector": {"app": work_name},
                      "ports": service_ports,
                      "clusterIP": "None"}}
    requests.post(url=url1, headers=get_header(), data=json.dumps(data1))
    requests.post(url=url2, headers=get_header(), data=json.dumps(data2))
    requests.post(url=url3, headers=get_header(), data=json.dumps(data1))
    response = requests.post(url=url4, headers=get_header(), data=json.dumps(data2))
    return response


@allure.step('创建daemonsets')
def step_create_daemonset(project_name, work_name, container_name, image, ports, volumemount,
                          volume_info):
    url1 = config.url + '/apis/apps/v1/namespaces/' + project_name + '/daemonsets?dryRun=All'
    url2 = config.url + '/apis/apps/v1/namespaces/' + project_name + '/daemonsets'
    data = {"apiVersion": "apps/v1", "kind": "DaemonSet",
            "metadata": {
                "namespace": project_name,
                "labels": {"app": work_name},
                "name": work_name,
                "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"replicas": 1,
                     "selector": {"matchLabels": {"app": work_name}},
                     "template": {
                         "metadata": {
                             "labels": {"app": work_name},
                             "annotations": {"logging.kubesphere.io/logsidecar-config": "{}"}},
                         "spec": {
                             "containers": [{
                                 "name": container_name,
                                 "imagePullPolicy": "IfNotPresent",
                                 "image": image,
                                 "ports": ports,
                                 "volumeMounts": volumemount}],
                             "serviceAccount": "default",
                             "affinity": {},
                             "initContainers": [],
                             "volumes": volume_info,
                             "imagePullSecrets": None}},
                     "updateStrategy": {
                         "type": "RollingUpdate",
                         "rollingUpdate": {"maxUnavailable": "20%"}}, "minReadySeconds": 0}}
    requests.post(url=url1, headers=get_header(), data=json.dumps(data))
    response = requests.post(url=url2, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('创建service')
def step_create_service(project_name, service_name, port):
    url1 = config.url + '/api/v1/namespaces/' + project_name + '/services?dryRun=All'
    url2 = config.url + '/api/v1/namespaces/' + project_name + '/services'

    data = {"apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "namespace": project_name,
                "labels": {"version": "v1", "app": service_name},
                "annotations": {"kubesphere.io/serviceType": "statelessservice", "kubesphere.io/creator": "admin"},
                "name": service_name},
            "spec": {
                "sessionAffinity": "None",
                "selector": {"app": service_name},
                "template": {
                    "metadata": {"labels": {"version": "v1", "app": service_name}}},
                "ports": port}}
    requests.post(url=url1, headers=get_header(), data=json.dumps(data))
    response = requests.post(url=url2, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('创建路由')
def step_create_route(project_name, ingress_name, host, service_info):
    url = config.url + '/apis/extensions/v1beta1/namespaces/' + project_name + '/ingresses'
    data = {"apiVersion": "extensions/v1beta1",
            "kind": "Ingress",
            "metadata": {
                "namespace": project_name,
                "labels": {},
                "name": ingress_name,
                "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {
                "rules": [{
                    "protocol": "http",
                    "host": host,
                    "http": {
                        "paths": [{
                            "path": "/",
                            "backend": service_info}]}}],
                "tls": []}}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('设置网关')
def step_create_gateway(project_name, type, annotations):
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha2/namespaces/' + project_name + '/router'
    data = {"type": type, "annotations": annotations}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('编辑网关')
def step_edit_gateway(project_name, type, annotations):
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha2/namespaces/' + project_name + '/router'
    data = {"type": type, "annotations": annotations}
    response = requests.put(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('删除网关')
def step_delete_gateway(project_name):
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha2/namespaces/' + project_name + '/router'
    data = {}
    response = requests.delete(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('查看项目网关')
def step_get_gateway(project_name):
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha2/namespaces/' + project_name + '/router'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('删除service')
def step_delete_service(project_name, service_name):
    url = config.url + '/api/v1/namespaces/' + project_name + '/services/' + service_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('修改工作负载副本数')
def step_modify_work_replicas(project_name, work_name, replicas):
    """
    :param project_name: 项目名称
    :param work_name: 工作负载名称
    :param replicas: 副本数
    """
    url = config.url + '/apis/apps/v1/namespaces/' + project_name + '/deployments/' + work_name
    data = {"spec": {"replicas": replicas}}
    r = requests.patch(url=url, headers=get_header_for_patch(), data=json.dumps(data))
    # 验证修改后的副本数
    assert r.json()['spec']['replicas'] == replicas


@allure.step('获取工作负载中所有的容器组的运行状态')
def step_get_work_pod_status(project_name, work_name):
    status = []
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + '/pods' \
                                                                                              '?ownerKind=ReplicaSet&labelSelector=app%3' + work_name + '&name=' + work_name + '&sortBy=startTime'

    r = requests.get(url=url, headers=get_header())
    for i in range(r.json()['totalItems']):
        status.append(r.json()['items'][i]['status']['phase'])

    return status


@allure.step('获取指定的工作负载')
def step_get_workload(project_name, type, condition):
    """

    :param project_name: 项目名称
    :param type: 负载类型
    :param condition: 查询条件  如：name=test
    :return:
    """
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' \
          + project_name + '/' + type + '?' + condition
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('删除指定的工作负载')
def step_delete_workload(project_name, type, work_name):
    url = config.url + '/apis/apps/v1/namespaces/' + project_name + '/' + type + '/' + work_name
    data = {"kind": "DeleteOptions", "apiVersion": "v1", "propagationPolicy": "Background"}
    response = requests.delete(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('创建存储卷')
def step_create_volume(project_name, volume_name):
    url = config.url + '/api/v1/namespaces/' + project_name + '/persistentvolumeclaims'
    data = {"apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {"namespace": project_name, "name": volume_name, "labels": {},
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"accessModes": ["ReadWriteOnce"], "resources": {"requests": {"storage": "10Gi"}},
                     "storageClassName": "local"}}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('删除存储卷')
def step_delete_volume(project_name, volume_name):
    url = config.url + '/api/v1/namespaces/' + project_name + '/persistentvolumeclaims/' + volume_name
    # 删除存储卷
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('查询指定的存储卷')
def step_get_volume(project_name, volume_name):
    url1 = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + \
           '/persistentvolumeclaims?name=' + volume_name + '&sortBy=createTime&limit=10'
    response = requests.get(url=url1, headers=get_header())
    return response


@allure.step('获取存储卷状态')
def step_get_volume_status(project_name, volume_name):
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + '/persistentvolumeclaims?name=' + volume_name + '&sortBy=createTime&limit=10'
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


@allure.step('查询指定的项目')
def step_get_project(ws_name, project_name):
    url1 = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + \
           '/namespaces?name=' + project_name
    response = requests.get(url=url1, headers=get_header())
    return response


@allure.step('编辑项目')
def step_edit_project(ws_name, project_name, alias_name, description):
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/namespaces/' + project_name
    data = {
        "metadata": {
            "name": project_name,
            "labels": {
                "kubesphere.io/namespace": "test-project",
                "kubesphere.io/workspace": "ws-for-test-project"
            },
            "annotations": {
                "kubesphere.io/creator": "admin",
                "kubesphere.io/alias-name": alias_name,
                "kubesphere.io/description": description},
            "finalizers": ["finalizers.kubesphere.io/namespaces"]},
        "spec": {"finalizers": ["kubernetes"]}}
    response = requests.patch(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('获取项目配额的resourceVersion')
def step_get_project_quota_version(project_name):
    url = config.url + '/api/v1/namespaces/' + project_name + '/resourcequotas/' + project_name
    response = requests.get(url=url, headers=get_header())
    try:
        if response.json():
            return response.json()['metadata']['resourceVersion']
        else:
            return None
    except Exception as e:
        print(e)


@allure.step('编辑项目配额')
def step_edit_project_quota(project_name, hard, resource_version):
    url_put = config.url + '/api/v1/namespaces/' + project_name + '/resourcequotas/' + project_name
    url_post = config.url + '/api/v1/namespaces/' + project_name + '/resourcequotas'
    data_post = {
        "apiVersion": "v1",
        "kind": "ResourceQuota",
        "metadata": {
            "annotations": {"kubesphere.io/creator": "admin"},
            "name": project_name,
            "namespace": project_name,
            "cluster": "default"
        },
        "spec": {
            "hard": hard}}
    data_put = {
        "apiVersion": "v1",
        "kind": "ResourceQuota",
        "metadata": {
            "name": project_name,
            "namespace": project_name,
            "cluster": "default",
            "resourceVersion": resource_version
        },
        "spec": {
            "hard": hard}}
    if resource_version is None:
        print('post')
        response = requests.post(url=url_post, headers=get_header(), data=json.dumps(data_post))
    else:
        response = requests.put(url=url_put, headers=get_header(), data=json.dumps(data_put))
    return response


@allure.step('查询项目配额')
def step_get_project_quota(project_name):
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha2/namespaces/' + project_name + '/quotas'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('获取容器默认资源请求')
def step_get_container_quota(project_name, ws_name):
    url = config.url + '/api/v1/namespaces/' + project_name + '/limitranges?workspace=' + ws_name
    try:
        response = requests.get(url=url, headers=get_header())
        return response
    except Exception as e:
        print(e)


@allure.step('编辑容器资源默认请求')
def step_edit_container_quota(project_name, name, resource_version, limit, request):
    url_post = config.url + '/api/v1/namespaces/' + project_name + '/limitranges'
    url_put = config.url + '/api/v1/namespaces/' + project_name + '/limitranges/' + name
    data_post = {
        "apiVersion": "v1",
        "kind": "LimitRange",
        "metadata": {
            "annotations": {"kubesphere.io/creator": "admin"}},
        "spec": {
            "limits": [
                {
                    "type": "Container",
                    "default": limit,
                    "defaultRequest": request
                }
            ]
        }
    }
    data_put = {
        "metadata": {
            "name": name,
            "namespace": project_name,
            "annotations": {"kubesphere.io/creator": "admin"},
            "resourceVersion": resource_version},
        "spec": {
            "limits": [
                {
                    "type": "Container",
                    "default": limit,
                    "defaultRequest": request
                }
            ]
        }
    }
    if resource_version is None:
        response = requests.post(url=url_post, headers=get_header(), data=json.dumps(data_post))
    else:
        response = requests.put(url=url_put, headers=get_header(), data=json.dumps(data_put))
    return response


@allure.step('在单集群环境删除指定的项目')
def step_delete_project(ws_name, project_name):
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/namespaces/' + project_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('在单集群环境创建项目')
def step_create_project(ws_name, project_name):
    """
    :param ws_name: 企业空间名称
    :param project_name: 项目名称
    """
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/namespaces'
    data = {"apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {"name": project_name,
                         "labels": {"kubesphere.io/workspace": "wx-ws"},
                         "annotations": {"kubesphere.io/creator": "admin"}
                         }
            }
    requests.post(url, headers=get_header(), data=json.dumps(data))


@allure.step('在指定集群创建项目')
def step_create_project_for_cluster(cluster_name, ws_name, project_name):
    url = config.url + '/kapis/clusters/' + cluster_name + '/tenant.kubesphere.io/v1alpha2/workspaces/' + \
          ws_name + '/namespaces'
    data = {"apiVersion": "v1", "kind": "Namespace",
            "metadata": {"name": project_name, "labels": {"kubesphere.io/workspace": ws_name},
                         "annotations": {"kubesphere.io/creator": "admin"}}, "cluster": cluster_name}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    print(response.json())
    return response


@allure.step('从指定集群删除项目')
def step_delete_project_from_cluster(cluster_name, ws_name, project_name):
    url = config.url + '/kapis/clusters/' + cluster_name + '/tenant.kubesphere.io/v1alpha2/workspaces/' + \
          ws_name + '/namespaces/' + project_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('在项目应用列表查看指定应用信息')
def step_get_app_status(ws_name, project_name, app_name):
    """
    :param ws_name: 企业空间
    :param project_name: 项目名称
    :param app_name: 应用名称
    :return: 应用状态
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/namespaces/' + project_name + '/applications?conditions=keyword%3D' + app_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在项目应用列表中查看应用是否存在')
def step_get_app_count(ws_name, project_name, app_name):
    """
    :param ws_name: 企业空间
    :param project_name: 项目名称
    :param app_name: 应用名称
    :return:
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/clusters/default/namespaces/' + \
          project_name + '/applications?conditions=status%3Dactive%7Cstopped%7Cpending%7Csuspended%2Ckeyword%3D' + \
          app_name + '&paging=limit%3D10%2Cpage%3D1&orderBy=status_time&reverse=true'
    r = requests.get(url=url, headers=get_header())
    return r.json()['total_count']


@allure.step('在项目应用列表获取指定应用的cluster_id')
def step_get_deployed_app(ws_name, project_name, app_name):
    """
    :param ws_name: 企业空间
    :param project_name: 项目名称
    :param app_name: 应用名称
    :return: 应用的cluster_id
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/namespaces/' + project_name + \
          '/applications?conditions=keyword%3D' + app_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('删除项目应用列表指定的应用')
def step_delete_app(ws_name, project_name, cluster_id):
    """
    :param ws_name: 企业空间
    :param project_name: 项目名称
    :param cluster_id: 部署后的应用的id
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/namespaces/' + project_name + \
          '/applications/' + cluster_id
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('查询项目的pod信息')
def step_get_pod_info_of_project(project_name):
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + '/pods?sortBy=startTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询企业空间的项目信息')
def step_get_project_info(ws_name):
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/namespaces?' \
                                                                                      'sortBy=createTime&labelSelector=%21kubesphere.io%2Fkubefed-host-namespace%2C%21kubesphere.io%2Fdevopsproject'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在项目中查询pod')
def step_get_pod_info(project_name, pod_name):
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + '/pods?' \
                                                                                              'name=' + pod_name + '&sortBy=startTime&limit=10'
    response = requests.get(url=url, headers=get_header())
    return response


#####多集群######
@allure.step('获取host集群的名称')
def step_get_host_name():
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/clusters?labelSelector=cluster-role.kubesphere.io%2Fhost'
    response = requests.get(url=url, headers=get_header())
    return response.json()['items'][0]['metadata']['name']


@allure.step('在多集群环境查询项目的federatedlimitranges')
def step_get_project_federatedlimitranges(project_name):
    url = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federatedlimitranges'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在多集群环境查询落盘日志收集功能')
def step_check_disk_log_collection(project_name):
    url = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + \
          '/federatednamespaces/' + project_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在多集群项目创建deployment')
def step_create_deploy_in_multi_project(cluster_name, project_name, work_name, container_name, image, replicas, ports,
                                        volumemount,
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
def step_create_stateful_in_multi_project(cluster_name, project_name, work_name, container_name, image, replicas, ports,
                                          service_ports,
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
def step_create_service_in_multi_project(cluster_name, project_name, service_name, port):
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
def step_create_route_in_multi_project(cluster_name, project_name, ingress_name, host, service_info):
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
def step_create_gateway_in_multi_project(cluster_name, project_name, type, annotations):
    url = config.url + '/kapis/clusters/' + cluster_name + \
          '/resources.kubesphere.io/v1alpha2/namespaces/' + project_name + '/router'
    data = {"type": type, "annotations": annotations}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('编辑多集群项目的网关')
def step_edit_gateway_in_multi_project(cluster_name, project_name, type, annotations):
    url = config.url + '/kapis/clusters/' + cluster_name + \
          '/resources.kubesphere.io/v1alpha2/namespaces/' + project_name + '/router'
    data = {"type": type, "annotations": annotations}
    response = requests.put(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('在多集群项目删除网关')
def step_delete_gateway_in_multi_project(cluster_name, project_name):
    url = config.url + '/kapis/clusters/' + cluster_name + \
          '/resources.kubesphere.io/v1alpha2/namespaces/' + project_name + '/router'
    data = {}
    response = requests.delete(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('查看多集群项目网关')
def step_get_gateway_in_multi_project(cluster_name, project_name):
    url = config.url + '/kapis/clusters/' + cluster_name + \
          '/resources.kubesphere.io/v1alpha2/namespaces/' + project_name + '/router'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('修改多集群项目工作负载副本数')
def step_modify_work_replicas_in_multi_project(cluster_name, project_name, type, work_name, replicas):
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
def step_get_work_pod_info_in_multi_project(cluster_name, project_name, work_name):
    status = []
    url = config.url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/namespaces/' + \
          project_name + '/pods?ownerKind=ReplicaSet&labelSelector=app%3D' + work_name

    r = requests.get(url=url, headers=get_header())
    return r


@allure.step('在多集群环境获取指定的工作负载')
def step_get_workload_in_multi_project(cluster_name, project_name, type, condition):
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


@allure.step('删除多集群项目指定的工作负载')
def step_delete_workload_in_multi_project(project_name, type, work_name):
    url = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + '/federated' + type + '/' + work_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('在多集群环境创建存储卷')
def step_create_volume_in_multi_project(cluster_name, project_name, volume_name):
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
def step_delete_volume_in_multi_project(project_name, volume_name):
    url = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + \
          '/federatedpersistentvolumeclaims/' + volume_name
    # 删除存储卷
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('获取多集群项目存储卷状态')
def step_get_volume_status_in_multi_project(cluster_name, project_name, volume_name):
    url = config.url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/namespaces/' \
          + project_name + '/persistentvolumeclaims?names=' + volume_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询指定的存储卷快照')
def step_get_volume_snapshot(project_name, snapshot_name):
    url1 = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + \
           '/volumesnapshots?name=' + snapshot_name + '&sortBy=createTime&limit=10'
    response = requests.get(url=url1, headers=get_header())
    return response


@allure.step('查询指定的多集群项目')
def step_get_project_in_multi_project(ws_name, project_name):
    url1 = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + \
           '/federatednamespaces?name=' + project_name
    response = requests.get(url=url1, headers=get_header())
    return response


@allure.step('编辑多集群项目')
def step_edit_project_in_multi_project(cluster_name, ws_name, project_name, alias_name, description):
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
def step_get_project_quota_version_in_multi_project(cluster_name, project_name):
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
def step_edit_project_quota_in_multi_project(cluster_name, project_name, hard, resource_version):
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
def step_get_project_quota_in_multi_project(cluster_name, project_name):
    url = config.url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha2/namespaces/' + \
          project_name + '/quotas'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('获取多集群环境容器默认资源请求')
def step_get_container_quota_in_multi_project(project_name, ws_name):
    url = config.url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + \
          '/federatedlimitranges?workspace=' + ws_name
    try:
        response = requests.get(url=url, headers=get_header())
        return response
    except Exception as e:
        print(e)


@allure.step('在多集群项目编辑容器资源默认请求')
def step_edit_container_quota_in_multi_project(cluster_name, project_name, resource_version, limit, request):
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
    response = workspace_steps.step_get_ws_info('')
    ws_count = response.json()['totalItems']
    for k in range(0, ws_count):
        # 获取每个企业空间的名称
        ws_name = response.json()['items'][k]['metadata']['name']
        if ws_name != 'system-workspace':
            # 查询环境中存在的所有多集群项目
            r = step_get_project_in_multi_project(ws_name, '')
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
def step_create_secret_default_in_multi_project(cluster_name, project_name, secret_name, key, value):
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
def step_create_secret_tls_in_multi_project(cluster_name, project_name, secret_name, credential, key):
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


@allure.step('在单集群项目查询密钥')
def step_get_secret(project_name, secret_name):
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + \
          '/secrets?name=' + secret_name + '&sortBy=createTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在多集群项目查询配置')
def step_get_config_map(project_name, config_name):
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + \
          '/configmaps?name=' + config_name + '&sortBy=createTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在多集群项目创建镜像仓库类型密钥')
def step_create_secret_image_in_multi_project(cluster_name, project_name, secret_name):
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
def step_create_secret_account_in_multi_project(cluster_name, project_name, secret_name, username, password):
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
def step_create_config_map_in_multi_project(cluster_name, project_name, config_name, key, value):
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


@allure.step('在多集群环境查询项目的监控信息')
def step_get_project_metrics_in_multi_project(cluster_name, project_name, start_time, end_time, step, times):
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
def step_get_project_abnormalworkloads_in_multi_project(cluster_name, project_name):
    url = config.url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha2/namespaces/' + \
          project_name + '/abnormalworkloads'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在多集群环境查询项目的workloads')
def step_get_project_workloads_in_multi_project(cluster_name, project_name):
    url = config.url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/namespaces/' + \
          project_name + '/workloads?type=rank&metrics_filter=workload_cpu_usage%7Cworkload_memory_usage_wo_cache%7C' \
                         'workload_net_bytes_transmitted%7Cworkload_net_bytes_received%7Creplica&page=1&limit=10' \
                         '&sort_type=desc&sort_metric=workload_cpu_usage'
    response = requests.get(url=url, headers=get_header())
    return response
