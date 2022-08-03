import requests
import json
import allure
import sys
from common.getHeader import get_header, get_header_for_patch
from common import commonFunction
from common.getConfig import get_apiserver

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

env_url = get_apiserver()


@allure.step('创建一个计算圆周率的任务')
def step_create_job(project_name, job_name):
    """
    :param project_name: 项目名称
    :param job_name: 任务名称
    """
    container_name = 'container-' + job_name
    url = env_url + '/apis/batch/v1/namespaces/' + project_name + '/jobs?dryRun=All'
    url1 = env_url + '/apis/batch/v1/namespaces/' + project_name + '/jobs'
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
                                                           "image": "perl:5.34",
                                                           "command": ["perl", "-Mbignum=bpi", "-wle",
                                                                       "print bpi(2000)"]}],  # 输出π，2000位
                                           "restartPolicy": "OnFailure",
                                           "serviceAccount": "default",
                                           "initContainers": [],
                                           "volumes": []}},
                     "backoffLimit": 2, "completions": 2, "parallelism": 2, "activeDeadlineSeconds": 200}}

    requests.post(url=url, headers=get_header(), data=json.dumps(data))
    requests.post(url=url1, headers=get_header(), data=json.dumps(data))


@allure.step('查看任务信息')
def step_get_job_detail(project_name, job_name):
    """
    :param project_name: 项目名称
    :param job_name: 任务名称
    """
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + \
          '/jobs?name=' + job_name + '&sortBy=updateTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('验证任务状态为运行中,并返回任务的uid')
def step_get_job_status_run(project_name, job_name):
    """
    :param project_name: 项目名称
    :param job_name: 任务名称
    :return: 任务的uid
    """
    # 验证任务状态为运行中
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + \
          '/jobs?name=' + job_name + '&sortBy=updateTime&limit=10'
    r2 = requests.get(url=url, headers=get_header())
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
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + '/jobs?' + way + '=' + \
          condition + '&sortBy=updateTime&limit=10'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('删除指定任务，并返回删除结果')
def step_delete_job(project_name, job_name):
    """
    :param project_name: 项目名称
    :param job_name: 任务名称
    :return: 结果
    """
    url = env_url + '/apis/batch/v1/namespaces/' + project_name + '/jobs/' + job_name
    data = {"kind": "DeleteOptions",
            "apiVersion": "v1",
            "propagationPolicy": "Background"}
    response = requests.delete(url=url, headers=get_header(), data=json.dumps(data))
    # 返回删除结果
    return response


@allure.step('查看任务的容器组信息')
def step_get_job_pods(project_name, uid):
    """
    :param project_name: 项目名称
    :param uid: 容器的uid
    """
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + \
          '/pods?limit=10&ownerKind=Job&labelSelector=controller-uid%3D' + uid + '&sortBy=startTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('获取容器组的日志')
def step_get_pods_log(project_name, pod_name, job_name):
    """
    :param project_name: 项目名称
    :param pod_name: 容器名称
    :param job_name: 任务名称
    """
    container_name = 'container-' + job_name
    url = env_url + '/api/v1/namespaces/' + project_name + '/pods/' + pod_name + '/log?container=' + container_name + '&tailLines=1000&timestamps=true&follow=false'
    response = requests.get(url=url, headers=get_header())
    return response.text


@allure.step('创建deployment')
def step_create_deploy(project_name, work_name, container_name, image, replicas, ports, volumemount,
                       volume_info, strategy, *cluster_name):
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
    if cluster_name:
        for i in cluster_name:
            path_1 = '/apis/clusters/' + str(i)
            path_2 = '/apis/clusters/' + str(i)
    else:
        path_1 = '/apis'
        path_2 = '/apis'
    url1 = env_url + path_1 + '/apps/v1/namespaces/' + project_name + '/' + 'deployments?dryRun=All'
    url2 = env_url + path_2 + '/apps/v1/namespaces/' + project_name + '/deployments'
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
    url1 = env_url + '/apis/apps/v1/namespaces/' + project_name + '/statefulsets?dryRun=All'
    url3 = env_url + '/apis/apps/v1/namespaces/' + project_name + '/statefulsets'
    url2 = env_url + '/api/v1/namespaces/' + project_name + '/services?dryRun=All'
    url4 = env_url + '/api/v1/namespaces/' + project_name + '/services'
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
    url1 = env_url + '/apis/apps/v1/namespaces/' + project_name + '/daemonsets?dryRun=All'
    url2 = env_url + '/apis/apps/v1/namespaces/' + project_name + '/daemonsets'
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
    url1 = env_url + '/api/v1/namespaces/' + project_name + '/services?dryRun=All'
    url2 = env_url + '/api/v1/namespaces/' + project_name + '/services'

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
    url = env_url + '/apis/networking.k8s.io/v1/namespaces/' + project_name + '/ingresses'
    data = {"apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "namespace": project_name,
                "labels": {},
                "name": ingress_name,
                "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {
                "rules": [
                    {"protocol": "http",
                     "host": host,
                     "http": {
                         "paths": [
                             {"path": "/",
                              "backend": {"service": service_info},
                              "pathType": "ImplementationSpecific"}]}}], "tls": []}}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('开启项目网关')
def step_create_gateway(project_name, type, status):
    url = env_url + '/kapis/gateway.kubesphere.io/v1alpha1/namespaces/' + project_name + '/gateways/'
    if type == 'NodePort':
        data = {"apiVersion": "gateway.kubesphere.io/v1alpha1", "kind": "Gateway",
                "metadata": {"namespace": project_name, "name": "", "creator": "admin",
                             "annotations": {"kubesphere.io/annotations": "", "kubesphere.io/creator": "admin"}},
                "spec": {
                    "controller": {"replicas": 1, "annotations": {}, "config": {},
                                   "scope": {"enabled": True, "namespace": project_name}},
                    "deployment": {"annotations": {"servicemesh.kubesphere.io/enabled": status}, "replicas": 1},
                    "service": {"annotations": {}, "type": type}}}
    elif type == 'LoadBalancer':
        data = {"apiVersion": "gateway.kubesphere.io/v1alpha1", "kind": "Gateway",
                "metadata": {"namespace": project_name, "name": "", "creator": "admin",
                             "annotations": {"kubesphere.io/annotations": "QingCloud Kubernetes Engine",
                                             "kubesphere.io/creator": "admin"}}, "spec": {
                "controller": {"replicas": 1, "annotations": {}, "config": {},
                               "scope": {"enabled": True, "namespace": project_name}},
                "deployment": {"annotations": {"servicemesh.kubesphere.io/enabled": status}, "replicas": 1},
                "service": {
                    "annotations": {"service.beta.kubernetes.io/qingcloud-load-balancer-eip-ids": "",
                                    "service.beta.kubernetes.io/qingcloud-load-balancer-type": "0"},
                    "type": type}}}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('编辑类型为LoadBalancer的网关')
def step_edit_gateway_lb(project_name, uid, resourceversion, provider, annotations, configuration, status):
    """
    :param project_name:
    :param uid:
    :param resourceversion:
    :param provider: 负载均衡器提供商 ex "QingCloud Kubernetes Engine"、"Huawei Cloud CCE"
    :param annotations: 注解 ex {"service.beta.kubernetes.io/qingcloud-load-balancer-eip-ids": "",
                                "service.beta.kubernetes.io/qingcloud-load-balancer-type": "0"}
    :param configuration: 配置选项 ex {"qw":"12"}
    :param status: 链路追踪开启状态
    :return:
    """
    url = env_url + '/kapis/gateway.kubesphere.io/v1alpha1/namespaces/' + project_name + '/gateways/'
    data = {"metadata": {"name": "kubesphere-router-" + project_name, "namespace": "kubesphere-controls-system",
                         "uid": uid, "resourceVersion": resourceversion, "generation": 1,
                         "annotations": {"kubesphere.io/annotations": provider,
                                         "kubesphere.io/creator": "admin"}, "managedFields": [
            {"manager": "ks-apiserver", "operation": "Update", "apiVersion": "gateway.kubesphere.io/v1alpha1",
             "fieldsType": "FieldsV1"}]},
            "spec": {"controller": {"replicas": 1,
                                    "config": configuration,
                                    "scope": {"enabled": True, "namespace": project_name}},
                     "service": {"type": "LoadBalancer",
                                 "annotations": annotations},
                     "deployment": {"replicas": 1, "annotations": {"servicemesh.kubesphere.io/enabled": status}}}}
    response = requests.put(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('编辑类型为NodePort的网关')
def step_edit_gateway_np(project_name, uid, resourceversion, configuration, status):
    url = env_url + '/kapis/gateway.kubesphere.io/v1alpha1/namespaces/' + project_name + '/gateways/'
    data = {"metadata": {"name": "kubesphere-router-" + project_name, "namespace": "kubesphere-controls-system",
                         "uid": uid, "resourceVersion": resourceversion, "generation": 1,
                         "annotations": {"kubesphere.io/annotations": "", "kubesphere.io/creator": "admin"},
                         "managedFields": [{"manager": "ks-apiserver", "operation": "Update",
                                            "apiVersion": "gateway.kubesphere.io/v1alpha1",
                                            "fieldsType": "FieldsV1"}]},
            "spec": {"controller": {"replicas": 1,
                                    "config": configuration,
                                    "scope": {"enabled": True, "namespace": project_name}},
                     "service": {"annotations": {}, "type": "NodePort"},
                     "deployment": {"replicas": 1, "annotations": {"servicemesh.kubesphere.io/enabled": status}}},
            "apiVersion": "gateway.kubesphere.io/v1alpha1", "kind": "Gateway"}
    response = requests.put(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('关闭网关')
def step_delete_gateway(project_name):
    url = env_url + '/kapis/gateway.kubesphere.io/v1alpha1/namespaces/' + project_name + '/gateways/'
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('查看项目网关')
def step_get_gateway(project_name):
    url = env_url + '/kapis/gateway.kubesphere.io/v1alpha1/namespaces/' + project_name + '/gateways/'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('删除service')
def step_delete_service(project_name, service_name):
    url = env_url + '/api/v1/namespaces/' + project_name + '/services/' + service_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('修改工作负载副本数')
def step_modify_work_replicas(project_name, work_name, replicas):
    """
    :param project_name: 项目名称
    :param work_name: 工作负载名称
    :param replicas: 副本数
    """
    url = env_url + '/apis/apps/v1/namespaces/' + project_name + '/deployments/' + work_name
    data = {"spec": {"replicas": replicas}}
    response = requests.patch(url=url, headers=get_header_for_patch(), data=json.dumps(data))
    return response


@allure.step('获取工作负载中所有的容器组的运行状态')
def step_get_work_pod_status(project_name, work_name):
    status = []
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + '/pods' \
                                                                                           '?ownerKind=ReplicaSet&labelSelector=app%3' + work_name + '&name=' + work_name + '&sortBy=startTime'

    r = requests.get(url=url, headers=get_header())
    for i in range(r.json()['totalItems']):
        status.append(r.json()['items'][i]['status']['phase'])

    return status


@allure.step('获取指定的工作负载')
def step_get_workload(project_name, type, condition, *cluster_name):
    """
    :param project_name: 项目名称
    :param type: 负载类型
    :param condition: 查询条件  如：name=test
    :return:
    """
    if cluster_name:
        for i in cluster_name:
            path = '/kapis/clusters/' + str(i)
    else:
        path = '/kapis'
    url = env_url + path + '/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + '/' + type + '?' + condition
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('删除指定的工作负载')
def step_delete_workload(project_name, type, work_name):
    url = env_url + '/apis/apps/v1/namespaces/' + project_name + '/' + type + '/' + work_name
    data = {"kind": "DeleteOptions", "apiVersion": "v1", "propagationPolicy": "Background"}
    response = requests.delete(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('创建存储卷')
def step_create_volume(project_name, volume_name):
    url = env_url + '/api/v1/namespaces/' + project_name + '/persistentvolumeclaims'
    data = {"apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {"namespace": project_name, "name": volume_name, "labels": {},
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"accessModes": ["ReadWriteOnce"], "resources": {"requests": {"storage": "10Gi"}},
                     "storageClassName": "local"}}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('查询指定的存储卷')
def step_get_volume(project_name, volume_name, *cluster_name):
    if cluster_name:
        for i in cluster_name:
            path = '/kapis/clusters/' + str(i)
    else:
        path = '/kapis'
    url1 = env_url + path + '/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + \
                            '/persistentvolumeclaims?name=' + volume_name + '&sortBy=createTime'
    response = requests.get(url=url1, headers=get_header())
    return response


@allure.step('删除存储卷')
def step_delete_volume(project_name, volume_name):
    url = env_url + '/api/v1/namespaces/' + project_name + '/persistentvolumeclaims/' + volume_name
    # 删除存储卷
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('获取存储卷状态')
def step_get_volume_status(project_name, volume_name, *cluster_name):
    if cluster_name:
        for i in cluster_name:
            path = 'kapis/clusters/' + str(i)
    else:
        path = '/kapis'
    url = env_url + path + '/resources.kubesphere.io/v1alpha3/namespaces/' \
          + project_name + '/persistentvolumeclaims?name=' + volume_name + '&sortBy=createTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('创建sa')
def step_create_sa(project_name, sa_name):
    url = env_url + '/api/v1/namespaces/' + project_name + '/serviceaccounts'
    data = {"apiVersion": "v1", "kind": "ServiceAccount",
            "metadata": {"namespace": project_name, "labels": {}, "name": sa_name,
                         "annotations": {"kubesphere.io/creator": "admin"}}}
    requests.post(url=url, headers=get_header(), data=json.dumps(data))


@allure.step('查询指定sa')
def step_get_sa(project_name, sa_name):
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + '/serviceaccounts?name=' + sa_name + '&sortBy=createTime&limit=10'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询项目的角色信息')
def step_get_role(project_name, role_name):
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + project_name + '/roles?name=' + role_name + '&annotation=kubesphere.io%2Fcreator'
    response = requests.get(url, headers=get_header())
    return response


@allure.step('创建角色')
def step_create_role(project_name, role_name):
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + project_name + '/roles'
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
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + project_name + '/roles?name=' + rloe_name
    response = requests.get(url, headers=get_header())
    return response


@allure.step('修改角色信息')
def step_edit_project_role(project_name, role_name, resourceversion, annotations):
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + project_name + '/roles/' + role_name
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
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + project_name + '/roles/' + role_name
    response = requests.delete(url, headers=get_header())
    return response


@allure.step('查看指定用户')
def step_get_project_member(project_name, user_name):
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + project_name + '/members?name=' + user_name
    response = requests.get(url, headers=get_header())
    return response


@allure.step('查看指定sa详情信息')
def step_get_sa_detail(project_name, sa_name):
    url = env_url + '/api/v1/namespaces/' + project_name + '/serviceaccounts/' + sa_name
    r = requests.get(url=url, headers=get_header())


@allure.step('查看指定密钥并返回密钥类型')
def step_get_secret(project_name, secret_name):
    url = env_url + '/api/v1/namespaces/' + project_name + '/secrets/' + secret_name
    r = requests.get(url=url, headers=get_header())
    return r.json()['type']


@allure.step('删除指定sa')
def step_delete_sa(project_name, sa_name):
    url = env_url + '/api/v1/namespaces/' + project_name + '/serviceaccounts/' + sa_name
    r = requests.delete(url=url, headers=get_header())


@allure.step('删除存储卷快照')
def step_delete_volume_snapshot(project_name, snapshot_name):
    url = env_url + '/apis/snapshot.storage.k8s.io/v1beta1/namespaces/' + project_name + \
          '/volumesnapshots/' + snapshot_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('查询指定的存储卷快照')
def step_get_volume_snapshot(project_name, snapshot_name):
    url1 = env_url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + \
           '/volumesnapshots?name=' + snapshot_name + '&sortBy=createTime&limit=10'
    response = requests.get(url=url1, headers=get_header())
    return response


@allure.step('查询指定的项目')
def step_get_project(ws_name, project_name):
    url1 = env_url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + \
           '/namespaces?name=' + project_name
    response = requests.get(url=url1, headers=get_header())
    return response


@allure.step('编辑项目')
def step_edit_project(ws_name, project_name, alias_name, description):
    url = env_url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/namespaces/' + project_name
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
    url = env_url + '/api/v1/namespaces/' + project_name + '/resourcequotas/' + project_name
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
    url_put = env_url + '/api/v1/namespaces/' + project_name + '/resourcequotas/' + project_name
    url_post = env_url + '/api/v1/namespaces/' + project_name + '/resourcequotas'
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
        response = requests.post(url=url_post, headers=get_header(), data=json.dumps(data_post))
    else:
        response = requests.put(url=url_put, headers=get_header(), data=json.dumps(data_put))
    return response


@allure.step('查询项目配额')
def step_get_project_quota(project_name):
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha2/namespaces/' + project_name + '/quotas'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('获取容器默认资源请求')
def step_get_container_quota(project_name, ws_name):
    url = env_url + '/api/v1/namespaces/' + project_name + '/limitranges?workspace=' + ws_name
    try:
        response = requests.get(url=url, headers=get_header())
        return response
    except Exception as e:
        print(e)


@allure.step('编辑容器资源默认请求')
def step_edit_container_quota(project_name, name, resource_version, limit, request):
    url_post = env_url + '/api/v1/namespaces/' + project_name + '/limitranges'
    url_put = env_url + '/api/v1/namespaces/' + project_name + '/limitranges/' + name
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


@allure.step('删除企业空间指定的项目')
def step_delete_project(ws_name, project_name, *cluster_name):
    if cluster_name:
        for i in cluster_name:
            path = '/kapis/clusters/' + str(i)
    else:
        path = '/kapis'
    url = env_url + path + '/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/namespaces/' + project_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('删除指定项目')
def step_delete_project_by_name(project_name):
    url = env_url + '/api/v1/namespaces/' + project_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('在单集群环境创建项目')
def step_create_project(ws_name, project_name):
    """
    :param ws_name: 企业空间名称
    :param project_name: 项目名称
    """
    url = env_url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/namespaces'
    data = {"apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {"name": project_name,
                         "labels": {"kubesphere.io/workspace": ws_name},
                         "annotations": {"kubesphere.io/creator": "admin"}
                         }
            }
    requests.post(url, headers=get_header(), data=json.dumps(data))


@allure.step('在项目应用列表查看指定应用信息')
def step_get_app_status(ws_name, project_name, app_name):
    """
    :param ws_name: 企业空间
    :param project_name: 项目名称
    :param app_name: 应用名称
    :return: 应用状态
    """
    url = env_url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/namespaces/' + project_name + '/applications?conditions=keyword%3D' + app_name
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
    url = env_url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/clusters/default/namespaces/' + \
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
    url = env_url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/namespaces/' + project_name + \
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
    url = env_url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/namespaces/' + project_name + \
          '/applications/' + cluster_id
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('查询项目的pod信息')
def step_get_pod_info_of_project(project_name):
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + '/pods?sortBy=startTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询企业空间的项目信息')
def step_get_project_info(ws_name):
    url = env_url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/namespaces?' \
                                                                                   'sortBy=createTime&labelSelector=%21kubesphere.io%2Fkubefed-host-namespace%2C%21kubesphere.io%2Fdevopsproject'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在项目中查询pod')
def step_get_pod_info(project_name, pod_name):
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + '/pods?' \
                                                                                           'name=' + pod_name + '&sortBy=startTime&limit=10'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在项目设置中设置日志收集状态')
def step_set_logsidecar(ws_name, project_name, status):
    """
    :param ws_name:
    :param project_name:
    :param status: ex "enabled"、"disabled"
    :return:
    """
    url = env_url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/namespaces/' + project_name
    data = {"metadata": {"labels": {"logging.kubesphere.io/logsidecar-injection": status}}}
    response = requests.patch(url=url, headers=get_header_for_patch(), data=json.dumps(data))
    return response


@allure.step('在项目设置中查看日志收集状态')
def step_get_status_logsidecar(project_name):
    url = env_url + '/api/v1/namespaces/' + project_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('项目/应用负载/容器组，查看容器组详情信息')
def step_get_pod_detail(project_name, pod_name):
    url = env_url + '/api/v1/namespaces/' + project_name + '/pods/' + pod_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('项目/项目设置，编辑项目成员角色')
def step_edit_project_member_role(project_name, user_name, role):
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + project_name + '/members/' + user_name
    data = {"username": user_name, "roleRef": role}
    response = requests.put(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('项目/项目设置，添加项目成员')
def step_invite_member(project_name, user_name, role):
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + project_name + '/members'
    data = [{"username": user_name,
             "roleRef": role
             }]
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('项目/项目设置，移出项目成员')
def step_remove_project_member(project_name, user_name):
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + project_name + '/members/' + user_name
    response = requests.delete(url, headers=get_header())
    return response


@allure.step('项目/应用负载/容器组，查询容器组')
def step_get_pod(project_name, pod_name):
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + '/pods?name=' + pod_name + '&sortBy=startTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('项目/应用负载/工作负载，查询工作负载')
def step_get_deployment(project_name, type, **condition):
    condition_actual = ''
    for i in condition:
        condition_actual += str(i) + '&'
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + '/' + type + '?' + condition_actual + 'sortBy=updateTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('项目/应用负载/工作负载，删除工作负载')
def step_delete_workload(project_name, type, work_name):
    url = env_url + '/apis/apps/v1/namespaces/' + project_name + '/' + type + '/' + work_name
    data = {"kind": "DeleteOptions", "apiVersion": "v1", "propagationPolicy": "Background"}
    response = requests.delete(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('项目/应用负载/工作负载，设置弹性伸缩')
def step_set_auto_scale(project_name, work_name):
    url = env_url + '/apis/autoscaling/v2beta2/namespaces/' + project_name + '/horizontalpodautoscalers'
    data = {"metadata": {"name": work_name, "namespace": project_name,
                         "annotations": {"cpuCurrentUtilization": "0", "cpuTargetUtilization": "50",
                                         "memoryCurrentValue": "0", "memoryTargetValue": "2Mi",
                                         "kubesphere.io/creator": "admin"}},
            "spec": {"scaleTargetRef": {"apiVersion": "apps/v1",
                                        "kind": "Deployment",
                                        "name": work_name}, "minReplicas": 1, "maxReplicas": 20,
                     "metrics": [{"type": "Resource",
                                  "resource": {"name": "memory",
                                               "target": {"type": "AverageValue", "averageValue": "2Mi"}}},
                                 {"type": "Resource", "resource": {"name": "cpu", "target":
                                     {"type": "Utilization", "averageUtilization": 50}}}]},
            "apiVersion": "autoscaling/v2beta2", "kind": "HorizontalPodAutoscaler"}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('项目/存储/持久卷声明，删除持久卷声明')
def step_delete_pvc(project_name, pvc_name, *cluster_name):
    if cluster_name:
        for i in cluster_name:
            path = '/api/clusters/' + str(i)
    else:
        path = '/api'
    url = env_url + path + '/v1/namespaces/' + project_name + '/persistentvolumeclaims/' + pvc_name
    response = requests.delete(url=url, headers=get_header())
    return response


#####多集群######
@allure.step('查询指定的存储卷快照')
def step_get_volume_snapshot(project_name, snapshot_name):
    url1 = env_url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + \
           '/volumesnapshots?name=' + snapshot_name + '&sortBy=createTime&limit=10'
    response = requests.get(url=url1, headers=get_header())
    return response


@allure.step('编辑多集群项目')
def step_edit_project_in_multi_project(cluster_name, ws_name, project_name, alias_name, description):
    url = env_url + '/apis/types.kubefed.io/v1beta1/namespaces/' + project_name + \
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


@allure.step('获取环境中所有的多集群项目的名称')
def step_get_multi_projects_name():
    url = env_url + '/kapis/tenant.kubesphere.io/v1alpha2/federatednamespaces?sortBy=createTime'
    response = requests.get(url=url, headers=get_header())
    multi_project_name = []
    for i in range(0, response.json()['totalItems']):
        multi_project_name.append(response.json()['items'][i]['metadata']['name'])
    return multi_project_name


@allure.step('按名称删除项目')
def step_delete_project_by_name(project_name):
    url = env_url + '/api/v1/namespaces/' + project_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('在单集群项目查询密钥')
def step_get_secret(project_name, secret_name):
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + \
          '/secrets?name=' + secret_name + '&sortBy=createTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('获取集群中所有的系统项目的名称')
def step_get_system_project(cluster_name):
    # 判断环境是否是多集群环境
    if commonFunction.check_multi_cluster() is True:
        url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/namespaces?' \
                                                            'sortBy=createTime&labelSelector=kubesphere.io%2Fworkspace%3Dsystem-workspace'
    else:
        url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces?' \
                        'sortBy=createTime&labelSelector=kubesphere.io%2Fworkspace%3Dsystem-workspace'
    response = requests.get(url=url, headers=get_header())
    count = response.json()['totalItems']
    ns = []
    for i in range(0, count):
        ns.append(response.json()['items'][i]['metadata']['name'])
    return ns


@allure.step('获取应用负载')
def step_get_deployment(project_name, type):
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + '/' + type + '?'
    params = {
        'sortBy': 'updateTime',
        'limit': '10'
    }
    r = requests.get(url=url, headers=get_header(), params=params)
    return r


@allure.step('项目/工作负载/容器组,删除pod')
def step_delete_pod(project_name, pod_name):
    url = env_url + '/api/v1/namespaces/' + project_name + '/pods/' + pod_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('项目/工作负载/应用路由，查询指定应用路由')
def step_get_route(project_name, condition):
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + \
          '/ingresses?' + condition + '&sortBy=createTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('项目/工作负载/应用路由，删除路由')
def step_delete_route(project_name, ingress_name):
    url = env_url + '/apis/networking.k8s.io/v1/namespaces/' + project_name + '/ingresses/' + ingress_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('项目/工作负载，删除deployment')
def step_delete_deployment(project_name, deploy_name, *cluster_name):
    if cluster_name:
        for i in cluster_name:
            path = '/apis/clusters/' + str(i)
    else:
        path = '/apis'
    url = env_url + path + '/apps/v1/namespaces/' + project_name + '/deployments/' + deploy_name
    response = requests.delete(url=url, headers=get_header())
    return response
