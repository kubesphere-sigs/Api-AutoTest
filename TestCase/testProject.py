import requests
import pytest
import json
import allure
import sys
import time

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from config import config
from common.getData import DoexcleByPandas
from common.getHeader import get_header
from common import commonFunction
from step import project_steps, workspace_steps, platform_steps


@allure.feature('Project')
@pytest.mark.skipif(commonFunction.check_multi_cluster() is True, reason='多集群环境下不执行')
class TestProject(object):
    volume_name = 'testvolume'  # 存储卷名称，在创建、删除存储卷和创建存储卷快照时使用,excle中的用例也用到了这个存储卷
    snapshot_name = 'testshot'  # 存储卷快照的名称,在创建和删除存储卷快照时使用，在excle中的用例也用到了这个快照
    user_name = 'user-for-test-project'  # 系统用户名称
    user_role = 'users-manager'  # 用户角色
    ws_name = 'ws-for-test-project' + str(commonFunction.get_random())
    project_name_for_exel = 'test-project'  # 项目名称，从excle中获取的测试用例中用到了这个项目名称
    project_name = 'test-project' + str(commonFunction.get_random())
    ws_role_name = ws_name + '-viewer'  # 企业空间角色名称
    project_role_name = 'test-project-role'  # 项目角色名称
    job_name = 'demo-job'  # 任务名称,在创建和删除任务时使用
    work_name = 'workload-demo'  # 工作负载名称，在创建、编辑、删除工作负载时使用
    # 从文件中读取用例信息
    parametrize = DoexcleByPandas().get_data_for_pytest(filename='../data/data.xlsx', sheet_name='project')

    # 所有用例执行之前执行该方法
    def setup_class(self):
        platform_steps.step_create_user(self.user_name, self.user_role)  # 创建一个用户
        workspace_steps.step_create_workspace(self.ws_name)  # 创建一个企业空间
        workspace_steps.step_invite_user(self.ws_name, self.user_name, self.ws_name + '-viewer')  # 将创建的用户邀请到企业空间
        project_steps.step_create_project(self.ws_name, self.project_name)  # 创建一个project工程
        project_steps.step_create_project(self.ws_name, self.project_name_for_exel)  # 创建一个project工程
        # 创建存储卷
        project_steps.step_create_volume(self.project_name_for_exel, self.volume_name)

    # 所有用例执行完之后执行该方法
    def teardown_class(self):
        # 删除存储卷
        project_steps.step_delete_volume(self.project_name, self.volume_name)
        project_steps.step_delete_project(self.ws_name, self.project_name)  # 删除创建的项目
        project_steps.step_delete_project(self.ws_name, self.project_name_for_exel)  # 删除创建的项目
        time.sleep(5)
        workspace_steps.step_delete_workspace(self.ws_name)  # 删除创建的工作空间
        platform_steps.step_delete_user(self.user_name)  # 删除创建的用户

    '''
    以下用例由于存在较多的前置条件，不便于从excle中获取信息，故使用一个方法一个用例的方式
    '''

    @allure.story('存储管理-存储卷')
    @allure.title('创建存储卷，然后将存储卷绑定到新建的deployment上，最后验证资源和存储卷的状态正常')
    @allure.severity(allure.severity_level.BLOCKER)
    def test_create_volume_for_deployment(self):
        type_name = 'volume-type'  # 存储卷的类型
        volume_name = 'volume' + str(commonFunction.get_random())
        replicas = 1  # 副本数
        image = 'redis'  # 镜像名称
        container_name = 'container1'  # 容器名称
        condition = 'name=' + self.work_name  # 查询条件
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80}]  # 容器的端口信息
        volumeMounts = [{"name": type_name, "readOnly": False, "mountPath": "/data"}]  # 设置挂载哦的存储卷
        strategy_info = {"type": "RollingUpdate", "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
        volume_info = [{"name": type_name, "persistentVolumeClaim": {"claimName": volume_name}}]  # 存储卷的信息
        # 创建存储卷
        project_steps.step_create_volume(self.project_name, volume_name)
        # 创建资源并将存储卷绑定到资源
        project_steps.step_create_deploy(self.project_name, work_name=self.work_name, image=image, replicas=replicas,
                                         container_name=container_name, volume_info=volume_info, ports=port,
                                         volumemount=volumeMounts, strategy=strategy_info)
        # 验证资源创建成功
        time.sleep(10)  # 等待资源创建成功
        # 获取工作负载的状态
        response = project_steps.step_get_workload(self.project_name, type='deployments', condition=condition)
        status = response.json()['items'][0]['status']
        # 验证资源的所有副本已就绪
        assert 'unavailableReplicas' not in status
        # 获取存储卷状态
        response = project_steps.step_get_volume_status(self.project_name, volume_name)
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
        project_steps.step_create_volume(self.project_name, volume_name)
        # 创建资源并将存储卷绑定到资源
        project_steps.step_create_stateful(project_name=self.project_name, work_name=work_name,
                                           container_name=container_name,
                                           image=image, replicas=replicas, ports=port, service_ports=service_port,
                                           volumemount=volumemounts, volume_info=volume_info, service_name=service_name)

        # 验证资源创建成功
        time.sleep(10)  # 等待资源创建成功
        # 获取工作负载的状态
        response = project_steps.step_get_workload(self.project_name, type='statefulsets', condition=condition)
        readyReplicas = response.json()['items'][0]['status']['readyReplicas']
        # 验证资源的所有副本已就绪
        assert readyReplicas == replicas
        # 获取存储卷状态
        response = project_steps.step_get_volume_status(self.project_name, volume_name)
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
        project_steps.step_create_volume(self.project_name, volume_name)
        # 创建资源并将存储卷绑定到资源
        project_steps.step_create_daemonset(self.project_name, work_name=work_name, image=image,
                                            container_name=container_name, volume_info=volume_info, ports=port,
                                            volumemount=volumeMounts)
        # 验证资源创建成功
        time.sleep(10)  # 等待资源创建成功
        # 获取工作负载的状态
        response = project_steps.step_get_workload(self.project_name, type='daemonsets', condition=condition)
        numberReady = response.json()['items'][0]['status']['numberReady']  # 验证资源的所有副本已就绪
        assert numberReady == 1
        # 获取存储卷状态
        response = project_steps.step_get_volume_status(self.project_name, volume_name)
        status = response.json()['items'][0]['status']['phase']
        # 验证存储卷状态正常
        assert status == 'Bound'

    @allure.story('存储管理-存储卷')
    @allure.title('创建存储卷，然后将存储卷绑定到新建的service上，最后验证资源和存储卷的状态正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_volume_for_service(self):
        volume_name = 'volume-service'  # 存储卷的名称
        type_name = 'volume-type'  # 存储卷的类型
        service_name = 'service' + str(commonFunction.get_random())  # 工作负载的名称
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
        project_steps.step_create_volume(self.project_name, volume_name)
        # 创建service
        project_steps.step_create_service(self.project_name, service_name, port_service)
        # 创建service绑定的deployment
        project_steps.step_create_deploy(project_name=self.project_name, work_name=service_name,
                                         container_name=container_name,
                                         ports=port_deploy, volumemount=volumeMounts, image=image, replicas=replicas,
                                         volume_info=volume_info, strategy=strategy_info)
        # 验证service创建成功
        response = project_steps.step_get_workload(self.project_name, type='services', condition=condition)
        name = response.json()['items'][0]['metadata']['name']
        assert name == service_name
        # 验证deploy创建成功
        time.sleep(3)
        re = project_steps.step_get_workload(self.project_name, type='deployments', condition=condition)
        # 获取并验证deployment的名称正确
        name = re.json()['items'][0]['metadata']['name']
        assert name == service_name
        # 获取存储卷状态
        response = project_steps.step_get_volume_status(self.project_name, volume_name)
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
        r = project_steps.step_get_role(self.project_name, role_name)
        print("actual_result:r.json()['totalItems']=" + str(r.json()['totalItems']))  # 在日志中打印出实际结果
        print('expect_result: 3')  # 在日志中打印出预期结果
        assert r.json()['totalItems'] == 3  # 验证初始的角色数量为3

    @allure.story("项目设置-项目角色")
    @allure.title('查找project工程中指定的角色')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_role_one(self):
        role_name = 'viewer'
        r = project_steps.step_get_role(self.project_name, role_name)
        print("actual_result:r.json()['items'][0]['metadata']['name']=" + r.json()['items'][0]['metadata'][
            'name'])  # 在日志中打印出实际结果
        print('expect_result:' + role_name)  # 在日志中打印出预期结果
        assert r.json()['items'][0]['metadata']['name'] == role_name  # 验证查询的角色结果为viewer

    @allure.story("项目设置-项目角色")
    @allure.title('查找project工程中不存在的角色')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_role_none(self):
        role_name = 'viewer123'
        r = project_steps.step_get_role(self.project_name, role_name)
        print("actual_result:r.json()['totalItems'] =" + str(r.json()['totalItems']))  # 在日志中打印出实际结果
        print('expect_result: 0')  # 在日志中打印出预期结果
        assert r.json()['totalItems'] == 0  # 验证查询到的结果为空

    @allure.story("项目设置-项目角色")
    @allure.title('模糊查找project工程中的角色')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_role_fuzzy(self):
        role_name = 'adm'
        r = project_steps.step_get_role(self.project_name, role_name)
        assert r.json()['totalItems'] == 1  # 验证查询到的结果数量为2
        # 验证查找到的角色
        print("actual_result:r.json()['items'][0]['metadata']['name']=" + r.json()['items'][0]['metadata'][
            'name'])  # 在日志中打印出实际结果
        print('expect_result: operator')  # 在日志中打印出预期结果
        assert r.json()['items'][0]['metadata']['name'] == 'admin'

    @allure.story("项目设置-项目角色")
    @allure.title('在project工程中创建角色')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_role_create(self):
        role_name = 'role' + str(commonFunction.get_random())
        r = project_steps.step_create_role(self.project_name, role_name)
        print("actual_result:r.json()['metadata']['name']=" + r.json()['metadata']['name'])  # 在日志中打印出实际结果
        print('expect_result:' + role_name)  # 在日志中打印出预期结果
        assert r.json()['metadata']['name'] == role_name  # 验证新建的角色名称

    @allure.story("项目设置-项目角色")
    @allure.title('在project工程中创建角色-角色名称为空')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_role_create_name_none(self):
        role_name = ''
        r = project_steps.step_create_role(self.project_name, role_name)
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
        print("actual_result:r.json()['metadata']['annotations']['kubesphere.io/alias-name']=" +
              r.json()['metadata']['annotations']['kubesphere.io/alias-name'])  # 在日志中打印出实际结果
        print('expect_result:' + alias_name)  # 在日志中打印出预期结果
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
        print("actual_result:r.json()['metadata']['annotations']['iam.kubesphere.io/aggregation-roles']=" +
              r.json()['metadata']['annotations']['iam.kubesphere.io/aggregation-roles'])  # 在日志中打印出实际结果
        print('expect_result:' + authority)  # 在日志中打印出预期结果
        assert r.json()['metadata']['annotations']['iam.kubesphere.io/aggregation-roles'] == authority  # 验证修改后的权限信息

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
        assert count == 1
        # 删除角色
        project_steps.step_project_delete_role(self.project_name, role_name)
        # 验证角色删除成功
        r = project_steps.step_get_project_role(self.project_name, role_name)
        count_new = r.json()['totalItems']
        assert count_new == 0

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
        r = project_steps.step_get_project_user(self.project_name, user_condition)

        print("actual_result:r.json()['items'][0]['metadata']['name']=" + r.json()['items'][0]['metadata'][
            'name'])  # 在日志中打印出实际结果
        print('expect_result:' + user_condition)  # 在日志中打印出预期结果
        assert r.json()['items'][0]['metadata']['name'] == user_condition  # 验证查找的结果为admin

    @allure.story("项目设置-项目成员")
    @allure.title('模糊查找project的用户')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_user_fuzzy(self):
        user_condition = 'ad'
        r = project_steps.step_get_project_user(self.project_name, user_condition)
        print("actual_result:r.json()['items'][0]['metadata']['name']=" + r.json()['items'][0]['metadata'][
            'name'])  # 在日志中打印出实际结果
        print('expect_result: admin')  # 在日志中打印出预期结果
        assert r.json()['items'][0]['metadata']['name'] == 'admin'  # 验证查找的结果为admin

    @allure.story("项目设置-项目成员")
    @allure.title('查找project工程不存在的用户')
    @allure.severity(allure.severity_level.NORMAL)
    def test_project_user_none(self):
        user_condition = 'wx-ad'
        r = project_steps.step_get_project_user(self.project_name, user_condition)
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
        url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + self.project_name + \
              '/members/' + self.user_name
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
        job_name = 'job' + str(commonFunction.get_random())
        project_steps.step_create_job(self.project_name, job_name)  # 创建任务
        uid = project_steps.step_get_job_status(self.project_name, job_name)  # 验证任务的运行状态为完成,并获取uid
        pod_name = project_steps.step_get_job_pods(self.project_name, uid)  # 查看任务的资源状态，并获取容器组名称
        project_steps.step_get_pods_log(self.project_name, pod_name, job_name)  # 查看任务的第一个容器的运行日志，并验证任务的运行结果
        # 删除创建的任务
        project_steps.step_delete_job(self.project_name, job_name)

    @allure.story('应用负载-任务')
    @allure.title('按名称模糊查询存在的任务')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_query_job(self):
        # 创建任务
        job_name = 'job' + str(commonFunction.get_random())
        project_steps.step_create_job(self.project_name, job_name)
        # 模糊查询存在的任务
        response = project_steps.step_get_assign_job(self.project_name, 'name', job_name[1:])
        assert response.json()['totalItems'] == 1

    @allure.story('应用负载-任务')
    @allure.title('按状态查询已完成的任务')
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_job_status_completed(self):
        job_name = 'job' + str(commonFunction.get_random())
        project_steps.step_create_job(self.project_name, job_name)  # 创建任务
        project_steps.step_get_job_status(self.project_name, job_name)  # 验证任务的运行状态为完成
        response = project_steps.step_get_assign_job(self.project_name, 'status', 'completed')
        # 获取查询结果数量
        job_count = response.json()['totalItems']
        # 获取查询结果中job的名称
        job_names = []
        for i in range(0, job_count):
            job_names.append(response.json()['items'][i]['metadata']['name'])
        # 验证查询结果正确
        assert job_name in job_names
        # 删除创建的任务
        project_steps.step_delete_job(self.project_name, job_name)

    @allure.story('应用负载-任务')
    @allure.title('按状态查询运行中的任务')
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_job_status_running(self):
        job_name = 'job' + str(commonFunction.get_random())
        # 创建任务
        project_steps.step_create_job(self.project_name, job_name)
        # 验证任务状态为运行中
        project_steps.step_get_job_status_run(self.project_name, job_name)
        # 按状态为运行中查询任务
        response = project_steps.step_get_assign_job(self.project_name, 'status', 'running')
        # 验证查询结果
        assert response.json()['totalItems'] >= 1

    @allure.story('应用负载-容器组')
    @allure.title('按名称精确查询存在的容器组')
    @allure.severity(allure.severity_level.NORMAL)
    def test_precise_query_pod(self):
        # 创建任务
        job_name = 'job' + str(commonFunction.get_random())
        project_steps.step_create_job(self.project_name, job_name)
        uid = project_steps.step_get_job_status(self.project_name, job_name)  # 验证任务的运行状态为完成,并获取uid
        pod_name = project_steps.step_get_job_pods(self.project_name, uid)  # 查看任务的资源状态，并获取容器组名称
        # 在项目中查询pod信息
        r = project_steps.step_get_pod_info(self.project_name, pod_name)
        # 验证查询到的容器名称
        print("actual_result:r.json()['items'][0]['metadata']['name'] = " + r.json()['items'][0]['metadata']['name'])
        print("expect_result:" + pod_name)
        assert r.json()['items'][0]['metadata']['name'] == pod_name
        # 删除创建的任务
        project_steps.step_delete_job(self.project_name, job_name)

    @allure.story('应用负载-容器组')
    @allure.title('按名称模糊查询存在的容器组')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_query_pod(self):
        # 创建任务
        job_name = 'job' + str(commonFunction.get_random())
        project_steps.step_create_job(self.project_name, job_name)
        project_steps.step_get_job_status(self.project_name, job_name)  # 验证任务的运行状态为完成
        pod_name = job_name
        # 在项目中查询pod信息
        r = project_steps.step_get_pod_info(self.project_name, pod_name)
        # 验证查询到的容器名称
        print("actual_result:r.json()['totalItems'] = " + str(r.json()['totalItems']))
        print("expect_result:" + str(4))
        assert r.json()['totalItems'] == 4
        # 删除创建的任务
        project_steps.step_delete_job(self.project_name, job_name)

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
        # 创建任务
        job_name = 'job' + str(commonFunction.get_random())
        project_steps.step_create_job(self.project_name, job_name)
        uid = project_steps.step_get_job_status(self.project_name, job_name)  # 验证任务的运行状态为完成,并获取uid
        pod_name = project_steps.step_get_job_pods(self.project_name, uid)  # 查看任务的资源状态，并获取容器组名称
        url = config.url + '/api/v1/namespaces/' + self.project_name + '/pods/' + pod_name
        r = requests.get(url=url, headers=get_header())
        # 验证查询结果
        print("actual_result:r.json()['status']['phase'] = " + r.json()['status']['phase'])
        print("expect_result: Succeeded")
        assert r.json()['status']['phase'] == 'Succeeded'
        # 删除创建的任务
        project_steps.step_delete_job(self.project_name, job_name)

    @allure.story('应用负载-容器组')
    @allure.title('删除状态为已完成的容器组')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_pod(self):
        # 创建任务
        job_name = 'job' + str(commonFunction.get_random())
        project_steps.step_create_job(self.project_name, job_name)
        uid = project_steps.step_get_job_status(self.project_name, job_name)  # 验证任务的运行状态为完成,并获取uid
        pod_name = project_steps.step_get_job_pods(self.project_name, uid)  # 查看任务的资源状态，并获取容器组名称
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
        job_name = 'job' + str(commonFunction.get_random())
        project_steps.step_create_job(self.project_name, job_name)  # 创建任务
        project_steps.step_get_job_status_run(self.project_name, job_name)  # 验证任务状态为运行中
        # 删除任务
        result = project_steps.step_delete_job(self.project_name, job_name)
        # 验证删除结果为Success
        assert result == 'Success'
        # 在列表中查询任务，验证查询结果为空
        response = project_steps.step_get_assign_job(self.project_name, 'name', job_name)
        assert response.json()['totalItems'] == 0

    @allure.story('应用负载-任务')
    @allure.title('删除状态为已完成的任务')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_job(self):
        # 创建任务
        job_name = 'job' + str(commonFunction.get_random())
        project_steps.step_create_job(self.project_name, job_name)
        project_steps.step_get_job_status(self.project_name, job_name)  # 验证任务的运行状态为完成
        # 删除任务
        result = project_steps.step_delete_job(self.project_name, job_name)
        # 验证删除结果为Success
        assert result == 'Success'
        # 在列表中查询任务，验证查询结果为空
        response = project_steps.step_get_assign_job(self.project_name, 'name', job_name)
        assert response.json()['totalItems'] == 0

    @allure.story('应用负载-任务')
    @allure.title('删除不存在的任务')
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_job_no(self):
        job_name = 'test123'
        # 删除任务
        result = project_steps.step_delete_job(self.project_name, job_name)
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
        project_steps.step_create_deploy(project_name=self.project_name, work_name=workload_name,
                                         container_name=container_name, ports=port, volumemount=volumeMounts,
                                         image=image, replicas=replicas, volume_info=volume_info,
                                         strategy=strategy_info)

        # 在工作负载列表中查询创建的工作负载，并验证其状态为运行中，最长等待时间60s
        i = 0
        while i < 60:
            response = project_steps.step_get_workload(project_name=self.project_name, type='deployments',
                                                       condition=condition)
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
        project_steps.step_create_deploy(project_name=self.project_name, work_name=workload_name,
                                         container_name=container_name, ports=port, volumemount=volumeMounts,
                                         image=image, replicas=replicas, volume_info=volume_info,
                                         strategy=strategy_info)
        # 按名称精确查询deployment
        time.sleep(3)
        response = project_steps.step_get_workload(self.project_name, type='deployments', condition=condition)
        # 获取并验证deployment的名称正确
        name = response.json()['items'][0]['metadata']['name']
        assert name == workload_name
        # 删除deployment
        re = project_steps.step_delete_workload(project_name=self.project_name, type='deployments',
                                                work_name=workload_name)
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
        project_steps.step_create_deploy(project_name=self.project_name, work_name=workload_name,
                                         container_name=container_name, ports=port, volumemount=volumeMounts,
                                         image=image, replicas=replicas, volume_info=volume_info,
                                         strategy=strategy_info)
        # 按名称精确查询deployment
        time.sleep(3)
        response = project_steps.step_get_workload(self.project_name, type='deployments', condition=conndition)
        # 获取并验证deployment的名称正确
        name = response.json()['items'][0]['metadata']['name']
        assert name == workload_name
        # 删除deployment
        re = project_steps.step_delete_workload(project_name=self.project_name, type='deployments',
                                                work_name=workload_name)
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
        project_steps.step_create_stateful(project_name=self.project_name, work_name=workload_name,
                                           container_name=container_name,
                                           image=image, replicas=replicas, volume_info=volume_info, ports=port,
                                           service_ports=service_port, volumemount=volumemounts,
                                           service_name=service_name)

        # 在工作负载列表中查询创建的工作负载，并验证其状态为运行中，最长等待时间60s
        time.sleep(3)
        i = 3
        while i < 60:
            response = project_steps.step_get_workload(project_name=self.project_name, type='statefulsets',
                                                       condition=condition)
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
        project_steps.step_create_stateful(project_name=self.project_name, work_name=workload_name,
                                           container_name=container_name,
                                           image=image, replicas=replicas, volume_info=volume_info, ports=port,
                                           service_ports=service_port, volumemount=volumemounts,
                                           service_name=service_name)

        # 按名称精确查询statefulsets
        time.sleep(1)
        response = project_steps.step_get_workload(self.project_name, type=type, condition=condition)
        # 获取并验证deployment的名称正确
        name = response.json()['items'][0]['metadata']['name']
        assert name == workload_name
        # 删除创建的statefulsets
        re = project_steps.step_delete_workload(project_name=self.project_name, type=type, work_name=workload_name)
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
        project_steps.step_create_stateful(project_name=self.project_name, work_name=workload_name,
                                           container_name=container_name,
                                           image=image, replicas=replicas, volume_info=volume_info, ports=port,
                                           service_ports=service_port, volumemount=volumemounts,
                                           service_name=service_name)

        # 按状态精确查询statefulsets
        time.sleep(5)
        response = project_steps.step_get_workload(self.project_name, type=type, condition=condition)
        # 获取并验证deployment的名称正确
        name = response.json()['items'][0]['metadata']['name']
        assert name == workload_name
        # 删除创建的statefulsets
        re = project_steps.step_delete_workload(project_name=self.project_name, type=type, work_name=workload_name)
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
        project_steps.step_create_daemonset(project_name=self.project_name, work_name=workload_name,
                                            container_name=container_name, image=image, ports=port,
                                            volume_info=volume_info, volumemount=volumemount)
        # 在工作负载列表中查询创建的工作负载，并验证其状态为运行中，最长等待时间60s
        time.sleep(3)
        i = 3
        while i < 60:
            response = project_steps.step_get_workload(project_name=self.project_name, type='daemonsets',
                                                       condition=condition)
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
        project_steps.step_create_daemonset(project_name=self.project_name, work_name=workload_name,
                                            container_name=container_name, image=image, ports=port,
                                            volume_info=volume_info, volumemount=volumemount)
        # 按名称查询DaemonSets
        time.sleep(3)
        response = project_steps.step_get_workload(self.project_name, type=type, condition=condition)
        # 获取并验证deployment的名称正确
        name = response.json()['items'][0]['metadata']['name']
        # 删除创建的daemonsets
        re = project_steps.step_delete_workload(project_name=self.project_name, type=type, work_name=workload_name)
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
        project_steps.step_create_daemonset(project_name=self.project_name, work_name=workload_name,
                                            container_name=container_name, image=image, ports=port,
                                            volume_info=volume_info, volumemount=volumemount)
        # 按名称查询DaemonSets
        time.sleep(3)
        response = project_steps.step_get_workload(self.project_name, type=type, condition=condition)
        # 获取并验证deployment的名称正确
        name = response.json()['items'][0]['metadata']['name']
        # 删除创建的daemonsets
        re = project_steps.step_delete_workload(project_name=self.project_name, type=type, work_name=workload_name)
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
        project_steps.step_create_service(self.project_name, service_name, port_service)
        # 创建service绑定的deployment
        project_steps.step_create_deploy(project_name=self.project_name, work_name=service_name,
                                         container_name=container_name,
                                         ports=port_deploy, volumemount=volumeMounts, image=image, replicas=replicas,
                                         volume_info=volume_info, strategy=strategy_info)
        # 验证service创建成功
        response = project_steps.step_get_workload(self.project_name, type='services', condition=condition)
        name = response.json()['items'][0]['metadata']['name']
        assert name == service_name
        # 验证deploy创建成功
        time.sleep(3)
        re = project_steps.step_get_workload(self.project_name, type='deployments', condition=condition)
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
        project_steps.step_create_service(self.project_name, service_name, port_service)
        # 验证service创建成功
        response = project_steps.step_get_workload(self.project_name, type='services', condition=condition)
        name = response.json()['items'][0]['metadata']['name']
        assert name == service_name
        # 删除service
        project_steps.step_delete_service(self.project_name, service_name)
        # 验证service删除成功
        response = project_steps.step_get_workload(self.project_name, type='services', condition=condition)
        count = response.json()['totalItems']
        assert count == 0

    @allure.story('应用负载-应用路由')
    @allure.title('为服务创建应用路由')
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
        project_steps.step_create_service(self.project_name, service_name, port_service)
        # 创建service绑定的deployment
        project_steps.step_create_deploy(project_name=self.project_name, work_name=service_name,
                                         container_name=container_name,
                                         ports=port_deploy, volumemount=volumeMounts, image=image, replicas=replicas,
                                         volume_info=volume_info, strategy=strategy_info)
        # 验证service创建成功
        response = project_steps.step_get_workload(self.project_name, type='services', condition=condition)
        name = response.json()['items'][0]['metadata']['name']
        assert name == service_name
        # 验证deploy创建成功
        time.sleep(3)
        re = project_steps.step_get_workload(self.project_name, type='deployments', condition=condition)
        # 获取并验证deployment的名称正确
        name = re.json()['items'][0]['metadata']['name']
        assert name == service_name
        # 为服务创建路由
        ingress_name = 'ingress' + str(commonFunction.get_random())
        host = 'www.test.com'
        service_info = {"serviceName": service_name, "servicePort": 80}
        response = project_steps.step_create_route(project_name=self.project_name, ingress_name=ingress_name, host=host,
                                                   service_info=service_info)
        # 获取路由绑定的服务名称
        name = response.json()['spec']['rules'][0]['http']['paths'][0]['backend']['serviceName']
        # 验证路由创建成功
        assert name == service_name

    @allure.story('项目设置-高级设置')
    @allure.title('设置网关-NodePort')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_gateway(self):
        type = 'NodePort'  # 网关类型
        annotations = {"servicemesh.kubesphere.io/enabled": "false"}  # 网关的注释信息
        # 创建网关
        response = project_steps.step_create_gateway(self.project_name, type, annotations)
        # 验证网关创建成功
        assert response.status_code == 200
        # 删除网关
        project_steps.step_delete_gateway(self.project_name)
        # 验证网关删除成功
        response = project_steps.step_get_gateway(self.project_name)
        assert response.json()['message'] == 'service \"kubesphere-router-' + self.project_name + '\" not found'

    @allure.story('项目设置-高级设置')
    @allure.title('设置网关-LoadBalancer')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_gateway(self):
        type = 'LoadBalancer'  # 网关类型
        annotations = {"service.beta.kubernetes.io/qingcloud-load-balancer-eip-ids": "",
                       "service.beta.kubernetes.io/qingcloud-load-balancer-type": "0",
                       "servicemesh.kubesphere.io/enabled": "false"}  # 网关的注释信息
        # 创建网关
        response = project_steps.step_create_gateway(self.project_name, type, annotations)
        # 验证网关创建成功
        assert response.status_code == 200
        # 删除网关
        project_steps.step_delete_gateway(self.project_name)
        # 验证网关删除成功
        response = project_steps.step_get_gateway(self.project_name)
        assert response.json()['message'] == 'service \"kubesphere-router-' + self.project_name + '\" not found'

    @allure.story('项目设置-高级设置')
    @allure.title('编辑网关')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_edit_gateway(self):
        type = 'LoadBalancer'  # 网关类型
        type_new = 'NodePort'
        annotations = {"service.beta.kubernetes.io/qingcloud-load-balancer-eip-ids": "",
                       "service.beta.kubernetes.io/qingcloud-load-balancer-type": "0",
                       "servicemesh.kubesphere.io/enabled": "false"}  # 网关的注释信息

        annotations_new = {"servicemesh.kubesphere.io/enabled": "false"}  # 网关的注释信息
        # 创建网关
        project_steps.step_create_gateway(self.project_name, type, annotations)
        # 编辑网关
        project_steps.step_edit_gateway(self.project_name, type_new, annotations_new)
        # 验证网关编辑成功
        response = project_steps.step_get_gateway(self.project_name)
        type_actual = response.json()['spec']['type']
        assert type_actual == type_new
        # 删除网关
        project_steps.step_delete_gateway(self.project_name)

    @allure.story('应用负载-工作负载')
    @allure.title('修改工作负载副本并验证运行正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_add_work_replica(self):
        # 依赖于用例'创建工作负载，并验证运行成功'创建的工作负载
        replicas = 3  # 副本数
        # 修改副本数
        project_steps.step_modify_work_replicas(project_name=self.project_name, work_name=self.work_name,
                                                replicas=replicas)
        # 获取工作负载中所有的容器组，并验证其运行正常，最长等待时间60s
        status_test = []  # 创建一个对比数组
        for j in range(replicas):
            status_test.append('Running')
        i = 0
        while i < 60:
            status = project_steps.step_get_work_pod_status(project_name=self.project_name, work_name=self.work_name)
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
    @allure.severity(allure.severity_level.CRITICAL)
    # 依赖于用例"创建存储卷，然后将存储卷绑定到新建的deployment上，最后验证资源和存储卷的状态正常"
    def test_delete_work(self):
        url = config.url + '/apis/apps/v1/namespaces/' + self.project_name + '/deployments/' + self.work_name
        data = {"kind": "DeleteOptions", "apiVersion": "v1", "propagationPolicy": "Background"}
        r = requests.delete(url=url, headers=get_header(), data=json.dumps(data))
        # 验证删除成功
        assert r.json()['status'] == 'Success'

    @allure.story('配置中心-服务账号')
    @allure.title('创建sa并验证sa内容正确、生成的密钥正确、然后删除sa')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_sa(self):
        sa_name = 'satest'
        # 步骤1：创建sa
        project_steps.step_create_sa(project_name=self.project_name, sa_name=sa_name)

        # 步骤2：验证sa创建成功并返回secret
        sa_secret = project_steps.step_get_sa(project_name=self.project_name, sa_name=sa_name)

        # 步骤3：查询sa详情
        project_steps.step_get_sa_detail(project_name=self.project_name, sa_name=sa_name)

        # 步骤4：查询sa的密钥信息并返回密钥类型
        secret_type = project_steps.step_get_secret(project_name=self.project_name, secret_name=sa_secret)
        assert secret_type == 'kubernetes.io/service-account-token'

        # 步骤5：删除sa
        project_steps.step_delete_sa(project_name=self.project_name, sa_name=sa_name)

        # 步骤6：验证删除成功
        num = project_steps.step_get_sa(project_name=self.project_name, sa_name=sa_name)

        assert num == 0

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

    @allure.story('存储管理-存储卷快照')
    @allure.title('删除创建的存储卷快照，并验证删除成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_volume_snapshot(self):
        # 删除存储卷快照
        project_steps.step_delete_volume_snapshot(self.project_name, self.snapshot_name)
        # 查询被删除的存储卷快照
        i = 0
        # 验证存储卷快照被删除，最长等待时间为30s
        while i < 30:
            response = project_steps.step_get_volume_status(self.project_name, self.snapshot_name)
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
        # 创建存储卷
        volume_name = 'volume' + str(commonFunction.get_random())
        project_steps.step_create_volume(self.project_name, volume_name)
        # 删除存储卷
        project_steps.step_delete_volume(self.project_name, volume_name)
        # 查询被删除的存储卷
        i = 0
        # 验证存储卷被删除，最长等待时间为30s
        while i < 30:
            response = project_steps.step_get_volume(self.project_name, volume_name)
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
        # 获取修改后的配额信息
        response = project_steps.step_get_project_quota(self.project_name)
        hard_actual = response.json()['data']['hard']
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
    def test_edit_project_quota_memory(self):
        # 配额信息
        hard = {"limits.memory": "10Gi", "requests.memory": "1Gi"}
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
        # 获取项目配额的resource_version
        resource_version = project_steps.step_get_project_quota_version(self.project_name)
        # 修改资源配额
        project_steps.step_edit_project_quota(self.project_name, hard, resource_version)
        # 获取修改后的配额信息
        response = project_steps.step_get_project_quota(self.project_name)
        hard_actual = response.json()['data']['hard']
        # 验证配额修改成功
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
        # print(response.text)
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
        assert limit == limit_actual
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
    def test_delete_project(self):
        # 删除创建的项目
        project_steps.step_delete_project(self.ws_name, self.project_name)
        i = 0
        # 验证项目删除结果，最长等待时间为60s
        while i < 60:
            response = project_steps.step_get_project(self.ws_name, self.project_name)
            if response.json()['totalItems'] == 0:
                print("删除项目耗时:" + str(i) + '秒')
                break
            time.sleep(1)
            i = i + 1
        assert response.json()['totalItems'] == 0


if __name__ == "__main__":
    pytest.main(['-s', 'testProject.py'])  # -s参数是为了显示用例的打印信息。 -q参数只显示结果，不显示过程
