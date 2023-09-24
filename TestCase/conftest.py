import pytest
import time
from common import commonFunction
from datetime import datetime
from step import cluster_steps, multi_project_steps, multi_workspace_steps, project_steps, network_steps, \
    platform_steps, \
    workspace_steps, app_steps, devops_steps, storage_steps, multi_cluster_steps, multi_cluster_storages_step


@pytest.fixture()
def create_project(create_ws):
    # 创建项目
    project_name = 'test-pro' + str(commonFunction.get_random())
    project_steps.step_create_project(create_ws, project_name)
    # 等待项目创建成功
    i = 0
    while i < 60:
        try:
            project_info = project_steps.step_get_project_info_by_name(create_ws, project_name)
            if project_info.json()['totalItems'] == 1:
                break
            else:
                time.sleep(1)
                i += 1
        except KeyError as e:
            print(e)
            time.sleep(1)
            i += 1
    yield project_name
    # 删除创建的项目
    project_steps.step_delete_project(create_ws, project_name)


@pytest.fixture()
def create_job(create_project):
    # 创建任务
    job_name = 'job' + str(commonFunction.get_random())
    project_steps.step_create_job(create_project, job_name)
    time.sleep(2)
    yield job_name
    # 删除任务
    time.sleep(1)
    project_steps.step_delete_job(create_project, job_name)


@pytest.fixture()
def workload_name():
    workload_name = 'workload' + str(commonFunction.get_random())  # 工作负载名称
    return workload_name


@pytest.fixture()
def strategy_info():
    # 创建deployment的策略信息
    strategy_info = {"type": "RollingUpdate", "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}
    return strategy_info


@pytest.fixture()
def create_deployment(create_project, workload_name, container_name, strategy_info):
    image = 'nginx'  # 镜像名称
    port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 81}]  # 容器的端口信息
    volume_mounts = []  # 设置挂载的存储卷
    replicas = 2  # 副本数
    volume_info = []
    # 创建deployment
    project_steps.step_create_deploy(project_name=create_project, work_name=workload_name,
                                     container_name=container_name, ports=port, volumemount=volume_mounts,
                                     image=image, replicas=replicas, volume_info=volume_info,
                                     strategy=strategy_info)


@pytest.fixture()
def create_service(workload_name, container_name, strategy_info, create_project):
    port_service = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]  # service的端口信息
    image = 'nginx'  # 镜像名称
    port_deploy = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]  # 容器的端口信息
    volume_mounts = []  # 设置挂载的存储卷
    replicas = 2  # 副本数
    volume_info = []
    # 创建service
    project_steps.step_create_service(create_project, workload_name, port_service)
    # 创建service绑定的deployment
    project_steps.step_create_deploy(project_name=create_project, work_name=workload_name,
                                     container_name=container_name,
                                     ports=port_deploy, volumemount=volume_mounts, image=image, replicas=replicas,
                                     volume_info=volume_info, strategy=strategy_info)


@pytest.fixture()
def create_project_role(create_project):
    role_name = 'role' + str(commonFunction.get_random())
    # 创建角色
    project_steps.step_create_role(create_project, role_name)
    # 等待角色创建成功
    i = 0
    while i < 60:
        role_info = project_steps.step_get_role(create_project, role_name)
        if role_info.json()['totalItems'] == 1:
            break
        else:
            time.sleep(1)
            i += 1
    yield role_name
    project_steps.step_project_delete_role(create_project, role_name)


@pytest.fixture()
def create_role():
    authority = '["role-template-view-basic"]'
    role_name = 'role' + str(commonFunction.get_random())
    # 创建角色
    platform_steps.step_create_role(role_name, authority)
    yield role_name
    # 删除角色
    platform_steps.step_delete_role(role_name)


@pytest.fixture()
def create_multi_workspace():
    # 创建一个多集群企业空间（包含所有的集群）
    ws_name = 'ws-multi-' + str(commonFunction.get_random())
    alias_name = '跨集群'
    description = '包含所有的集群的企业空间'
    clusters = cluster_steps.step_get_cluster_name()
    multi_workspace_steps.step_create_multi_ws(ws_name, clusters, alias_name, description)
    yield ws_name
    multi_workspace_steps.step_delete_workspace(ws_name)


@pytest.fixture()
def create_multi_project(create_multi_workspace):
    # 创建一个多集群项目(包含所有集群)
    pro_name = 'pro-multi-' + str(commonFunction.get_random())
    clusters = cluster_steps.step_get_cluster_name()
    multi_project_steps.step_create_fed_project(create_multi_workspace, pro_name, clusters)
    yield pro_name
    multi_project_steps.step_delete_fed_project(project_name=pro_name)


@pytest.fixture()
def create_role():
    authority = '["role-template-view-basic"]'
    role_name = 'role' + str(commonFunction.get_random())
    # 创建角色
    platform_steps.step_create_role(role_name, authority)
    time.sleep(1)
    yield role_name
    # 删除角色
    platform_steps.step_delete_role(role_name)


@pytest.fixture()
def create_user(create_role):
    user_name = 'user' + str(commonFunction.get_random())
    email = 'qq' + str(commonFunction.get_random()) + '@qq.com'
    password = 'P@88w0rd'
    # 使用新创建的角色创建用户
    platform_steps.step_create_user(user_name, create_role, email, password)
    # # 等待用户创建成功
    i = 0
    while i < 10:
        try:
            user_info = platform_steps.step_get_user_info(user_name)
            if user_info.json()['items'][0]['status']['state']:
                break
        except Exception as e:
            print(e)
            time.sleep(1)
            i += 1
    yield user_name
    # 删除用户
    platform_steps.step_delete_user(user_name)


@pytest.fixture()
def create_ws():
    ws_name = 'test-ws' + str(commonFunction.get_random())
    # 创建企业空间
    workspace_steps.step_create_workspace(ws_name)
    # 等待企业空间创建成功
    i = 0
    while i < 60:
        ws_info = workspace_steps.step_get_ws_info(ws_name)
        if ws_info.json()['totalItems'] == 1:
            break
        else:
            time.sleep(1)
            i += 1
    yield ws_name
    # 删除企业空间
    workspace_steps.step_delete_workspace(ws_name)


@pytest.fixture()
def workbench_info():
    # 获取当前时间的10位时间戳
    now_time = datetime.now()
    now_timestamp = str(datetime.timestamp(now_time))[0:10]
    # 获取180分钟戳
    before_timestamp = commonFunction.get_before_timestamp(now_time, 180)
    # 查询工作台的基本信息
    response = platform_steps.step_get_base_info(before_timestamp, now_timestamp, '600', '20')
    return response


@pytest.fixture()
def create_category():
    category_name = 'category' + str(commonFunction.get_random())
    response = app_steps.step_create_category(category_name)
    time.sleep(3)
    # 获取创建分类的category_id
    category_id = response.json()['category_id']
    yield category_id
    # 删除分类
    time.sleep(1)
    app_steps.step_delete_category(category_id)


@pytest.fixture()
def node_name():
    # 获取节点列表中第一个节点的名称
    response = cluster_steps.step_get_nodes()
    node_name = response.json()['items'][0]['metadata']['name']
    return node_name


@pytest.fixture()
# 在单集群环境创建ippool
def create_ippool(ip_pool_name, ip_address):
    # 创建ippool
    network_steps.step_create_ippool(ip_pool_name, ip_address)
    yield ip_pool_name
    # 删除ippool
    network_steps.step_delete_ippool(ip_pool_name)


@pytest.fixture()
# 在多集群环境创建ippool
def create_multi_ippool(request, ip_pool_name, ip_address):
    # 获取参数
    # 创建ippool
    network_steps.step_create_ippool(ip_pool_name, ip_address, cluster_name=request.param)
    yield ip_pool_name
    # 删除ippool
    i = 0
    while i < 60:
        r = network_steps.step_delete_ippool(ip_pool_name, request.param)
        if r.status_code == 200:
            break
        i += 1
        time.sleep(1)


@pytest.fixture()
def create_devops(create_ws):
    dev_name = 'test-dev' + str(commonFunction.get_random())
    devops_steps.step_create_devops(create_ws, dev_name)  # 创建一个devops工程
    i = 0
    devops_name_new = ''
    while i < 10:
        response = devops_steps.step_get_devopinfo(create_ws, dev_name)
        devops_name_new = response.json()['items'][0]['metadata']['name']
        status = response.json()['items'][0]['metadata']['annotations']['devopsproject.devops.kubesphere.io/syncstatus']
        if status == 'successful':
            break
        time.sleep(1)
        i += 1
    yield devops_name_new
    # 删除devops工程
    devops_steps.step_delete_devops(create_ws, devops_name_new)


@pytest.fixture()
def create_sc():
    sc_name = 'sc-' + str(commonFunction.get_random())
    ex = True
    # 创建存储类
    storage_steps.create_sc(sc_name, ex)
    yield sc_name
    # 删除存储类
    storage_steps.delete_sc(sc_name)


@pytest.fixture()
def create_multi_cluster_sc():
    sc_name = 'sc-' + str(commonFunction.get_random())
    ex = True
    cluster_name = multi_cluster_steps.step_get_host_cluster_name()
    # 创建存储类
    multi_cluster_storages_step.step_create_sc(cluster_name, sc_name, ex)
    yield sc_name
    # 删除存储类
    multi_cluster_storages_step.delete_sc(cluster_name, sc_name)


@pytest.fixture()
def create_code_repository(create_devops):
    # 创建代码仓库
    name = 'test-git' + str(commonFunction.get_random())
    provider = 'git'
    url = 'https://gitee.com/linuxsuren/demo-go-http'
    devops_steps.step_import_code_repository(create_devops, name, provider, url)
    yield url


@pytest.fixture()
# 创建网络策略
def create_network_policy(create_project):
    # 创建网络策略
    policy_name = 'network-policy-' + str(commonFunction.get_random())
    network_steps.step_create_network_policy(create_project, policy_name)
    yield policy_name
    # 删除网络策略
    network_steps.step_delete_network_policy(create_project, policy_name)


@pytest.fixture()
def ip_pool_name():
    return 'ip-pool-' + str(commonFunction.get_random())


@pytest.fixture()
def ip_address():
    return commonFunction.random_ip()


@pytest.fixture()
# 返回企业空间名称
def ws_name():
    ws_name = 'ws-test' + str(commonFunction.get_random())
    return ws_name


@pytest.fixture()
# 返回项目名称
def pro_name():
    pro_name = 'pro-test' + str(commonFunction.get_random())
    return pro_name


@pytest.fixture()
# 返回deploy名称
def deploy_name():
    deploy_name = 'deploy-test' + str(commonFunction.get_random())
    return deploy_name


@pytest.fixture()
# 返回container名称
def container_name():
    container_name = 'container-test' + str(commonFunction.get_random())
    return container_name


@pytest.fixture()
# 在多集群环境创建卷快照类
def create_multi_volume_snapshot_class(request):
    cluster_name = request.param
    vsc_name = 'vsc-' + str(commonFunction.get_random())
    diver = 'disk.csi.qingcloud.com'
    policy = 'Delete'
    # 创建卷快照类
    multi_cluster_storages_step.step_create_vsc(cluster_name, vsc_name, diver, policy)
    yield vsc_name
    # 删除卷快照类
    multi_cluster_storages_step.delete_vsc(cluster_name, vsc_name)
