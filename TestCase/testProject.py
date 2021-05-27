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


@allure.step('创建任务')
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
            "spec": {"accessModes": ["ReadWriteOnce"], "resources": {"requests": {"storage": "10Gi"}}}}
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


@allure.step('删除指定的项目')
def step_delete_project(ws_name, project_name):
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/namespaces/' + project_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.feature('Project')
class TestProject(object):
    volume_name = 'testvolume'  # 存储卷名称，在创建、删除存储卷和创建存储卷快照时使用,excle中的用例也用到了这个存储卷
    snapshot_name = 'testshot'  # 存储卷快照的名称,在创建和删除存储卷快照时使用，在excle中的用例也用到了这个快照
    user_name = 'user-for-test-project'  # 系统用户名称
    ws_name = 'ws-for-test-project'  # 企业空间名称,不可修改，从excle中获取的测试用例中用到了这个企业空间
    project_name = 'test-project'  # 项目名称，从excle中获取的测试用例中用到了这个项目名称
    ws_role_name = ws_name + '-viewer'  # 企业空间角色名称
    project_role_name = 'test-project-role'  # 项目角色名称
    job_name = 'demo-job'  # 任务名称,在创建和删除任务时使用
    work_name = 'workload-demo'  # 工作负载名称，在创建、编辑、删除工作负载时使用
    # 从文件中读取用例信息
    parametrize = DoexcleByPandas().get_data_for_pytest(filename='../data/data.xlsx', sheet_name='project')

    # 所有用例执行之前执行该方法
    def setup_class(self):
        commonFunction.create_user(self.user_name)  # 创建一个用户
        commonFunction.create_workspace(self.ws_name)  # 创建一个企业空间
        commonFunction.ws_invite_user(self.ws_name, self.user_name, self.ws_name + '-viewer')  # 将创建的用户邀请到企业空间
        commonFunction.create_project(self.ws_name, self.project_name)  # 创建一个project工程

    # 所有用例执行完之后执行该方法
    def teardown_class(self):
        commonFunction.delete_project(self.ws_name, self.project_name)  # 删除创建的项目
        time.sleep(5)
        commonFunction.delete_workspace(self.ws_name)  # 删除创建的工作空间
        commonFunction.delete_user(self.user_name)  # 删除创建的用户

    '''
    以下用例由于存在较多的前置条件，不便于从excle中获取信息，故使用一个方法一个用例的方式
    '''

    @allure.story('存储管理-存储卷')
    @allure.title('创建存储卷，然后将存储卷绑定到新建的deployment上，最后验证资源和存储卷的状态正常')
    @allure.severity(allure.severity_level.BLOCKER)
    def test_create_volume_for_deployment(self):
        type_name = 'volume-type'  # 存储卷的类型
        replicas = 1  # 副本数
        image = 'redis'  # 镜像名称
        container_name = 'container1'  # 容器名称
        condition = 'name=' + self.work_name  # 查询条件
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80}]  # 容器的端口信息
        volumeMounts = [{"name": type_name, "readOnly": False, "mountPath": "/data"}]  # 设置挂载哦的存储卷
        strategy_info = {"type": "RollingUpdate", "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
        volume_info = [{"name": type_name, "persistentVolumeClaim": {"claimName": self.volume_name}}]  # 存储卷的信息
        # 创建存储卷
        step_create_volume(self.project_name, self.volume_name)
        # 创建资源并将存储卷绑定到资源
        step_create_deploy(self.project_name, work_name=self.work_name, image=image, replicas=replicas,
                           container_name=container_name, volume_info=volume_info, ports=port,
                           volumemount=volumeMounts, strategy=strategy_info)
        # 验证资源创建成功
        time.sleep(10)  # 等待资源创建成功
        # 获取工作负载的状态
        response = step_get_workload(self.project_name, type='deployments', condition=condition)
        status = response.json()['items'][0]['status']
        # 验证资源的所有副本已就绪
        assert 'unavailableReplicas' not in status
        # 获取存储卷状态
        response = step_get_volume_status(self.project_name, self.volume_name)
        status = response.json()['items'][0]['status']['phase']
        # 验证存储卷状态正常
        assert status == 'Bound'

    @allure.story('存储管理-存储卷')
    @allure.title('创建存储卷，然后将存储卷绑定到新建的statefulsets上，最后验证资源和存储卷的状态正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_volume_for_statefulsets(self):
        volume_name = 'volume-stateful'  # 存储卷的名称
        type_name = 'volume-type'  # 存储卷的类型
        work_name = 'stateful-with-volume'  # 工作负载的名称
        service_name = 'service' + volume_name
        replicas = 2  # 副本数
        image = 'nginx'  # 镜像名称
        container_name = 'container-stateful'  # 容器名称
        condition = 'name=' + work_name  # 查询条件
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]
        service_port = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]
        volumemounts = [{"name": type_name, "readOnly": False, "mountPath": "/data"}]
        volume_info = [{"name": type_name, "persistentVolumeClaim": {"claimName": volume_name}}]  # 存储卷的信息
        # 创建存储卷
        step_create_volume(self.project_name, volume_name)
        # 创建资源并将存储卷绑定到资源
        step_create_stateful(project_name=self.project_name, work_name=work_name, container_name=container_name,
                             image=image, replicas=replicas, ports=port, service_ports=service_port,
                             volumemount=volumemounts, volume_info=volume_info, service_name=service_name)

        # 验证资源创建成功
        time.sleep(10)  # 等待资源创建成功
        # 获取工作负载的状态
        response = step_get_workload(self.project_name, type='statefulsets', condition=condition)
        readyReplicas = response.json()['items'][0]['status']['readyReplicas']
        # 验证资源的所有副本已就绪
        assert readyReplicas == replicas
        # 获取存储卷状态
        response = step_get_volume_status(self.project_name, volume_name)
        status = response.json()['items'][0]['status']['phase']
        # 验证存储卷状态正常
        assert status == 'Bound'

    @allure.story('存储管理-存储卷')
    @allure.title('创建存储卷，然后将存储卷绑定到新建的daemonsets上，最后验证资源和存储卷的状态正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_volume_for_daemonsets(self):
        volume_name = 'volume-deamon'  # 存储卷的名称
        type_name = 'volume-type'  # 存储卷的类型
        work_name = 'workload-daemon'  # 工作负载的名称
        image = 'redis'  # 镜像名称
        container_name = 'container-daemon'  # 容器名称
        condition = 'name=' + work_name  # 查询条件
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80}]  # 容器的端口信息
        volumeMounts = [{"name": type_name, "readOnly": False, "mountPath": "/data"}]  # 设置挂载哦的存储卷
        volume_info = [{"name": type_name, "persistentVolumeClaim": {"claimName": volume_name}}]  # 存储卷的信息
        # 创建存储卷
        step_create_volume(self.project_name, volume_name)
        # 创建资源并将存储卷绑定到资源
        step_create_daemonset(self.project_name, work_name=work_name, image=image,
                              container_name=container_name, volume_info=volume_info, ports=port,
                              volumemount=volumeMounts)
        # 验证资源创建成功
        time.sleep(10)  # 等待资源创建成功
        # 获取工作负载的状态
        response = step_get_workload(self.project_name, type='daemonsets', condition=condition)
        numberReady = response.json()['items'][0]['status']['numberReady']  # 验证资源的所有副本已就绪
        assert numberReady == 1
        # 获取存储卷状态
        response = step_get_volume_status(self.project_name, volume_name)
        status = response.json()['items'][0]['status']['phase']
        # 验证存储卷状态正常
        assert status == 'Bound'

    @allure.story('存储管理-存储卷')
    @allure.title('创建存储卷，然后将存储卷绑定到新建的service上，最后验证资源和存储卷的状态正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_volume_for_service(self):
        volume_name = 'volume-service'  # 存储卷的名称
        type_name = 'volume-type'  # 存储卷的类型
        service_name = 'service' + str(commonFunction.get_random())   # 工作负载的名称
        image = 'redis'  # 镜像名称
        container_name = 'container-daemon'  # 容器名称
        condition = 'name=' + service_name  # 查询条件
        port_service = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]  # service的端口信息
        port_deploy = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80}]  # 容器的端口信息
        volumeMounts = [{"name": type_name, "readOnly": False, "mountPath": "/data"}]  # 设置挂载哦的存储卷
        volume_info = [{"name": type_name, "persistentVolumeClaim": {"claimName": volume_name}}]  # 存储卷的信息
        strategy_info = {"type": "RollingUpdate", "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
        replicas = 2  # 副本数
        # 创建存储卷
        step_create_volume(self.project_name, volume_name)
        # 创建service
        step_create_service(self.project_name, service_name, port_service)
        # 创建service绑定的deployment
        step_create_deploy(project_name=self.project_name, work_name=service_name, container_name=container_name,
                           ports=port_deploy, volumemount=volumeMounts, image=image, replicas=replicas,
                           volume_info=volume_info, strategy=strategy_info)
        # 验证service创建成功
        response = step_get_workload(self.project_name, type='services', condition=condition)
        name = response.json()['items'][0]['metadata']['name']
        assert name == service_name
        # 验证deploy创建成功
        time.sleep(3)
        re = step_get_workload(self.project_name, type='deployments', condition=condition)
        # 获取并验证deployment的名称正确
        name = re.json()['items'][0]['metadata']['name']
        assert name == service_name
        # 获取存储卷状态
        response = step_get_volume_status(self.project_name, volume_name)
        status = response.json()['items'][0]['status']['phase']
        # 验证存储卷状态正常
        assert status == 'Bound'

    @allure.story('存储管理-存储卷快照')
    @allure.title('创建存储卷快照，并验证创建成功')
    @allure.severity(allure.severity_level.BLOCKER)
    def wx_test_create_volume_snapshot(self):
        url = config.url + '/apis/snapshot.storage.k8s.io/v1beta1/namespaces/' + self.project_name + '/volumesnapshots'
        data = {"apiVersion": "snapshot.storage.k8s.io/v1beta1",
                "kind": "VolumeSnapshot",
                "metadata": {"name": self.snapshot_name,
                             "annotations": {"kubesphere.io/creator": "admin"}},
                "spec": {"volumeSnapshotClassName": "csi-standard",
                         "source": {"kind": "PersistentVolumeClaim",
                                    "persistentVolumeClaimName": self.volume_name}}}
        # 创建存储卷快照
        r = requests.post(url=url, headers=get_header(), data=json.dumps(data))

        print("actual_result:r.json()['metadata']['name'] = " + r.json()['metadata']['name'])
        print("expect_result:" + self.snapshot_name)
        assert r.json()['metadata']['name'] == self.snapshot_name

        # 查询创建的存储卷快照
        url1 = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + self.project_name + \
               '/volumesnapshots?name=' + self.snapshot_name + '&sortBy=createTime&limit=10'
        i = 0
        # 验证存储卷快照状态为准备就绪，最长等待时间为150s
        while i < 150:
            r1 = requests.get(url=url1, headers=get_header())
            # 存储卷快照的状态为布尔值，故先将结果转换我字符类型
            if str(r1.json()['items'][0]['status']['readyToUse']) == 'True':
                print("创建存储卷快照耗时:" + str(i) + '秒')
                break
            time.sleep(1)
            i = i + 1
        print("actual_result:r1.json()['items'][0]['status']['readyToUse'] = " + str(
            r1.json()['items'][0]['status']['readyToUse']))
        print("expect_result: True")
        # 验证存储卷快照的状态为准备就绪
        assert str(r1.json()['items'][0]['status']['readyToUse']) == 'True'

    @allure.story("项目设置-项目角色")
    @allure.title('查看project工程默认的所有角色')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_project_role_all(self):
        role_name = ''
        r = step_get_role(self.project_name, role_name)
        print("actual_result:r.json()['totalItems']=" + str(r.json()['totalItems']))  # 在日志中打印出实际结果
        print('expect_result: 3')  # 在日志中打印出预期结果
        assert r.json()['totalItems'] == 3  # 验证初始的角色数量为3

    @allure.story("项目设置-项目角色")
    @allure.title('查找project工程中指定的角色')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_role_one(self):
        role_name = 'viewer'
        r = step_get_role(self.project_name, role_name)
        print("actual_result:r.json()['items'][0]['metadata']['name']=" + r.json()['items'][0]['metadata'][
            'name'])  # 在日志中打印出实际结果
        print('expect_result:' + role_name)  # 在日志中打印出预期结果
        assert r.json()['items'][0]['metadata']['name'] == role_name  # 验证查询的角色结果为viewer

    @allure.story("项目设置-项目角色")
    @allure.title('查找project工程中不存在的角色')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_role_none(self):
        role_name = 'viewer123'
        r = step_get_role(self.project_name, role_name)
        print("actual_result:r.json()['totalItems'] =" + str(r.json()['totalItems']))  # 在日志中打印出实际结果
        print('expect_result: 0')  # 在日志中打印出预期结果
        assert r.json()['totalItems'] == 0  # 验证查询到的结果为空

    @allure.story("项目设置-项目角色")
    @allure.title('模糊查找project工程中的角色')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_role_fuzzy(self):
        role_name = 'a'
        r = step_get_role(self.project_name, role_name)
        assert r.json()['totalItems'] == 2  # 验证查询到的结果数量为2
        # 验证查找到的角色
        print("actual_result:r.json()['items'][0]['metadata']['name']=" + r.json()['items'][0]['metadata'][
            'name'])  # 在日志中打印出实际结果
        print('expect_result: operator')  # 在日志中打印出预期结果
        assert r.json()['items'][0]['metadata']['name'] == 'operator'
        assert r.json()['items'][1]['metadata']['name'] == 'admin'

    @allure.story("项目设置-项目角色")
    @allure.title('在project工程中创建角色')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_role_create(self):
        role_name = 'role' + str(commonFunction.get_random())
        r = step_create_role(self.project_name, role_name)
        print("actual_result:r.json()['metadata']['name']=" + r.json()['metadata']['name'])  # 在日志中打印出实际结果
        print('expect_result:' + role_name)  # 在日志中打印出预期结果
        assert r.json()['metadata']['name'] == role_name  # 验证新建的角色名称

    @allure.story("项目设置-项目角色")
    @allure.title('在project工程中创建角色-角色名称为空')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_role_create_name_none(self):
        role_name = ''
        r = step_create_role(self.project_name, role_name)
        # 验证创建角色失败的异常提示信息
        print("actual_result:" + r.text.strip())  # 在日志中打印出实际结果
        print(
            'expect_result:Role.rbac.authorization.k8s.io "" is invalid: metadata.name: Required value: name or generateName is required')  # 在日志中打印出预期结果
        assert r.text.strip() == 'Role.rbac.authorization.k8s.io "" is invalid: metadata.name: Required value: name or generateName is required'

    @allure.story("项目设置-项目角色")
    @allure.title('在project工程中编辑角色基本信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_project_role_edit_info(self):
        alias_name = '我是别名'  # 别名
        url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + self.project_name + '/roles/' + self.project_role_name
        data = {"metadata": {"name": self.project_role_name,
                             "namespace": self.project_name,
                             "annotations": {"iam.kubesphere.io/aggregation-roles": "[\"role-template-view-basic\"]",
                                             "kubesphere.io/alias-name": alias_name,
                                             "kubesphere.io/creator": "admin",
                                             "kubesphere.io/description": "我是描述信息"}
                             }
                }
        r = requests.patch(url, headers=get_header(), data=json.dumps(data))
        print("actual_result:r.json()['metadata']['annotations']['kubesphere.io/alias-name']=" +
              r.json()['metadata']['annotations']['kubesphere.io/alias-name'])  # 在日志中打印出实际结果
        print('expect_result:' + alias_name)  # 在日志中打印出预期结果
        assert r.json()['metadata']['annotations']['kubesphere.io/alias-name'] == '我是别名'  # 验证修改后的别名
        assert r.json()['metadata']['annotations']['kubesphere.io/description'] == '我是描述信息'  # 验证修改后的描述信息

    @allure.story("项目设置-项目角色")
    @allure.title('在project工程中编辑角色的权限信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_project_role_edit_authority(self):
        # 获取角色的resourceVersion
        resourceVersion = commonFunction.get_project_role_version(self.project_name, self.project_role_name)
        # 编辑觉得的权限
        authority = '["role-template-view-basic","role-template-view-volumes","role-template-view-secrets","role-template-view-configmaps","role-template-view-snapshots","role-template-view-app-workloads"]'
        url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + self.project_name + '/roles/' + self.project_role_name
        data = {"metadata": {"name": self.project_role_name,
                             "namespace": self.project_name,
                             "resourceVersion": resourceVersion,
                             "annotations": {"iam.kubesphere.io/aggregation-roles": authority,

                                             "kubesphere.io/alias-name": "",
                                             "kubesphere.io/creator": "admin", "kubesphere.io/description": ""}
                             }
                }
        r = requests.put(url, headers=get_header(), data=json.dumps(data))

        print("actual_result:r.json()['metadata']['annotations']['iam.kubesphere.io/aggregation-roles']=" +
              r.json()['metadata']['annotations']['iam.kubesphere.io/aggregation-roles'])  # 在日志中打印出实际结果
        print('expect_result:' + authority)  # 在日志中打印出预期结果
        assert r.json()['metadata']['annotations']['iam.kubesphere.io/aggregation-roles'] == authority  # 验证修改后的权限信息

    @allure.story("项目设置-项目角色")
    @allure.title('在project工程中删除角色')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_project_role_delete(self):
        url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + self.project_name + '/roles/' + self.project_role_name
        r = requests.delete(url, headers=get_header())

        print("actual_result:r.json()['message']=" + r.json()['message'])  # 在日志中打印出实际结果
        print('expect_result: success')  # 在日志中打印出预期结果
        assert r.json()['message'] == 'success'

    @allure.story("项目设置-项目成员")
    @allure.title('查看project默认的所有用户')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_project_user_all(self):
        url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + self.project_name + '/members'
        r = requests.get(url, headers=get_header())

        print("actual_result:r.json()['items'][0]['metadata']['name']=" + r.json()['items'][0]['metadata'][
            'name'])  # 在日志中打印出实际结果
        print('expect_result: admin')  # 在日志中打印出预期结果
        assert r.json()['items'][0]['metadata']['name'] == 'admin'  # 验证默认的用户仅有admin

    @allure.story("项目设置-项目成员")
    @allure.title('查找project指定的用户')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_user_one(self):
        user_condition = 'admin'
        url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + self.project_name + '/members?name=' + user_condition
        r = requests.get(url, headers=get_header())

        print("actual_result:r.json()['items'][0]['metadata']['name']=" + r.json()['items'][0]['metadata'][
            'name'])  # 在日志中打印出实际结果
        print('expect_result:' + user_condition)  # 在日志中打印出预期结果
        assert r.json()['items'][0]['metadata']['name'] == user_condition  # 验证查找的结果为admin

    @allure.story("项目设置-项目成员")
    @allure.title('模糊查找project的用户')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_user_fuzzy(self):
        user_condition = 'ad'
        url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + self.project_name + '/members?name=' + user_condition
        r = requests.get(url, headers=get_header())

        print("actual_result:r.json()['items'][0]['metadata']['name']=" + r.json()['items'][0]['metadata'][
            'name'])  # 在日志中打印出实际结果
        print('expect_result: admin')  # 在日志中打印出预期结果
        assert r.json()['items'][0]['metadata']['name'] == 'admin'  # 验证查找的结果为admin

    @allure.story("项目设置-项目成员")
    @allure.title('查找project工程不存在的用户')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_user_none(self):
        user_condition = 'wx-ad'
        url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + self.project_name + '/members?name=' + user_condition
        r = requests.get(url, headers=get_header())

        print("actual_result:r.json()['totalItems']=" + str(r.json()['totalItems']))  # 在日志中打印出实际结果
        print('expect_result: 0')  # 在日志中打印出预期结果
        assert r.json()['totalItems'] == 0  # 验证查找的结果为空

    @allure.story("项目设置-项目成员")
    @allure.title('邀请用户到project')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_project_invite_user(self):
        url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + self.project_name + '/members'
        data = [{"username": self.user_name,
                 "roleRef": 'viewer'
                 }]
        r = requests.post(url, headers=get_header(), data=json.dumps(data))

        print("actual_result:r.json()[0]['username']=" + r.json()[0]['username'])  # 在日志中打印出实际结果
        print('expect_result:' + self.user_name)  # 在日志中打印出预期结果
        assert r.json()[0]['username'] == self.user_name  # 验证邀请后的用户名称

    # 用例的执行结果应当为false。接口没有对不存在的用户做限制
    @allure.title('邀请不存在的用户到project')
    @allure.severity(allure.severity_level.CRITICAL)
    def wx_test_project_invite_none_user(self):
        url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + self.project_name + '/members'
        data = [{"username": 'wxqw',
                 "roleRef": "viewer"}]
        r = requests.post(url, headers=get_header(), data=json.dumps(data))
        print(r.text)

    @allure.story("项目设置-项目角色")
    @allure.title('编辑project成员的角色')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_project_edit_user(self):
        url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + self.project_name + '/members/' + self.user_name
        data = {"username": self.user_name,
                "roleRef": "operator"}
        r = requests.put(url, headers=get_header(), data=json.dumps(data))
        assert r.json()['roleRef'] == 'operator'  # 验证修改后的用户角色

    @allure.story("项目设置-项目成员")
    @allure.title('删除project的成员')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_project_delete_user(self):
        url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + self.project_name + '/members/' + self.user_name
        r = requests.delete(url, headers=get_header())
        assert r.json()['message'] == 'success'  # 验证删除成功

    # 以下4条用例的执行结果应当为false，未已test开头表示未执行。接口没有对角色的名称做限制
    @allure.title('在project工程中创建角色-名称中包含大写字母')
    @allure.severity(allure.severity_level.CRITICAL)
    def wx_test_project_role_create_name(self):
        project_role_name = 'WX'
        url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + self.project_name + '/roles'
        data = {"apiVersion": "rbac.authorization.k8s.io/v1",
                "kind": "Role",
                "metadata": {"namespace": self.project_name,
                             "name": project_role_name,
                             "annotations": {"iam.kubesphere.io/aggregation-roles": "[\"role-template-view-basic\"]",
                                             "kubesphere.io/creator": "admin"}
                             },
                "rules": []}
        r = requests.post(url, headers=get_header(), data=json.dumps(data))
        print(r.text)

    @allure.title('在project工程中创建角色-名称中包含非分隔符("-")的特殊符号')
    @allure.severity(allure.severity_level.CRITICAL)
    def wx_test_project_role_create_name1(self):
        project_role_name = 'w@x'
        url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + self.project_name + '/roles'
        data = {"apiVersion": "rbac.authorization.k8s.io/v1",
                "kind": "Role",
                "metadata": {"namespace": self.project_name,
                             "name": project_role_name,
                             "annotations": {"iam.kubesphere.io/aggregation-roles": "[\"role-template-view-basic\"]",
                                             "kubesphere.io/creator": "admin"}
                             },
                "rules": []}
        r = requests.post(url, headers=get_header(), data=json.dumps(data))
        print(r.text)

    @allure.title('在project工程中创建角色-名称以分隔符("-")开头')
    @allure.severity(allure.severity_level.CRITICAL)
    def wx_test_project_role_create_name2(self):
        project_role_name = '-wx'
        url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + self.project_name + '/roles'
        data = {"apiVersion": "rbac.authorization.k8s.io/v1",
                "kind": "Role",
                "metadata": {"namespace": self.project_name,
                             "name": project_role_name,
                             "annotations": {"iam.kubesphere.io/aggregation-roles": "[\"role-template-view-basic\"]",
                                             "kubesphere.io/creator": "admin"}
                             },
                "rules": []}
        r = requests.post(url, headers=get_header(), data=json.dumps(data))
        print(r.text)

    @allure.title('在project工程中创建角色-名称以分隔符("-")结尾')
    @allure.severity(allure.severity_level.CRITICAL)
    def wx_test_project_role_create_name3(self):
        project_role_name = 'wx-'
        url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + self.project_name + '/roles'
        data = {"apiVersion": "rbac.authorization.k8s.io/v1",
                "kind": "Role",
                "metadata": {"namespace": self.project_name,
                             "name": project_role_name,
                             "annotations": {"iam.kubesphere.io/aggregation-roles": "[\"role-template-view-basic\"]",
                                             "kubesphere.io/creator": "admin"}
                             },
                "rules": []}
        r = requests.post(url, headers=get_header(), data=json.dumps(data))
        print(r.text)

    @allure.story('应用负载-任务')
    @allure.title('创建任务，并验证运行正常')
    @allure.description('创建一个计算圆周率的任务')
    @allure.severity(allure.severity_level.BLOCKER)
    def test_create_job(self):
        step_create_job(self.project_name, self.job_name)  # 创建任务
        uid = step_get_job_status(self.project_name, self.job_name)  # 验证任务的运行状态为完成,并获取uid
        pod_name = step_get_job_pods(self.project_name, uid)  # 查看任务的资源状态，并获取容器组名称
        step_get_pods_log(self.project_name, pod_name, self.job_name)  # 查看任务的第一个容器的运行日志，并验证任务的运行结果

    @allure.story('应用负载-任务')
    @allure.title('按名称模糊查询存在的任务')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_query_job(self):
        fuzzy_name = 'demo'
        result = step_get_assign_job(self.project_name, 'name', fuzzy_name)  # 模糊查询存在的任务
        assert result == 1

    @allure.story('应用负载-任务')
    @allure.title('按状态查询已完成的任务')
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_job_status_completed(self):
        # 查询状态为已完成的任务，依赖于用例'创建任务，并验证运行正常'创建的任务
        result = step_get_assign_job(self.project_name, 'status', 'completed')
        # 验证查询结果为1
        assert result == 1

    @allure.story('应用负载-任务')
    @allure.title('按状态查询运行中的任务')
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_job_status_running(self):
        job_name = 'test-job1'
        # 创建任务
        step_create_job(self.project_name, job_name)
        # 验证任务状态为运行中
        step_get_job_status_run(self.project_name, job_name)
        # 按状态为运行中查询任务
        result = step_get_assign_job(self.project_name, 'status', 'running')
        # 验证查询结果为1
        assert result == 1

    @allure.story('应用负载-容器组')
    @allure.title('按名称精确查询存在的容器组')
    @allure.severity(allure.severity_level.NORMAL)
    def test_precise_query_pod(self):
        # 获取容器组名称，使用用例'创建任务，并验证运行正常'，创建的容器组
        uid = step_get_job_status(self.project_name, self.job_name)  # 验证任务的运行状态为完成,并获取uid
        pod_name = step_get_job_pods(self.project_name, uid)  # 查看任务的资源状态，并获取容器组名称
        url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + self.project_name + '/pods?' \
                                                                                                       'name=' + pod_name + '&sortBy=startTime&limit=10'

        r = requests.get(url=url, headers=get_header())
        # 验证查询到的容器名称
        print("actual_result:r.json()['items'][0]['metadata']['name'] = " + r.json()['items'][0]['metadata']['name'])
        print("expect_result:" + pod_name)
        assert r.json()['items'][0]['metadata']['name'] == pod_name

    @allure.story('应用负载-容器组')
    @allure.title('按名称模糊查询存在的容器组')
    @allure.severity(allure.severity_level.NORMAL)
    # 在用例'创建任务，并验证运行正常'中创建的是一个有4个容器组的任务
    def test_fuzzy_query_pod(self):
        pod_name = self.job_name
        url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + self.project_name + '/pods?' \
                                                                                                       'name=' + pod_name + '&sortBy=startTime&limit=10'
        r = requests.get(url=url, headers=get_header())
        # 验证查询到的容器名称
        print("actual_result:r.json()['totalItems'] = " + str(r.json()['totalItems']))
        print("expect_result:" + str(4))
        assert r.json()['totalItems'] == 4

    @allure.story('应用负载-容器组')
    @allure.title('按名称查询不存在的容器组')
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_no_pod(self):
        pod_name = 'test123'  # 不存在的容器组名称
        url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + self.project_name + '/pods?' \
                                                                                                       'name=' + pod_name + '&sortBy=startTime&limit=10'
        r = requests.get(url=url, headers=get_header())
        # 验证查询到的容器名称
        print("actual_result:r.json()['totalItems'] = " + str(r.json()['totalItems']))
        print("expect_result:" + str(0))
        assert r.json()['totalItems'] == 0

    @allure.story('应用负载-容器组')
    @allure.title('查看容器组详情')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_check_pod(self):
        uid = step_get_job_status(self.project_name, self.job_name)  # 验证任务的运行状态为完成,并获取uid
        pod_name = step_get_job_pods(self.project_name, uid)  # 查看任务的资源状态，并获取容器组名称
        url = config.url + '/api/v1/namespaces/' + self.project_name + '/pods/' + pod_name
        r = requests.get(url=url, headers=get_header())
        # 验证查询结果
        print("actual_result:r.json()['status']['phase'] = " + r.json()['status']['phase'])
        print("expect_result: Succeeded")
        assert r.json()['status']['phase'] == 'Succeeded'

    @allure.story('应用负载-容器组')
    @allure.title('删除状态为已完成的容器组')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_pod(self):
        uid = step_get_job_status(self.project_name, self.job_name)  # 验证任务的运行状态为完成,并获取uid
        pod_name = step_get_job_pods(self.project_name, uid)  # 查看任务的资源状态，并获取容器组名称
        url = config.url + '/api/v1/namespaces/' + self.project_name + '/pods/' + pod_name

        r = requests.delete(url=url, headers=get_header())
        # 验证删除操作成功
        print("actual_result:r.json()['status']['phase'] = " + r.json()['status']['phase'])
        print("expect_result: Succeeded")
        assert r.json()['status']['phase'] == 'Succeeded'

    @allure.story('应用负载-容器组')
    @allure.title('删除不存在的容器组')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_pod_no(self):
        pod_name = 'pod-test'
        url = config.url + '/api/v1/namespaces/' + self.project_name + '/pods/' + pod_name
        r = requests.delete(url=url, headers=get_header())
        # 验证删除失败
        print("actual_result:r.json()['status'] = " + r.json()['status'])
        print("expect_result: Failure")
        assert r.json()['status'] == 'Failure'

    @allure.story('应用负载-任务')
    @allure.title('删除状态为运行中的任务')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_running_job(self):
        job_name = 'test-job-demo'
        step_create_job(self.project_name, job_name)  # 创建任务
        step_get_job_status_run(self.project_name, job_name)  # 验证任务状态为运行中
        # 删除任务
        result = step_delete_job(self.project_name, job_name)
        # 验证删除结果为Success
        assert result == 'Success'
        # 在列表中查询任务，验证查询结果为空
        result1 = step_get_assign_job(self.project_name, 'name', job_name)
        assert result1 == 0

    @allure.story('应用负载-任务')
    @allure.title('删除状态为已完成的任务')
    @allure.severity(allure.severity_level.CRITICAL)
    # 删除用例'创建任务，并验证运行正常'创建的任务
    def test_delete_job(self):
        result = step_delete_job(self.project_name, self.job_name)
        # 验证删除结果为Success
        assert result == 'Success'
        # 在列表中查询任务，验证查询结果为空
        result1 = step_get_assign_job(self.project_name, 'name', self.job_name)
        assert result1 == 0

    @allure.story('应用负载-任务')
    @allure.title('删除不存在的任务')
    @allure.severity(allure.severity_level.NORMAL)
    # 删除用例'创建任务，并验证运行正常'创建的任务
    def test_delete_job_no(self):
        job_name = 'test123'
        result = step_delete_job(self.project_name, job_name)
        # 验证删除结果
        print("actual_result: " + result)
        print("expect_result: Failure")
        assert result == 'Failure'

    @allure.story('应用负载-工作负载')
    @allure.title('创建未绑定存储卷的deployment，并验证运行成功')
    @allure.severity(allure.severity_level.BLOCKER)
    def test_create_workload(self):
        workload_name = 'workload2'  # 工作负载名称
        container_name = 'container-nginx'  # 容器名称
        image = 'nginx'  # 镜像名称
        condition = 'name=' + workload_name  # 查询条件
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 81}]  # 容器的端口信息
        volumeMounts = []  # 设置挂载哦的存储卷
        strategy_info = {"type": "RollingUpdate", "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
        replicas = 2  # 副本数
        volume_info = []
        # 创建工作负载
        step_create_deploy(project_name=self.project_name, work_name=workload_name,
                           container_name=container_name, ports=port, volumemount=volumeMounts,
                           image=image, replicas=replicas, volume_info=volume_info,
                           strategy=strategy_info)

        # 在工作负载列表中查询创建的工作负载，并验证其状态为运行中，最长等待时间60s
        i = 0
        while i < 60:
            response = step_get_workload(project_name=self.project_name, type='deployments', condition=condition)
            status = response.json()['items'][0]['status']
            # 验证资源的所有副本已就绪
            if 'unavailableReplicas' not in status:
                print('创建工作负载耗时:' + str(i) + 's')
                break
            time.sleep(1)
            i = i + 1
        assert 'unavailableReplicas' not in status

    @allure.story('应用负载-工作负载')
    @allure.title('按状态查询存在的deployment')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_deployment_by_status(self):
        workload_name = 'workload' + str(commonFunction.get_random())  # 工作负载名称
        condition = 'status=running'
        container_name = 'container-nginx'  # 容器名称
        image = 'nginx'  # 镜像名称
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 81}]  # 容器的端口信息
        volumeMounts = []  # 设置挂载的存储卷
        strategy_info = {"type": "RollingUpdate", "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
        replicas = 1  # 副本数
        volume_info = []
        # 创建工作负载
        step_create_deploy(project_name=self.project_name, work_name=workload_name,
                           container_name=container_name, ports=port, volumemount=volumeMounts,
                           image=image, replicas=replicas, volume_info=volume_info,
                           strategy=strategy_info)
        # 按名称精确查询deployment
        time.sleep(3)
        response = step_get_workload(self.project_name, type='deployments', condition=condition)
        # 获取并验证deployment的名称正确
        name = response.json()['items'][0]['metadata']['name']
        assert name == workload_name
        # 删除deployment
        re = step_delete_workload(project_name=self.project_name, type='deployments', work_name=workload_name)
        assert re.json()['status'] == 'Success'

    @allure.story('应用负载-工作负载')
    @allure.title('按名称查询存在的deployment')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_deployment_by_name(self):
        workload_name = 'workload' + str(commonFunction.get_random())  # 工作负载名称
        conndition = 'name=' + workload_name  # 查询条件
        container_name = 'container-nginx'  # 容器名称
        image = 'nginx'  # 镜像名称
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 81}]  # 容器的端口信息
        volumeMounts = []  # 设置挂载哦的存储卷
        strategy_info = {"type": "RollingUpdate", "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
        replicas = 2  # 副本数
        volume_info = []
        # 创建工作负载
        step_create_deploy(project_name=self.project_name, work_name=workload_name,
                           container_name=container_name, ports=port, volumemount=volumeMounts,
                           image=image, replicas=replicas, volume_info=volume_info,
                           strategy=strategy_info)
        # 按名称精确查询deployment
        time.sleep(3)
        response = step_get_workload(self.project_name, type='deployments', condition=conndition)
        # 获取并验证deployment的名称正确
        name = response.json()['items'][0]['metadata']['name']
        assert name == workload_name
        # 删除deployment
        re = step_delete_workload(project_name=self.project_name, type='deployments', work_name=workload_name)
        assert re.json()['status'] == 'Success'

    @allure.story('应用负载-工作负载')
    @allure.title('创建未绑定存储卷的StatefulSets，并验证运行成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_statefulsets(self):
        workload_name = 'workload3'  # 工作负载名称
        container_name = 'container-nginx'  # 容器名称
        image = 'nginx'  # 镜像名称
        replicas = 2  # 副本数
        condition = 'name=' + workload_name  # 查询条件
        volume_info = []
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]
        service_port = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]
        service_name = 'service' + workload_name
        volumemounts = []
        # 创建工作负载
        step_create_stateful(project_name=self.project_name, work_name=workload_name,
                             container_name=container_name,
                             image=image, replicas=replicas, volume_info=volume_info, ports=port,
                             service_ports=service_port, volumemount=volumemounts, service_name=service_name)

        # 在工作负载列表中查询创建的工作负载，并验证其状态为运行中，最长等待时间60s
        time.sleep(3)
        i = 3
        while i < 60:
            response = step_get_workload(project_name=self.project_name, type='statefulsets', condition=condition)
            readyReplicas = response.json()['items'][0]['status']['readyReplicas']
            # 验证资源的所有副本已就绪
            if readyReplicas == replicas:
                print('创建工作负载耗时:' + str(i) + 's')
                break
            time.sleep(1)
            i = i + 1
        assert readyReplicas == replicas

    @allure.story('应用负载-工作负载')
    @allure.title('按名称查询存在的StatefulSets')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_statefulstes_by_name(self):
        workload_name = 'workload' + str(commonFunction.get_random())  # 工作负载名称
        condition = 'name=' + workload_name
        type = 'statefulsets'
        container_name = 'container-nginx'  # 容器名称
        image = 'nginx'  # 镜像名称
        replicas = 2  # 副本数
        volume_info = []
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]
        service_port = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]
        service_name = 'service' + workload_name
        volumemounts = []
        # 创建工作负载
        step_create_stateful(project_name=self.project_name, work_name=workload_name,
                             container_name=container_name,
                             image=image, replicas=replicas, volume_info=volume_info, ports=port,
                             service_ports=service_port, volumemount=volumemounts, service_name=service_name)

        # 按名称精确查询statefulsets
        time.sleep(1)
        response = step_get_workload(self.project_name, type=type, condition=condition)
        # 获取并验证deployment的名称正确
        name = response.json()['items'][0]['metadata']['name']
        assert name == workload_name
        # 删除创建的statefulsets
        re = step_delete_workload(project_name=self.project_name, type=type, work_name=workload_name)
        assert re.json()['status'] == 'Success'

    @allure.story('应用负载-工作负载')
    @allure.title('按状态查询存在的StatefulSets')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_statefulstes_by_status(self):
        workload_name = 'workload' + str(commonFunction.get_random())  # 工作负载名称
        condition = 'status=running'
        type = 'statefulsets'
        container_name = 'container-nginx'  # 容器名称
        image = 'nginx'  # 镜像名称
        replicas = 2  # 副本数
        volume_info = []
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]
        service_port = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]
        service_name = 'service' + workload_name
        volumemounts = []
        # 创建工作负载
        step_create_stateful(project_name=self.project_name, work_name=workload_name,
                             container_name=container_name,
                             image=image, replicas=replicas, volume_info=volume_info, ports=port,
                             service_ports=service_port, volumemount=volumemounts, service_name=service_name)

        # 按状态精确查询statefulsets
        time.sleep(5)
        response = step_get_workload(self.project_name, type=type, condition=condition)
        # 获取并验证deployment的名称正确
        name = response.json()['items'][0]['metadata']['name']
        assert name == workload_name
        # 删除创建的statefulsets
        re = step_delete_workload(project_name=self.project_name, type=type, work_name=workload_name)
        assert re.json()['status'] == 'Success'

    @allure.story('应用负载-工作负载')
    @allure.title('创建未绑定存储卷的DaemonSets，并验证运行成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_daemonsets(self):
        workload_name = 'workload4'  # 工作负载名称
        container_name = 'container-nginx'  # 容器名称
        image = 'nginx'  # 镜像名称
        condition = 'name=' + workload_name  # 查询条件
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80}]  # 容器的端口信息
        volume_info = []
        volumemount = []
        # 创建工作负载
        step_create_daemonset(project_name=self.project_name, work_name=workload_name,
                              container_name=container_name, image=image, ports=port,
                              volume_info=volume_info, volumemount=volumemount)
        # 在工作负载列表中查询创建的工作负载，并验证其状态为运行中，最长等待时间60s
        time.sleep(3)
        i = 3
        while i < 60:
            response = step_get_workload(project_name=self.project_name, type='daemonsets', condition=condition)
            numberReady = response.json()['items'][0]['status']['numberReady']  # 验证资源的所有副本已就绪
            # 验证资源的所有副本已就绪
            if numberReady == 1:
                print('创建工作负载耗时:' + str(i) + 's')
                break
            time.sleep(1)
            i = i + 1
        assert numberReady == 1

    @allure.story('应用负载-工作负载')
    @allure.title('按名称查询存在的DaemonSets')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_daemonsets_by_name(self):
        workload_name = 'workload' + str(commonFunction.get_random())  # 工作负载名称
        container_name = 'container-nginx'  # 容器名称
        condition = 'name=' + workload_name
        image = 'nginx'  # 镜像名称
        type = 'daemonsets'
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80}]  # 容器的端口信息
        volume_info = []
        volumemount = []
        # 创建工作负载
        step_create_daemonset(project_name=self.project_name, work_name=workload_name,
                              container_name=container_name, image=image, ports=port,
                              volume_info=volume_info, volumemount=volumemount)
        # 按名称查询DaemonSets
        time.sleep(3)
        response = step_get_workload(self.project_name, type=type, condition=condition)
        # 获取并验证deployment的名称正确
        name = response.json()['items'][0]['metadata']['name']
        # 删除创建的daemonsets
        re = step_delete_workload(project_name=self.project_name, type=type, work_name=workload_name)
        assert re.json()['status'] == 'Success'

    @allure.story('应用负载-工作负载')
    @allure.title('按状态查询存在的DaemonSets')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_daemonsets_by_name(self):
        workload_name = 'workload' + str(commonFunction.get_random())  # 工作负载名称
        container_name = 'container-nginx'  # 容器名称
        condition = 'status=running'
        image = 'nginx'  # 镜像名称
        type = 'daemonsets'
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80}]  # 容器的端口信息
        volume_info = []
        volumemount = []
        # 创建工作负载
        step_create_daemonset(project_name=self.project_name, work_name=workload_name,
                              container_name=container_name, image=image, ports=port,
                              volume_info=volume_info, volumemount=volumemount)
        # 按名称查询DaemonSets
        time.sleep(3)
        response = step_get_workload(self.project_name, type=type, condition=condition)
        # 获取并验证deployment的名称正确
        name = response.json()['items'][0]['metadata']['name']
        # 删除创建的daemonsets
        re = step_delete_workload(project_name=self.project_name, type=type, work_name=workload_name)
        assert re.json()['status'] == 'Success'

    @allure.story('应用负载-服务')
    @allure.title('创建未绑定存储卷的service，并验证运行成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_service(self):
        service_name = 'service' + str(commonFunction.get_random())
        port_service = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]  # service的端口信息
        image = 'nginx'  # 镜像名称
        container_name = 'container-nginx'  # 容器名称
        condition = 'name=' + service_name  # 查询deploy和service条件
        port_deploy = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]  # 容器的端口信息
        volumeMounts = []  # 设置挂载的存储卷
        strategy_info = {"type": "RollingUpdate", "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
        replicas = 2  # 副本数
        volume_info = []
        # 创建service
        step_create_service(self.project_name, service_name, port_service)
        # 创建service绑定的deployment
        step_create_deploy(project_name=self.project_name, work_name=service_name, container_name=container_name,
                           ports=port_deploy, volumemount=volumeMounts, image=image, replicas=replicas,
                           volume_info=volume_info, strategy=strategy_info)
        # 验证service创建成功
        response = step_get_workload(self.project_name, type='services', condition=condition)
        name = response.json()['items'][0]['metadata']['name']
        assert name == service_name
        # 验证deploy创建成功
        time.sleep(3)
        re = step_get_workload(self.project_name, type='deployments', condition=condition)
        # 获取并验证deployment的名称正确
        name = re.json()['items'][0]['metadata']['name']
        assert name == service_name

    @allure.story('应用负载-服务')
    @allure.title('删除service，并验证删除成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_service(self):
        service_name = 'service' + str(commonFunction.get_random())
        port_service = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]  # service的端口信息
        condition = 'name=' + service_name  # 查询service的条件
        # 创建service
        step_create_service(self.project_name, service_name, port_service)
        # 验证service创建成功
        response = step_get_workload(self.project_name, type='services', condition=condition)
        name = response.json()['items'][0]['metadata']['name']
        assert name == service_name
        # 删除service
        step_delete_service(self.project_name, service_name)
        # 验证service删除成功
        response = step_get_workload(self.project_name, type='services', condition=condition)
        count = response.json()['totalItems']
        assert count == 0

    @allure.story('应用负载-应用路由')
    @allure.title('为服务创建应有路由')
    def test_create_route(self):
        # 创建服务
        service_name = 'service' + str(commonFunction.get_random())  # 服务名称
        port_service = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]  # service的端口信息
        image = 'nginx'  # 镜像名称
        container_name = 'container-nginx'  # 容器名称
        condition = 'name=' + service_name  # 查询deploy和service条件
        port_deploy = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]  # 容器的端口信息
        volumeMounts = []  # 设置挂载的存储卷
        strategy_info = {"type": "RollingUpdate", "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
        replicas = 2  # 副本数
        volume_info = []
        # 创建service
        step_create_service(self.project_name, service_name, port_service)
        # 创建service绑定的deployment
        step_create_deploy(project_name=self.project_name, work_name=service_name, container_name=container_name,
                           ports=port_deploy, volumemount=volumeMounts, image=image, replicas=replicas,
                           volume_info=volume_info, strategy=strategy_info)
        # 验证service创建成功
        response = step_get_workload(self.project_name, type='services', condition=condition)
        name = response.json()['items'][0]['metadata']['name']
        assert name == service_name
        # 验证deploy创建成功
        time.sleep(3)
        re = step_get_workload(self.project_name, type='deployments', condition=condition)
        # 获取并验证deployment的名称正确
        name = re.json()['items'][0]['metadata']['name']
        assert name == service_name
        # 为服务创建路由
        ingress_name = 'ingress' + str(commonFunction.get_random())
        host = 'www.test.com'
        service_info = {"serviceName": service_name, "servicePort": 80}
        response = step_create_route(project_name=self.project_name, ingress_name=ingress_name, host=host,
                                     service_info=service_info)
        # 获取路由绑定的服务名称
        name = response.json()['spec']['rules'][0]['http']['paths'][0]['backend']['serviceName']
        # 验证路由创建成功
        assert name == service_name

    @allure.story('应用负载-任务')
    @allure.title('部署示例应用')
    @allure.severity(allure.severity_level.CRITICAL)
    def wx_test_deployment_test_apo(self):
        """
        应用组件：productpage、reviews、details、ratings

        """
        url1 = config.url + '/apis/app.k8s.io/v1beta1/namespaces/' + self.project_name + '/applications?dryRun=All'
        data1 = {"apiVersion": "app.k8s.io/v1beta1",
                 "kind": "Application",
                 "metadata": {"name": "bookinfo", "namespace": "wx",
                              "labels": {"app.kubernetes.io/version": "v1", "app.kubernetes.io/name": "bookinfo"},
                              "annotations": {"servicemesh.kubesphere.io/enabled": "false",
                                              "kubesphere.io/creator": "admin"}},
                 "spec": {"selector": {
                     "matchLabels": {"app.kubernetes.io/version": "v1", "app.kubernetes.io/name": "bookinfo"}},
                     "addOwnerRef": "true", "descriptor": {"icons": [{"src": "/assets/bookinfo.svg"}]},
                     "componentKinds": [{"group": "", "kind": "Service"},
                                        {"group": "apps", "kind": "Deployment"},
                                        {"group": "apps", "kind": "StatefulSet"},
                                        {"group": "extensions", "kind": "Ingress"},
                                        {"group": "servicemesh.kubesphere.io", "kind": "Strategy"},
                                        {"group": "servicemesh.kubesphere.io", "kind": "ServicePolicy"}]}}

        url2 = config.url + '/apis/extensions/v1beta1/namespaces/' + self.project_name + '/ingresses?dryRun=All'
        data2 = {"apiVersion": "extensions/v1beta1", "kind": "Ingress",
                 "metadata": {"namespace": "wx",
                              "labels": {"app.kubernetes.io/version": "v1", "app.kubernetes.io/name": "bookinfo"},
                              "name": "bookinfo-ingress",
                              "annotations": {
                                  "nginx.ingress.kubernetes.io/upstream-vhost": "productpage.wx.svc.cluster.local",
                                  "kubesphere.io/creator": "admin"}},
                 "spec": {"rules": [{"http": {
                     "paths": [{"path": "/", "backend": {"serviceName": "productpage", "servicePort": 9080}}]},
                     "host": "productpage.wx.192.168.0.5.nip.io"}]}}

        url3 = config.urlc + '/apis/apps/v1/namespaces/' + self.project_name + '/deployments?dryRun=All'
        data3 = {"apiVersion": "apps/v1", "kind": "Deployment", "metadata": {"namespace": "wx", "annotations": {
            "kubesphere.io/isElasticReplicas": "false", "kubesphere.io/creator": "admin"},
                                                                             "labels": {"app": "productpage",
                                                                                        "version": "v1",
                                                                                        "app.kubernetes.io/version": "v1",
                                                                                        "app.kubernetes.io/name": "bookinfo"},
                                                                             "name": "productpage-v1"},
                 "spec": {"replicas": 1, "selector": {
                     "matchLabels": {"app": "productpage", "version": "v1", "app.kubernetes.io/version": "v1",
                                     "app.kubernetes.io/name": "bookinfo"}}, "template": {"metadata": {
                     "labels": {"app": "productpage", "version": "v1", "app.kubernetes.io/version": "v1",
                                "app.kubernetes.io/name": "bookinfo"},
                     "annotations": {"sidecar.istio.io/inject": "true"}}, "spec": {"containers": [
                     {"name": "productpage", "resources": {"requests": {"cpu": "10m", "memory": "10Mi"},
                                                           "limits": {"cpu": "1", "memory": "1000Mi"}},
                      "imagePullPolicy": "IfNotPresent", "image": "kubesphere/examples-bookinfo-productpage-v1:1.13.0",
                      "ports": [{"name": "http-web", "protocol": "TCP", "containerPort": 9080, "servicePort": 9080}]}],
                     "serviceAccount": "default"}},
                          "strategy": {"type": "RollingUpdate",
                                       "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}}}

        url4 = config.url + '/api/v1/namespaces/' + self.project_name + '/services?dryRun=All'
        data4 = {"apiVersion": "v1", "kind": "Service", "metadata": {"namespace": "wx", "labels": {"app": "productpage",
                                                                                                   "app.kubernetes.io/version": "v1",
                                                                                                   "app.kubernetes.io/name": "bookinfo"},
                                                                     "annotations": {
                                                                         "kubesphere.io/workloadType": "Deployment",
                                                                         "kubesphere.io/creator": "admin"},
                                                                     "name": "productpage"},
                 "spec": {"type": "ClusterIP", "sessionAffinity": "None",
                          "selector": {"app": "productpage", "app.kubernetes.io/version": "v1",
                                       "app.kubernetes.io/name": "bookinfo"},
                          "ports": [{"name": "http-web", "protocol": "TCP", "port": 9080, "targetPort": 9080}]}}

        url5 = config.url + '/apis/apps/v1/namespaces/' + self.project_name + '/deployments?dryRun=All'
        data5 = {"apiVersion": "apps/v1", "kind": "Deployment", "metadata": {"namespace": "wx", "annotations": {
            "kubesphere.io/isElasticReplicas": "false", "kubesphere.io/creator": "admin"}, "labels": {"app": "reviews",
                                                                                                      "version": "v1",
                                                                                                      "app.kubernetes.io/version": "v1",
                                                                                                      "app.kubernetes.io/name": "bookinfo"},
                                                                             "name": "reviews-v1"},
                 "spec": {"replicas": 1, "selector": {
                     "matchLabels": {"app": "reviews", "version": "v1", "app.kubernetes.io/version": "v1",
                                     "app.kubernetes.io/name": "bookinfo"}}, "template": {"metadata": {
                     "labels": {"app": "reviews", "version": "v1", "app.kubernetes.io/version": "v1",
                                "app.kubernetes.io/name": "bookinfo"},
                     "annotations": {"sidecar.istio.io/inject": "true"}}, "spec": {"containers": [{"name": "reviews",
                                                                                                   "resources": {
                                                                                                       "requests": {
                                                                                                           "cpu": "10m",
                                                                                                           "memory": "10Mi"},
                                                                                                       "limits": {
                                                                                                           "cpu": "1",
                                                                                                           "memory": "1000Mi"}},
                                                                                                   "imagePullPolicy": "IfNotPresent",
                                                                                                   "image": "kubesphere/examples-bookinfo-reviews-v1:1.13.0",
                                                                                                   "ports": [{
                                                                                                       "name": "http-web",
                                                                                                       "protocol": "TCP",
                                                                                                       "containerPort": 9080,
                                                                                                       "servicePort": 9080}]}],
                                                                                   "serviceAccount": "default"}},
                          "strategy": {"type": "RollingUpdate",
                                       "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}}}

        url6 = config.url + '/api/v1/namespaces/' + self.project_name + '/services?dryRun=All'
        data6 = {"apiVersion": "v1", "kind": "Service", "metadata": {"namespace": "wx", "labels": {"app": "reviews",
                                                                                                   "app.kubernetes.io/version": "v1",
                                                                                                   "app.kubernetes.io/name": "bookinfo"},
                                                                     "annotations": {
                                                                         "kubesphere.io/workloadType": "Deployment",
                                                                         "kubesphere.io/creator": "admin"},
                                                                     "name": "reviews"},
                 "spec": {"type": "ClusterIP", "sessionAffinity": "None",
                          "selector": {"app": "reviews", "app.kubernetes.io/version": "v1",
                                       "app.kubernetes.io/name": "bookinfo"},
                          "ports": [{"name": "http-web", "protocol": "TCP", "port": 9080, "targetPort": 9080}]}}

        url7 = config.url + '/apis/apps/v1/namespaces/' + self.project_name + '/deployments?dryRun=All'
        data7 = {"apiVersion": "apps/v1", "kind": "Deployment", "metadata": {"namespace": "wx", "annotations": {
            "kubesphere.io/isElasticReplicas": "false", "kubesphere.io/creator": "admin"}, "labels": {"app": "details",
                                                                                                      "version": "v1",
                                                                                                      "app.kubernetes.io/version": "v1",
                                                                                                      "app.kubernetes.io/name": "bookinfo"},
                                                                             "name": "details-v1"},
                 "spec": {"replicas": 1, "selector": {
                     "matchLabels": {"app": "details", "version": "v1", "app.kubernetes.io/version": "v1",
                                     "app.kubernetes.io/name": "bookinfo"}}, "template": {"metadata": {
                     "labels": {"app": "details", "version": "v1", "app.kubernetes.io/version": "v1",
                                "app.kubernetes.io/name": "bookinfo"},
                     "annotations": {"sidecar.istio.io/inject": "true"}}, "spec": {"containers": [{"name": "details",
                                                                                                   "resources": {
                                                                                                       "requests": {
                                                                                                           "cpu": "10m",
                                                                                                           "memory": "10Mi"},
                                                                                                       "limits": {
                                                                                                           "cpu": "1",
                                                                                                           "memory": "1000Mi"}},
                                                                                                   "imagePullPolicy": "IfNotPresent",
                                                                                                   "image": "kubesphere/examples-bookinfo-details-v1:1.13.0",
                                                                                                   "ports": [{
                                                                                                       "name": "http-web",
                                                                                                       "protocol": "TCP",
                                                                                                       "containerPort": 9080,
                                                                                                       "servicePort": 9080}]}],
                                                                                   "serviceAccount": "default"}},
                          "strategy": {"type": "RollingUpdate",
                                       "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}}}

        url8 = config.url + '/api/v1/namespaces/' + self.project_name + '/services?dryRun=All'
        data8 = {"apiVersion": "v1", "kind": "Service", "metadata": {"namespace": "wx", "labels": {"app": "details",
                                                                                                   "app.kubernetes.io/version": "v1",
                                                                                                   "app.kubernetes.io/name": "bookinfo"},
                                                                     "annotations": {
                                                                         "kubesphere.io/workloadType": "Deployment",
                                                                         "kubesphere.io/creator": "admin"},
                                                                     "name": "details"},
                 "spec": {"type": "ClusterIP", "sessionAffinity": "None",
                          "selector": {"app": "details", "app.kubernetes.io/version": "v1",
                                       "app.kubernetes.io/name": "bookinfo"},
                          "ports": [{"name": "http-web", "protocol": "TCP", "port": 9080, "targetPort": 9080}]}}

        url9 = config.url + '/apis/apps/v1/namespaces/' + self.project_name + '/deployments?dryRun=All'
        data9 = {"apiVersion": "apps/v1", "kind": "Deployment", "metadata": {"namespace": "wx", "annotations": {
            "kubesphere.io/isElasticReplicas": "false", "kubesphere.io/creator": "admin"}, "labels": {"app": "ratings",
                                                                                                      "version": "v1",
                                                                                                      "app.kubernetes.io/version": "v1",
                                                                                                      "app.kubernetes.io/name": "bookinfo"},
                                                                             "name": "ratings-v1"},
                 "spec": {"replicas": 1, "selector": {
                     "matchLabels": {"app": "ratings", "version": "v1", "app.kubernetes.io/version": "v1",
                                     "app.kubernetes.io/name": "bookinfo"}}, "template": {"metadata": {
                     "labels": {"app": "ratings", "version": "v1", "app.kubernetes.io/version": "v1",
                                "app.kubernetes.io/name": "bookinfo"},
                     "annotations": {"sidecar.istio.io/inject": "true"}}, "spec": {"containers": [{"name": "ratings",
                                                                                                   "resources": {
                                                                                                       "requests": {
                                                                                                           "cpu": "10m",
                                                                                                           "memory": "10Mi"},
                                                                                                       "limits": {
                                                                                                           "cpu": "1",
                                                                                                           "memory": "1000Mi"}},
                                                                                                   "imagePullPolicy": "IfNotPresent",
                                                                                                   "image": "kubesphere/examples-bookinfo-ratings-v1:1.13.0",
                                                                                                   "ports": [{
                                                                                                       "name": "http-web",
                                                                                                       "protocol": "TCP",
                                                                                                       "containerPort": 9080,
                                                                                                       "servicePort": 9080}]}],
                                                                                   "serviceAccount": "default"}},
                          "strategy": {"type": "RollingUpdate",
                                       "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}}}

        url10 = config.url + '/api/v1/namespaces/' + self.project_name + '/services?dryRun=All'
        data10 = {"apiVersion": "v1", "kind": "Service", "metadata": {"namespace": "wx", "labels": {"app": "ratings",
                                                                                                    "app.kubernetes.io/version": "v1",
                                                                                                    "app.kubernetes.io/name": "bookinfo"},
                                                                      "annotations": {
                                                                          "kubesphere.io/workloadType": "Deployment",
                                                                          "kubesphere.io/creator": "admin"},
                                                                      "name": "ratings"},
                  "spec": {"type": "ClusterIP", "sessionAffinity": "None",
                           "selector": {"app": "ratings", "app.kubernetes.io/version": "v1",
                                        "app.kubernetes.io/name": "bookinfo"},
                           "ports": [{"name": "http-web", "protocol": "TCP", "port": 9080, "targetPort": 9080}]}}

        url11 = config.url + '/apis/app.k8s.io/v1beta1/namespaces/' + self.project_name + '/applications'
        data11 = {"apiVersion": "app.k8s.io/v1beta1", "kind": "Application",
                  "metadata": {"name": "bookinfo", "namespace": "wx",
                               "labels": {"app.kubernetes.io/version": "v1", "app.kubernetes.io/name": "bookinfo"},
                               "annotations": {"servicemesh.kubesphere.io/enabled": "false",
                                               "kubesphere.io/creator": "admin"}}, "spec": {
                "selector": {"matchLabels": {"app.kubernetes.io/version": "v1", "app.kubernetes.io/name": "bookinfo"}},
                "addOwnerRef": "true", "descriptor": {"icons": [{"src": "/assets/bookinfo.svg"}]},
                "componentKinds": [{"group": "", "kind": "Service"}, {"group": "apps", "kind": "Deployment"},
                                   {"group": "apps", "kind": "StatefulSet"}, {"group": "extensions", "kind": "Ingress"},
                                   {"group": "servicemesh.kubesphere.io", "kind": "Strategy"},
                                   {"group": "servicemesh.kubesphere.io", "kind": "ServicePolicy"}]}}

        url12 = config.url + '/apis/extensions/v1beta1/namespaces/' + self.project_name + '/ingresses'
        data12 = {"apiVersion": "extensions/v1beta1", "kind": "Ingress", "metadata": {"namespace": "wx", "labels": {
            "app.kubernetes.io/version": "v1", "app.kubernetes.io/name": "bookinfo"}, "name": "bookinfo-ingress",
                                                                                      "annotations": {
                                                                                          "nginx.ingress.kubernetes.io/upstream-vhost": "productpage.wx.svc.cluster.local",
                                                                                          "kubesphere.io/creator": "admin"}},
                  "spec": {"rules": [{"http": {
                      "paths": [{"path": "/", "backend": {"serviceName": "productpage", "servicePort": 9080}}]},
                      "host": "productpage.wx.192.168.0.5.nip.io"}]}}

        url13 = config.url + '/apis/apps/v1/namespaces/' + self.project_name + '/deployments'
        data13 = {"apiVersion": "apps/v1", "kind": "Deployment", "metadata": {"namespace": "wx", "annotations": {
            "kubesphere.io/isElasticReplicas": "false", "kubesphere.io/creator": "admin"},
                                                                              "labels": {"app": "productpage",
                                                                                         "version": "v1",
                                                                                         "app.kubernetes.io/version": "v1",
                                                                                         "app.kubernetes.io/name": "bookinfo"},
                                                                              "name": "productpage-v1"},
                  "spec": {"replicas": 1, "selector": {
                      "matchLabels": {"app": "productpage", "version": "v1", "app.kubernetes.io/version": "v1",
                                      "app.kubernetes.io/name": "bookinfo"}}, "template": {"metadata": {
                      "labels": {"app": "productpage", "version": "v1", "app.kubernetes.io/version": "v1",
                                 "app.kubernetes.io/name": "bookinfo"},
                      "annotations": {"sidecar.istio.io/inject": "true"}}, "spec": {"containers": [
                      {"name": "productpage", "resources": {"requests": {"cpu": "10m", "memory": "10Mi"},
                                                            "limits": {"cpu": "1", "memory": "1000Mi"}},
                       "imagePullPolicy": "IfNotPresent", "image": "kubesphere/examples-bookinfo-productpage-v1:1.13.0",
                       "ports": [{"name": "http-web", "protocol": "TCP", "containerPort": 9080, "servicePort": 9080}]}],
                      "serviceAccount": "default"}},
                           "strategy": {"type": "RollingUpdate",
                                        "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}}}

        url14 = config.url + '/api/v1/namespaces/' + self.project_name + '/services'
        data14 = {"apiVersion": "v1", "kind": "Service", "metadata": {"namespace": "wx",
                                                                      "labels": {"app": "productpage",
                                                                                 "app.kubernetes.io/version": "v1",
                                                                                 "app.kubernetes.io/name": "bookinfo"},
                                                                      "annotations": {
                                                                          "kubesphere.io/workloadType": "Deployment",
                                                                          "kubesphere.io/creator": "admin"},
                                                                      "name": "productpage"},
                  "spec": {"type": "ClusterIP", "sessionAffinity": "None",
                           "selector": {"app": "productpage", "app.kubernetes.io/version": "v1",
                                        "app.kubernetes.io/name": "bookinfo"},
                           "ports": [{"name": "http-web", "protocol": "TCP", "port": 9080, "targetPort": 9080}]}}

        url15 = config.url + '/apis/apps/v1/namespaces/' + self.project_name + '/deployments'
        data15 = {"apiVersion": "apps/v1", "kind": "Deployment", "metadata": {"namespace": "wx", "annotations": {
            "kubesphere.io/isElasticReplicas": "false", "kubesphere.io/creator": "admin"}, "labels": {"app": "reviews",
                                                                                                      "version": "v1",
                                                                                                      "app.kubernetes.io/version": "v1",
                                                                                                      "app.kubernetes.io/name": "bookinfo"},
                                                                              "name": "reviews-v1"},
                  "spec": {"replicas": 1, "selector": {
                      "matchLabels": {"app": "reviews", "version": "v1", "app.kubernetes.io/version": "v1",
                                      "app.kubernetes.io/name": "bookinfo"}}, "template": {"metadata": {
                      "labels": {"app": "reviews", "version": "v1", "app.kubernetes.io/version": "v1",
                                 "app.kubernetes.io/name": "bookinfo"},
                      "annotations": {"sidecar.istio.io/inject": "true"}}, "spec": {"containers": [{"name": "reviews",
                                                                                                    "resources": {
                                                                                                        "requests": {
                                                                                                            "cpu": "10m",
                                                                                                            "memory": "10Mi"},
                                                                                                        "limits": {
                                                                                                            "cpu": "1",
                                                                                                            "memory": "1000Mi"}},
                                                                                                    "imagePullPolicy": "IfNotPresent",
                                                                                                    "image": "kubesphere/examples-bookinfo-reviews-v1:1.13.0",
                                                                                                    "ports": [{
                                                                                                        "name": "http-web",
                                                                                                        "protocol": "TCP",
                                                                                                        "containerPort": 9080,
                                                                                                        "servicePort": 9080}]}],
                                                                                    "serviceAccount": "default"}},
                           "strategy": {"type": "RollingUpdate",
                                        "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}}}

        url16 = config.url + '/api/v1/namespaces/' + self.project_name + '/services'
        data16 = {"apiVersion": "v1", "kind": "Service", "metadata": {"namespace": "wx", "labels": {"app": "reviews",
                                                                                                    "app.kubernetes.io/version": "v1",
                                                                                                    "app.kubernetes.io/name": "bookinfo"},
                                                                      "annotations": {
                                                                          "kubesphere.io/workloadType": "Deployment",
                                                                          "kubesphere.io/creator": "admin"},
                                                                      "name": "reviews"},
                  "spec": {"type": "ClusterIP", "sessionAffinity": "None",
                           "selector": {"app": "reviews", "app.kubernetes.io/version": "v1",
                                        "app.kubernetes.io/name": "bookinfo"},
                           "ports": [{"name": "http-web", "protocol": "TCP", "port": 9080, "targetPort": 9080}]}}

        url17 = config.url + '/apis/apps/v1/namespaces/' + self.project_name + '/deployments'
        data17 = {"apiVersion": "apps/v1", "kind": "Deployment", "metadata": {"namespace": "wx", "annotations": {
            "kubesphere.io/isElasticReplicas": "false", "kubesphere.io/creator": "admin"}, "labels": {"app": "details",
                                                                                                      "version": "v1",
                                                                                                      "app.kubernetes.io/version": "v1",
                                                                                                      "app.kubernetes.io/name": "bookinfo"},
                                                                              "name": "details-v1"},
                  "spec": {"replicas": 1, "selector": {
                      "matchLabels": {"app": "details", "version": "v1", "app.kubernetes.io/version": "v1",
                                      "app.kubernetes.io/name": "bookinfo"}}, "template": {"metadata": {
                      "labels": {"app": "details", "version": "v1", "app.kubernetes.io/version": "v1",
                                 "app.kubernetes.io/name": "bookinfo"},
                      "annotations": {"sidecar.istio.io/inject": "true"}}, "spec": {"containers": [{"name": "details",
                                                                                                    "resources": {
                                                                                                        "requests": {
                                                                                                            "cpu": "10m",
                                                                                                            "memory": "10Mi"},
                                                                                                        "limits": {
                                                                                                            "cpu": "1",
                                                                                                            "memory": "1000Mi"}},
                                                                                                    "imagePullPolicy": "IfNotPresent",
                                                                                                    "image": "kubesphere/examples-bookinfo-details-v1:1.13.0",
                                                                                                    "ports": [{
                                                                                                        "name": "http-web",
                                                                                                        "protocol": "TCP",
                                                                                                        "containerPort": 9080,
                                                                                                        "servicePort": 9080}]}],
                                                                                    "serviceAccount": "default"}},
                           "strategy": {"type": "RollingUpdate",
                                        "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}}}

        url18 = config.url + '/api/v1/namespaces/' + self.project_name + '/services'
        data18 = {"apiVersion": "v1", "kind": "Service", "metadata": {"namespace": "wx", "labels": {"app": "details",
                                                                                                    "app.kubernetes.io/version": "v1",
                                                                                                    "app.kubernetes.io/name": "bookinfo"},
                                                                      "annotations": {
                                                                          "kubesphere.io/workloadType": "Deployment",
                                                                          "kubesphere.io/creator": "admin"},
                                                                      "name": "details"},
                  "spec": {"type": "ClusterIP", "sessionAffinity": "None",
                           "selector": {"app": "details", "app.kubernetes.io/version": "v1",
                                        "app.kubernetes.io/name": "bookinfo"},
                           "ports": [{"name": "http-web", "protocol": "TCP", "port": 9080, "targetPort": 9080}]}}

        url19 = config.url + '/apis/apps/v1/namespaces/' + self.project_name + '/deployments'
        data20 = {"apiVersion": "apps/v1", "kind": "Deployment", "metadata": {"namespace": "wx", "annotations": {
            "kubesphere.io/isElasticReplicas": "false", "kubesphere.io/creator": "admin"}, "labels": {"app": "ratings",
                                                                                                      "version": "v1",
                                                                                                      "app.kubernetes.io/version": "v1",
                                                                                                      "app.kubernetes.io/name": "bookinfo"},
                                                                              "name": "ratings-v1"},
                  "spec": {"replicas": 1, "selector": {
                      "matchLabels": {"app": "ratings", "version": "v1", "app.kubernetes.io/version": "v1",
                                      "app.kubernetes.io/name": "bookinfo"}}, "template": {"metadata": {
                      "labels": {"app": "ratings", "version": "v1", "app.kubernetes.io/version": "v1",
                                 "app.kubernetes.io/name": "bookinfo"},
                      "annotations": {"sidecar.istio.io/inject": "true"}}, "spec": {"containers": [{"name": "ratings",
                                                                                                    "resources": {
                                                                                                        "requests": {
                                                                                                            "cpu": "10m",
                                                                                                            "memory": "10Mi"},
                                                                                                        "limits": {
                                                                                                            "cpu": "1",
                                                                                                            "memory": "1000Mi"}},
                                                                                                    "imagePullPolicy": "IfNotPresent",
                                                                                                    "image": "kubesphere/examples-bookinfo-ratings-v1:1.13.0",
                                                                                                    "ports": [{
                                                                                                        "name": "http-web",
                                                                                                        "protocol": "TCP",
                                                                                                        "containerPort": 9080,
                                                                                                        "servicePort": 9080}]}],
                                                                                    "serviceAccount": "default"}},
                           "strategy": {"type": "RollingUpdate",
                                        "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}}}

        url20 = config.url + '/api/v1/namespaces/' + self.project_name + '/services'
        data20 = {"apiVersion": "v1", "kind": "Service", "metadata": {"namespace": "wx", "labels": {"app": "ratings",
                                                                                                    "app.kubernetes.io/version": "v1",
                                                                                                    "app.kubernetes.io/name": "bookinfo"},
                                                                      "annotations": {
                                                                          "kubesphere.io/workloadType": "Deployment",
                                                                          "kubesphere.io/creator": "admin"},
                                                                      "name": "ratings"},
                  "spec": {"type": "ClusterIP", "sessionAffinity": "None",
                           "selector": {"app": "ratings", "app.kubernetes.io/version": "v1",
                                        "app.kubernetes.io/name": "bookinfo"},
                           "ports": [{"name": "http-web", "protocol": "TCP", "port": 9080, "targetPort": 9080}]}}

    @allure.story('应用负载-工作负载')
    @allure.title('修改工作负载副本并验证运行正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_add_work_replica(self):
        # 依赖于用例'创建工作负载，并验证运行成功'创建的工作负载
        replicas = 3  # 副本数
        # 修改副本数
        step_modify_work_replicas(project_name=self.project_name, work_name=self.work_name, replicas=replicas)
        # 获取工作负载中所有的容器组，并验证其运行正常，最长等待时间60s
        status_test = []  # 创建一个对比数组
        for j in range(replicas):
            status_test.append('Running')
        i = 0
        while i < 60:
            status = step_get_work_pod_status(project_name=self.project_name, work_name=self.work_name)
            if status == status_test:
                break
            else:
                time.sleep(5)
                i = i + 5
        assert status == status_test

    @allure.story('应用负载-工作负载')
    @allure.title('按状态查询存在的工作负载')
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_work_by_status(self):
        # 依赖于用例"创建工作负载，并验证运行成功"
        status = 'running'
        url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + self.project_name + '/deployments' \
                                                                                                       '?status=' + status + '&sortBy=updateTime&limit=10'
        r = requests.get(url=url, headers=get_header())
        assert r.json()['totalItems'] >= 1

    @allure.story('应用负载-工作负载')
    @allure.title('按名称精确查询存在的工作负载')
    @allure.severity(allure.severity_level.NORMAL)
    # 依赖于用例"创建存储卷，然后将存储卷绑定到新建的deployment上，最后验证资源和存储卷的状态正常"
    def test_query_work_by_name(self):
        url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + self.project_name + '/deployments' \
                                                                                                       '?name=' + self.work_name

        r = requests.get(url=url, headers=get_header())
        # 验证查询结果
        assert r.json()['items'][0]['metadata']['name'] == self.work_name

    @allure.story('应用负载-工作负载')
    @allure.title('按名称模糊查询存在的工作负载')
    @allure.severity(allure.severity_level.NORMAL)
    # 依赖于用例"创建存储卷，然后将存储卷绑定到新建的deployment上，最后验证资源和存储卷的状态正常"
    def test_fuzzy_query_work_by_name(self):
        name = 'demo'
        url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + self.project_name + '/deployments' \
                                                                                                       '?name=' + name
        r = requests.get(url=url, headers=get_header())
        # 验证查询结果
        assert r.json()['items'][0]['metadata']['name'] == self.work_name

    @allure.story('应用负载-工作负载')
    @allure.title('按名称查询不存在的工作负载')
    @allure.severity(allure.severity_level.NORMAL)
    # 依赖于用例"创建存储卷，然后将存储卷绑定到新建的deployment上，最后验证资源和存储卷的状态正常"
    def test_fuzzy_query_work_by_name(self):
        name = 'demo123'
        url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/namespaces/' + self.project_name + '/deployments' \
                                                                                                       '?name=' + name
        r = requests.get(url=url, headers=get_header())
        # 验证查询结果
        assert r.json()['totalItems'] == 0

    @allure.story('应用负载-工作负载')
    @allure.title('工作负载设置弹性伸缩')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_work_by_status(self):

        url = config.url + '/apis/autoscaling/v2beta2/namespaces/' + self.project_name + '/horizontalpodautoscalers'
        data = {"metadata": {"name": self.work_name, "namespace": self.project_name,
                             "annotations": {"cpuCurrentUtilization": "0", "cpuTargetUtilization": "50",
                                             "memoryCurrentValue": "0", "memoryTargetValue": "2Mi",
                                             "kubesphere.io/creator": "admin"}},
                "spec": {"scaleTargetRef": {"apiVersion": "apps/v1",
                                            "kind": "Deployment",
                                            "name": self.work_name}, "minReplicas": 1, "maxReplicas": 20,
                         "metrics": [{"type": "Resource",
                                      "resource": {"name": "memory",
                                                   "target": {"type": "AverageValue", "averageValue": "2Mi"}}},
                                     {"type": "Resource", "resource": {"name": "cpu", "target":
                                         {"type": "Utilization", "averageUtilization": 50}}}]},
                "apiVersion": "autoscaling/v2beta2", "kind": "HorizontalPodAutoscaler"}
        r = requests.post(url=url, headers=get_header(), data=json.dumps(data))
        # 验证设置成功
        assert r.json()['kind'] == 'HorizontalPodAutoscaler'

    @allure.story('应用负载-工作负载')
    @allure.title('删除工作负载')
    # 依赖于用例"创建存储卷，然后将存储卷绑定到新建的deployment上，最后验证资源和存储卷的状态正常"
    def test_delete_work(self):
        url = config.url + '/apis/apps/v1/namespaces/' + self.project_name + '/deployments/' + self.work_name
        data = {"kind": "DeleteOptions", "apiVersion": "v1", "propagationPolicy": "Background"}
        r = requests.delete(url=url, headers=get_header(), data=json.dumps(data))
        # 验证删除成功
        assert r.json()['status'] == 'Success'

    @allure.story('配置中心-服务账号')
    @allure.title('创建sa并验证sa内容正确、生成的密钥正确、然后删除sa')
    def test_create_sa(self):
        sa_name = 'satest'
        # 步骤1：创建sa
        step_create_sa(project_name=self.project_name, sa_name=sa_name)

        # 步骤2：验证sa创建成功并返回secret
        sa_secret = step_get_sa(project_name=self.project_name, sa_name=sa_name)

        # 步骤3：查询sa详情
        step_get_sa_detail(project_name=self.project_name, sa_name=sa_name)

        # 步骤4：查询sa的密钥信息并返回密钥类型
        secret_type = step_get_secret(project_name=self.project_name, secret_name=sa_secret)
        assert secret_type == 'kubernetes.io/service-account-token'

        # 步骤5：删除sa
        step_delete_sa(project_name=self.project_name, sa_name=sa_name)

        # 步骤6：验证删除成功
        num = step_get_sa(project_name=self.project_name, sa_name=sa_name)

        assert num == 0

    @allure.title('{title}')  # 设置用例标题
    @allure.severity(allure.severity_level.CRITICAL)  # 设置用例优先级
    # 将用例信息以参数化的方式传入测试方法
    @pytest.mark.parametrize('id,url,data,story,title,method,severity,condition,except_result', parametrize)
    def test_project(self, id, url, data, story, title, method, severity, condition, except_result):

        """
        :param id: 用例编号
        :param url: 用例请求的URL地址
        :param data: 用例使用的请求数据
        :param story: 用例模块
        :param title: 用例标题
        :param method: 用例的请求方式
        :param severity: 用例优先级
        :param condition: 用例的校验条件
        :param except_result: 用例的预期结果
        """

        allure.dynamic.story(story)  # 动态生成模块
        allure.dynamic.severity(severity)  # 动态生成用例等级

        # test开头的测试函数
        url = config.url + url
        if method == 'get':
            # 测试get方法
            r = requests.get(url, headers=get_header())

        elif method == 'post':
            # 测试post方法
            data = eval(data)
            r = requests.post(url, headers=get_header(), data=json.dumps(data))

        elif method == 'patch':
            # 测试patch方法
            data = eval(data)
            print(data)
            r = requests.patch(url, headers=get_header_for_patch(), data=json.dumps(data))

        elif method == 'delete':
            # 测试delete方法
            r = requests.delete(url, headers=get_header())

        # 将校验条件和预期结果参数化
        if condition != 'nan':
            condition_new = eval(condition)  # 将字符串转化为表达式
            if isinstance(condition_new, str):
                # 判断表达式的结果是否为字符串，如果为字符串格式，则去掉其首尾的空格
                assert condition_new.strip() == except_result
            else:
                assert condition_new == except_result

        # 将用例中的内容打印在报告中
        print(
            '用例编号: ' + str(id) + '\n'
                                 '用例请求的URL地址: ' + str(url) + '\n'
                                                             '用例使用的请求数据: ' + str(data) + '\n'
                                                                                         '用例模块: ' + story + '\n'
                                                                                                            '用例标题: ' + title + '\n'
                                                                                                                               '用例的请求方式: ' + method + '\n'
                                                                                                                                                      '用例优先级: ' + severity + '\n'
                                                                                                                                                                             '用例的校验条件: ' + str(
                condition) + '\n'
                             '用例的实际结果: ' + str(condition_new) + '\n'
                                                                '用例的预期结果: ' + str(except_result)
        )

    @allure.story('存储管理-存储卷快照')
    @allure.title('删除创建的存储卷快照，并验证删除成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_volume_snapshot(self):
        # 删除存储卷快照
        step_delete_volume_snapshot(self.project_name, self.snapshot_name)
        # 查询被删除的存储卷快照
        i = 0
        # 验证存储卷快照被删除，最长等待时间为30s
        while i < 30:
            response = step_get_volume_status(self.project_name, self.snapshot_name)
            # 存储卷快照的状态为布尔值，故先将结果转换我字符类型
            if response.json()['totalItems'] == 0:
                print("删除存储卷快照耗时:" + str(i) + '秒')
                break
            time.sleep(1)
            i = i + 1
        print("actual_result:r1.json()['totalItems'] = " + str(response.json()['totalItems']))
        print("expect_result: 0")
        assert response.json()['totalItems'] == 0

    @allure.story('存储管理-存储卷')
    @allure.title('删除存在的存储卷，并验证删除成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_volume(self):
        # 删除存储卷
        step_delete_volume(self.project_name, self.volume_name)
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

    @allure.story('项目管理')
    @allure.title('删除项目，并验证删除成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_project(self):
        # 删除创建的项目
        step_delete_project(self.ws_name, self.project_name)
        i = 0
        # 验证项目删除结果，最长等待时间为60s
        while i < 60:
            response = step_get_project(self.ws_name, self.project_name)
            if response.json()['totalItems'] == 0:
                print("删除项目耗时:" + str(i) + '秒')
                break
            time.sleep(1)
            i = i + 1
        assert response.json()['totalItems'] == 0


if __name__ == "__main__":
    pytest.main(['-s', 'testProject.py'])  # -s参数是为了显示用例的打印信息。 -q参数只显示结果，不显示过程
