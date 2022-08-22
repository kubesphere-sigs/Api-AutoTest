import pytest
import time
from common import commonFunction
from step import project_steps, workspace_steps


@pytest.fixture
def create_ws():
    # 创建企业空间
    ws_name = 'test-ws' + str(commonFunction.get_random())
    workspace_steps.step_create_workspace(ws_name)
    time.sleep(2)
    yield ws_name
    # 删除创建的企业空间
    workspace_steps.step_delete_workspace(ws_name)


@pytest.fixture
def create_project(create_ws):
    # 创建项目
    project_name = 'test-pro' + str(commonFunction.get_random())
    project_steps.step_create_project(create_ws, project_name)
    time.sleep(3)
    yield project_name
    # 删除创建的项目
    project_steps.step_delete_project(create_ws, project_name)


@pytest.fixture
def create_job(create_project):
    # 创建任务
    job_name = 'job' + str(commonFunction.get_random())
    project_steps.step_create_job(create_project, job_name)
    time.sleep(2)
    yield job_name
    # 删除任务
    project_steps.step_delete_job(create_project, job_name)


@pytest.fixture
def workload_name():
    workload_name = 'workload' + str(commonFunction.get_random())  # 工作负载名称
    return workload_name


@pytest.fixture
def container_name():
    container_name = 'container-nginx' + str(commonFunction.get_random())  # 容器名称
    return container_name


@pytest.fixture
def strategy_info():
    # 创建deployment的策略信息
    strategy_info = {"type": "RollingUpdate", "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}
    return strategy_info


@pytest.fixture
def create_deployment(create_project, workload_name, container_name, strategy_info):
    image = 'nginx'  # 镜像名称
    port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 81}]  # 容器的端口信息
    volumeMounts = []  # 设置挂载的存储卷
    replicas = 2  # 副本数
    volume_info = []
    # 创建deployment
    project_steps.step_create_deploy(project_name=create_project, work_name=workload_name,
                                     container_name=container_name, ports=port, volumemount=volumeMounts,
                                     image=image, replicas=replicas, volume_info=volume_info,
                                     strategy=strategy_info)


@pytest.fixture
def create_service(workload_name, container_name, strategy_info, create_project):
    port_service = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]  # service的端口信息
    image = 'nginx'  # 镜像名称
    port_deploy = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]  # 容器的端口信息
    volumeMounts = []  # 设置挂载的存储卷
    replicas = 2  # 副本数
    volume_info = []
    # 创建service
    project_steps.step_create_service(create_project, workload_name, port_service)
    # 创建service绑定的deployment
    project_steps.step_create_deploy(project_name=create_project, work_name=workload_name,
                                     container_name=container_name,
                                     ports=port_deploy, volumemount=volumeMounts, image=image, replicas=replicas,
                                     volume_info=volume_info, strategy=strategy_info)
