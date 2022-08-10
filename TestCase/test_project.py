# -- coding: utf-8 --
import pytest
import allure
import sys
import time
from pytest import assume

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from common.getData import DoexcleByPandas
from common import commonFunction
from step import project_steps, platform_steps, workspace_steps, cluster_steps


@allure.feature('Project')
@pytest.mark.skipif(commonFunction.check_multi_cluster() is True, reason='多集群环境下不执行')
class TestProject(object):
    if commonFunction.check_multi_cluster() is True:
        # 如果为单集群环境，则不会collect该class的所有用例。 __test__ = False
        __test__ = False
    else:
        __test__ = True

    volume_name = 'testvolume'  # 存储卷名称，在创建、删除存储卷时使用,excle中的用例也用到了这个存储卷
    user_name = 'user-for-test-project'  # 系统用户名称
    user_role = 'users-manager'  # 用户角色
    ws_name = 'ws-for-test-project' + str(commonFunction.get_random())
    project_name = 'test-project' + str(commonFunction.get_random())
    project_name_for_exel = 'test-project'  # 项目名称，从excle中获取的测试用例中用到了这个项目名称
    ws_role_name = ws_name + '-viewer'  # 企业空间角色名称
    project_role_name = 'test-project-role'  # 项目角色名称
    job_name = 'demo-job'  # 任务名称,在创建和删除任务时使用
    work_name = 'workload-demo'  # 工作负载名称，在创建、编辑、删除工作负载时使用
    # 从文件中读取用例信息
    parametrize = DoexcleByPandas().get_data_from_yaml(filename='../data/project.yaml')

    # 所有用例执行之前执行该方法
    def setup_class(self):
        platform_steps.step_create_user(self.user_name, self.user_role)  # 创建一个用户
        workspace_steps.step_create_workspace(self.ws_name)  # 创建一个企业空间
        workspace_steps.step_invite_user(self.ws_name, self.user_name, self.ws_name + '-viewer')  # 将创建的用户邀请到企业空间
        project_steps.step_create_project(self.ws_name, self.project_name)  # 创建一个project工程
        project_steps.step_create_project(self.ws_name, self.project_name_for_exel)  # 创建一个project工程用于执行excle中的用例
        project_steps.step_create_volume(self.project_name_for_exel, self.volume_name)  # 创建存储卷

    # 所有用例执行完之后执行该方法
    def teardown_class(self):
        project_steps.step_delete_volume(self.project_name_for_exel, self.volume_name)  # 删除存储卷
        project_steps.step_delete_project(self.ws_name, self.project_name)  # 删除创建的项目
        time.sleep(5)
        # 等待pvc删除成功，再删除项目
        i = 0
        while i < 300:
            r = project_steps.step_get_volume(self.project_name_for_exel, self.volume_name)
            if r.json()['totalItems'] == 0:
                break
            else:
                time.sleep(3)
                i += 3
        project_steps.step_delete_project(self.ws_name, self.project_name_for_exel)
        time.sleep(5)

        # workspace_steps.step_delete_workspace(self.ws_name)  # 删除创建的企业空间
        # platform_steps.step_delete_user(self.user_name)  # 删除创建的用户

    @pytest.fixture
    def create_project(self):
        # 创建项目
        project_name = 'test-pro' + str(commonFunction.get_random())
        project_steps.step_create_project(self.ws_name, project_name)
        yield project_name
        # 删除创建的项目
        project_steps.step_delete_project(self.ws_name, project_name)

    @pytest.fixture
    def create_job(self, create_project):
        # 创建任务
        job_name = 'job' + str(commonFunction.get_random())
        project_steps.step_create_job(create_project, job_name)
        yield job_name
        # 删除任务
        project_steps.step_delete_job(create_project, job_name)

    @pytest.fixture
    def workload_name(self):
        workload_name = 'workload' + str(commonFunction.get_random())  # 工作负载名称
        return workload_name

    @pytest.fixture
    def container_name(self):
        container_name = 'container-nginx' + str(commonFunction.get_random())  # 容器名称
        return container_name

    @pytest.fixture
    def strategy_info(self):
        # 创建deployment的策略信息
        strategy_info = {"type": "RollingUpdate", "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}
        return strategy_info

    @pytest.fixture
    def create_workload(self, create_project, workload_name, container_name, strategy_info):
        image = 'nginx'  # 镜像名称
        # condition = 'name=' + workload_name  # 查询条件
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 81}]  # 容器的端口信息
        volumeMounts = []  # 设置挂载的存储卷
        # strategy_info = {"type": "RollingUpdate", "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
        replicas = 2  # 副本数
        volume_info = []
        # 创建工作负载
        project_steps.step_create_deploy(project_name=create_project, work_name=workload_name,
                                         container_name=container_name, ports=port, volumemount=volumeMounts,
                                         image=image, replicas=replicas, volume_info=volume_info,
                                         strategy=strategy_info)

    @allure.story('存储管理-存储卷')
    @allure.title('创建存储卷，然后将存储卷绑定到新建的deployment上，最后验证资源和存储卷的状态正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_volume_for_deployment(self, create_project, workload_name, container_name, strategy_info):
        type_name = 'volume-type'  # 存储卷的类型
        volume_name = 'volume' + str(commonFunction.get_random())
        replicas = 1  # 副本数
        image = 'redis'  # 镜像名称
        condition = 'name=' + workload_name  # 查询条件
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80}]  # 容器的端口信息
        volumeMounts = [{"name": type_name, "readOnly": False, "mountPath": "/data"}]  # 设置挂载的存储卷
        volume_info = [{"name": type_name, "persistentVolumeClaim": {"claimName": volume_name}}]  # 存储卷的信息
        # 创建存储卷
        project_steps.step_create_volume(create_project, volume_name)
        # 创建资源并将存储卷绑定到资源
        project_steps.step_create_deploy(create_project, work_name=workload_name, image=image, replicas=replicas,
                                         container_name=container_name, volume_info=volume_info, ports=port,
                                         volumemount=volumeMounts, strategy=strategy_info)
        # 验证资源创建成功
        i = 0
        while i < 300:
            try:
                # 获取工作负载的状态
                response = project_steps.step_get_workload(create_project, type='deployments', condition=condition)
                status = response.json()['items'][0]['status']
                # 验证资源的所有副本已就绪
                if 'unavailableReplicas' not in status:
                    break
            except Exception as e:
                print(e)
            finally:
                time.sleep(10)
                i += 10
        # 获取存储卷状态
        response = project_steps.step_get_volume_status(create_project, volume_name)
        status = response.json()['items'][0]['status']['phase']
        # 验证存储卷状态正常
        with assume:
            assert status == 'Bound'
        # 删除工作负载
        project_steps.step_delete_deployment(create_project, workload_name)
        # 等待工作负载删除成功，再删除pvc
        j = 0
        while j < 300:
            re = project_steps.step_get_workload(create_project, type='deployments', condition=condition)
            if re.json()['totalItems'] == 0:
                break
            else:
                time.sleep(3)
                j += 3
        project_steps.step_delete_pvc(create_project, volume_name)
        # 等待pvc删除成功，再删除项目
        k = 0
        while k < 300:
            r = project_steps.step_get_volume(create_project, volume_name)
            if r.json()['totalItems'] == 0:
                break
            else:
                time.sleep(3)
                k += 3

    @allure.story('存储管理-存储卷')
    @allure.title('创建存储卷，然后将存储卷绑定到新建的statefulsets上，最后验证资源和存储卷的状态正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_volume_for_statefulsets(self, create_project, workload_name, container_name):
        volume_name = 'volume-stateful' + str(commonFunction.get_random())  # 存储卷的名称
        type_name = 'volume-type'  # 存储卷的类型
        service_name = 'service' + volume_name
        replicas = 2  # 副本数
        image = 'nginx'  # 镜像名称
        condition = 'name=' + workload_name  # 查询条件
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]
        service_port = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]
        volumemounts = [{"name": type_name, "readOnly": False, "mountPath": "/data"}]
        volume_info = [{"name": type_name, "persistentVolumeClaim": {"claimName": volume_name}}]  # 存储卷的信息
        # 创建存储卷
        project_steps.step_create_volume(create_project, volume_name)
        # 创建资源并将存储卷绑定到资源
        project_steps.step_create_stateful(project_name=create_project, work_name=workload_name,
                                           container_name=container_name,
                                           image=image, replicas=replicas, ports=port, service_ports=service_port,
                                           volumemount=volumemounts, volume_info=volume_info, service_name=service_name)
        # 验证资源创建成功
        readyReplicas = 0
        i = 0
        while i < 120:
            # 获取工作负载的状态
            response = project_steps.step_get_workload(create_project, type='statefulsets', condition=condition)
            try:
                readyReplicas = response.json()['items'][0]['status']['readyReplicas']
            except Exception as e:
                print(e)
            # 验证资源的所有副本已就绪
            if readyReplicas == replicas:
                break
            else:
                time.sleep(1)
                i += 1
        # 获取存储卷状态
        response = project_steps.step_get_volume_status(create_project, volume_name)
        status = response.json()['items'][0]['status']['phase']
        # 验证存储卷状态正常
        pytest.assume(status == 'Bound')
        # 删除工作负载
        project_steps.step_delete_workload(create_project, 'statefulsets', workload_name)
        # 等待工作负载删除成功，再删除pvc
        j = 0
        while j < 300:
            re = project_steps.step_get_workload(create_project, type='statefulsets', condition=condition)
            if re.json()['totalItems'] == 0:
                break
            else:
                time.sleep(3)
                j += 3
        project_steps.step_delete_pvc(create_project, volume_name)
        # 等待pvc删除成功，再删除项目
        k = 0
        while k < 300:
            r = project_steps.step_get_volume(create_project, volume_name)
            if r.json()['totalItems'] == 0:
                break
            else:
                time.sleep(3)
                k += 3

    @allure.story('存储管理-存储卷')
    @allure.title('创建daemonsets并使用hostpath存储卷，最后验证资源和存储卷的状态正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_volume_for_daemonsets(self, create_project, workload_name, container_name):
        volume_name = 'volume-deamon' + str(commonFunction.get_random())  # 存储卷的名称
        image = 'redis'  # 镜像名称
        condition = 'name=' + workload_name  # 查询条件
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80}]  # 容器的端口信息
        volumeMounts = [{"name": volume_name, "readOnly": False, "mountPath": "/data"}]  # 设置挂载哦的存储卷
        volume_info = [{"hostPath": {"path": "/data"}, "name": volume_name}]  # 存储卷的信息
        # 获取集群中所有的节点数
        res = cluster_steps.step_get_node_all()
        cluster_node_all = res.json()['totalItems']
        # 获取所有没有污点的节点数量
        cluster_node_no_taint = 0
        for i in range(0, cluster_node_all):
            try:
                if res.json()['items'][i]['spec']['taints']:
                    cluster_node_no_taint += 1
            except Exception as e:
                print(e)
        # 创建资源并将存储卷绑定到资源
        project_steps.step_create_daemonset(create_project, work_name=workload_name, image=image,
                                            container_name=container_name, volume_info=volume_info, ports=port,
                                            volumemount=volumeMounts)
        # 验证资源创建成功
        numberReady = ''
        i = 0
        while i < 180:
            # 获取工作负载的状态
            response = project_steps.step_get_workload(create_project, type='daemonsets', condition=condition)
            numberReady = response.json()['items'][0]['status']['numberReady']  # 验证资源的所有副本已就绪
            if numberReady == cluster_node_no_taint:
                break
            else:
                time.sleep(30)
                i += 30
        pytest.assume(numberReady == cluster_node_no_taint)

        # 删除工作负载
        project_steps.step_delete_workload(create_project, 'daemonsets', workload_name)
        # 等待工作负载删除成功，再删除pvc
        j = 0
        while j < 300:
            re = project_steps.step_get_workload(create_project, type='daemonsets', condition=condition)
            if re.json()['totalItems'] == 0:
                break
            else:
                time.sleep(3)
                j += 3
        project_steps.step_delete_pvc(create_project, volume_name)
        # 等待pvc删除成功，再删除项目
        k = 0
        while k < 300:
            r = project_steps.step_get_volume(create_project, volume_name)
            if r.json()['totalItems'] == 0:
                break
            else:
                time.sleep(3)
                k += 3

    @allure.story('存储管理-存储卷')
    @allure.title('创建存储卷，然后将存储卷绑定到新建的service上，最后验证资源和存储卷的状态正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_volume_for_service(self, create_project, workload_name, container_name, strategy_info):
        volume_name = 'volume-service'  # 存储卷的名称
        type_name = 'volume-type'  # 存储卷的类型
        image = 'redis'  # 镜像名称
        condition = 'name=' + workload_name  # 查询条件
        port_service = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]  # service的端口信息
        port_deploy = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80}]  # 容器的端口信息
        volumeMounts = [{"name": type_name, "readOnly": False, "mountPath": "/data"}]  # 设置挂载哦的存储卷
        volume_info = [{"name": type_name, "persistentVolumeClaim": {"claimName": volume_name}}]  # 存储卷的信息
        replicas = 2  # 副本数
        # 创建存储卷
        project_steps.step_create_volume(create_project, volume_name)
        # 创建service
        project_steps.step_create_service(create_project, workload_name, port_service)
        # 创建service绑定的deployment
        project_steps.step_create_deploy(project_name=create_project, work_name=workload_name,
                                         container_name=container_name,
                                         ports=port_deploy, volumemount=volumeMounts, image=image, replicas=replicas,
                                         volume_info=volume_info, strategy=strategy_info)
        # 验证service创建成功
        response = project_steps.step_get_workload(create_project, type='services', condition=condition)
        name = response.json()['items'][0]['metadata']['name']
        pytest.assume(name == workload_name)
        # 验证deploy创建成功
        readyReplicas = 0
        i = 0
        while i < 180:
            re = project_steps.step_get_workload(create_project, type='deployments', condition=condition)
            # 获取并验证deployment创建成功
            try:
                readyReplicas = re.json()['items'][0]['status']['readyReplicas']
            except Exception as e:
                print(e)
            if readyReplicas == replicas:
                break
            else:
                time.sleep(10)
                i += 10
        # 获取存储卷状态
        response = project_steps.step_get_volume_status(create_project, volume_name)
        status = response.json()['items'][0]['status']['phase']
        # 验证存储卷状态正常
        pytest.assume(status == 'Bound')

        # 删除工作负载
        project_steps.step_delete_workload(create_project, 'deployments', workload_name)
        # 等待工作负载删除成功，再删除pvc
        j = 0
        while j < 300:
            re = project_steps.step_get_workload(create_project, type='deployments', condition=condition)
            if re.json()['totalItems'] == 0:
                break
            else:
                time.sleep(3)
                j += 3
        project_steps.step_delete_pvc(create_project, volume_name)
        # 等待pvc删除成功，再删除项目
        k = 0
        while k < 300:
            r = project_steps.step_get_volume(create_project, volume_name)
            if r.json()['totalItems'] == 0:
                break
            else:
                time.sleep(3)
                k += 3

    @allure.story("项目设置-项目角色")
    @allure.title('查看project工程默认的所有角色')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_project_role_all(self):
        role_name = ''
        r = project_steps.step_get_role(self.project_name, role_name)
        assert r.json()['totalItems'] == 3  # 验证初始的角色数量为3

    @allure.story("项目设置-项目角色")
    @allure.title('查找project工程中指定的角色')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_role_one(self):
        role_name = 'viewer'
        r = project_steps.step_get_role(self.project_name, role_name)
        assert r.json()['items'][0]['metadata']['name'] == role_name  # 验证查询的角色结果为viewer

    @allure.story("项目设置-项目角色")
    @allure.title('查找project工程中不存在的角色')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_role_none(self):
        role_name = 'viewer123'
        response = project_steps.step_get_role(self.project_name, role_name)
        assert response.json()['totalItems'] == 0  # 验证查询到的结果为空

    @allure.story("项目设置-项目角色")
    @allure.title('模糊查找project工程中的角色')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_role_fuzzy(self):
        role_name = 'adm'
        r = project_steps.step_get_role(self.project_name, role_name)
        assert r.json()['totalItems'] == 1  # 验证查询到的结果数量为2
        # 验证查找到的角色
        assert r.json()['items'][0]['metadata']['name'] == 'admin'

    @allure.story("项目设置-项目角色")
    @allure.title('在project工程中创建角色')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_role_create(self):
        role_name = 'role' + str(commonFunction.get_random())
        r = project_steps.step_create_role(self.project_name, role_name)
        assert r.json()['metadata']['name'] == role_name  # 验证新建的角色名称

    @allure.story("项目设置-项目角色")
    @allure.title('在project工程中创建角色-角色名称为空')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_role_create_name_none(self):
        role_name = ''
        r = project_steps.step_create_role(self.project_name, role_name)
        # 验证创建角色失败的异常提示信息
        assert r.text.strip() == 'Role.rbac.authorization.k8s.io "" is invalid: metadata.name: Required value: name or generateName is required'

    @allure.story("项目设置-项目角色")
    @allure.title('在project工程中编辑角色基本信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_project_role_edit_info(self):
        alias_name = '我是别名'  # 别名
        role_name = 'role' + str(commonFunction.get_random())
        # 角色信息
        annotations = {"iam.kubesphere.io/aggregation-roles": "[\"role-template-view-basic\"]",
                       "kubesphere.io/alias-name": alias_name,
                       "kubesphere.io/creator": "admin",
                       "kubesphere.io/description": "我是描述信息"}
        resourceVersion = ''
        # 创建角色
        project_steps.step_create_role(self.project_name, role_name)

        r = project_steps.step_edit_project_role(self.project_name, role_name, resourceVersion, annotations)
        assert r.json()['metadata']['annotations']['kubesphere.io/alias-name'] == '我是别名'  # 验证修改后的别名
        assert r.json()['metadata']['annotations']['kubesphere.io/description'] == '我是描述信息'  # 验证修改后的描述信息

    @allure.story("项目设置-项目角色")
    @allure.title('在project工程中编辑角色的权限信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_project_role_edit_authority(self):
        # 创建项目角色
        role_name = 'role' + str(commonFunction.get_random())
        project_steps.step_create_role(self.project_name, role_name)
        # 获取角色的resourceVersion
        response = project_steps.step_get_project_role(self.project_name, role_name)
        resourceVersion = response.json()['items'][0]['metadata']['resourceVersion']
        # 编辑角色的权限
        authority = '["role-template-view-basic","role-template-view-volumes","role-template-view-secrets",' \
                    '"role-template-view-configmaps","role-template-view-snapshots","role-template-view-app-workloads"]'
        annotations = {"iam.kubesphere.io/aggregation-roles": authority,
                       "kubesphere.io/alias-name": "",
                       "kubesphere.io/creator": "admin", "kubesphere.io/description": ""}
        r = project_steps.step_edit_project_role(self.project_name, role_name, resourceVersion, annotations)
        pytest.assume(
            r.json()['metadata']['annotations']['iam.kubesphere.io/aggregation-roles'] == authority)  # 验证修改后的权限信息
        # 删除项目角色
        project_steps.step_project_delete_role(self.project_name, role_name)

    @allure.story("项目设置-项目角色")
    @allure.title('在project工程中删除角色')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_project_delete_role(self):
        # 创建角色
        role_name = 'role' + str(commonFunction.get_random())
        project_steps.step_create_role(self.project_name, role_name)
        # 验证角色创建成功
        response = project_steps.step_get_project_role(self.project_name, role_name)
        count = response.json()['totalItems']
        pytest.assume(count == 1)
        # 删除角色
        project_steps.step_project_delete_role(self.project_name, role_name)
        # 验证角色删除成功
        r = project_steps.step_get_project_role(self.project_name, role_name)
        count_new = r.json()['totalItems']
        assert count_new == 0

    @allure.story("项目设置-项目成员")
    @allure.title('查看project默认的所有用户')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_project_user_all(self, create_project):
        # 查看项目成员，并获取成员名称
        time.sleep(2)
        response = project_steps.step_get_project_member(create_project, '')
        name = response.json()['items'][0]['metadata']['name']
        pytest.assume(name == 'admin')  # 验证默认的用户仅有admin

    @allure.story("项目设置-项目成员")
    @allure.title('查找project指定的用户')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_user_one(self):
        user_condition = 'admin'
        r = project_steps.step_get_project_member(self.project_name, user_condition)
        assert r.json()['items'][0]['metadata']['name'] == user_condition  # 验证查找的结果为admin

    @allure.story("项目设置-项目成员")
    @allure.title('模糊查找project的用户')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_user_fuzzy(self):
        user_condition = 'ad'
        r = project_steps.step_get_project_member(self.project_name, user_condition)
        assert r.json()['items'][0]['metadata']['name'] == 'admin'  # 验证查找的结果为admin

    @allure.story("项目设置-项目成员")
    @allure.title('查找project工程不存在的用户')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_user_none(self):
        user_condition = 'wx-ad'
        r = project_steps.step_get_project_member(self.project_name, user_condition)
        assert r.json()['totalItems'] == 0  # 验证查找的结果为空

    @allure.story("项目设置-项目成员")
    @allure.title('邀请用户到project')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_project_invite_user(self, create_project):
        time.sleep(3)
        # 将用户邀请到项目
        role = 'viewer'
        project_steps.step_invite_member(create_project, self.user_name, role)
        role_actual = ''
        i = 0
        while i < 60:
            try:
                # 查看项目成员，并获取其角色
                response = project_steps.step_get_project_member(create_project, self.user_name)
                role_actual = response.json()['items'][0]['metadata']['annotations']['iam.kubesphere.io/role']
                if role_actual:
                    break
            except Exception as e:
                print(e)
        pytest.assume(role_actual == role)

    # 用例的执行结果应当为false。接口没有对不存在的用户做限制
    @allure.title('邀请不存在的用户到project')
    @allure.severity(allure.severity_level.CRITICAL)
    def wx_test_project_invite_none_user(self):
        username = 'wxqw'
        role = 'viewer'
        project_steps.step_invite_member(self.project_name, username, role)

    @allure.story("项目设置-项目角色")
    @allure.title('编辑project成员的角色')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_project_edit_user(self):
        # 编辑项目成员角色
        role = 'operator'
        project_steps.step_edit_project_member_role(self.project_name, self.user_name, role)
        # 查看项目成员，并获取其角色
        response = project_steps.step_get_project_member(self.project_name, self.user_name)
        role_actual = response.json()['items'][0]['metadata']['annotations']['iam.kubesphere.io/role']
        assert role_actual == role  # 验证修改后的用户角色

    @allure.story("项目设置-项目成员")
    @allure.title('删除project的成员')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_project_delete_user(self, create_project):
        # 将用户邀请到项目
        role = 'admin'
        project_steps.step_invite_member(create_project, self.user_name, role)
        # 查看项目成员，并验证添加成功
        name = ''
        i = 0
        while i < 60:
            try:
                res = project_steps.step_get_project_member(create_project, self.user_name)
                name = res.json()['items'][0]['metadata']['name']
                if name:
                    break
            except Exception as e:
                print(e)
        pytest.assume(name == self.user_name)
        # 移出项目成员
        project_steps.step_remove_project_member(create_project, self.user_name)
        # 查询被移出的成员
        response = project_steps.step_get_project_member(create_project, self.user_name)
        count = response.json()['totalItems']
        # 验证查询结果为空
        pytest.assume(count == 0)

    # 以下4条用例的执行结果应当为false，未已test开头表示未执行。接口没有对角色的名称做限制
    @allure.title('在project工程中创建角色-名称中包含大写字母')
    @allure.severity(allure.severity_level.CRITICAL)
    def wx_test_project_role_create_name(self):
        project_role_name = 'WX'
        project_steps.step_create_role(self.project_name, project_role_name)

    @allure.title('在project工程中创建角色-名称中包含非分隔符("-")的特殊符号')
    @allure.severity(allure.severity_level.CRITICAL)
    def wx_test_project_role_create_name1(self):
        project_role_name = 'w@x'
        project_steps.step_create_role(self.project_name, project_role_name)

    @allure.title('在project工程中创建角色-名称以分隔符("-")开头')
    @allure.severity(allure.severity_level.CRITICAL)
    def wx_test_project_role_create_name2(self):
        project_role_name = '-wx'
        project_steps.step_create_role(self.project_name, project_role_name)

    @allure.title('在project工程中创建角色-名称以分隔符("-")结尾')
    @allure.severity(allure.severity_level.CRITICAL)
    def wx_test_project_role_create_name3(self):
        project_role_name = 'wx-'
        project_steps.step_create_role(self.project_name, project_role_name)

    @allure.story('应用负载-任务')
    @allure.title('创建任务，并验证运行正常')
    @allure.description('创建一个计算圆周率的任务')
    @allure.severity(allure.severity_level.BLOCKER)
    def test_create_job(self, create_project, create_job):
        # 查看任务详情
        response = project_steps.step_get_job_detail(create_project, create_job)
        # 获取任务uid
        uid = response.json()['items'][0]['metadata']['uid']
        # 获取任务中指定的容器组完成数量
        completions = response.json()['items'][0]['spec']['completions']
        # 捕获异常，不对异常作处理,每隔5秒查询一次任务状态
        res = ''
        i = 0
        while i < 60:
            try:
                res = project_steps.step_get_job_detail(create_project, create_job)
                if res.json()['items'][0]['status']['succeeded'] == 2:
                    break
            except KeyError:
                time.sleep(3)
                i = i + 3
        # 获取任务的成功的容器数量
        succeeded = res.json()['items'][0]['status']['succeeded']
        # 验证指定容器组完成数量==实际成功的容器数量
        pytest.assume(completions == succeeded)
        # 查看任务的资源状态，并获取第一个容器组的名称
        re = project_steps.step_get_job_pods(create_project, uid)
        pod_name = re.json()['items'][0]['metadata']['name']
        # 查看任务的第一个容器的运行日志，并验证任务的运行结果
        logs = project_steps.step_get_pods_log(create_project, pod_name, create_job)
        pytest.assume('3.1415926' in logs)

    @allure.story('应用负载-任务')
    @allure.title('按名称模糊查询存在的任务')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_job(self, create_project, create_job):
        project_steps.step_create_job(create_project, create_job)
        # 模糊查询存在的任务
        response = project_steps.step_get_assign_job(create_project, 'name', create_job[1:])
        pytest.assume(response.json()['totalItems'] == 1)

    @allure.story('应用负载-任务')
    @allure.title('按状态查询已完成的任务')
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_job_status_completed(self, create_project, create_job):
        # 捕获异常，不对异常作处理,每隔5秒查询一次任务状态
        i = 0
        while i < 60:
            try:
                res = project_steps.step_get_job_detail(create_project, create_job)
                if res.json()['items'][0]['status']['succeeded'] == 2:
                    break
            except KeyError:
                time.sleep(3)
                i = i + 3
        response = project_steps.step_get_assign_job(create_project, 'status', 'completed')  # 查询指定的任务
        # 获取查询结果中job的名称
        job_name_actual = response.json()['items'][0]['metadata']['name']
        # 验证查询结果正确
        pytest.assume(create_job == job_name_actual)

    @allure.story('应用负载-任务')
    @allure.title('按状态查询运行中的任务')
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_job_status_running(self, create_project, create_job):
        # 验证任务状态为运行中
        project_steps.step_get_job_status_run(create_project, create_job)
        # 按状态为运行中查询任务
        response = project_steps.step_get_assign_job(create_project, 'status', 'running')
        # 验证查询结果
        pytest.assume(response.json()['totalItems'] >= 1)

    @allure.story('应用负载-容器组')
    @allure.title('按名称精确查询存在的容器组')
    @allure.severity(allure.severity_level.NORMAL)
    def test_precise_query_pod(self, create_project, create_job):
        # 捕获异常，不对异常作处理,每隔5秒查询一次任务状态
        res = ''
        i = 0
        while i < 60:
            try:
                res = project_steps.step_get_job_detail(create_project, create_job)
                if res.json()['items'][0]['status']['succeeded'] == 2:
                    break
            except KeyError:
                time.sleep(3)
                i = i + 3
        uid = res.json()['items'][0]['metadata']['uid']
        # 查看任务的资源状态，并获取容器组名称
        response = project_steps.step_get_job_pods(create_project, uid)
        pod_name = response.json()['items'][0]['metadata']['name']
        # 在项目中查询pod信息
        r = project_steps.step_get_pod_info(create_project, pod_name)
        # 验证查询到的容器名称
        pytest.assume(r.json()['items'][0]['metadata']['name'] == pod_name)

    @allure.story('应用负载-容器组')
    @allure.title('按名称模糊查询存在的容器组')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_query_pod(self, create_project, create_job):
        # 捕获异常，不对异常作处理,每隔5秒查询一次任务状态
        i = 0
        while i < 60:
            try:
                res = project_steps.step_get_job_detail(create_project, create_job)
                if res.json()['items'][0]['status']['succeeded'] == 2:
                    break
            except KeyError:
                time.sleep(3)
                i = i + 3
        pod_name = create_job
        # 在项目中查询pod信息
        r = project_steps.step_get_pod_info(create_project, pod_name)
        # 验证查询到的容器数量
        pytest.assume(r.json()['totalItems'] == 2)

    @allure.story('应用负载-容器组')
    @allure.title('按名称查询不存在的容器组')
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_no_pod(self):
        pod_name = 'test123'  # 不存在的容器组名称
        # 查询容器组
        response = project_steps.step_get_pod(self.project_name, pod_name)
        # 验证查询到的容器名称
        assert response.json()['totalItems'] == 0

    @allure.story('应用负载-容器组')
    @allure.title('查看容器组详情')
    @allure.severity(allure.severity_level.NORMAL)
    def test_check_pod(self, create_project, create_job):
        # 捕获异常，不对异常作处理,每隔5秒查询一次任务状态
        res = ''
        i = 0
        while i < 180:
            try:
                res = project_steps.step_get_job_detail(create_project, create_job)
                if res.json()['items'][0]['status']['succeeded'] == 2:
                    break
            except KeyError:
                time.sleep(5)
                i = i + 5
        # 并获取uid
        uid = res.json()['items'][0]['metadata']['uid']
        # 查看任务的资源状态，并获取容器组名称
        response = project_steps.step_get_job_pods(create_project, uid)
        pod_name = response.json()['items'][0]['metadata']['name']

        r = project_steps.step_get_pod_detail(create_project, pod_name)
        # 验证查询结果
        pytest.assume(r.json()['status']['phase'] == 'Succeeded')

    @allure.story('应用负载-容器组')
    @allure.title('删除状态为已完成的容器组')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_pod(self, create_project, create_job):
        # 捕获异常，不对异常作处理,每隔5秒查询一次任务状态
        res = ''
        i = 0
        while i < 60:
            try:
                res = project_steps.step_get_job_detail(create_project, create_job)
                if res.json()['items'][0]['status']['succeeded'] == 2:
                    break
            except Exception as e:
                print(e)
            finally:
                time.sleep(5)
                i = i + 5
        # 并获取uid
        uid = res.json()['items'][0]['metadata']['uid']
        re = project_steps.step_get_job_pods(create_project, uid)  # 查看任务的资源状态，并获取容器组名称
        pod_name = re.json()['items'][0]['metadata']['name']
        response = project_steps.step_delete_pod(create_project, pod_name)
        # 验证删除操作成功
        pytest.assume(response.json()['status']['phase'] == 'Succeeded')

    @allure.story('应用负载-容器组')
    @allure.title('删除不存在的容器组')
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_pod_no(self):
        pod_name = 'pod-test'
        response = project_steps.step_delete_pod(self.project_name, pod_name)
        # 验证删除失败
        assert response.json()['status'] == 'Failure'

    @allure.story('应用负载-任务')
    @allure.title('删除状态为运行中的任务')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_running_job(self, create_project, create_job):
        # 查看任务并验证其状态
        count = 0
        i = 0
        while i < 60:
            try:
                response = project_steps.step_get_job_detail(create_project, create_job)
                count = response.json()['items'][0]['status']['active']
                if count:
                    break
            except Exception as e:
                print(e)
                i += 1
                time.sleep(1)
        # 运行中的pod数为2
        pytest.assume(count == 2)
        # 删除任务
        project_steps.step_delete_job(create_project, create_job)
        # 在列表中查询任务，验证查询结果为空
        re = project_steps.step_get_assign_job(create_project, 'name', create_job)
        pytest.assume(re.json()['totalItems'] == 0)

    @allure.story('应用负载-任务')
    @allure.title('删除状态为已完成的任务')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_job(self, create_project, create_job):
        i = 0
        while i < 200:
            # 查看任务详情，并获取其完成pod数量,当完成数量为2时，表示已完成
            re = project_steps.step_get_job_detail(create_project, create_job)
            completions = re.json()['items'][0]['spec']['completions']
            if completions == 2:
                break
        # 删除任务,并获取结果
        project_steps.step_delete_job(create_project, create_job)
        # 在列表中查询任务，验证查询结果为空
        response = project_steps.step_get_assign_job(create_project, 'name', create_job)
        pytest.assume(response.json()['totalItems'] == 0)

    @allure.story('应用负载-任务')
    @allure.title('删除不存在的任务')
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_job_no(self):
        job_name = 'test123'
        # 删除任务
        response = project_steps.step_delete_job(self.project_name, job_name)
        # 验证删除结果
        result = response.json()['status']
        assert result == 'Failure'

    @allure.story('应用负载-工作负载')
    @allure.title('创建未绑定存储卷的deployment，并验证运行成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_workload(self, create_project, workload_name, container_name, create_workload):
        condition = 'name=' + workload_name  # 查询条件
        # 在工作负载列表中查询创建的工作负载，并验证其状态为运行中，最长等待时间60s
        status = ''
        i = 0
        while i < 60:
            response = project_steps.step_get_workload(project_name=create_project, type='deployments',
                                                       condition=condition)
            status = response.json()['items'][0]['status']
            # 验证资源的所有副本已就绪
            if 'unavailableReplicas' not in status:
                break
            time.sleep(1)
            i = i + 1
        pytest.assume('unavailableReplicas' not in status)
        # 删除工作负载
        project_steps.step_delete_workload(create_project, 'deployments', workload_name)
        # 等待工作负载删除成功，再删除项目
        j = 0
        while j < 300:
            r = project_steps.step_get_workload(create_project, type='deployments', condition=condition)
            if r.json()['totalItems'] == 0:
                break
            else:
                time.sleep(3)
                j += 3

    @allure.story('应用负载-工作负载')
    @allure.title('按状态查询存在的deployment')
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_deployment_by_status(self, create_project, workload_name, create_workload):
        condition = 'status=running'
        name = ''
        i = 0
        while i < 120:
            try:
                # 按名称精确查询deployment
                response = project_steps.step_get_workload(create_project, type='deployments', condition=condition)
                # 获取并验证deployment的名称正确
                name = response.json()['items'][0]['metadata']['name']
                if name:
                    break
            except Exception as e:
                print(e)
                time.sleep(2)
                i += 2
        with assume:
            assert name == workload_name
        # 删除deployment
        project_steps.step_delete_workload(project_name=create_project, type='deployments', work_name=workload_name)
        # 等待工作负载删除成功，再删除项目
        j = 0
        while j < 300:
            r = project_steps.step_get_workload(create_project, type='deployments', condition=condition)
            if r.json()['totalItems'] == 0:
                break
            else:
                time.sleep(3)
                j += 3

    @allure.story('应用负载-工作负载')
    @allure.title('按名称查询存在的deployment')
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_deployment_by_name(self, create_project, workload_name, create_workload):
        conndition = 'name=' + workload_name  # 查询条件
        # 按名称精确查询deployment
        time.sleep(3)
        response = project_steps.step_get_workload(create_project, type='deployments', condition=conndition)
        # 获取并验证deployment的名称正确
        name = response.json()['items'][0]['metadata']['name']
        pytest.assume(name == workload_name)
        # 删除deployment
        project_steps.step_delete_workload(project_name=create_project, type='deployments', work_name=workload_name)
        # 等待工作负载删除成功，再删除项目
        j = 0
        while j < 300:
            try:
                r = project_steps.step_get_workload(create_project, type='deployments',
                                                    condition='name=' + workload_name)
                if r.json()['totalItems'] == 0:
                    break
            except Exception as e:
                print(e)
            finally:
                time.sleep(3)
                j += 3

    @allure.story('应用负载-工作负载')
    @allure.title('创建未绑定存储卷的StatefulSets，并验证运行成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_statefulsets(self, create_project, workload_name, container_name):
        image = 'nginx'  # 镜像名称
        replicas = 2  # 副本数
        condition = 'name=' + workload_name  # 查询条件
        volume_info = []
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]
        service_port = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]
        service_name = 'service' + workload_name
        volumemounts = []
        # 创建工作负载
        project_steps.step_create_stateful(project_name=create_project, work_name=workload_name,
                                           container_name=container_name,
                                           image=image, replicas=replicas, volume_info=volume_info, ports=port,
                                           service_ports=service_port, volumemount=volumemounts,
                                           service_name=service_name)

        # 在工作负载列表中查询创建的工作负载，并验证其状态为运行中，最长等待时间60s
        time.sleep(3)
        readyReplicas = 0
        i = 3
        while i < 60:
            response = project_steps.step_get_workload(project_name=create_project, type='statefulsets',
                                                       condition=condition)
            try:
                readyReplicas = response.json()['items'][0]['status']['readyReplicas']
                # 验证资源的所有副本已就绪
                if readyReplicas == replicas:
                    break
            except Exception as e:
                print(e)
            time.sleep(1)
            i = i + 1
        pytest.assume(readyReplicas == replicas)
        # 删除工作负载
        project_steps.step_delete_workload(project_name=create_project, type='statefulsets', work_name=workload_name)
        # 等待工作负载删除成功，再删除项目
        j = 0
        while j < 300:
            r = project_steps.step_get_workload(create_project, type='statefulsets', condition=condition)
            if r.json()['totalItems'] == 0:
                break
            else:
                time.sleep(3)
                j += 3

    @allure.story('应用负载-工作负载')
    @allure.title('按名称查询存在的StatefulSets')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_statefulstes_by_name(self, create_project, workload_name, container_name):
        condition = 'name=' + workload_name
        type = 'statefulsets'
        image = 'nginx'  # 镜像名称
        replicas = 2  # 副本数
        volume_info = []
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]
        service_port = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]
        service_name = 'service' + workload_name
        volumemounts = []
        # 创建工作负载
        project_steps.step_create_stateful(project_name=create_project, work_name=workload_name,
                                           container_name=container_name,
                                           image=image, replicas=replicas, volume_info=volume_info, ports=port,
                                           service_ports=service_port, volumemount=volumemounts,
                                           service_name=service_name)

        # 按名称精确查询statefulsets
        time.sleep(1)
        response = project_steps.step_get_workload(create_project, type=type, condition=condition)
        # 获取并验证deployment的名称正确
        name = response.json()['items'][0]['metadata']['name']
        pytest.assume(name == workload_name)
        # 删除创建的statefulsets
        project_steps.step_delete_workload(project_name=create_project, type=type, work_name=workload_name)
        # 等待工作负载删除成功，再删除项目
        j = 0
        while j < 300:
            r = project_steps.step_get_workload(create_project, type='statefulsets', condition=condition)
            if r.json()['totalItems'] == 0:
                break
            else:
                time.sleep(3)
                j += 3

    @allure.story('应用负载-工作负载')
    @allure.title('按状态查询存在的StatefulSets')
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_statefulstes_by_status(self, create_project, workload_name, container_name):
        condition = 'status=running'
        type = 'statefulsets'
        image = 'nginx'  # 镜像名称
        replicas = 2  # 副本数
        volume_info = []
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]
        service_port = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]
        service_name = 'service' + workload_name
        volumemounts = []
        # 创建工作负载
        project_steps.step_create_stateful(project_name=create_project, work_name=workload_name,
                                           container_name=container_name,
                                           image=image, replicas=replicas, volume_info=volume_info, ports=port,
                                           service_ports=service_port, volumemount=volumemounts,
                                           service_name=service_name)

        # 查询工作负载，直至其状态为运行中
        i = 0
        while i < 60:
            r = project_steps.step_get_workload(create_project, type=type, condition='name=' + workload_name)
            try:
                readyReplicas = r.json()['items'][0]['status']['readyReplicas']
                if readyReplicas == replicas:
                    break
            except Exception as e:
                print(e)
            i += 1
            time.sleep(1)
        # 按状态精确查询statefulsets
        response = project_steps.step_get_workload(create_project, type=type, condition=condition)
        # 获取工作负载的名称
        name = response.json()['items'][0]['metadata']['name']
        # 验证deployment的名称正确
        pytest.assume(workload_name == name)
        # 删除创建的statefulsets
        re = project_steps.step_delete_workload(project_name=create_project, type=type, work_name=workload_name)
        pytest.assume(re.json()['status'] == 'Success')
        # 等待工作负载删除成功，再删除项目
        j = 0
        while j < 300:
            r = project_steps.step_get_workload(create_project, type='statefulsets', condition=condition)
            if r.json()['totalItems'] == 0:
                break
            else:
                time.sleep(3)
                j += 3

    @allure.story('应用负载-工作负载')
    @allure.title('创建未绑定存储卷的DaemonSets，并验证运行成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_daemonsets(self, create_project, workload_name, container_name):
        image = 'nginx'  # 镜像名称
        condition = 'name=' + workload_name  # 查询条件
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80}]  # 容器的端口信息
        volume_info = []
        volumemount = []
        # 获取集群中所有的节点数
        res = cluster_steps.step_get_node_all()
        cluster_node_all = res.json()['totalItems']
        # 获取所有没有污点的节点数量
        cluster_node_no_taint = 0
        for i in range(0, cluster_node_all):
            try:
                if res.json()['items'][i]['spec']['taints']:
                    cluster_node_no_taint += 1
            except Exception as e:
                print(e)
        # 创建工作负载
        project_steps.step_create_daemonset(project_name=create_project, work_name=workload_name,
                                            container_name=container_name, image=image, ports=port,
                                            volume_info=volume_info, volumemount=volumemount)
        # 在工作负载列表中查询创建的工作负载，并验证其状态为运行中，最长等待时间180s
        numberReady = ''
        i = 0
        while i < 180:
            response = project_steps.step_get_workload(project_name=create_project, type='daemonsets',
                                                       condition=condition)
            numberReady = response.json()['items'][0]['status']['numberReady']  # 验证资源的所有副本已就绪
            # 验证资源的所有副本已就绪
            if numberReady == cluster_node_no_taint:
                break
            time.sleep(30)
            i = i + 30
        with assume:
            assert numberReady == cluster_node_no_taint
        # 删除创建的daemonsets
        project_steps.step_delete_workload(project_name=create_project, type='daemonsets', work_name=workload_name)
        # 等待工作负载删除成功，再删除项目
        j = 0
        while j < 300:
            r = project_steps.step_get_workload(create_project, type='daemonsets', condition=condition)
            if r.json()['totalItems'] == 0:
                break
            else:
                time.sleep(3)
                j += 3

    @allure.story('应用负载-工作负载')
    @allure.title('按名称查询存在的DaemonSets')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_daemonsets_by_name(self, create_project, workload_name, container_name):
        condition = 'name=' + workload_name
        image = 'nginx'  # 镜像名称
        type = 'daemonsets'
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80}]  # 容器的端口信息
        volume_info = []
        volumemount = []
        # 创建工作负载
        project_steps.step_create_daemonset(project_name=create_project, work_name=workload_name,
                                            container_name=container_name, image=image, ports=port,
                                            volume_info=volume_info, volumemount=volumemount)
        # 按名称查询DaemonSets
        name = ''
        i = 0
        while i < 60:
            try:
                response = project_steps.step_get_workload(create_project, type=type, condition=condition)
                # 获取并验证deployment的名称正确
                name = response.json()['items'][0]['metadata']['name']
                if name:
                    break
            except Exception as e:
                print(e)
            finally:
                i += 3
                time.sleep(3)
        with assume:
            assert name == workload_name
        # 删除创建的daemonsets
        re = project_steps.step_delete_workload(project_name=create_project, type=type, work_name=workload_name)
        with assume:
            assert re.json()['status'] == 'Success'
        # 等待工作负载删除成功，再删除项目
        j = 0
        while j < 300:
            r = project_steps.step_get_workload(create_project, type='daemonsets', condition=condition)
            if r.json()['totalItems'] == 0:
                break
            else:
                time.sleep(3)
                j += 3

    @allure.story('应用负载-工作负载')
    @allure.title('按状态查询存在的DaemonSets')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_daemonsets_by_name(self, workload_name, container_name):
        name = ''
        condition = 'status=running'
        image = 'nginx'  # 镜像名称
        type = 'daemonsets'
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80}]  # 容器的端口信息
        volume_info = []
        volumemount = []
        # 创建工作负载
        project_steps.step_create_daemonset(project_name=self.project_name, work_name=workload_name,
                                            container_name=container_name, image=image, ports=port,
                                            volume_info=volume_info, volumemount=volumemount)
        i = 0
        while i < 120:
            try:
                # 按名称查询DaemonSets
                response = project_steps.step_get_workload(self.project_name, type=type, condition=condition)
                # 获取并验证daemonsets的名称正确
                name = response.json()['items'][0]['metadata']['name']
                if name:
                    break
            except Exception as e:
                print(e)
                i += 5
                time.sleep(5)
        with assume:
            assert name == workload_name
        # 删除创建的daemonsets
        project_steps.step_delete_workload(project_name=self.project_name, type=type, work_name=workload_name)

    @allure.story('应用负载-服务')
    @allure.title('创建未绑定存储卷的service，并验证运行成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_service(self, workload_name, container_name, strategy_info):
        port_service = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]  # service的端口信息
        image = 'nginx'  # 镜像名称
        condition = 'name=' + workload_name  # 查询deploy和service条件
        port_deploy = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]  # 容器的端口信息
        volumeMounts = []  # 设置挂载的存储卷
        replicas = 2  # 副本数
        volume_info = []
        # 创建service
        project_steps.step_create_service(self.project_name, workload_name, port_service)
        # 创建service绑定的deployment
        project_steps.step_create_deploy(project_name=self.project_name, work_name=workload_name,
                                         container_name=container_name,
                                         ports=port_deploy, volumemount=volumeMounts, image=image, replicas=replicas,
                                         volume_info=volume_info, strategy=strategy_info)
        # 验证service创建成功
        response = project_steps.step_get_workload(self.project_name, type='services', condition=condition)
        name = response.json()['items'][0]['metadata']['name']
        with assume:
            assert name == workload_name
        # 验证deploy创建成功
        time.sleep(3)
        re = project_steps.step_get_workload(self.project_name, type='deployments', condition=condition)
        # 获取并验证deployment的名称正确
        name = re.json()['items'][0]['metadata']['name']
        assert name == workload_name

    @allure.story('应用负载-服务')
    @allure.title('删除service，并验证删除成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_service(self, workload_name):
        port_service = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]  # service的端口信息
        condition = 'name=' + workload_name  # 查询service的条件
        # 创建service
        project_steps.step_create_service(self.project_name, workload_name, port_service)
        # 验证service创建成功
        response = project_steps.step_get_workload(self.project_name, type='services', condition=condition)
        name = response.json()['items'][0]['metadata']['name']
        with assume:
            assert name == workload_name
        # 删除service
        project_steps.step_delete_service(self.project_name, workload_name)
        # 验证service删除成功
        response = project_steps.step_get_workload(self.project_name, type='services', condition=condition)
        count = response.json()['totalItems']
        assert count == 0

    @allure.story('应用负载-应用路由')
    @allure.title('为服务创建应用路由')
    def test_create_route(self, create_project, workload_name, container_name, strategy_info):
        # 创建服务
        port_service = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]  # service的端口信息
        image = 'nginx'  # 镜像名称
        condition = 'name=' + workload_name  # 查询deploy和service条件
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
        # 验证service创建成功
        response = project_steps.step_get_workload(create_project, type='services', condition=condition)
        name = response.json()['items'][0]['metadata']['name']
        with assume:
            assert name == workload_name
        # 验证deploy创建成功
        time.sleep(3)
        re = project_steps.step_get_workload(create_project, type='deployments', condition=condition)
        # 获取并验证deployment的名称正确
        name = re.json()['items'][0]['metadata']['name']
        with assume:
            assert name == workload_name
        # 为服务创建路由
        ingress_name = 'ingress' + str(commonFunction.get_random())
        host = 'www.test.com'
        service_info = {"name": workload_name, "port": {"number": 80}}
        project_steps.step_create_route(project_name=create_project, ingress_name=ingress_name,
                                        host=host, service_info=service_info)
        # 查询应用路由，并获取名称
        res = project_steps.step_get_route(create_project, 'name=' + ingress_name)
        na = res.json()['items'][0]['metadata']['name']
        # 验证路由创建成功
        with assume:
            assert na == ingress_name
        # 删除路由
        project_steps.step_delete_route(create_project, ingress_name)
        # 删除服务
        project_steps.step_delete_service(create_project, workload_name)
        # 删除deployment
        project_steps.step_delete_deployment(create_project, workload_name)

    @allure.story('项目设置-网关设置')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('type, title',
                             [('NodePort', '在未开启集群网关的前提下开启项目网关并设置类型为NodePort'),
                              ('LoadBalancer', '在未开启集群网关的前提下开启项目网关并设置类型为LoadBalancer')
                              ])
    def test_create_project_gateway(self, type, title, create_project):
        status = 'true'  # 链路追踪开启状态
        # 创建网关
        project_steps.step_create_gateway(create_project, type, status)
        # 查看项目网关，并验证网关类型
        response = project_steps.step_get_gateway(create_project)
        type_actual = response.json()[0]['spec']['service']['type']
        pytest.assume(type_actual == type)
        # 关闭网关
        project_steps.step_delete_gateway(create_project)
        time.sleep(10)

    @allure.story('项目设置-网关设置')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('project_type, cluster_type, title',
                             [
                                 ('LoadBalancer', 'NodePort', '在已开启集群网关的前提下开启项目网关并设置类型为LoadBalancer'),
                                 ('NodePort', 'NodePort', '在已开启集群网关的前提下开启项目网关并设置类型为NodePort'),
                                 ('NodePort', 'LoadBalancer', '在已开启集群网关的前提下开启项目网关并设置类型为NodePort'),
                                 ('LoadBalancer', 'LoadBalancer', '在已开启集群网关的前提下开启项目网关并设置类型为LoadBalancer')
                             ])
    def test_create_project_gateway_after_cluster(self, project_type, cluster_type, title, create_project):
        # 开启集群网关
        cluster_steps.step_open_cluster_gateway(cluster_type)
        status = 'true'  # 链路追踪开启状态
        # 创建网关
        response = project_steps.step_create_gateway(create_project, project_type, status)
        result = response.text
        # 验证创建结果
        with assume:
            assert result == "can't create project gateway if global gateway enabled\n"
        # 关闭集群网关
        cluster_steps.step_delete_cluster_gateway()

    @allure.story('项目设置-网关设置')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('project_type, cluster_type, title',
                             [('NodePort', 'LoadBalancer', '在已开启项目网关的前提下开启集群网关并设置类型为NodePort'),
                              ('LoadBalancer', 'LoadBalancer', '在已开启项目网关的前提下开启集群网关并设置类型为LoadBalancer'),
                              ('NodePort', 'NodePort', '在已开启项目网关的前提下开启集群网关并设置类型为NodePort'),
                              ('LoadBalancer', 'NodePort', '在已开启项目网关的前提下开启集群网关并设置类型为LoadBalancer')
                              ])
    def test_create_cluster_gateway_after_project(self, project_type, cluster_type, title, create_project):
        status = 'true'  # 链路追踪开启状态
        # 创建项目网关
        project_steps.step_create_gateway(create_project, project_type, status)
        # 创建集群网关
        cluster_steps.step_open_cluster_gateway(cluster_type)
        # 在项目中查看网关信息
        response = project_steps.step_get_gateway(create_project)
        cluster_gateway_name = response.json()[0]['metadata']['name']
        project_gateway_name = response.json()[1]['metadata']['name']
        # 验证网关名称
        pytest.assume(cluster_gateway_name == 'kubesphere-router-kubesphere-system')
        pytest.assume(project_gateway_name == 'kubesphere-router-' + create_project)
        # 关闭项目网关
        project_steps.step_delete_gateway(create_project)
        # 关闭集群网关
        cluster_steps.step_delete_cluster_gateway()
        time.sleep(10)

    @allure.story('项目设置-网关设置')
    @allure.title('将网关类型修改为LoadBalancer并编辑供应商、注解和配置信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_edit_gateway_lb(self, create_project):
        type_old = 'NodePort'
        status = 'false'
        # 创建网关
        project_steps.step_create_gateway(create_project, type_old, status)
        # 查询网关并获取网关的uid和resourceversion
        time.sleep(3)
        response = project_steps.step_get_gateway(create_project)
        uid = response.json()[0]['metadata']['uid']
        reVersion = response.json()[0]['metadata']['resourceVersion']
        # 修改网关类型为LoadBalancer,并编辑供应商、注解和配置信息
        provider = 'QingCloud Kubernetes Engine'
        annotations = {"service.beta.kubernetes.io/qingcloud-load-balancer-eip-ids": "",
                       "service.beta.kubernetes.io/qingcloud-load-balancer-type": "0"}
        configuration = {"qw": "12"}
        status_new = 'true'
        project_steps.step_edit_gateway_lb(create_project, uid, reVersion, provider, annotations, configuration,
                                           status_new)
        # 验证网关编辑成功
        response = project_steps.step_get_gateway(create_project)
        type_actual = response.json()[0]['spec']['service']['type']
        pytest.assume(type_actual == 'LoadBalancer')
        # 删除网关
        project_steps.step_delete_gateway(create_project)

    @allure.story('项目设置-网关设置')
    @allure.title('将网关类型修改为NodePort并编辑配置信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_edit_gateway_np(self, create_project):
        type_old = 'LoadBalancer'
        status = 'true'
        # 创建网关
        project_steps.step_create_gateway(create_project, type_old, status)
        # 查询网关并获取网关的uid和resourceversion
        time.sleep(1)
        response = project_steps.step_get_gateway(create_project)
        uid = response.json()[0]['metadata']['uid']
        reVersion = response.json()[0]['metadata']['resourceVersion']
        # 修改网关类型为NodePort,并编辑配置信息
        configuration = {"qa": "test"}
        status_new = 'false'
        project_steps.step_edit_gateway_np(create_project, uid, reVersion, configuration, status_new)
        # 验证网关编辑成功
        re = project_steps.step_get_gateway(create_project)
        type_actual = re.json()[0]['spec']['service']['type']
        pytest.assume(type_actual == 'NodePort')
        # 删除网关
        project_steps.step_delete_gateway(create_project)

    @allure.story('应用负载-工作负载')
    @allure.title('修改工作负载副本并验证运行正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_add_work_replica(self, create_project, workload_name, create_workload):
        time.sleep(5)
        replicas = 3  # 副本数
        # 修改副本数
        project_steps.step_modify_work_replicas(project_name=create_project, work_name=workload_name,
                                                replicas=replicas)
        # 获取工作负载中所有的容器组，并验证其运行正常，最长等待时间60s
        status_test = []  # 创建一个对比数组
        for j in range(replicas):
            status_test.append('Running')
        status = ''
        i = 0
        while i < 60:
            status = project_steps.step_get_work_pod_status(project_name=create_project, work_name=workload_name)
            if status == status_test:
                break
            else:
                time.sleep(3)
                i = i + 3
        pytest.assume(status == status_test)
        # 删除deployment
        project_steps.step_delete_workload(project_name=create_project, type='deployments', work_name=workload_name)
        # 等待工作负载删除成功，再删除项目
        j = 0
        while j < 300:
            r = project_steps.step_get_workload(create_project, type='deployments', condition='name=' + workload_name)
            if r.json()['totalItems'] == 0:
                break
            else:
                time.sleep(3)
                j += 3

    @allure.story('应用负载-工作负载')
    @allure.title('按状态查询存在的工作负载')
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_work_by_status(self, create_project, workload_name, create_workload):
        condition = 'status=running'
        count = 0
        i = 0
        while i < 60:
            try:
                # 按状态查询工作负载
                response = project_steps.step_get_workload(create_project, 'deployments', condition)
                count = response.json()['totalItems']
                if count:
                    break
                i += 3
                time.sleep(3)
            except Exception as e:
                print(e)
        pytest.assume(count == 1)
        # 删除deployment
        project_steps.step_delete_workload(project_name=create_project, type='deployments', work_name=workload_name)
        # 等待工作负载删除成功，再删除项目
        j = 0
        while j < 300:
            r = project_steps.step_get_workload(create_project, type='deployments', condition=condition)
            if r.json()['totalItems'] == 0:
                break
            else:
                time.sleep(3)
                j += 3

    @allure.story('应用负载-工作负载')
    @allure.title('按名称精确查询存在的工作负载')
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_workload_by_name(self, create_project, workload_name, create_workload):
        condition = 'name=' + workload_name
        # 按名称查询工作负载
        name_actual = ''
        i = 0
        try:
            while i < 60:
                response = project_steps.step_get_workload(create_project, 'deployments', condition)
                name_actual = response.json()['items'][0]['metadata']['name']
                if name_actual:
                    break
                else:
                    time.sleep(3)
                    i += 3
        except Exception as e:
            print(e)
        # 验证查询结果
        pytest.assume(name_actual == workload_name)
        # 删除deployment
        project_steps.step_delete_workload(project_name=create_project, type='deployments', work_name=workload_name)
        # 等待工作负载删除成功，再删除项目
        j = 0
        while j < 300:
            r = project_steps.step_get_workload(create_project, type='deployments', condition=condition)
            if r.json()['totalItems'] == 0:
                break
            else:
                time.sleep(3)
                j += 3

    @allure.story('应用负载-工作负载')
    @allure.title('按名称模糊查询存在的工作负载')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_query_work_by_name(self, create_project, workload_name, create_workload):
        condition = 'name=workload'
        # 按状态查询工作负载
        response = project_steps.step_get_workload(create_project, 'deployments', condition)
        name_actual = response.json()['items'][0]['metadata']['name']
        # 验证查询结果
        pytest.assume(name_actual == workload_name)
        # 删除deployment
        project_steps.step_delete_workload(project_name=create_project, type='deployments', work_name=workload_name)
        # 等待工作负载删除成功，再删除项目
        j = 0
        while j < 300:
            r = project_steps.step_get_workload(create_project, type='deployments', condition=condition)
            if r.json()['totalItems'] == 0:
                break
            else:
                time.sleep(3)
                j += 3

    @allure.story('应用负载-工作负载')
    @allure.title('按名称查询不存在的工作负载')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_query_work_by_name_no(self):
        condition = 'name=demo123'
        # 按状态查询工作负载
        response = project_steps.step_get_workload(self.project_name, 'deployments', condition)
        # 验证查询结果
        assert response.json()['totalItems'] == 0

    @allure.story('应用负载-工作负载')
    @allure.title('工作负载设置弹性伸缩')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_work_by_status(self, create_project, workload_name, create_workload):
        condition = 'name=' + workload_name
        # 设置弹性伸缩
        response = project_steps.step_set_auto_scale(create_project, workload_name)
        # 验证设置成功
        pytest.assume(response.json()['kind'] == 'HorizontalPodAutoscaler')
        # 删除工作负载
        project_steps.step_delete_workload(create_project, 'deployments', workload_name)
        # 等待工作负载删除成功，再删除项目
        j = 0
        while j < 300:
            r = project_steps.step_get_workload(create_project, type='deployments', condition=condition)
            if r.json()['totalItems'] == 0:
                break
            else:
                time.sleep(3)
                j += 3

    @allure.story('应用负载-工作负载')
    @allure.title('删除工作负载')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_workload(self, create_project, workload_name, create_workload):
        # 按名称查询工作负载
        condition = 'name=' + workload_name
        response = project_steps.step_get_workload(create_project, 'deployments', condition)
        pytest.assume(response.json()['totalItems'] == 1)
        # 删除工作负载
        project_steps.step_delete_workload(create_project, 'deployments', workload_name)
        # 验证删除成功
        # 按名称查询工作负载
        re = project_steps.step_get_workload(create_project, 'deployments', condition)
        pytest.assume(re.json()['totalItems'] == 0)

    @allure.story('配置中心-服务账号')
    @allure.title('创建sa并验证sa内容正确、生成的密钥正确、然后删除sa')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_sa(self, create_project):
        sa_name = 'satest'
        # 步骤1：创建sa
        project_steps.step_create_sa(project_name=create_project, sa_name=sa_name)
        # 步骤2：验证sa创建成功并返回secret
        sa_secret = ''
        i = 0
        while i < 60:
            try:
                response = project_steps.step_get_sa(project_name=create_project, sa_name=sa_name)
                if response.json()['totalItems'] > 0:
                    sa_secret = response.json()['items'][0]['secrets'][0]['name']
                    break
                i += 3
                time.sleep(3)
            except Exception as e:
                print(e)
        # 步骤3：查询sa详情
        project_steps.step_get_sa_detail(project_name=create_project, sa_name=sa_name)
        # 步骤4：查询sa的密钥信息并返回密钥类型
        secret_type = \
        project_steps.step_get_secret(project_name=create_project, secret_name=sa_secret).json()['items'][0]['type']
        with assume:
            assert secret_type == 'kubernetes.io/service-account-token'
        # 步骤5：删除sa
        project_steps.step_delete_sa(project_name=create_project, sa_name=sa_name)
        # 步骤6：验证删除成功
        num = project_steps.step_get_sa(project_name=create_project, sa_name=sa_name).json()['totalItems']
        with assume:
            assert num == 0

    @allure.story('存储管理-存储卷')
    @allure.title('删除存在的存储卷，并验证删除成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_volume(self, create_project):
        # 创建存储卷
        volume_name = 'volume' + str(commonFunction.get_random())
        project_steps.step_create_volume(create_project, volume_name)
        # 删除存储卷
        project_steps.step_delete_volume(create_project, volume_name)
        # 查询被删除的存储卷
        i = 0
        # 验证存储卷被删除，最长等待时间为30s
        response = ''
        while i < 60:
            response = project_steps.step_get_volume(create_project, volume_name)
            # 存储卷快照的状态为布尔值，故先将结果转换成字符类型
            if response.json()['totalItems'] == 0:
                break
            time.sleep(1)
            i = i + 1
        # 验证存储卷删除成功
        with assume:
            assert response.json()['totalItems'] == 0

    @allure.story('项目设置-基本信息')
    @allure.title('编辑项目信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_edit_project(self):
        alias_name = 'test-231313!#!G@#K!G#G!PG#'  # 别名信息
        description = '测试test123！@#'  # 描述信息
        # 编辑项目信息
        response = project_steps.step_edit_project(self.ws_name, self.project_name, alias_name, description)
        # 验证编辑成功
        assert response.status_code == 200

    @allure.story('项目设置-项目配额')
    @allure.title('只设置项目配额-CPU')
    def test_edit_project_quota_cpu(self):
        # 配额信息
        hard = {"limits.cpu": "11",
                "requests.cpu": "1"
                }
        # 获取项目配额的resource_version
        resource_version = project_steps.step_get_project_quota_version(self.project_name)
        # 编辑配额信息
        project_steps.step_edit_project_quota(self.project_name, hard, resource_version)
        hard_actual = ''
        i = 0
        while i < 60:
            try:
                # 获取修改后的配额信息
                response = project_steps.step_get_project_quota(self.project_name)
                hard_actual = response.json()['data']['hard']
                if hard_actual:
                    break
            except Exception as e:
                print(e)
                i += 2
                time.sleep(2)
        # 验证配额修改成功
        assert hard_actual == hard

    @allure.story('项目设置-项目配额')
    @allure.title('设置项目配额-输入错误的cpu信息(包含字母)')
    def test_edit_project_quota_wrong_cpu(self):
        # 配额信息,错误的cpu信息
        hard = {"limits.cpu": "11www",
                "requests.cpu": "1www"
                }
        # 获取项目配额的resource_version
        resource_version = project_steps.step_get_project_quota_version(self.project_name)
        # 编辑配额信息
        r = project_steps.step_edit_project_quota(self.project_name, hard, resource_version)
        # 获取编辑结果
        status = r.json()['status']
        # 验证编辑失败
        assert status == 'Failure'

    @allure.story('项目设置-项目配额')
    @allure.title('设置项目配额-输入错误的cpu信息(包含负数)')
    def test_edit_project_quota_wrong_cpu_1(self):
        # 配额信息,错误的cpu信息
        hard = {"limits.cpu": "-11",
                "requests.cpu": "1"
                }
        # 获取项目配额的resource_version
        resource_version = project_steps.step_get_project_quota_version(self.project_name)
        # 编辑配额信息
        r = project_steps.step_edit_project_quota(self.project_name, hard, resource_version)
        # 获取编辑结果
        status = r.json()['status']
        # 验证编辑失败
        assert status == 'Failure'

    @allure.story('项目设置-项目配额')
    @allure.title('只设置项目配额-内存')
    def test_edit_project_quota_memory(self, create_project):
        # 配额信息
        hard = {"limits.memory": "10Gi", "requests.memory": "1Gi"}
        # 获取项目配额的resource_version
        resource_version = project_steps.step_get_project_quota_version(create_project)
        # 编辑配额信息
        project_steps.step_edit_project_quota(create_project, hard, resource_version)
        # 获取修改后的配额信息
        response = project_steps.step_get_project_quota(create_project)
        hard_actual = response.json()['data']['hard']
        # 验证配额修改成功
        with assume:
            assert hard_actual == hard

    @allure.story('项目设置-项目配额')
    @allure.title('设置项目配额-输入错误的内存(包含非单位字母)')
    def test_edit_project_quota_wrong_memory(self):
        # 配额信息
        hard = {"limits.memory": "10Gi", "requests.memory": "1Gi"}
        # 获取项目配额的resource_version
        resource_version = project_steps.step_get_project_quota_version(self.project_name)
        # 编辑配额信息
        response = project_steps.step_edit_project_quota(self.project_name, hard, resource_version)
        # 获取编辑结果
        status = response.json()['status']
        # 验证编辑失败
        assert status == 'Failure'

    @allure.story('项目设置-项目配额')
    @allure.title('设置项目配额-输入错误的内存(包含负数)')
    def test_edit_project_quota_wrong_memory(self):
        # 配额信息
        hard = {"limits.memory": "-10Gi", "requests.memory": "1Gi"}
        # 获取项目配额的resource_version
        resource_version = project_steps.step_get_project_quota_version(self.project_name)
        # 编辑配额信息
        response = project_steps.step_edit_project_quota(self.project_name, hard, resource_version)
        # 获取编辑结果
        status = response.json()['status']
        # 验证编辑失败
        assert status == 'Failure'

    @allure.story('项目设置-项目配额')
    @allure.title('设置项目配额-CPU、内存')
    def test_edit_project_quota_cpu_memory(self):
        # 配额信息
        hard = {"limits.memory": "10Gi", "requests.memory": "1Gi",
                "limits.cpu": "10", "requests.cpu": "1"}
        # 获取项目配额的resource_version
        resource_version = project_steps.step_get_project_quota_version(self.project_name)
        # 编辑配额信息
        project_steps.step_edit_project_quota(self.project_name, hard, resource_version)
        # 获取修改后的配额信息
        response = project_steps.step_get_project_quota(self.project_name)
        hard_actual = response.json()['data']['hard']
        # 验证配额修改成功
        assert hard_actual == hard

    @allure.story('项目设置-项目配额')
    @allure.title('只设置项目配额-资源配额')
    def test_edit_project_quota_resource(self, create_project):
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
        # 获取项目配额的resource_version
        resource_version = project_steps.step_get_project_quota_version(create_project)
        # 修改资源配额
        project_steps.step_edit_project_quota(create_project, hard, resource_version)
        # 获取修改后的配额信息
        hard_actual = ''
        i = 0
        while i < 60:
            try:
                response = project_steps.step_get_project_quota(create_project)
                hard_actual = response.json()['data']['hard']
                if hard_actual:
                    break
                i += 3
                time.sleep(3)
            except Exception as e:
                print(e)
        # 验证配额修改成功
        with assume:
            assert hard_actual == hard

    @allure.story('项目设置-项目配额')
    @allure.title('只设置项目配额-输入错误的资源配额信息(包含字母)')
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
        # 获取项目配额的resource_version
        resource_version = project_steps.step_get_project_quota_version(self.project_name)
        # 修改资源配额
        response = project_steps.step_edit_project_quota(self.project_name, hard, resource_version)
        # 获取编辑结果
        status = response.json()['status']
        # 验证编辑失败
        assert status == 'Failure'

    @allure.story('项目设置-项目配额')
    @allure.title('只设置项目配额-输入错误的资源配额信息(包含负数)')
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
        # 获取项目配额的resource_version
        resource_version = project_steps.step_get_project_quota_version(self.project_name)
        # 修改资源配额
        response = project_steps.step_edit_project_quota(self.project_name, hard, resource_version)
        # 获取编辑结果
        status = response.json()['status']
        # 验证编辑失败
        assert status == 'Failure'

    @allure.story('项目设置-项目配额')
    @allure.title('设置项目配额-cpu、memory、资源配额')
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
                "limits.cpu": "20", "limits.memory": "100Gi",
                "requests.cpu": "2", "requests.memory": "3Gi"}
        # 获取项目配额的resource_version
        resource_version = project_steps.step_get_project_quota_version(self.project_name)
        # 修改资源配额
        project_steps.step_edit_project_quota(self.project_name, hard, resource_version)
        # 获取修改后的配额信息
        response = project_steps.step_get_project_quota(self.project_name)
        hard_actual = response.json()['data']['hard']
        # 验证配额修改成功
        assert hard_actual == hard

    @allure.story('项目设置-资源默认请求')
    @allure.title('只设置资源默认请求-cpu')
    def test_edit_container_quota_cpu(self):
        # 获取资源默认请求
        response = project_steps.step_get_container_quota(self.project_name, self.ws_name)
        name = ''
        resource_version = None
        try:
            if response.json()['items'][0]['metadata']['name']:
                name = response.json()['items'][0]['metadata']['name']
                resource_version = response.json()['items'][0]['metadata']['resourceVersion']
            else:
                name = None
                resource_version = None
        except Exception as e:
            print(e)
        # 编辑资源默认请求
        limit = {"cpu": "16"}
        request = {"cpu": "2"}
        project_steps.step_edit_container_quota(self.project_name, name, resource_version, limit, request)
        # 查询编辑结果
        response = project_steps.step_get_container_quota(self.project_name, self.ws_name)
        limit_actual = response.json()['items'][0]['spec']['limits'][0]['default']
        request_actual = response.json()['items'][0]['spec']['limits'][0]['defaultRequest']
        # 验证编辑成功
        assert limit == limit_actual
        assert request == request_actual

    @allure.story('项目设置-资源默认请求')
    @allure.title('只设置资源默认请求-输入错误的cpu信息(包含字母)')
    def test_edit_container_quota_wrong_cpu(self):
        # 获取资源默认请求
        response = project_steps.step_get_container_quota(self.project_name, self.ws_name)
        name = ''
        resource_version = None
        try:
            if response.json()['items'][0]['metadata']['name']:
                name = response.json()['items'][0]['metadata']['name']
                resource_version = response.json()['items'][0]['metadata']['resourceVersion']
            else:
                name = None
                resource_version = None
        except Exception as e:
            print(e)
        # 编辑资源默认请求
        limit = {"cpu": "16aa"}
        request = {"cpu": "2"}
        r = project_steps.step_edit_container_quota(self.project_name, name, resource_version, limit, request)
        # 获取编辑结果
        status = r.json()['status']
        # 验证编辑失败
        assert status == 'Failure'

    @allure.story('项目设置-资源默认请求')
    @allure.title('只设置资源默认请求-输入错误的cpu信息(包含负数)')
    def test_edit_container_quota_wrong_cpu_1(self):
        # 获取资源默认请求
        response = project_steps.step_get_container_quota(self.project_name, self.ws_name)
        name = ''
        resource_version = None
        try:
            if response.json()['items'][0]['metadata']['name']:
                name = response.json()['items'][0]['metadata']['name']
                resource_version = response.json()['items'][0]['metadata']['resourceVersion']
            else:
                name = None
                resource_version = None
        except Exception as e:
            print(e)
        # 编辑资源默认请求
        limit = {"cpu": "-16"}
        request = {"cpu": "2"}
        r = project_steps.step_edit_container_quota(self.project_name, name, resource_version, limit, request)
        # 获取编辑结果
        status = r.json()['status']
        # 验证编辑失败
        assert status == 'Failure'

    @allure.story('项目设置-资源默认请求')
    @allure.title('只设置资源默认请求-内存')
    def test_edit_container_quota_memory(self):
        # 获取资源默认请求
        response = project_steps.step_get_container_quota(self.project_name, self.ws_name)
        name = ''
        resource_version = None
        try:
            if response.json()['items'][0]['metadata']['name']:
                name = response.json()['items'][0]['metadata']['name']
                resource_version = response.json()['items'][0]['metadata']['resourceVersion']
            else:
                name = None
                resource_version = None
        except Exception as e:
            print(e)
        # 编辑资源默认请求
        limit = {"memory": "1000Mi"}
        request = {"memory": "1Mi"}
        project_steps.step_edit_container_quota(self.project_name, name, resource_version, limit, request)
        # 查询编辑结果
        response = project_steps.step_get_container_quota(self.project_name, self.ws_name)
        limit_actual = response.json()['items'][0]['spec']['limits'][0]['default']
        request_actual = response.json()['items'][0]['spec']['limits'][0]['defaultRequest']
        # 验证编辑成功
        with assume:
            assert limit == limit_actual
        with assume:
            assert request == request_actual

    @allure.story('项目设置-资源默认请求')
    @allure.title('只设置资源默认请求-输入错误的内存信息(包含非单位字母)')
    def test_edit_container_quota_wrong_memory(self):
        # 获取资源默认请求
        response = project_steps.step_get_container_quota(self.project_name, self.ws_name)
        name = ''
        resource_version = None
        try:
            if response.json()['items'][0]['metadata']['name']:
                name = response.json()['items'][0]['metadata']['name']
                resource_version = response.json()['items'][0]['metadata']['resourceVersion']
            else:
                name = None
                resource_version = None
        except Exception as e:
            print(e)
        # 编辑资源默认请求
        limit = {"memory": "100aMi"}
        request = {"memory": "1Mi"}
        r = project_steps.step_edit_container_quota(self.project_name, name, resource_version, limit, request)
        # 获取编辑结果
        status = r.json()['status']
        # 验证编辑失败
        assert status == 'Failure'

    @allure.story('项目设置-资源默认请求')
    @allure.title('只设置资源默认请求-输入错误的内存信息(包含负数)')
    def test_edit_container_quota_wrong_memory_1(self):
        # 获取资源默认请求
        response = project_steps.step_get_container_quota(self.project_name, self.ws_name)
        name = ''
        resource_version = None
        try:
            if response.json()['items'][0]['metadata']['name']:
                name = response.json()['items'][0]['metadata']['name']
                resource_version = response.json()['items'][0]['metadata']['resourceVersion']
            else:
                name = None
                resource_version = None
        except Exception as e:
            print(e)
        # 编辑资源默认请求
        limit = {"memory": "-100Mi"}
        request = {"memory": "1Mi"}
        r = project_steps.step_edit_container_quota(self.project_name, name, resource_version, limit, request)
        # 获取编辑结果
        status = r.json()['status']
        # 验证编辑失败
        assert status == 'Failure'

    @allure.story('项目设置-资源默认请求')
    @allure.title('只设置资源默认请求-内存、cpu')
    def test_edit_container_quota_memory(self):
        # 获取资源默认请求
        response = project_steps.step_get_container_quota(self.project_name, self.ws_name)
        name = ''
        resource_version = None
        try:
            if response.json()['items'][0]['metadata']['name']:
                name = response.json()['items'][0]['metadata']['name']
                resource_version = response.json()['items'][0]['metadata']['resourceVersion']
            else:
                name = None
                resource_version = None
        except Exception as e:
            print(e)
        # 编辑资源默认请求
        limit = {"cpu": "15", "memory": "1000Mi"}
        request = {"cpu": "2", "memory": "1Mi"}
        project_steps.step_edit_container_quota(self.project_name, name, resource_version, limit, request)
        # 查询编辑结果
        response = project_steps.step_get_container_quota(self.project_name, self.ws_name)
        limit_actual = response.json()['items'][0]['spec']['limits'][0]['default']
        request_actual = response.json()['items'][0]['spec']['limits'][0]['defaultRequest']
        # 验证编辑成功
        assert limit == limit_actual
        assert request == request_actual

    @allure.story('项目设置-基本信息')
    @allure.title('删除项目，并验证删除成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_project(self, create_project):
        # 删除创建的项目
        project_steps.step_delete_project(self.ws_name, create_project)
        # 验证项目删除结果，最长等待时间为60s
        response = ''
        i = 0
        while i < 60:
            response = project_steps.step_get_project(self.ws_name, create_project)
            if response.json()['totalItems'] == 0:
                break
            time.sleep(2)
            i = i + 2
        assert response.json()['totalItems'] == 0

    @allure.story('项目设置-日志收集')
    @allure.title('开启日志收集，然后将其关闭')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_open_logsidecar(self):
        # 开启日志收集
        project_steps.step_set_logsidecar(self.ws_name, self.project_name, status='enabled')
        # 查看并验证日志收集状态
        response = project_steps.step_get_status_logsidecar(self.project_name)
        status_actual = response.json()['metadata']['labels']['logging.kubesphere.io/logsidecar-injection']
        with assume:
            assert status_actual == 'enabled'
        # 关闭日志收集
        project_steps.step_set_logsidecar(self.ws_name, self.project_name, status='disabled')
        # 查看并验证日志收集状态
        response = project_steps.step_get_status_logsidecar(self.project_name)
        status_actual = response.json()['metadata']['labels']['logging.kubesphere.io/logsidecar-injection']
        assert status_actual == 'disabled'

    @allure.title('{title}')  # 设置用例标题
    @allure.severity(allure.severity_level.CRITICAL)  # 设置用例优先级
    # 将用例信息以参数化的方式传入测试方法
    @pytest.mark.parametrize('id,url,params,data,story,title,method,severity,condition,except_result', parametrize)
    def test_project(self, id, url, params, data, story, title, method, severity, condition, except_result):

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
        # 执行excel中的用例
        commonFunction.request_resource(url, params, data, story, title, method, severity, condition, except_result)


if __name__ == "__main__":
    pytest.main(['-s', 'test_project.py'])  # -s参数是为了显示用例的打印信息。 -q参数只显示结果，不显示过程
