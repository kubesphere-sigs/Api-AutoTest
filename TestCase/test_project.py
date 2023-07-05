# -- coding: utf-8 --
import allure
import pytest
import sys
import time

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from common.getData import DoexcleByPandas
from common import commonFunction
from step import project_steps, platform_steps, workspace_steps, cluster_steps


@allure.feature('Project')
@pytest.mark.skipif(commonFunction.check_multi_cluster() is True, reason='多集群环境下不执行')
class TestProject(object):
    if commonFunction.check_multi_cluster() is True:
        # 如果为多集群环境，则不会collect该class的所有用例。 __test__ = False
        __test__ = False
    else:
        __test__ = True

    volume_name = 'testvolume'  # 存储卷名称，在创建、删除存储卷时使用,excle中的用例也用到了这个存储卷
    user_name = 'user-for-test-project'  # 系统用户名称
    user_role = 'platform-self-provisioner'  # 用户角色
    email = 'qq' + str(commonFunction.get_random()) + '@qq.com'
    password = 'P@88w0rd'
    ws_name = 'ws-for-test-project' + str(commonFunction.get_random())
    project_name = 'test-project' + str(commonFunction.get_random())
    # 获取集群的默认存储类
    storage_class = cluster_steps.step_get_cluster_default_storage_class()
    # 项目名称，从yaml中获取的测试用例中用到了这个项目名称
    project_name_for_exel = 'test-project-for-exel' + str(commonFunction.get_random())
    # 从文件中读取用例信息
    parametrize = DoexcleByPandas().get_data_from_yaml(filename='../data/project.yaml')

    # 所有用例执行之前执行该方法
    def setup_class(self):
        platform_steps.step_create_user(self.user_name, self.user_role, self.email, self.password)  # 创建一个用户
        workspace_steps.step_create_workspace(self.ws_name)  # 创建一个企业空间
        workspace_steps.step_invite_user(self.ws_name, self.user_name, self.ws_name + '-viewer')  # 将创建的用户邀请到企业空间
        project_steps.step_create_project(self.ws_name, self.project_name)  # 创建一个project工程
        project_steps.step_create_project(self.ws_name, self.project_name_for_exel)  # 创建一个project工程用于执行excle中的用例
        project_steps.step_create_volume(self.project_name_for_exel, self.volume_name, self.storage_class)  # 创建存储卷

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
                time.sleep(10)
                i += 10
        project_steps.step_delete_project(self.ws_name, self.project_name_for_exel)
        time.sleep(5)

        workspace_steps.step_delete_workspace(self.ws_name)  # 删除创建的企业空间
        platform_steps.step_delete_user(self.user_name)  # 删除创建的用户

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
        volume_mounts = [{"name": type_name, "readOnly": False, "mountPath": "/data"}]  # 设置挂载的存储卷
        volume_info = [{"name": type_name, "persistentVolumeClaim": {"claimName": volume_name}}]  # 存储卷的信息
        # 创建存储卷
        project_steps.step_create_volume(create_project, volume_name, self.storage_class)
        # 创建资源并将存储卷绑定到资源
        project_steps.step_create_deploy(create_project, work_name=workload_name, image=image, replicas=replicas,
                                         container_name=container_name, volume_info=volume_info, ports=port,
                                         volumemount=volume_mounts, strategy=strategy_info)
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
        with pytest.assume:
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
                time.sleep(10)
                j += 10
        project_steps.step_delete_pvc(create_project, volume_name)
        # 等待pvc删除成功，再删除项目
        k = 0
        while k < 300:
            r = project_steps.step_get_volume(create_project, volume_name)
            if r.json()['totalItems'] == 0:
                break
            else:
                time.sleep(10)
                k += 10

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
        volume_mounts = [{"name": type_name, "readOnly": False, "mountPath": "/data"}]
        volume_info = [{"name": type_name, "persistentVolumeClaim": {"claimName": volume_name}}]  # 存储卷的信息
        # 创建存储卷
        project_steps.step_create_volume(create_project, volume_name, self.storage_class)
        # 创建资源并将存储卷绑定到资源
        project_steps.step_create_stateful(project_name=create_project, work_name=workload_name,
                                           container_name=container_name,
                                           image=image, replicas=replicas, ports=port, service_ports=service_port,
                                           volumemount=volume_mounts, volume_info=volume_info,
                                           service_name=service_name)
        # 验证资源创建成功
        ready_replicas = 0
        i = 0
        while i < 120:
            # 获取工作负载的状态
            response = project_steps.step_get_workload(create_project, type='statefulsets', condition=condition)
            try:
                ready_replicas = response.json()['items'][0]['status']['readyReplicas']
            except Exception as e:
                print(e)
            # 验证资源的所有副本已就绪
            if ready_replicas == replicas:
                break
            else:
                time.sleep(10)
                i += 10
        # 获取存储卷状态
        response = project_steps.step_get_volume_status(create_project, volume_name)
        status = response.json()['items'][0]['status']['phase']
        # 验证存储卷状态正常
        with pytest.assume:
            assert status == 'Bound'
        # 删除工作负载
        project_steps.step_delete_workload(create_project, 'statefulsets', workload_name)
        # 等待工作负载删除成功，再删除pvc
        j = 0
        while j < 300:
            re = project_steps.step_get_workload(create_project, type='statefulsets', condition=condition)
            if re.json()['totalItems'] == 0:
                break
            else:
                time.sleep(10)
                j += 10
        project_steps.step_delete_pvc(create_project, volume_name)
        # 等待pvc删除成功，再删除项目
        k = 0
        while k < 300:
            r = project_steps.step_get_volume(create_project, volume_name)
            if r.json()['totalItems'] == 0:
                break
            else:
                time.sleep(10)
                k += 10

    @allure.story('存储管理-存储卷')
    @allure.title('创建daemonsets并使用hostpath存储卷，最后验证资源和存储卷的状态正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_volume_for_daemonsets(self, create_project, workload_name, container_name):
        volume_name = 'volume-deamon' + str(commonFunction.get_random())  # 存储卷的名称
        image = 'redis'  # 镜像名称
        condition = 'name=' + workload_name  # 查询条件
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80}]  # 容器的端口信息
        volume_mounts = [{"name": volume_name, "readOnly": False, "mountPath": "/data"}]  # 设置挂载哦的存储卷
        volume_info = [{"hostPath": {"path": "/data"}, "name": volume_name}]  # 存储卷的信息
        # 获取集群中所有的节点数
        res = cluster_steps.step_get_node_all()
        cluster_node_all = res.json()['totalItems']
        # 获取所有没有污点的节点数量
        cluster_node_with_taint = 0
        for i in range(0, cluster_node_all):
            try:
                if res.json()['items'][i]['spec']['taints']:
                    cluster_node_with_taint += 1
            except Exception as e:
                print(e)
        # 创建资源并将存储卷绑定到资源
        project_steps.step_create_daemonset(create_project, work_name=workload_name, image=image,
                                            container_name=container_name, volume_info=volume_info, ports=port,
                                            volumemount=volume_mounts)
        # 验证资源创建成功
        number_ready = ''
        i = 0
        while i < 180:
            # 获取工作负载的状态
            response = project_steps.step_get_workload(create_project, type='daemonsets', condition=condition)
            number_ready = response.json()['items'][0]['status']['numberReady']  # 验证资源的所有副本已就绪
            if number_ready == cluster_node_all - cluster_node_with_taint:
                break
            else:
                time.sleep(30)
                i += 30
        with pytest.assume:
            assert number_ready == cluster_node_all - cluster_node_with_taint

        # 删除工作负载
        project_steps.step_delete_workload(create_project, 'daemonsets', workload_name)
        # 等待工作负载删除成功，再删除pvc
        j = 0
        while j < 300:
            re = project_steps.step_get_workload(create_project, type='daemonsets', condition=condition)
            if re.json()['totalItems'] == 0:
                break
            else:
                time.sleep(10)
                j += 10
        project_steps.step_delete_pvc(create_project, volume_name)
        # 等待pvc删除成功，再删除项目
        k = 0
        while k < 300:
            r = project_steps.step_get_volume(create_project, volume_name)
            if r.json()['totalItems'] == 0:
                break
            else:
                time.sleep(10)
                k += 10

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
        volume_mounts = [{"name": type_name, "readOnly": False, "mountPath": "/data"}]  # 设置挂载哦的存储卷
        volume_info = [{"name": type_name, "persistentVolumeClaim": {"claimName": volume_name}}]  # 存储卷的信息
        replicas = 2  # 副本数
        # 创建存储卷
        project_steps.step_create_volume(create_project, volume_name, self.storage_class)
        # 创建service
        project_steps.step_create_service(create_project, workload_name, port_service)
        # 创建service绑定的deployment
        project_steps.step_create_deploy(project_name=create_project, work_name=workload_name,
                                         container_name=container_name,
                                         ports=port_deploy, volumemount=volume_mounts, image=image, replicas=replicas,
                                         volume_info=volume_info, strategy=strategy_info)
        # 验证service创建成功
        response = project_steps.step_get_workload(create_project, type='services', condition=condition)
        name = response.json()['items'][0]['metadata']['name']
        with pytest.assume:
            assert name == workload_name
        # 验证deploy创建成功
        ready_replicas = 0
        i = 0
        while i < 180:
            re = project_steps.step_get_workload(create_project, type='deployments', condition=condition)
            # 获取并验证deployment创建成功
            try:
                ready_replicas = re.json()['items'][0]['status']['readyReplicas']
            except Exception as e:
                print(e)
            if ready_replicas == replicas:
                break
            else:
                time.sleep(10)
                i += 10
        # 获取存储卷状态
        response = project_steps.step_get_volume_status(create_project, volume_name)
        status = response.json()['items'][0]['status']['phase']
        # 验证存储卷状态正常
        with pytest.assume:
            assert status == 'Bound'

        # 删除工作负载
        project_steps.step_delete_workload(create_project, 'deployments', workload_name)
        # 等待工作负载删除成功，再删除pvc
        j = 0
        while j < 300:
            re = project_steps.step_get_workload(create_project, type='deployments', condition=condition)
            if re.json()['totalItems'] == 0:
                break
            else:
                time.sleep(10)
                j += 10
        project_steps.step_delete_pvc(create_project, volume_name)
        # 等待pvc删除成功，再删除项目
        k = 0
        while k < 300:
            r = project_steps.step_get_volume(create_project, volume_name)
            if r.json()['totalItems'] == 0:
                break
            else:
                time.sleep(10)
                k += 10

    @allure.story("项目设置-项目角色")
    @allure.title('查看项目默认的所有角色')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_project_role_all(self, create_project):
        # 查看项目中的所有角色
        r = project_steps.step_get_role(create_project)
        assert r.json()['totalItems'] == 3  # 验证初始的角色数量为3

    @allure.story("项目设置-项目角色")
    @allure.title('查找项目中指定的角色')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_role_one(self, create_project):
        role_name = 'viewer'
        r = project_steps.step_get_role(create_project, role_name)
        assert r.json()['items'][0]['metadata']['name'] == role_name  # 验证查询的角色结果为viewer

    @allure.story("项目设置-项目角色")
    @allure.title('查找项目中不存在的角色')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_role_none(self, create_project):
        role_name = 'viewer123'
        response = project_steps.step_get_role(create_project, role_name)
        assert response.json()['totalItems'] == 0  # 验证查询到的结果为空

    @allure.story("项目设置-项目角色")
    @allure.title('模糊查找项目中的角色')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_role_fuzzy(self, create_project):
        role_name = 'adm'
        r = project_steps.step_get_role(create_project, role_name)
        assert r.json()['totalItems'] == 1  # 验证查询到的结果数量为1
        # 验证查找到的角色
        assert r.json()['items'][0]['metadata']['name'] == 'admin'

    @allure.story("项目设置-项目角色")
    @allure.title('在项目中创建角色')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_role_create(self, create_project_role, create_project):
        # 查看角色
        r = project_steps.step_get_role(create_project, create_project_role)
        assert r.json()['totalItems'] == 1

    @allure.story("项目设置-项目角色")
    @allure.title('在项目中创建角色-角色名称为空')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_role_create_name_none(self, create_project):
        role_name = ''
        r = project_steps.step_create_role(create_project, role_name)
        # 验证创建角色失败的异常提示信息
        assert r.text.strip() == 'Role.rbac.authorization.k8s.io "" is invalid: metadata.name: Required value: name or generateName is required'

    @allure.story("项目设置-项目角色")
    @allure.title('项目中编辑角色基本信息')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_role_edit_info(self, create_project_role, create_project):
        alias_name = '我是别名'  # 别名
        # 角色信息
        annotations = {"iam.kubesphere.io/aggregation-roles": "[\"role-template-view-basic\"]",
                       "kubesphere.io/alias-name": alias_name,
                       "kubesphere.io/creator": "admin",
                       "kubesphere.io/description": "我是描述信息"}
        resource_version = ''
        # 编辑角色
        project_steps.step_edit_project_role(create_project, create_project_role, resource_version, annotations)
        time.sleep(1)
        # 查看角色
        r = project_steps.step_get_role(create_project, create_project_role)
        assert r.json()['items'][0]['metadata']['annotations']['kubesphere.io/alias-name'] == alias_name  # 验证修改后的别名
        assert r.json()['items'][0]['metadata']['annotations'][
                   'kubesphere.io/description'] == '我是描述信息'  # 验证修改后的描述信息

    @allure.story("项目设置-项目角色")
    @allure.title('项目中编辑角色的权限信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_project_role_edit_authority(self, create_project):
        # 创建项目角色
        role_name = 'role' + str(commonFunction.get_random())
        project_steps.step_create_role(create_project, role_name)
        time.sleep(1)
        # 获取角色的resource_version
        response = project_steps.step_get_project_role(create_project, role_name)
        resource_version = response.json()['items'][0]['metadata']['resourceVersion']
        # 编辑角色的权限
        authority = '["role-template-view-basic","role-template-view-volumes","role-template-view-secrets",' \
                    '"role-template-view-configmaps","role-template-view-snapshots","role-template-view-app-workloads"]'
        annotations = {"iam.kubesphere.io/aggregation-roles": authority,
                       "kubesphere.io/alias-name": "",
                       "kubesphere.io/creator": "admin", "kubesphere.io/description": ""}
        project_steps.step_edit_project_role(create_project, role_name, resource_version, annotations)
        time.sleep(1)
        # 查看角色
        r = project_steps.step_get_role(create_project, role_name)
        # 验证修改后的权限信息
        with pytest.assume:
            assert r.json()['items'][0]['metadata']['annotations']['iam.kubesphere.io/aggregation-roles'] == authority
        # 删除项目角色
        project_steps.step_project_delete_role(create_project, role_name)

    @allure.story("项目设置-项目角色")
    @allure.title('项目中删除角色')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_project_delete_role(self, create_project_role, create_project):
        # 验证角色创建成功
        time.sleep(3)
        response = project_steps.step_get_project_role(create_project, create_project_role)
        count = response.json()['totalItems']
        with pytest.assume:
            assert count == 1
        # 删除角色
        project_steps.step_project_delete_role(create_project, create_project_role)
        # 验证角色删除成功
        r = project_steps.step_get_project_role(create_project, create_project_role)
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
        assert name == 'admin'  # 验证默认的用户仅有admin

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
    @allure.title('查找项目不存在的用户')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_user_none(self):
        user_condition = 'wx-ad'
        r = project_steps.step_get_project_member(self.project_name, user_condition)
        assert r.json()['totalItems'] == 0  # 验证查找的结果为空

    @allure.story("项目设置-项目成员")
    @allure.title('邀请用户到project')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_project_invite_user(self):
        # 将用户邀请到项目
        role = 'viewer'
        project_steps.step_invite_member(self.project_name, self.user_name, role)
        role_actual = ''
        i = 0
        while i < 120:
            try:
                # 查看项目成员，并获取其角色
                response = project_steps.step_get_project_member(self.project_name, self.user_name)
                role_actual = response.json()['items'][0]['metadata']['annotations']['iam.kubesphere.io/role']
                if role_actual:
                    break
            except Exception as e:
                print(e)
                i += 5
                time.sleep(5)
        assert role_actual == role

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
        i = 0
        role_actual = ''
        while i < 60:
            try:
                # 查看项目成员，并获取其角色
                response = project_steps.step_get_project_member(self.project_name, self.user_name)
                role_actual = response.json()['items'][0]['metadata']['annotations']['iam.kubesphere.io/role']
                if len(role_actual) > 0:
                    break
            except Exception as e:
                print(e)
                i += 3
                time.sleep(3)
        assert role_actual == role  # 验证修改后的用户角色

    @allure.story("项目设置-项目成员")
    @allure.title('删除project的成员')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_project_delete_user(self, create_user, create_ws, create_project):
        workspace_steps.step_invite_user(create_ws, create_user, create_ws + '-viewer')  # 将创建的用户邀请到企业空间
        # 将用户邀请到项目
        role = 'admin'
        project_steps.step_invite_member(create_project, create_user, role)
        # 查看项目成员，并验证添加成功
        name = ''
        i = 0
        while i < 60:
            try:
                res = project_steps.step_get_project_member(create_project, create_user)
                name = res.json()['items'][0]['metadata']['name']
                if name:
                    break
            except Exception as e:
                print(e)
                i += 5
                time.sleep(5)
        with pytest.assume:
            assert name == create_user
        # 移出项目成员
        project_steps.step_remove_project_member(create_project, create_user)
        # 查询被移出的成员
        response = project_steps.step_get_project_member(create_project, create_user)
        count = response.json()['totalItems']
        # 验证查询结果为空
        assert count == 0

    # 以下4条用例的执行结果应当为false，未已test开头表示未执行。接口没有对角色的名称做限制
    @allure.title('项目中创建角色-名称中包含大写字母')
    @allure.severity(allure.severity_level.NORMAL)
    def wx_test_project_role_create_name(self):
        project_role_name = 'WX'
        project_steps.step_create_role(self.project_name, project_role_name)

    @allure.title('项目中创建角色-名称中包含非分隔符("-")的特殊符号')
    @allure.severity(allure.severity_level.NORMAL)
    def wx_test_project_role_create_name1(self):
        project_role_name = 'w@x'
        project_steps.step_create_role(self.project_name, project_role_name)

    @allure.title('项目中创建角色-名称以分隔符("-")开头')
    @allure.severity(allure.severity_level.NORMAL)
    def wx_test_project_role_create_name2(self):
        project_role_name = '-wx'
        project_steps.step_create_role(self.project_name, project_role_name)

    @allure.title('项目中创建角色-名称以分隔符("-")结尾')
    @allure.severity(allure.severity_level.NORMAL)
    def wx_test_project_role_create_name3(self):
        project_role_name = 'wx-'
        project_steps.step_create_role(self.project_name, project_role_name)

    @allure.story('应用负载-任务')
    @allure.title('创建任务，并验证运行正常')
    @allure.description('创建一个计算圆周率的任务')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_job(self, create_project, create_job):
        # 查看任务详情
        response = project_steps.step_get_job_detail(create_project, create_job)
        # 获取任务uid
        uid = response.json()['items'][0]['metadata']['uid']
        # 获取任务中指定的容器组完成数量
        completions = response.json()['items'][0]['spec']['completions']
        # 等待任务完成
        if project_steps.step_get_job_status_complete(create_project, create_job, completions):
            # 查看任务的资源状态，并获取第一个容器组的名称
            re = project_steps.step_get_job_pods(create_project, uid)
            pod_name = re.json()['items'][0]['metadata']['name']
            # 查看任务的第一个容器的运行日志，并验证任务的运行结果
            logs = project_steps.step_get_pods_log(create_project, pod_name, create_job)
            assert '3.1415926' in logs
        else:
            pytest.xfail('任务运行失败')

    @allure.story('应用负载-任务')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.parametrize('job_name, title',
                             [('Test', '任务名称中包含大写字母'),
                              ('te@st', '任务名称中包含符号'),
                              ('test-', '任务名称以-结束'),
                              ('-test', '任务名称以-开始')]
                             )
    def test_create_job_wrong_name(self, job_name, title, create_project):
        # 创建任务并验证结果失败
        assert project_steps.step_create_job(create_project, job_name).json()['status'] == 'Failure'

    @allure.story('应用负载-任务')
    @allure.title('按名称模糊查询存在的任务')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_job(self, create_project, create_job):
        project_steps.step_create_job(create_project, create_job)
        # 模糊查询存在的任务
        response = project_steps.step_get_assign_job(create_project, 'name', create_job[1:])
        assert response.json()['totalItems'] == 1

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
                time.sleep(5)
                i = i + 5
        response = project_steps.step_get_assign_job(create_project, 'status', 'completed')  # 查询指定的任务
        # 获取查询结果中job的名称
        job_name_actual = response.json()['items'][0]['metadata']['name']
        # 验证查询结果正确
        assert create_job == job_name_actual

    @allure.story('应用负载-任务')
    @allure.title('按状态查询运行中的任务')
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_job_status_running(self, create_project, create_job):
        # 验证任务状态为运行中
        project_steps.step_get_job_status_run(create_project, create_job)
        # 按状态为运行中查询任务
        response = project_steps.step_get_assign_job(create_project, 'status', 'running')
        # 验证查询结果
        assert response.json()['totalItems'] >= 1

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
                time.sleep(5)
                i = i + 5
        uid = res.json()['items'][0]['metadata']['uid']
        # 查看任务的资源状态，并获取容器组名称
        response = project_steps.step_get_job_pods(create_project, uid)
        pod_name = response.json()['items'][0]['metadata']['name']
        # 在项目中查询pod信息
        r = project_steps.step_get_pod_info(create_project, pod_name)
        # 验证查询到的容器名称
        assert r.json()['items'][0]['metadata']['name'] == pod_name

    @allure.story('应用负载-容器组')
    @allure.title('按名称模糊查询存在的容器组')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_query_pod(self):
        # 在项目中查询pod信息
        r = project_steps.step_get_pod_info('kubesphere-system', 'controller')
        # 验证查询到的容器数量
        assert r.json()['totalItems'] == 1

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
        assert r.json()['status']['phase'] == 'Succeeded'

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
        assert response.json()['status']['phase'] == 'Succeeded'

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
                i += 3
                time.sleep(3)
        # 运行中的pod数为2
        with pytest.assume:
            assert count == 2
        # 删除任务
        project_steps.step_delete_job(create_project, create_job)
        # 在列表中查询任务，验证查询结果为空
        re = project_steps.step_get_assign_job(create_project, 'name', create_job)
        assert re.json()['totalItems'] == 0

    @allure.story('应用负载-任务')
    @allure.title('删除状态为已完成的任务')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_job(self, create_project, create_job):
        i = 0
        while i < 200:
            try:
                # 查看任务详情，并获取其完成pod数量,当完成数量为2时，表示已完成
                re = project_steps.step_get_job_detail(create_project, create_job)
                completions = re.json()['items'][0]['spec']['completions']
                if completions == 2:
                    break
            except Exception as e:
                print(e)
                i += 5
                time.sleep(5)
        # 删除任务,并获取结果
        project_steps.step_delete_job(create_project, create_job)
        # 在列表中查询任务，验证查询结果为空
        response = project_steps.step_get_assign_job(create_project, 'name', create_job)
        assert response.json()['totalItems'] == 0

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
    @allure.title('{title}')
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.parametrize('deploy_name, title',
                             [('tEst', '创建的deployment的名称中包含大写字母'),
                              ('te@st', '创建的deployment的名称中包含符号'),
                              ('test-', '创建的deployment的名称以-结束'),
                              ('-test', '创建的deployment的名称以-开始')])
    def test_create_deployment_wrong_name(self, deploy_name, title, create_project, container_name, strategy_info):
        image = 'nginx'  # 镜像名称
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 81}]  # 容器的端口信息
        volume_mounts = []  # 设置挂载的存储卷
        replicas = 2  # 副本数
        volume_info = []
        # 创建deployment并验证创建失败
        assert project_steps.step_create_deploy(project_name=create_project, work_name=deploy_name,
                                                container_name=container_name, ports=port, volumemount=volume_mounts,
                                                image=image, replicas=replicas, volume_info=volume_info,
                                                strategy=strategy_info).json()['status'] == 'Failure'

    @allure.story('应用负载-工作负载')
    @allure.title('创建未绑定存储卷的deployment，并验证运行成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_workload(self, create_project, workload_name, container_name, create_deployment):
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
            time.sleep(3)
            i = i + 3
        with pytest.assume:
            assert 'unavailableReplicas' not in status
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
    def test_get_deployment_by_status(self, create_project, workload_name, create_deployment):
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
        with pytest.assume:
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
    def test_get_deployment_by_name(self, create_project, workload_name, create_deployment):
        conndition = 'name=' + workload_name  # 查询条件
        # 按名称精确查询deployment
        time.sleep(3)
        response = project_steps.step_get_workload(create_project, type='deployments', condition=conndition)
        # 获取并验证deployment的名称正确
        name = response.json()['items'][0]['metadata']['name']
        with pytest.assume:
            assert name == workload_name
        # 删除deployment
        project_steps.step_delete_workload(project_name=create_project, type='deployments', work_name=workload_name)

    @allure.story('应用负载-工作负载')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.parametrize('workload_name, title',
                             [('tEst', '创建的statefulsets的名称中包含大写字母'),
                              ('te@st', '创建的statefulsets的名称中包含符号'),
                              ('test-', '创建的statefulsets的名称以-结束'),
                              ('-test', '创建的statefulsets的名称以-开始')]
                             )
    def test_create_statefulsets_wrong_name(self, workload_name, title, create_project, container_name):
        image = 'nginx'  # 镜像名称
        replicas = 2  # 副本数
        volume_info = []
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]
        service_port = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]
        service_name = 'service' + workload_name
        volume_mounts = []
        # 创建statefulsets并验证创建失败
        assert project_steps.step_create_stateful(project_name=create_project, work_name=workload_name,
                                                  container_name=container_name,
                                                  image=image, replicas=replicas, volume_info=volume_info, ports=port,
                                                  service_ports=service_port, volumemount=volume_mounts,
                                                  service_name=service_name).json()['status'] == 'Failure'

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
        volume_mounts = []
        # 创建工作负载
        project_steps.step_create_stateful(project_name=create_project, work_name=workload_name,
                                           container_name=container_name,
                                           image=image, replicas=replicas, volume_info=volume_info, ports=port,
                                           service_ports=service_port, volumemount=volume_mounts,
                                           service_name=service_name)

        # 在工作负载列表中查询创建的工作负载，并验证其状态为运行中，最长等待时间60s
        time.sleep(3)
        ready_replicas = 0
        i = 3
        while i < 60:
            response = project_steps.step_get_workload(project_name=create_project, type='statefulsets',
                                                       condition=condition)
            try:
                ready_replicas = response.json()['items'][0]['status']['readyReplicas']
                # 验证资源的所有副本已就绪
                if ready_replicas == replicas:
                    break
            except Exception as e:
                print(e)
            time.sleep(3)
            i = i + 3
        with pytest.assume:
            assert ready_replicas == replicas
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
    def test_get_statefulstes_by_name(self):
        workload_type = 'statefulsets'
        workload_name = 'prometheus-k8s'
        project_name = 'kubesphere-monitoring-system'
        condition = 'name=' + workload_name
        # 按名称精确查询statefulsets
        response = project_steps.step_get_workload(project_name, type=workload_type, condition=condition)
        # 获取并验证deployment的名称正确
        name = response.json()['items'][0]['metadata']['name']
        with pytest.assume:
            assert name == workload_name

    @allure.story('应用负载-工作负载')
    @allure.title('按状态查询存在的StatefulSets')
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_statefulstes_by_status(self):
        project_name = 'kubesphere-monitoring-system'
        condition = 'status=running'
        workload_type = 'statefulsets'
        # 按状态精确查询statefulsets
        response = project_steps.step_get_workload(project_name, type=workload_type, condition=condition)
        # 获取工作负载的数量
        count = response.json()['totalItems']
        # 验证deployment的名称正确
        with pytest.assume:
            assert count > 0

    @allure.story('应用负载-工作负载')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.parametrize('workload_name, title',
                             [('tEst', '创建的DaemonSets的名称中包含大写字母'),
                              ('te@st', '创建的DaemonSets的名称中包含符号'),
                              ('test-', '创建的DaemonSets的名称以-结束'),
                              ('-test', '创建的DaemonSets的名称以-开始')]
                             )
    def test_create_daemonsets_wrong_name(self, workload_name, title, create_project, container_name):
        image = 'nginx'  # 镜像名称
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80}]  # 容器的端口信息
        volume_info = []
        volumemount = []
        # 创建工作负载
        assert project_steps.step_create_daemonset(project_name=create_project, work_name=workload_name,
                                                   container_name=container_name, image=image, ports=port,
                                                   volume_info=volume_info, volumemount=volumemount).json()[
                   'status'] == 'Failure'

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
        cluster_node_with_taint = 0
        for i in range(0, cluster_node_all):
            try:
                if res.json()['items'][i]['spec']['taints']:
                    cluster_node_with_taint += 1
            except Exception as e:
                print(e)
        # 创建工作负载
        project_steps.step_create_daemonset(project_name=create_project, work_name=workload_name,
                                            container_name=container_name, image=image, ports=port,
                                            volume_info=volume_info, volumemount=volumemount)
        # 在工作负载列表中查询创建的工作负载，并验证其状态为运行中，最长等待时间180s
        number_ready = ''
        i = 0
        while i < 180:
            response = project_steps.step_get_workload(project_name=create_project, type='daemonsets',
                                                       condition=condition)
            number_ready = response.json()['items'][0]['status']['numberReady']  # 验证资源的所有副本已就绪
            # 验证资源的所有副本已就绪
            if number_ready == cluster_node_all - cluster_node_with_taint:
                break
            time.sleep(30)
            i = i + 30
        with pytest.assume:
            assert number_ready == cluster_node_all - cluster_node_with_taint
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
        project_name = 'kube-system'
        workload_name = 'kube-proxy'
        condition = 'name=' + workload_name
        workload_type = 'daemonsets'
        # 按名称查询DaemonSets
        response = project_steps.step_get_workload(project_name, type=workload_type, condition=condition)
        # 获取并验证daemonsets的名称正确
        name = response.json()['items'][0]['metadata']['name']
        with pytest.assume:
            assert name == workload_name

    @allure.story('应用负载-工作负载')
    @allure.title('按状态查询存在的DaemonSets')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_daemonsets_by_name(self):
        project_name = 'kube-system'
        condition = 'status=running'
        workload_type = 'daemonsets'
        # 按名称查询DaemonSets
        response = project_steps.step_get_workload(project_name, type=workload_type, condition=condition)
        # 获取并验证daemonsets的数量
        count = response.json()['totalItems']
        with pytest.assume:
            assert count > 0

    @allure.story('应用负载-工作负载')
    @allure.title('按状态查询存在的工作负载')
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_work_by_status(self):
        project_name = 'kubesphere-system'
        condition = 'status=running'
        workload_type = 'deployments'
        # 按状态查询工作负载
        response = project_steps.step_get_workload(project_name, workload_type, condition)
        count = response.json()['totalItems']
        # 验证查询结果
        with pytest.assume:
            assert count > 0

    @allure.story('应用负载-工作负载')
    @allure.title('按名称精确查询存在的工作负载')
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_workload_by_name(self):
        project_name = 'kubesphere-system'
        workload_name = 'ks-console'
        condition = 'name=' + workload_name
        workload_type = 'deployments'
        response = project_steps.step_get_workload(project_name, workload_type, condition)
        name_actual = response.json()['items'][0]['metadata']['name']
        # 验证查询结果
        with pytest.assume:
            assert name_actual == workload_name

    @allure.story('应用负载-工作负载')
    @allure.title('按名称模糊查询存在的工作负载')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_query_work_by_name(self):
        project_name = 'kubesphere-system'
        workload_name = 'ks-cons'
        condition = 'name=' + workload_name
        workload_type = 'deployments'
        response = project_steps.step_get_workload(project_name, workload_type, condition)
        name_actual = response.json()['items'][0]['metadata']['name']
        # 验证查询结果
        with pytest.assume:
            assert name_actual == 'ks-console'

    @allure.story('应用负载-工作负载')
    @allure.title('按名称查询不存在的工作负载')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_query_work_by_name_no(self):
        condition = 'name=demo123'
        # 按状态查询工作负载
        response = project_steps.step_get_workload(self.project_name, 'deployments', condition)
        # 验证查询结果
        assert response.json()['totalItems'] == 0

    @allure.story('应用负载-服务')
    @allure.title('创建、删除service，并验证删除成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_service(self, workload_name, create_project):
        port_service = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]  # service的端口信息
        condition = 'name=' + workload_name  # 查询service的条件
        # 创建service
        project_steps.step_create_service(create_project, workload_name, port_service)
        # 验证service创建成功
        response = project_steps.step_get_workload(create_project, type='services', condition=condition)
        name = response.json()['items'][0]['metadata']['name']
        with pytest.assume:
            assert name == workload_name
        # 删除service
        project_steps.step_delete_service(create_project, workload_name)
        # 验证service删除成功
        response = project_steps.step_get_workload(create_project, type='services', condition=condition)
        count = response.json()['totalItems']
        assert count == 0

    @allure.story('应用负载-服务')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.parametrize('service_name, title',
                             [('tEst', '创建的服务的名称中包含大写字母'),
                              ('te@st', '创建的服务的名称中包含符号'),
                              ('test-', '创建的服务的名称以-结束'),
                              ('-test', '创建的服务的名称以-开始')]
                             )
    def test_create_service_wrong_name(self, service_name, title, create_project):
        # 创建服务并验证创建失败
        port_service = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]  # service的端口信息
        assert project_steps.step_create_service(create_project, service_name, port_service).json()[
                   'status'] == 'Failure'

    @allure.story('应用负载-应用路由')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.parametrize('ingress_name, title',
                             [('tEst', '创建的路由的名称中包含大写字母'),
                              ('te@st', '创建的路由的名称中包含符号'),
                              ('test-', '创建的路由的名称以-结束'),
                              ('-test', '创建的路由的名称以-开始'),
                              ('test', '创建的路由的名称符合规定')]
                             )
    def test_create_route_wrong_name(self, ingress_name, title, create_project, workload_name, container_name,
                                     strategy_info):
        # 创建服务
        port_service = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]  # service的端口信息
        image = 'nginx'  # 镜像名称
        condition = 'name=' + workload_name  # 查询deploy和service条件
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
        # 验证service创建成功
        response = project_steps.step_get_workload(create_project, type='services', condition=condition)
        name = response.json()['items'][0]['metadata']['name']
        with pytest.assume:
            assert name == workload_name
        # 验证deploy创建成功
        time.sleep(3)
        re = project_steps.step_get_workload(create_project, type='deployments', condition=condition)
        # 获取并验证deployment的名称正确
        name = re.json()['items'][0]['metadata']['name']
        with pytest.assume:
            assert name == workload_name
        # 为服务创建路由
        host = 'www.test.com'
        service_info = {"name": workload_name, "port": {"number": 80}}
        if ingress_name == 'test':
            ingress_name = 'ingress' + str(commonFunction.get_random())
            project_steps.step_create_route(project_name=create_project, ingress_name=ingress_name,
                                            host=host, service_info=service_info)
            # 查询应用路由，并获取名称
            res = project_steps.step_get_route(create_project, 'name=' + ingress_name)
            na = res.json()['items'][0]['metadata']['name']
            # 验证路由创建成功
            with pytest.assume:
                assert na == ingress_name
            # 删除路由
            project_steps.step_delete_route(create_project, ingress_name)
        else:
            with pytest.assume:
                assert project_steps.step_create_route(project_name=create_project, ingress_name=ingress_name,
                                                       host=host, service_info=service_info).json()[
                           'status'] == 'Failure'

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
        # 创建项目网关
        project_steps.step_create_gateway(create_project, type, status)
        # 查看项目网关，并验证网关类型
        response = project_steps.step_get_gateway(create_project)
        type_actual = response.json()[0]['spec']['service']['type']
        with pytest.assume:
            assert type_actual == type
        # 关闭网关
        project_steps.step_delete_gateway(create_project)

    @allure.story('项目设置-网关设置')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('project_type, cluster_type, title',
                             [
                                 ('LoadBalancer', 'NodePort',
                                  '在已开启集群网关的前提下开启项目网关并设置类型为LoadBalancer'),
                                 ('NodePort', 'NodePort', '在已开启集群网关的前提下开启项目网关并设置类型为NodePort'),
                                 ('NodePort', 'LoadBalancer',
                                  '在已开启集群网关的前提下开启项目网关并设置类型为NodePort'),
                                 ('LoadBalancer', 'LoadBalancer',
                                  '在已开启集群网关的前提下开启项目网关并设置类型为LoadBalancer')
                             ])
    def test_create_project_gateway_after_cluster(self, project_type, cluster_type, title, create_project):
        # 开启集群网关
        cluster_steps.step_open_cluster_gateway(cluster_type)
        status = 'true'  # 链路追踪开启状态
        # 创建项目网关
        response = project_steps.step_create_gateway(create_project, project_type, status)
        result = response.text
        # 验证创建结果
        with pytest.assume:
            assert result == "can't create project gateway if global gateway enabled\n"
        # 关闭集群网关
        cluster_steps.step_delete_cluster_gateway()
        time.sleep(3)

    @allure.story('项目设置-网关设置')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('project_type, cluster_type, title',
                             [('NodePort', 'LoadBalancer', '在已开启项目网关的前提下开启集群网关并设置类型为NodePort'),
                              ('LoadBalancer', 'LoadBalancer',
                               '在已开启项目网关的前提下开启集群网关并设置类型为LoadBalancer'),
                              ('NodePort', 'NodePort', '在已开启项目网关的前提下开启集群网关并设置类型为NodePort'),
                              ('LoadBalancer', 'NodePort',
                               '在已开启项目网关的前提下开启集群网关并设置类型为LoadBalancer')
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
        with pytest.assume:
            assert cluster_gateway_name == 'kubesphere-router-kubesphere-system'
        with pytest.assume:
            assert project_gateway_name == 'kubesphere-router-' + create_project
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
        # 创建项目网关
        project_steps.step_create_gateway(create_project, type_old, status)
        # 查询网关并获取网关的uid和resource_version
        response = project_steps.step_get_gateway(create_project)
        uid = response.json()[0]['metadata']['uid']
        resource_version = response.json()[0]['metadata']['resourceVersion']
        # 修改网关类型为LoadBalancer,并编辑供应商、注解和配置信息
        provider = 'QingCloud Kubernetes Engine'
        annotations = {"service.beta.kubernetes.io/qingcloud-load-balancer-eip-ids": "",
                       "service.beta.kubernetes.io/qingcloud-load-balancer-type": "0"}
        configuration = {"qw": "12"}
        status_new = 'true'
        project_steps.step_edit_gateway_lb(create_project, uid, resource_version, provider, annotations, configuration,
                                           status_new)
        # 验证网关编辑成功
        response = project_steps.step_get_gateway(create_project)
        type_actual = response.json()[0]['spec']['service']['type']
        with pytest.assume:
            assert type_actual == 'LoadBalancer'
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
        # 查询网关并获取网关的uid和resource_version
        response = project_steps.step_get_gateway(create_project)
        uid = response.json()[0]['metadata']['uid']
        resource_version = response.json()[0]['metadata']['resourceVersion']
        # 修改网关类型为NodePort,并编辑配置信息
        configuration = {"qa": "test"}
        status_new = 'false'
        project_steps.step_edit_gateway_np(create_project, uid, resource_version, configuration, status_new)
        time.sleep(2)
        # 验证网关编辑成功
        re = project_steps.step_get_gateway(create_project)
        type_actual = re.json()[0]['spec']['service']['type']
        with pytest.assume:
            assert type_actual == 'NodePort'
        # 删除网关
        project_steps.step_delete_gateway(create_project)

    @allure.story('应用负载-工作负载')
    @allure.title('修改工作负载副本并验证运行正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_add_work_replica(self, create_project, workload_name, create_deployment):
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
        with pytest.assume:
            assert status == status_test
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
    @allure.title('工作负载设置弹性伸缩')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_work_by_status(self, create_project, workload_name, create_deployment):
        condition = 'name=' + workload_name
        # 设置弹性伸缩
        response = project_steps.step_set_auto_scale(create_project, workload_name)
        # 验证设置成功
        with pytest.assume:
            assert response.json()['kind'] == 'HorizontalPodAutoscaler'
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
    def test_delete_workload(self, create_project, workload_name, create_deployment):
        # 按名称查询工作负载
        condition = 'name=' + workload_name
        response = project_steps.step_get_workload(create_project, 'deployments', condition)
        with pytest.assume:
            assert response.json()['totalItems'] == 1
        # 删除工作负载
        project_steps.step_delete_workload(create_project, 'deployments', workload_name)
        # 按名称查询工作负载，验证删除成功
        re = project_steps.step_get_workload(create_project, 'deployments', condition)
        assert re.json()['totalItems'] == 0

    @allure.story('配置-服务账户')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('role, title',
                             [('operator', '创建的服务账号角色为operator'),
                              ('viewer', '创建的服务账号角色为viewer'),
                              ('admin', '创建的服务账号角色为admin')
                              ])
    def test_create_sa(self, role, title, create_project):
        # 步骤1：创建sa
        sa_name = 'sa-test-' + str(commonFunction.get_random())
        project_steps.step_create_sa(create_project, sa_name, role)
        # 步骤2：验证sa创建成功并返回secret
        i = 0
        while i < 60:
            try:
                response = project_steps.step_get_sa(create_project, sa_name)
                if response.json()['totalItems'] > 0:
                    break
            except Exception as e:
                print(e)
            finally:
                i += 3
                time.sleep(3)
        # 步骤3：查询sa详情
        re = project_steps.step_get_sa_detail(create_project, sa_name)
        # 验证服务账户的角色正确
        with pytest.assume:
            assert re.json()['metadata']['annotations']['iam.kubesphere.io/role'] == role
        # 步骤4：删除sa
        project_steps.step_delete_sa(create_project, sa_name)
        # 步骤5：验证删除成功
        num = project_steps.step_get_sa(create_project, sa_name).json()['totalItems']
        with pytest.assume:
            assert num == 0

    @allure.story('配置-服务账户')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.parametrize('sa_name, title',
                             [('Test', '创建的服务账号名称包括大写字母'),
                              ('', '创建的服务账号无名称'),
                              ('te@st', '创建的服务账号名称包含特殊字符'),
                              ('test-', '创建的服务账号名称以-结尾'),
                              ('-test', '创建的服务账号名称以-开头')
                              ])
    def test_create_sa_wrong_name(self, sa_name, title, create_project):
        # 创建服务账户
        role = 'operator'
        response = project_steps.step_create_sa(create_project, sa_name, role)
        assert response.json()['status'] == 'Failure'

    @allure.story('配置-保密字典')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('type, title, data',
                             [('Opaque', '创建默认类型的保密字典', {"test": "d3g="}),
                              (
                              'kubernetes.io/tls', '创建TLS信息类型的保密字典', {"tls.crt": "cWE=", "tls.key": "cXc="}),
                              ('kubernetes.io/basic-auth', '创建用户名和密码类型的保密字典',
                               {"username": "dGVzdA==", "password": "d3g="}),
                              ('kubernetes.io/dockerconfigjson', '创建镜像服务信息类型的保密字典', {
                                  ".dockerconfigjson": "eyJhdXRocyI6eyJodHRwczovL2RvY2tlci5pbyI6eyJ1c2VybmFtZSI6InRlc3QiLCJwYXNzd29yZCI6Ind4IiwiZW1haWwiOiIiLCJhdXRoIjoiZEdWemREcDNlQT09In19fQ=="})
                              ])
    def test_create_secret(self, type, title, data, create_project):
        # 创建保密字典
        secret_name = 'test-secret-' + str(commonFunction.get_random())
        project_steps.step_create_secret(create_project, secret_name, type, data)
        i = 0
        data_actual = ''
        while i < 60:
            try:
                # 查看保密字典详情
                response = project_steps.step_get_secret(create_project, secret_name)
                # 获取保密字典的数据
                data_actual = response.json()['items'][0]['data']
                if len(data_actual) > 0:
                    break
            except Exception as e:
                print(e)
                i += 1
                time.sleep(1)
        # 验证数据正确
        with pytest.assume:
            assert data == data_actual
        # 删除保密字典
        project_steps.step_delete_secret(create_project, secret_name)

    @allure.story('配置-保密字典')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.parametrize('secret_name, title',
                             [('Test', '创建的保密字典名称包括大写字母'),
                              ('', '创建的保密字典无名称'),
                              ('te@st', '创建的保密字典名称包含特殊字符'),
                              ('test-', '创建的保密字典名称以-结尾'),
                              ('-test', '创建的保密字典名称以-开头')
                              ])
    def test_create_secret_wrong_name(self, secret_name, title, create_project):
        # 创建保密字典
        configuration_type = 'Opaque'
        data = {"test": "d3g="}
        response = project_steps.step_create_secret(create_project, secret_name, configuration_type, data)
        assert response.json()['status'] == 'Failure'

    @allure.story('配置-保密字典')
    @allure.title('删除保密字典')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_secret(self, create_project):
        # 创建保密字典
        secret_name = 'test-secret-' + str(commonFunction.get_random())
        configuration_type = 'Opaque'
        data = {"test": "d3g="}
        project_steps.step_create_secret(create_project, secret_name, configuration_type, data)
        # 验证创建成功
        i = 0
        count = 0
        while i < 60:
            try:
                # 查看保密字典详情
                response = project_steps.step_get_secret(create_project, secret_name)
                # 获取保密字典的数据
                count = response.json()['totalItems']
                if count > 0:
                    break
            except Exception as e:
                print(e)
                i += 1
                time.sleep(1)
        with pytest.assume:
            assert count == 1
        # 删除创建的保密字典
        project_steps.step_delete_secret(create_project, secret_name)
        # 验证删除成功
        time.sleep(1)
        res = project_steps.step_get_secret(create_project, secret_name)
        assert res.json()['totalItems'] == 0

    @allure.story('配置-配置字典')
    @allure.title('创建、查询、删除配置字典')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_configmap(self, create_project):
        # 创建配置字典
        configmap_name = 'test-configmap-' + str(commonFunction.get_random())
        data = {"wx": "test"}
        project_steps.step_create_configmap(create_project, configmap_name, data)
        # 验证配置字典创建成功
        time.sleep(1)
        with pytest.assume:
            assert project_steps.step_get_configmap(create_project, configmap_name).json()['items'][0]['data'] == data
        # 删除配置字典
        project_steps.step_delete_configmap(create_project, configmap_name)
        # 验证删除成功
        time.sleep(1)
        assert project_steps.step_get_configmap(create_project, configmap_name).json()['totalItems'] == 0

    @allure.story('配置-配置字典')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.parametrize('configmap_name, title',
                             [('Test', '创建的配置字典名称包括大写字母'),
                              ('', '创建的配置字典无名称'),
                              ('te@st', '创建的配置字典名称包含特殊字符'),
                              ('test-', '创建的配置字典名称以-结尾'),
                              ('-test', '创建的配置字典名称以-开头')
                              ])
    def test_create_configmap_wrong_name(self, configmap_name, title, create_project):
        # 创建配置字典
        data = {"wx": "test"}
        response = project_steps.step_create_configmap(create_project, configmap_name, data)
        assert response.json()['status'] == 'Failure'

    @allure.story('存储管理-存储卷')
    @allure.title('删除存在的存储卷，并验证删除成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_volume(self, create_project):
        # 创建存储卷
        volume_name = 'volume' + str(commonFunction.get_random())
        project_steps.step_create_volume(create_project, volume_name, self.storage_class)
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
        with pytest.assume:
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
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_project_quota_cpu(self, create_project):
        # 配额信息
        hard = {"limits.cpu": "11",
                "requests.cpu": "1"
                }
        # 获取项目配额的resource_version
        resource_version = project_steps.step_get_project_quota_version(create_project)
        # 编辑配额信息
        project_steps.step_edit_project_quota(create_project, hard, resource_version)
        hard_actual = ''
        i = 0
        while i < 60:
            try:
                # 获取修改后的配额信息
                response = project_steps.step_get_project_quota(create_project)
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
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_project_quota_wrong_cpu(self, create_project):
        # 配额信息,错误的cpu信息
        hard = {"limits.cpu": "11www",
                "requests.cpu": "1www"
                }
        # 获取项目配额的resource_version
        resource_version = project_steps.step_get_project_quota_version(create_project)
        # 编辑配额信息
        r = project_steps.step_edit_project_quota(create_project, hard, resource_version)
        # 获取编辑结果
        status = r.json()['status']
        # 验证编辑失败
        assert status == 'Failure'

    @allure.story('项目设置-项目配额')
    @allure.title('设置项目配额-输入错误的cpu信息(包含负数)')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_project_quota_wrong_cpu_1(self, create_project):
        # 配额信息,错误的cpu信息
        hard = {"limits.cpu": "-11",
                "requests.cpu": "1"
                }
        # 获取项目配额的resource_version
        resource_version = project_steps.step_get_project_quota_version(create_project)
        # 编辑配额信息
        r = project_steps.step_edit_project_quota(create_project, hard, resource_version)
        # 获取编辑结果
        status = r.json()['status']
        # 验证编辑失败
        assert status == 'Failure'

    @allure.story('项目设置-项目配额')
    @allure.title('只设置项目配额-内存')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_project_quota_memory(self, create_project):
        # 配额信息
        hard = {"limits.memory": "10Gi", "requests.memory": "1Gi"}
        # 获取项目配额的resource_version
        resource_version = project_steps.step_get_project_quota_version(create_project)
        # 编辑配额信息
        project_steps.step_edit_project_quota(create_project, hard, resource_version)
        i = 0
        hard_actual = ''
        while i < 60:
            try:
                # 获取修改后的配额信息
                response = project_steps.step_get_project_quota(create_project)
                hard_actual = response.json()['data']['hard']
                if len(hard_actual) > 0:
                    break
            except Exception as e:
                print(e)
                i += 1
                time.sleep(1)
        # 验证配额修改成功
        with pytest.assume:
            assert hard_actual == hard

    @allure.story('项目设置-项目配额')
    @allure.title('设置项目配额-输入错误的内存(包含非单位字母)')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_project_quota_wrong_memory(self, create_project):
        # 配额信息
        hard = {"limits.memory": "10Gi", "requests.memory": "1Gi"}
        # 获取项目配额的resource_version
        resource_version = project_steps.step_get_project_quota_version(create_project)
        # 编辑配额信息
        response = project_steps.step_edit_project_quota(create_project, hard, resource_version)
        # 获取编辑结果
        status = response.json()['status']
        # 验证编辑失败
        assert status == 'Failure'

    @allure.story('项目设置-项目配额')
    @allure.title('设置项目配额-输入错误的内存(包含负数)')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_project_quota_wrong_memory(self, create_project):
        # 配额信息
        hard = {"limits.memory": "-10Gi", "requests.memory": "1Gi"}
        # 获取项目配额的resource_version
        resource_version = project_steps.step_get_project_quota_version(create_project)
        # 编辑配额信息
        response = project_steps.step_edit_project_quota(create_project, hard, resource_version)
        # 获取编辑结果
        status = response.json()['status']
        # 验证编辑失败
        assert status == 'Failure'

    @allure.story('项目设置-项目配额')
    @allure.title('设置项目配额-CPU、内存')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_project_quota_cpu_memory(self, create_project):
        # 配额信息
        hard = {"limits.memory": "10Gi", "requests.memory": "1Gi",
                "limits.cpu": "10", "requests.cpu": "1"}
        # 获取项目配额的resource_version
        resource_version = project_steps.step_get_project_quota_version(create_project)
        # 编辑配额信息
        project_steps.step_edit_project_quota(create_project, hard, resource_version)
        # 获取修改后的配额信息
        i = 0
        hard_actual = ''
        while i < 60:
            try:
                response = project_steps.step_get_project_quota(create_project)
                hard_actual = response.json()['data']['hard']
                if len(hard_actual) > 0:
                    break
            except Exception as e:
                print(e)
                i += 1
                time.sleep(1)
        # 验证配额修改成功
        assert hard_actual == hard

    @allure.story('项目设置-项目配额')
    @allure.title('只设置项目配额-资源配额')
    @allure.severity(allure.severity_level.NORMAL)
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
            except Exception as e:
                print(e)
                i += 3
                time.sleep(3)
        # 验证配额修改成功
        with pytest.assume:
            assert hard_actual == hard

    @allure.story('项目设置-项目配额')
    @allure.title('只设置项目配额-输入错误的资源配额信息(包含字母)')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_project_quota_wrong_resource(self, create_project):
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
        resource_version = project_steps.step_get_project_quota_version(create_project)
        # 修改资源配额
        response = project_steps.step_edit_project_quota(create_project, hard, resource_version)
        # 获取编辑结果
        status = response.json()['status']
        # 验证编辑失败
        assert status == 'Failure'

    @allure.story('项目设置-项目配额')
    @allure.title('只设置项目配额-输入错误的资源配额信息(包含负数)')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_project_quota_wrong_resource_1(self, create_project):
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
        resource_version = project_steps.step_get_project_quota_version(create_project)
        # 修改资源配额
        response = project_steps.step_edit_project_quota(create_project, hard, resource_version)
        # 获取编辑结果
        status = response.json()['status']
        # 验证编辑失败
        assert status == 'Failure'

    @allure.story('项目设置-项目配额')
    @allure.title('设置项目配额-cpu、memory、资源配额')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_project_quota(self, create_project):
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
        resource_version = project_steps.step_get_project_quota_version(create_project)
        # 修改资源配额
        project_steps.step_edit_project_quota(create_project, hard, resource_version)
        # 获取修改后的配额信息
        response = project_steps.step_get_project_quota(create_project)
        hard_actual = response.json()['data']['hard']
        # 验证配额修改成功
        assert hard_actual == hard

    @allure.story('项目设置-资源默认请求')
    @allure.title('只设置资源默认请求-cpu')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_container_quota_cpu(self, create_project, create_ws):
        # 获取资源默认请求
        response = project_steps.step_get_container_quota(create_project, create_ws)
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
        project_steps.step_edit_container_quota(create_project, name, resource_version, limit, request)
        # 查询编辑结果
        response = project_steps.step_get_container_quota(create_project, create_ws)
        limit_actual = response.json()['items'][0]['spec']['limits'][0]['default']
        request_actual = response.json()['items'][0]['spec']['limits'][0]['defaultRequest']
        # 验证编辑成功
        assert limit == limit_actual
        assert request == request_actual

    @allure.story('项目设置-资源默认请求')
    @allure.title('只设置资源默认请求-输入错误的cpu信息(包含字母)')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_container_quota_wrong_cpu(self, create_project, create_ws):
        # 获取资源默认请求
        response = project_steps.step_get_container_quota(create_project, create_ws)
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
        r = project_steps.step_edit_container_quota(create_project, name, resource_version, limit, request)
        # 获取编辑结果
        status = r.json()['status']
        # 验证编辑失败
        assert status == 'Failure'

    @allure.story('项目设置-资源默认请求')
    @allure.title('只设置资源默认请求-输入错误的cpu信息(包含负数)')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_container_quota_wrong_cpu_1(self, create_project, create_ws):
        # 获取资源默认请求
        response = project_steps.step_get_container_quota(create_project, create_ws)
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
        r = project_steps.step_edit_container_quota(create_project, name, resource_version, limit, request)
        # 获取编辑结果
        status = r.json()['status']
        # 验证编辑失败
        assert status == 'Failure'

    @allure.story('项目设置-资源默认请求')
    @allure.title('只设置资源默认请求-内存')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_container_quota_memory(self, create_project, create_ws):
        # 获取资源默认请求
        response = project_steps.step_get_container_quota(create_project, create_ws)
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
        project_steps.step_edit_container_quota(create_project, name, resource_version, limit, request)
        # 查询编辑结果
        response = project_steps.step_get_container_quota(create_project, create_ws)
        limit_actual = response.json()['items'][0]['spec']['limits'][0]['default']
        request_actual = response.json()['items'][0]['spec']['limits'][0]['defaultRequest']
        # 验证编辑成功
        with pytest.assume:
            assert limit == limit_actual
        with pytest.assume:
            assert request == request_actual

    @allure.story('项目设置-资源默认请求')
    @allure.title('只设置资源默认请求-输入错误的内存信息(包含非单位字母)')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_container_quota_wrong_memory(self, create_project, create_ws):
        # 获取资源默认请求
        response = project_steps.step_get_container_quota(create_project, create_ws)
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
        r = project_steps.step_edit_container_quota(create_project, name, resource_version, limit, request)
        # 获取编辑结果
        status = r.json()['status']
        # 验证编辑失败
        assert status == 'Failure'

    @allure.story('项目设置-资源默认请求')
    @allure.title('只设置资源默认请求-输入错误的内存信息(包含负数)')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_container_quota_wrong_memory_1(self, create_project, create_ws):
        # 获取资源默认请求
        response = project_steps.step_get_container_quota(create_project, create_ws)
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
        r = project_steps.step_edit_container_quota(create_project, name, resource_version, limit, request)
        # 获取编辑结果
        status = r.json()['status']
        # 验证编辑失败
        assert status == 'Failure'

    @allure.story('项目设置-资源默认请求')
    @allure.title('只设置资源默认请求-内存、cpu')
    @allure.severity(allure.severity_level.NORMAL)
    def test_edit_container_quota_memory(self, create_project, create_ws):
        # 获取资源默认请求
        response = project_steps.step_get_container_quota(create_project, create_ws)
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
        project_steps.step_edit_container_quota(create_project, name, resource_version, limit, request)
        # 查询编辑结果
        response = project_steps.step_get_container_quota(create_project, create_ws)
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

    @allure.story('项目设置-网络隔离')
    @allure.title('开启、关闭网络隔离')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_set_network_isolation(self, create_ws, create_project):
        # 开启网络隔离
        status = 'enabled'
        project_steps.step_set_network_isolation(create_project, status)
        # 验证网络隔离状态为开启
        response = project_steps.step_get_network_isolation(create_ws, create_project)
        assert response.json()['metadata']['annotations']['kubesphere.io/network-isolate'] == 'enabled'
        # 关闭网络隔离
        status = ''
        project_steps.step_set_network_isolation(create_project, status)
        # 验证网络隔离状态为关闭
        response = project_steps.step_get_network_isolation(create_ws, create_project)
        assert response.json()['metadata']['annotations']['kubesphere.io/network-isolate'] == ''

    @allure.story('项目设置-网络隔离')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('title, spec',
                             [('添加白名单条目/内部白名单/出站',
                               {"egress": [{"to": [{"namespace": {"name": "default"}}]}]}),
                              ('添加白名单条目/内部白名单/入站',
                               {"ingress": [{"from": [{"namespace": {"name": "default"}}]}]}),
                              (
                              '添加白名单条目/外部白名单/出站', {"egress": [{"ports": [{"port": 80, "protocol": "TCP"}],
                                                                             "to": [{"ipBlock": {
                                                                                 "cidr": "10.10.10.10/24"}}]}]}),
                              ('添加白名单条目/外部白名单/入站',
                               {"ingress": [{"ports": [{"port": 80, "protocol": "TCP"}],
                                             "from": [{"ipBlock": {"cidr": "10.10.10.10/24"}}]}]}),
                              ])
    def test_add_allowlist(self, title, spec, create_ws, create_project):
        # 开启网络隔离
        status = 'enabled'
        project_steps.step_set_network_isolation(create_project, status)
        # 验证网络隔离状态为开启
        response = project_steps.step_get_network_isolation(create_ws, create_project)
        assert response.json()['metadata']['annotations']['kubesphere.io/network-isolate'] == 'enabled'
        # 添加白名单
        policy_name = 'test-policy-' + str(commonFunction.get_random())
        project_steps.step_add_allowlist(create_project, policy_name, spec)
        # 查看白名单详情，验证白名单创建成功
        assert project_steps.step_get_allowlist(create_project, create_ws).json()['items'][0]['spec'] == spec

    @allure.story('项目设置-日志收集')
    @allure.title('开启日志收集，然后将其关闭')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_open_logsidecar(self, create_project, create_ws):
        # 开启日志收集
        project_steps.step_set_logsidecar(create_ws, create_project, status='enabled')
        # 查看并验证日志收集状态
        response = project_steps.step_get_status_logsidecar(create_project)
        status_actual = response.json()['metadata']['labels']['logging.kubesphere.io/logsidecar-injection']
        with pytest.assume:
            assert status_actual == 'enabled'
        # 关闭日志收集
        project_steps.step_set_logsidecar(create_ws, create_project, status='disabled')
        # 查看并验证日志收集状态
        response = project_steps.step_get_status_logsidecar(create_project)
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
        # 将测试用例中的变量替换成指定内容
        targets = commonFunction.replace_str(url, params, data, condition, except_result,
                                             actual_value='${project_name}', expect_value=self.project_name_for_exel)
        # 使用修改过的内容进行测试
        commonFunction.request_resource(targets[0], targets[1], targets[2], story, title, method, severity,
                                        targets[3], targets[4])


if __name__ == "__main__":
    pytest.main(['-s', 'test_project.py'])  # -s参数是为了显示用例的打印信息。 -q参数只显示结果，不显示过程
