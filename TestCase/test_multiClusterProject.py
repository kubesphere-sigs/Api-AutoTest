# -- coding: utf-8 --
import pytest
import allure
import sys
import time
from datetime import datetime
sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from common import commonFunction
from step import project_steps, cluster_steps, multi_project_steps


@allure.feature('多集群项目管理')
@pytest.mark.skipif(commonFunction.check_multi_cluster() is False, reason='未开启多集群功能,单集群环境下不执行')
class TestProject(object):
    # 如果为单集群环境，则不会collect该class的所有用例。 __test__ = False
    __test__ = commonFunction.check_multi_cluster()

    @allure.story('存储管理-存储卷')
    @allure.title('在多集群项目创建存储卷，然后将存储卷绑定到新建的deployment上，最后验证资源和存储卷的状态正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_volume_for_deployment(self, create_multi_workspace, create_multi_project):
        clusters = cluster_steps.step_get_cluster_name()

        type_name = 'volume-type'  # 存储卷的名称
        work_name = 'workload' + str(commonFunction.get_random())  # 工作负载名称
        volume_name = 'volume-deploy' + str(commonFunction.get_random())  # 存储卷名称
        replicas = 1  # 副本数
        image = 'redis'  # 镜像名称
        container_name = 'container' + str(commonFunction.get_random())  # 容器名称
        condition = work_name  # 查询条件
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80}]  # 容器的端口信息
        volume_mounts = [{"name": type_name, "readOnly": False, "mountPath": "/data"}]  # 设置挂载的存储卷
        strategy_info = {"type": "RollingUpdate",
                         "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
        volume_info = [{"name": type_name, "persistentVolumeClaim": {"claimName": volume_name}}]  # 存储卷的信息
        # 创建存储卷
        multi_project_steps.step_create_volume_in_multi_project(cluster_name=clusters,
                                                                project_name=create_multi_project,
                                                                volume_name=volume_name)
        # 创建资源并将存储卷绑定到资源
        multi_project_steps.step_create_deploy_in_multi_project(cluster_name=clusters,
                                                                project_name=create_multi_project, work_name=work_name,
                                                                image=image, replicas=replicas,
                                                                container_name=container_name,
                                                                volume_info=volume_info, ports=port,
                                                                volumemount=volume_mounts, strategy=strategy_info)

        # 获取工作负载的状态
        for name in clusters:
            i = 0
            while i < 180:
                response = multi_project_steps.step_get_workload_in_multi_project(cluster_name=name,
                                                                                  project_name=create_multi_project,
                                                                                  type='deployments',
                                                                                  condition=condition)
                try:
                    ready_replicas = response.json()['status']['readyReplicas']
                    if ready_replicas == replicas:
                        break
                except Exception as e:
                    print(e)
                time.sleep(5)
                i += 5
            # 获取存储卷状态
            re = multi_project_steps.step_get_volume_status_in_multi_project(cluster_name=name,
                                                                             project_name=create_multi_project,
                                                                             volume_name=volume_name)
            status = re.json()['status']['phase']
            # 验证存储卷状态正常
            with pytest.assume:
                assert status == 'Bound'
        # 删除工作负载
        multi_project_steps.step_delete_workload_in_multi_project(project_name=create_multi_project, type='deployments',
                                                                  work_name=work_name)
        # 删除存储卷
        multi_project_steps.step_delete_volume_in_multi_project(create_multi_project, volume_name)

    @allure.story('存储管理-存储卷')
    @allure.title('在多集群项目创建存储卷，然后将存储卷绑定到新建的statefulsets上，最后验证资源和存储卷的状态正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_volume_for_sts(self, create_multi_workspace, create_multi_project):
        clusters = cluster_steps.step_get_cluster_name()

        volume_name = 'volume-stateful' + str(commonFunction.get_random())  # 存储卷的名称
        type_name = 'volume-type'  # 存储卷的类型
        work_name = 'stateful' + str(commonFunction.get_random())  # 工作负载的名称
        service_name = 'service' + volume_name  # 服务名称
        replicas = 1  # 副本数
        image = 'nginx'  # 镜像名称
        container_name = 'container-stateful' + str(commonFunction.get_random())  # 容器名称
        condition = work_name  # 查询条件
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]
        service_port = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]
        volume_mounts = [{"name": type_name, "readOnly": False, "mountPath": "/data"}]
        volume_info = [{"name": type_name, "persistentVolumeClaim": {"claimName": volume_name}}]  # 存储卷的信息
        # 创建存储卷
        multi_project_steps.step_create_volume_in_multi_project(cluster_name=clusters,
                                                                project_name=create_multi_project,
                                                                volume_name=volume_name)
        # 创建资源并将存储卷绑定到资源
        multi_project_steps.step_create_sts_in_multi_project(cluster_name=clusters,
                                                             project_name=create_multi_project, work_name=work_name,
                                                             container_name=container_name, image=image,
                                                             replicas=replicas,
                                                             ports=port, service_ports=service_port,
                                                             volumemount=volume_mounts, volume_info=volume_info,
                                                             service_name=service_name)
        # 验证资源创建成功
        for name in clusters:
            i = 0
            while i < 180:
                # 获取工作负载的状态
                response = multi_project_steps.step_get_workload_in_multi_project(cluster_name=name,
                                                                                  project_name=create_multi_project,
                                                                                  type='statefulsets',
                                                                                  condition=condition)
                try:
                    ready_replicas = response.json()['status']['readyReplicas']
                    if ready_replicas == replicas:
                        break
                except Exception as e:
                    print(e)
                i += 5
                time.sleep(5)
            # 获取存储卷状态
            re = multi_project_steps.step_get_volume_status_in_multi_project(cluster_name=name,
                                                                             project_name=create_multi_project,
                                                                             volume_name=volume_name)
            status = re.json()['status']['phase']
            # 验证存储卷状态正常
            with pytest.assume:
                assert status == 'Bound'
        # 删除工作负载
        multi_project_steps.step_delete_workload_in_multi_project(project_name=create_multi_project, type='statefulsets',
                                                                  work_name=work_name)
        # 删除存储卷
        multi_project_steps.step_delete_volume_in_multi_project(create_multi_project, volume_name)

    @allure.story('存储管理-存储卷')
    @allure.title('在多集群项目创建存储卷，然后将存储卷绑定到新建的service上，最后验证资源和存储卷的状态正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_volume_for_service(self, create_multi_workspace, create_multi_project):
        clusters = cluster_steps.step_get_cluster_name()

        volume_name = 'volume-service' + str(commonFunction.get_random())  # 存储卷的名称
        type_name = 'volume-type'  # 存储卷的类型
        service_name = 'service' + str(commonFunction.get_random())  # 工作负载的名称
        image = 'redis'  # 镜像名称
        container_name = 'container-daemon' + str(commonFunction.get_random())  # 容器名称
        condition = service_name  # 查询条件
        port_service = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]  # service的端口信息
        port_deploy = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80}]  # 容器的端口信息
        volume_mounts = [{"name": type_name, "readOnly": False, "mountPath": "/data"}]  # 设置挂载哦的存储卷
        volume_info = [{"name": type_name, "persistentVolumeClaim": {"claimName": volume_name}}]  # 存储卷的信息
        strategy_info = {"type": "RollingUpdate",
                         "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
        replicas = 2  # 副本数
        # 创建存储卷
        multi_project_steps.step_create_volume_in_multi_project(cluster_name=clusters,
                                                                project_name=create_multi_project,
                                                                volume_name=volume_name)
        # 创建service
        multi_project_steps.step_create_service_in_multi_project(cluster_name=clusters,
                                                                 project_name=create_multi_project,
                                                                 service_name=service_name, port=port_service)
        # 创建service绑定的deployment
        multi_project_steps.step_create_deploy_in_multi_project(cluster_name=clusters,
                                                                project_name=create_multi_project,
                                                                work_name=service_name,
                                                                container_name=container_name,
                                                                ports=port_deploy, volumemount=volume_mounts,
                                                                image=image,
                                                                replicas=replicas,
                                                                volume_info=volume_info, strategy=strategy_info)
        for name in clusters:
            i = 0
            while i < 180:
                # 获取工作负载的状态
                response = multi_project_steps.step_get_workload_in_multi_project(cluster_name=name,
                                                                                  project_name=create_multi_project,
                                                                                  type='deployments',
                                                                                  condition=condition)
                try:
                    ready_replicas = response.json()['status']['readyReplicas']
                    if ready_replicas == replicas:
                        break
                except Exception as e:
                    print(e)
                i += 5
                time.sleep(5)
            # 获取存储卷状态
            response = multi_project_steps.step_get_volume_status_in_multi_project(cluster_name=name,
                                                                                   project_name=create_multi_project,
                                                                                   volume_name=volume_name)
            status = response.json()['status']['phase']
            # 验证存储卷状态正常
            with pytest.assume:
                assert status == 'Bound'
        # 删除service
        multi_project_steps.step_delete_workload_in_multi_project(project_name=create_multi_project, type='services',
                                                                  work_name=service_name)
        # 删除deployment
        multi_project_steps.step_delete_workload_in_multi_project(project_name=create_multi_project, type='deployments',
                                                                  work_name=service_name)
        # 删除存储卷
        multi_project_steps.step_delete_volume_in_multi_project(create_multi_project, volume_name)

    @allure.story('应用负载-工作负载')
    @allure.title('在多集群项目创建未绑定存储卷的deployment，并验证运行成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_deployment(self, create_multi_workspace, create_multi_project):
        clusters = cluster_steps.step_get_cluster_name()
        workload_name = 'workload' + str(commonFunction.get_random())  # 工作负载名称
        container_name = 'container' + str(commonFunction.get_random())  # 容器名称
        image = 'nginx'  # 镜像名称
        condition = 'name=' + workload_name  # 查询条件
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 81}]  # 容器的端口信息
        volume_mounts = []  # 设置挂载的存储卷
        strategy_info = {"type": "RollingUpdate",
                         "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
        replicas = 1  # 副本数
        volume_info = []
        status = ''
        # 创建工作负载
        multi_project_steps.step_create_deploy_in_multi_project(cluster_name=clusters,
                                                                project_name=create_multi_project,
                                                                work_name=workload_name,
                                                                container_name=container_name, ports=port,
                                                                volumemount=volume_mounts,
                                                                image=image, replicas=replicas,
                                                                volume_info=volume_info,
                                                                strategy=strategy_info)

        for name in clusters:
            i = 0
            while i < 180:
                response = multi_project_steps.step_get_workload_in_multi_project(cluster_name=name,
                                                                                  project_name=create_multi_project,
                                                                                  type='deployments',
                                                                                  condition=condition)
                try:
                    status = response.json()['status']
                except Exception as e:
                    print(e)
                # 验证资源的所有副本已就绪
                if 'unavailableReplicas' not in status:
                    break
                time.sleep(1)
                i = i + 1
            with pytest.assume:
                assert 'unavailableReplicas' not in status
        # 删除deployment
        multi_project_steps.step_delete_workload_in_multi_project(project_name=create_multi_project,
                                                                       type='deployments', work_name=workload_name)

    @allure.story('应用负载-工作负载')
    @allure.title('在多集群项目按名称查询存在的deployment')
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_deployment_by_name(self, create_multi_workspace, create_multi_project):
        clusters = cluster_steps.step_get_cluster_name()

        workload_name = 'workload' + str(commonFunction.get_random())  # 工作负载名称
        conndition = workload_name  # 查询条件
        container_name = 'container' + str(commonFunction.get_random())  # 容器名称
        image = 'nginx'  # 镜像名称
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 81}]  # 容器的端口信息
        volume_mounts = []  # 设置挂载哦的存储卷
        strategy_info = {"type": "RollingUpdate",
                         "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
        replicas = 1  # 副本数
        volume_info = []
        name = ''
        # 创建工作负载
        multi_project_steps.step_create_deploy_in_multi_project(cluster_name=clusters,
                                                                project_name=create_multi_project,
                                                                work_name=workload_name,
                                                                container_name=container_name, ports=port,
                                                                volumemount=volume_mounts,
                                                                image=image, replicas=replicas,
                                                                volume_info=volume_info,
                                                                strategy=strategy_info)
        time.sleep(3)
        # 按名称精确查询deployment
        response = multi_project_steps.step_get_workload_in_multi_project_list(
            project_name=create_multi_project,
            type='deployments', condition=conndition)
        # 获取并验证deployment的名称正确
        try:
            name = response.json()['items'][0]['metadata']['name']
        except Exception as e:
            print(e)
        with pytest.assume:
            assert name == workload_name
        # 删除deployment
        multi_project_steps.step_delete_workload_in_multi_project(project_name=create_multi_project,
                                                                       type='deployments', work_name=workload_name)

    @allure.story('应用负载-工作负载')
    @allure.title('在多集群项目创建未绑定存储卷的StatefulSets，并验证运行成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_sts(self, create_multi_workspace, create_multi_project):
        clusters = cluster_steps.step_get_cluster_name()

        workload_name = 'workload' + str(commonFunction.get_random())  # 工作负载名称
        container_name = 'container' + str(commonFunction.get_random())  # 容器名称
        image = 'nginx'  # 镜像名称
        replicas = 2  # 副本数
        condition = workload_name  # 查询条件
        volume_info = []
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]
        service_port = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]
        service_name = 'service' + workload_name
        volume_mounts = []
        ready_replicas =''
        # 创建工作负载
        multi_project_steps.step_create_sts_in_multi_project(cluster_name=clusters,
                                                             project_name=create_multi_project,
                                                             work_name=workload_name,
                                                             container_name=container_name,
                                                             image=image, replicas=replicas,
                                                             volume_info=volume_info,
                                                             ports=port,
                                                             service_ports=service_port,
                                                             volumemount=volume_mounts,
                                                             service_name=service_name)
        # 验证资源创建成功
        for name in clusters:
            i = 0
            while i < 180:
                # 获取工作负载的状态
                response = multi_project_steps.step_get_workload_in_multi_project(cluster_name=name,
                                                                                  project_name=create_multi_project,
                                                                                  type='statefulsets',
                                                                                  condition=condition)
                try:
                    ready_replicas = response.json()['status']['readyReplicas']
                    if ready_replicas == replicas:
                        break
                except Exception as e:
                    print(e)
                i += 1
                time.sleep(1)
        with pytest.assume:
            assert ready_replicas == replicas
        # 删除创建的工作负载
        multi_project_steps.step_delete_workload_in_multi_project(project_name=create_multi_project,
                                                                  type='services', work_name=workload_name)
        multi_project_steps.step_delete_workload_in_multi_project(project_name=create_multi_project,
                                                                       type='statefulsets', work_name=workload_name)

    @allure.story('应用负载-工作负载')
    @allure.title('在多集群项目按名称查询存在的StatefulSets')
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_sts_by_name(self, create_multi_workspace, create_multi_project):
        clusters = cluster_steps.step_get_cluster_name()
        workload_name = 'workload' + str(commonFunction.get_random())  # 工作负载名称
        condition = workload_name
        workload_type = 'statefulsets'
        container_name = 'container' + str(commonFunction.get_random())  # 容器名称
        image = 'nginx'  # 镜像名称
        replicas = 2  # 副本数
        volume_info = []
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]
        service_port = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]
        service_name = 'service' + workload_name
        volume_mounts = []
        name = ''
        # 创建工作负载
        multi_project_steps.step_create_sts_in_multi_project(cluster_name=clusters,
                                                             project_name=create_multi_project,
                                                             work_name=workload_name,
                                                             container_name=container_name,
                                                             image=image, replicas=replicas,
                                                             volume_info=volume_info,
                                                             ports=port,
                                                             service_ports=service_port,
                                                             volumemount=volume_mounts,
                                                             service_name=service_name)

        # 按名称精确查询statefulsets
        time.sleep(1)
        response = multi_project_steps.step_get_workload_in_multi_project_list(
            project_name=create_multi_project,
            type=workload_type, condition=condition)
        # 获取并验证statefulsets的名称正确
        try:
            name = response.json()['items'][0]['metadata']['name']
        except Exception as e:
            print(e)
            # 删除创建的工作负载
            multi_project_steps.step_delete_workload_in_multi_project(project_name=create_multi_project,
                                                                      type=workload_type,
                                                                      work_name=workload_name)
            pytest.xfail('工作负载创建失败，标记为xfail')
        with pytest.assume:
            assert name == workload_name
        # 删除创建的statefulsets
        multi_project_steps.step_delete_workload_in_multi_project(project_name=create_multi_project,
                                                                  type='services', work_name=workload_name)
        multi_project_steps.step_delete_workload_in_multi_project(project_name=create_multi_project,
                                                                       type=workload_type,
                                                                       work_name=workload_name)

    @allure.story('应用负载-服务')
    @allure.title('创建未绑定存储卷的service，并验证运行成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_service(self, create_multi_workspace, create_multi_project):
        clusters = cluster_steps.step_get_cluster_name()
        service_name = 'service' + str(commonFunction.get_random())  # 服务名称
        port_service = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]  # service的端口信息
        image = 'nginx'  # 镜像名称
        container_name = 'container' + str(commonFunction.get_random())  # 容器名称
        condition = service_name  # 查询deploy和service条件
        port_deploy = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]  # 容器的端口信息
        volume_mounts = []  # 设置挂载的存储卷
        strategy_info = {"type": "RollingUpdate",
                         "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
        replicas = 2  # 副本数
        volume_info = []
        name = ''
        # 创建service
        multi_project_steps.step_create_service_in_multi_project(cluster_name=clusters,
                                                                 project_name=create_multi_project,
                                                                 service_name=service_name, port=port_service)
        # 创建service绑定的deployment
        multi_project_steps.step_create_deploy_in_multi_project(cluster_name=clusters,
                                                                project_name=create_multi_project,
                                                                work_name=service_name,
                                                                container_name=container_name,
                                                                ports=port_deploy, volumemount=volume_mounts,
                                                                image=image,
                                                                replicas=replicas,
                                                                volume_info=volume_info, strategy=strategy_info)
        i = 0
        while i < 180:
            # 验证service创建成功
            response = multi_project_steps.step_get_workload_in_multi_project_list(
                project_name=create_multi_project,
                type='services', condition=condition)
            try:
                status = response.json()['items'][0]['status']['conditions'][0]['status']
                name = response.json()['items'][0]['metadata']['name']
                if status == 'True':
                    break
            except Exception as e:
                print(e)
            time.sleep(1)
            i += 1
        with pytest.assume:
            assert name == service_name
        # 删除service
        multi_project_steps.step_delete_workload_in_multi_project(project_name=create_multi_project, type='services',
                                                                  work_name=service_name)
        # 删除deployment
        multi_project_steps.step_delete_workload_in_multi_project(project_name=create_multi_project, type='deployments',
                                                                  work_name=service_name)

    @allure.story('应用负载-服务')
    @allure.title('在多集群项目删除service，并验证删除成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_service(self, create_multi_workspace, create_multi_project):
        clusters = cluster_steps.step_get_cluster_name()
        service_name = 'service' + str(commonFunction.get_random())
        port_service = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]  # service的端口信息
        condition = service_name  # 查询service的条件
        name = ''
        count = ''
        # 创建service
        multi_project_steps.step_create_service_in_multi_project(cluster_name=clusters,
                                                                 project_name=create_multi_project,
                                                                 service_name=service_name, port=port_service)
        i = 0
        while i < 180:
            # 验证service创建成功
            response = multi_project_steps.step_get_workload_in_multi_project_list(
                project_name=create_multi_project,
                type='services', condition=condition)
            try:
                status = response.json()['items'][0]['status']['conditions'][0]['status']
                name = response.json()['items'][0]['metadata']['name']
                if status == 'True':
                    break
            except Exception as e:
                print(e)
            time.sleep(1)
            i += 1
        with pytest.assume:
            assert name == service_name
        # 删除service
        multi_project_steps.step_delete_workload_in_multi_project(project_name=create_multi_project, type='services',
                                                                  work_name=service_name)
        j = 0
        while j < 180:
            # 验证service删除成功
            response = multi_project_steps.step_get_workload_in_multi_project_list(
                project_name=create_multi_project,
                type='services', condition=condition)
            count = response.json()['totalItems']
            if count == 0:
                break
            else:
                time.sleep(3)
                j += 3
        assert count == 0

    @allure.story('应用负载-应用路由')
    @allure.title('在多集群项目为服务创建应用路由')
    def test_create_route(self, create_multi_workspace, create_multi_project):
        clusters = cluster_steps.step_get_cluster_name()
        # 创建服务
        service_name = 'service' + str(commonFunction.get_random())  # 服务名称
        port_service = [{"name": "tcp-80", "protocol": "TCP", "port": 80, "targetPort": 80}]  # service的端口信息
        image = 'nginx'  # 镜像名称
        container_name = 'container' + str(commonFunction.get_random())  # 容器名称
        condition = service_name  # 查询deploy和service条件
        port_deploy = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80, "servicePort": 80}]  # 容器的端口信息
        volume_mounts = []  # 设置挂载的存储卷
        strategy_info = {"type": "RollingUpdate",
                         "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
        replicas = 1  # 副本数
        volume_info = []
        name = ''
        # 创建service
        multi_project_steps.step_create_service_in_multi_project(cluster_name=clusters,
                                                                 project_name=create_multi_project,
                                                                 service_name=service_name, port=port_service)
        # 创建service绑定的deployment
        multi_project_steps.step_create_deploy_in_multi_project(cluster_name=clusters,
                                                                project_name=create_multi_project,
                                                                work_name=service_name,
                                                                container_name=container_name,
                                                                ports=port_deploy, volumemount=volume_mounts,
                                                                image=image,
                                                                replicas=replicas,
                                                                volume_info=volume_info, strategy=strategy_info)
        i = 0
        while i < 180:
            # 验证service创建成功
            response = multi_project_steps.step_get_workload_in_multi_project_list(
                project_name=create_multi_project,
                type='services', condition=condition)
            try:
                status = response.json()['items'][0]['status']['conditions'][0]['status']
                name = response.json()['items'][0]['metadata']['name']
                if status == 'True':
                    break
            except Exception as e:
                print(e)
            time.sleep(1)
            i += 1
        with pytest.assume:
            assert name == service_name
        # 为服务创建路由
        ingress_name = 'ingress' + str(commonFunction.get_random())
        host = 'www.test' + str(commonFunction.get_random()) + '.com'
        service_info = {"serviceName": service_name, "servicePort": 80}
        response = multi_project_steps.step_create_route_in_multi_project(cluster_name=clusters,
                                                                          project_name=create_multi_project,
                                                                          ingress_name=ingress_name, host=host,
                                                                          service_info=service_info)
        # 获取路由绑定的服务名称
        name = response.json()['spec']['overrides'][0]['clusterOverrides'][0]['value'][0]['http']['paths'][0][
            'backend']['serviceName']
        # 验证路由创建成功
        assert name == service_name

        # 删除路由
        multi_project_steps.step_delete_route_in_multi_project(project_name=create_multi_project, ingress_name=ingress_name)
        # 删除service
        multi_project_steps.step_delete_workload_in_multi_project(project_name=create_multi_project, type='services',
                                                                  work_name=service_name)
        # 删除deployment
        multi_project_steps.step_delete_workload_in_multi_project(project_name=create_multi_project, type='deployments',
                                                                  work_name=service_name)

    @allure.story('项目设置-高级设置')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('gateway_type, title, annotations',
                             [('NodePort', '在多集群项目设置网关-NodePort', {"servicemesh.kubesphere.io/enabled": "false"}),
                              ('LoadBalancer', '在多集群项目设置网关-LoadBalancer',
                               {"service.beta.kubernetes.io/qingcloud-load-balancer-eip-ids": "",
                                "service.beta.kubernetes.io/qingcloud-load-balancer-type": "0",
                                "servicemesh.kubesphere.io/enabled": "false"})
                              ])
    def test_create_gateway(self, create_multi_workspace, create_multi_project, title, gateway_type, annotations):
        clusters = cluster_steps.step_get_cluster_name()
        # 创建网关
        multi_project_steps.step_create_gateway_in_multi_project(cluster_name=clusters[0],
                                                                 project_name=create_multi_project,
                                                                 type=gateway_type, annotations=annotations)
        # 查询网关
        response = multi_project_steps.step_get_gateway_in_multi_project(cluster_name=clusters[0],
                                                                         project_name=create_multi_project)
        # 获取网关的类型
        gateway_type_new = response.json()['spec']['type']
        # 验证网关创建正确
        with pytest.assume:
            assert gateway_type_new == gateway_type
        # 验证网关创建成功
        with pytest.assume:
            assert response.status_code == 200
        # 删除网关
        multi_project_steps.step_delete_gateway_in_multi_project(cluster_name=clusters[0],
                                                                 project_name=create_multi_project)
        # 验证网关删除成功
        response = multi_project_steps.step_get_gateway_in_multi_project(cluster_name=clusters[0],
                                                                         project_name=create_multi_project)
        assert response.json()['message'] == 'service \"kubesphere-router-' + create_multi_project + '\" not found'

    @allure.story('项目设置-高级设置')
    @allure.title('在多集群项目编辑网关')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_edit_gateway(self, create_multi_workspace, create_multi_project):
        gateway_type = 'LoadBalancer'  # 网关类型
        gateway_type_new = 'NodePort'
        annotations = {"service.beta.kubernetes.io/qingcloud-load-balancer-eip-ids": "",
                       "service.beta.kubernetes.io/qingcloud-load-balancer-type": "0",
                       "servicemesh.kubesphere.io/enabled": "false"}  # 网关的注释信息
        annotations_new = {"servicemesh.kubesphere.io/enabled": "false"}  # 网关的注释信息
        clusters = cluster_steps.step_get_cluster_name()
        # 创建网关
        multi_project_steps.step_create_gateway_in_multi_project(cluster_name=clusters[0],
                                                                 project_name=create_multi_project,
                                                                 type=gateway_type, annotations=annotations)
        # 编辑网关
        multi_project_steps.step_edit_gateway_in_multi_project(cluster_name=clusters[0],
                                                               project_name=create_multi_project,
                                                               type=gateway_type_new, annotations=annotations_new)
        # 查询网关
        response = multi_project_steps.step_get_gateway_in_multi_project(cluster_name=clusters[0],
                                                                         project_name=create_multi_project)
        # 获取网关的注释信息
        gateway_annotations = response.json()['metadata']['annotations']
        # 验证网关修改成功
        with pytest.assume:
            assert gateway_annotations == annotations_new
        # 删除网关
        multi_project_steps.step_delete_gateway_in_multi_project(cluster_name=clusters[0],
                                                                 project_name=create_multi_project)

    @allure.story('应用负载-工作负载')
    @allure.title('在多集群项目修改工作负载副本并验证运行正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_add_work_replica(self, create_multi_workspace, create_multi_project):
        clusters = cluster_steps.step_get_cluster_name()
        workload_name = 'workload' + str(commonFunction.get_random())  # 工作负载名称
        container_name = 'container' + str(commonFunction.get_random())  # 容器名称
        image = 'nginx'  # 镜像名称
        condition = workload_name  # 查询条件
        port = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 81}]  # 容器的端口信息
        volume_mounts = []  # 设置挂载的存储卷
        strategy_info = {"type": "RollingUpdate",
                         "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}  # 策略信息
        replicas = 1  # 副本数
        volume_info = []
        # 创建工作负载
        multi_project_steps.step_create_deploy_in_multi_project(cluster_name=clusters,
                                                                project_name=create_multi_project,
                                                                work_name=workload_name,
                                                                container_name=container_name, ports=port,
                                                                volumemount=volume_mounts,
                                                                image=image, replicas=replicas,
                                                                volume_info=volume_info,
                                                                strategy=strategy_info)

        # 在工作负载列表中查询创建的工作负载，并验证其状态为运行中，最长等待时间180s
        for name in clusters:
            i = 0
            while i < 180:
                response = multi_project_steps.step_get_workload_in_multi_project(cluster_name=name,
                                                                                  project_name=create_multi_project,
                                                                                  type='deployments',
                                                                                  condition=condition)
                try:
                    status = response.json()['status']
                    # 验证资源的所有副本已就绪
                    if 'unavailableReplicas' not in status:
                        break
                except Exception as e:
                    print(e)
                time.sleep(10)
                i = i + 10
        replicas_new = 2  # 副本数
        # 修改副本数
        multi_project_steps.step_modify_work_replicas_in_multi_project(cluster_name=clusters[0],
                                                                       project_name=create_multi_project,
                                                                       type='deployments',
                                                                       work_name=workload_name,
                                                                       replicas=replicas_new)
        # 获取工作负载中所有的容器组，并验证其运行正常，最长等待时间60s
        time.sleep(5)
        # 查询容器的信息
        re = multi_project_steps.step_get_work_pod_info_in_multi_project(cluster_name=clusters[0],
                                                                         project_name=create_multi_project,
                                                                         work_name=workload_name)
        pod_count = re.json()['totalItems']
        # 验证pod数量正确
        with pytest.assume:
            assert pod_count == replicas_new
        # 删除deployment
        multi_project_steps.step_delete_workload_in_multi_project(project_name=create_multi_project, type='deployments',
                                                                  work_name=workload_name)

    @allure.story('存储管理-存储卷')
    @allure.title('在多集群项目删除存在的存储卷，并验证删除成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_volume(self, create_multi_workspace, create_multi_project):
        clusters = cluster_steps.step_get_cluster_name()
        volume_name = 'volume-stateful' + str(commonFunction.get_random())  # 存储卷的名称
        response = ''
        # 创建存储卷
        multi_project_steps.step_create_volume_in_multi_project(cluster_name=clusters,
                                                                project_name=create_multi_project,
                                                                volume_name=volume_name)
        # 删除存储卷
        multi_project_steps.step_delete_volume_in_multi_project(create_multi_project, volume_name)
        # 查询被删除的存储卷
        i = 0
        # 验证存储卷被删除，最长等待时间为30s
        while i < 30:
            response = project_steps.step_get_volume(create_multi_project, volume_name)
            # 存储卷快照的状态为布尔值，故先将结果转换我字符类型
            if response.json()['totalItems'] == 0:
                print("删除存储卷耗时:" + str(i) + '秒')
                break
            time.sleep(1)
            i = i + 1
        # 验证存储卷成功
        assert response.json()['totalItems'] == 0

    @allure.story('项目设置-基本信息')
    @allure.title('编辑多集群项目信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_edit_project(self, create_multi_workspace, create_multi_project):
        alias_name = 'test-231313!#!G@#K!G#G!PG#'  # 别名信息
        description = '测试test123！@#'  # 描述信息
        clusters = cluster_steps.step_get_cluster_name()
        # 编辑项目信息
        response = multi_project_steps.step_edit_project_in_multi_project(cluster_name=clusters,
                                                                          ws_name=create_multi_workspace,
                                                                          project_name=create_multi_project,
                                                                          alias_name=alias_name,
                                                                          description=description)
        # 验证编辑成功
        assert response.status_code == 200

    @allure.story('项目设置-项目配额')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('title, hard',
                             [('在多集群项目设置项目配额-输入错误的cpu信息(包含字母)', {"limits.cpu": "11www",
                                                                 "requests.cpu": "1www"
                                                                 }),
                              ('在多集群项目设置项目配额-输入错误的cpu信息(包含负数)', {"limits.cpu": "11www",
                                                                 "requests.cpu": "1www"
                                                                 }),
                              ('在多集群项目设置项目配额-输入错误的内存(包含非单位字母)', {"limits.memory": "10Gi",
                                                                 "requests.memory": "1Giw"}),
                              ('在多集群项目设置项目配额-输入错误的内存(包含负数)', {"limits.memory": "-10Gi",
                                                              "requests.memory": "1Gi"}),
                              ('在多集群项目只设置项目配额-输入错误的资源配额信息(包含字母)', {"count/pods": "100q",
                                                                   "count/deployments.apps": "6",
                                                                   "count/statefulsets.apps": "6",
                                                                   "count/jobs.batch": "1",
                                                                   "count/services": "5",
                                                                   "persistentvolumeclaims": "6",
                                                                   "count/daemonsets.apps": "5",
                                                                   "count/cronjobs.batch": "4",
                                                                   "count/ingresses.extensions": "4",
                                                                   "count/secrets": "8",
                                                                   "count/configmaps": "7"}),
                              ('在多集群项目只设置项目配额-输入错误的资源配额信息(包含负数)', {"count/pods": "-100",
                                                                   "count/deployments.apps": "6",
                                                                   "count/statefulsets.apps": "6",
                                                                   "count/jobs.batch": "1",
                                                                   "count/services": "5",
                                                                   "persistentvolumeclaims": "6",
                                                                   "count/daemonsets.apps": "5",
                                                                   "count/cronjobs.batch": "4",
                                                                   "count/ingresses.extensions": "4",
                                                                   "count/secrets": "8",
                                                                   "count/configmaps": "7"}),
                              ])
    def test_edit_project_quota_wrong(self, create_multi_workspace, create_multi_project, title, hard):
        clusters = cluster_steps.step_get_cluster_name()
        # 获取项目配额的resource_version
        resource_version = multi_project_steps.step_get_project_quota_version_in_multi_project(clusters[0], create_multi_project)
        # 编辑配额信息
        r = multi_project_steps.step_edit_project_quota_in_multi_project(clusters[0], create_multi_project, hard, resource_version)
        # 获取编辑结果
        status = r.json()['status']
        # 验证编辑失败
        assert status == 'Failure'

    @allure.story('项目设置-项目配额')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('title, hard',
                             [('在多集群项目只设置项目配额-CPU', {"limits.cpu": "40", "requests.cpu": "40"}),
                              ('在多集群项目只设置项目配额-内存', {"limits.memory": "1000Gi", "requests.memory": "1Gi"}),
                              ('在多集群项目设置项目配额-CPU、内存', {"limits.memory": "1000Gi", "requests.memory": "1Gi",
                                                       "limits.cpu": "100", "requests.cpu": "100"}),
                              ('在多集群项目只设置项目配额-资源配额', {"limits.memory": "1000Gi", "requests.memory": "1Gi",
                                                      "limits.cpu": "100", "requests.cpu": "100"}),
                              ('在多集群下项目设置项目配额-cpu、memory、资源配额', {"count/configmaps": "7",
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
                                                                 "requests.cpu": "200", "requests.memory": "3Gi"})
                              ])
    def test_edit_project_quota(self, create_multi_workspace, create_multi_project, title, hard):
        clusters = cluster_steps.step_get_cluster_name()
        # 获取项目配额的resource_version
        resource_version = multi_project_steps.step_get_project_quota_version_in_multi_project(clusters[0], create_multi_project)
        # 编辑配额信息
        multi_project_steps.step_edit_project_quota_in_multi_project(clusters[0], create_multi_project, hard, resource_version)
        # 获取修改后的配额信息
        i = 0
        while i < 180:
            response = multi_project_steps.step_get_project_quota_in_multi_project(clusters[0], create_multi_project)
            try:
                hard_actual = response.json()['data']['hard']
                if hard_actual:
                    # 验证配额修改成功
                    assert hard_actual == hard
                    break
            except Exception as e:
                print(e)
            time.sleep(2)
            i += 2

    @allure.story('项目设置-资源默认请求')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('title, limit, re',
                             [('在多集群项目只设置资源默认请求-cpu', {"cpu": "16"}, {"cpu": "2"}),
                              ('只设置资源默认请求-内存', {"memory": "1000Mi"}, {"memory": "1Mi"}),
                              ('在多集群项目只设置资源默认请求-内存、cpu', {"cpu": "15", "memory": "1000Mi"},
                               {"cpu": "2", "memory": "1Mi"})
                              ])
    def test_edit_container_quota(self, create_multi_workspace, create_multi_project, title, limit, re):
        clusters = cluster_steps.step_get_cluster_name()
        # 获取资源默认请求
        response = multi_project_steps.step_get_container_quota_in_multi_project(create_multi_project, create_multi_workspace)
        resource_version = None
        try:
            if response.json()['items'][0]['metadata']['resourceVersion']:
                resource_version = response.json()['items'][0]['metadata']['resourceVersion']
            else:
                resource_version = None
        except Exception as e:
            print(e)
        # 编辑资源默认请求
        multi_project_steps.step_edit_container_quota_in_multi_project(clusters, create_multi_project,
                                                                       resource_version, limit, re)
        # 查询编辑结果
        response = multi_project_steps.step_get_container_quota_in_multi_project(create_multi_project, create_multi_workspace)
        limit_actual = response.json()['items'][0]['spec']['template']['spec']['limits'][0]['default']
        request_actual = response.json()['items'][0]['spec']['template']['spec']['limits'][0]['defaultRequest']
        # 验证编辑成功
        assert limit == limit_actual
        assert re == request_actual

    # @allure.story('项目设置-资源默认请求')
    # @allure.title('在多集群项目只设置资源默认请求-输入错误的cpu信息(包含字母)')
    # # 接口未做限制
    # def wx_test_edit_container_quota_wrong_cpu(self):
    #     # 获取环境中所有的多集群项目
    #     multi_projects = multi_project_steps.step_get_multi_project_all(self.ws_name)
    #     for project_info in multi_projects:
    #         # 获取资源默认请求
    #         response = multi_project_steps.step_get_container_quota_in_multi_project(project_info[0], project_info[2])
    #         resource_version = None
    #         try:
    #             if response.json()['items'][0]['metadata']['resourceVersion']:
    #                 resource_version = response.json()['items'][0]['metadata']['resourceVersion']
    #             else:
    #                 resource_version = None
    #         except Exception as e:
    #             print(e)
    #         # 编辑资源默认请求
    #         limit = {"cpu": "16aa"}
    #         request = {"cpu": "2"}
    #         r = multi_project_steps.step_edit_container_quota_in_multi_project(project_info[1], project_info[0],
    #                                                                            resource_version, limit, request)
    #         # 获取编辑结果
    #         status = r.json()['status']
    #         # 验证编辑失败
    #         assert status == 'Failure'

    # @allure.story('项目设置-资源默认请求')
    # @allure.title('只设置资源默认请求-输入错误的cpu信息(包含负数)')
    # # 接口未做限制
    # def wx_test_edit_container_quota_wrong_cpu_1(self):
    #     # 获取环境中所有的多集群项目
    #     multi_projects = multi_project_steps.step_get_multi_project_all()
    #     for project_info in multi_projects:
    #         # 获取资源默认请求
    #         response = multi_project_steps.step_get_container_quota_in_multi_project(project_info[0], project_info[2])
    #         resource_version = None
    #         try:
    #             if response.json()['items'][0]['metadata']['resourceVersion']:
    #                 resource_version = response.json()['items'][0]['metadata']['resourceVersion']
    #             else:
    #                 resource_version = None
    #         except Exception as e:
    #             print(e)
    #         # 编辑资源默认请求
    #         limit = {"cpu": "-16"}
    #         request = {"cpu": "-2"}
    #         r = multi_project_steps.step_edit_container_quota_in_multi_project(project_info[1], project_info[0],
    #                                                                            resource_version, limit, request)
    #         # 获取编辑结果
    #         status = r.json()['status']
    #         # 验证编辑失败
    #         assert status == 'Failure'

    # @allure.story('项目设置-资源默认请求')
    # @allure.title('只设置资源默认请求-输入错误的内存信息(包含非单位字母)')
    # # 接口未做限制
    # def wx_test_edit_container_quota_wrong_memory(self):
    #     # 获取环境中所有的多集群项目
    #     multi_projects = multi_project_steps.step_get_multi_project_all()
    #     for project_info in multi_projects:
    #         # 获取资源默认请求
    #         response = multi_project_steps.step_get_container_quota_in_multi_project(project_info[0], project_info[2])
    #         resource_version = None
    #         try:
    #             if response.json()['items'][0]['metadata']['resourceVersion']:
    #                 resource_version = response.json()['items'][0]['metadata']['resourceVersion']
    #             else:
    #                 resource_version = None
    #         except Exception as e:
    #             print(e)
    #         # 编辑资源默认请求
    #         limit = {"memory": "1000aMi"}
    #         request = {"memory": "1Mi"}
    #         r = multi_project_steps.step_edit_container_quota_in_multi_project(project_info[1], project_info[0],
    #                                                                            resource_version, limit, request)
    #     # 获取编辑结果
    #     status = r.json()['status']
    #     # 验证编辑失败
    #     assert status == 'Failure'

    @allure.story('配置中心-密钥')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('title, type',
                             [('在多集群项目创建默认类型的密钥', 'default'),
                              ('在多集群项目创建TLS类型的密钥', 'TLS'),
                              ('在多集群项目创建image类型的密钥', 'image'),
                              ('在多集群项目创建账号密码类型的密钥', 'username')
                              ])
    def test_create_secret(self, create_multi_workspace, create_multi_project, title, type):
        clusters = cluster_steps.step_get_cluster_name()
        # 在多集群项目创建密钥
        secret_name = 'secret' + str(commonFunction.get_random())
        if type == 'default':
            multi_project_steps.step_create_secret_default_in_multi_project(cluster_name=clusters,
                                                                            project_name=create_multi_project,
                                                                            secret_name=secret_name, key='wx',
                                                                            value='dGVzdA==')
        elif type == 'TLS':
            multi_project_steps.step_create_secret_tls_in_multi_project(cluster_name=clusters,
                                                                        project_name=create_multi_project,
                                                                        secret_name=secret_name, credential='d3g=',
                                                                        key='dGVzdA==')
        elif type == 'image':
            multi_project_steps.step_create_secret_image_in_multi_project(cluster_name=clusters,
                                                                          project_name=create_multi_project,
                                                                          secret_name=secret_name)
        elif type == 'username':
            multi_project_steps.step_create_secret_account_in_multi_project(cluster_name=clusters,
                                                                            project_name=create_multi_project,
                                                                            secret_name=secret_name, username='d3g=',
                                                                            password='dGVzdA==')

        i = 0
        while i < 180:
            # 查询创建的密钥
            response = multi_project_steps.step_get_federatedsecret(project_name=create_multi_project,
                                                                    secret_name=secret_name)
            try:
                # 获取密钥的数量和状态
                secret_count = response.json()['totalItems']
                secret_status = response.json()['items'][0]['status']['conditions'][0]['status']
                if secret_status:
                    # 验证查询到的密钥数量和密钥的状态正确
                    with pytest.assume:
                        assert secret_count == 1
                    with pytest.assume:
                        assert secret_status == 'True'
                    break
            except Exception as e:
                print(e)
            time.sleep(5)
            i += 5
        # 删除创建的密钥
        multi_project_steps.step_delete_federatedsecret(project_name=create_multi_project, secret_name=secret_name)

    @allure.story('配置中心-密钥')
    @allure.title('在多集群项目创建配置')
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_config_map(self, create_multi_workspace, create_multi_project):
        clusters = cluster_steps.step_get_cluster_name()
        config_name = 'config-map' + str(commonFunction.get_random())
        # 在多集群项目创建配置
        multi_project_steps.step_create_config_map_in_multi_project(cluster_name=clusters,
                                                                    project_name=create_multi_project,
                                                                    config_name=config_name, key='wx', value='test')
        i = 0
        while i < 180:
            # 查询创建的配置
            response = multi_project_steps.step_get_federatedconfigmap(project_name=create_multi_project,
                                                                       config_name=config_name)
            try:
                # 获取配置的数量和状态
                secret_count = response.json()['totalItems']
                secret_status = response.json()['items'][0]['status']['conditions'][0]['status']
                if secret_status:
                    # 验证查询到的配置数量和密钥的状态正确
                    with pytest.assume:
                        assert secret_count == 1
                    with pytest.assume:
                        assert secret_status == 'True'
                    break
            except Exception as e:
                print(e)
            time.sleep(3)
            i += 3
        # 删除创建的配置
        multi_project_steps.step_delete_config_map(project_name=create_multi_project, config_name=config_name)

    @allure.story('项目设置-高级设置')
    @allure.title('落盘日志收集-开启')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.skipif(commonFunction.get_components_status_of_cluster('logging') is False, reason='集群未开启logging功能')
    def test_disk_log_collection_open(self, create_multi_workspace, create_multi_project):
        # 开启落盘日志收集功能
        multi_project_steps.step_set_disk_log_collection(project_name=create_multi_project, set='enabled')
        # 查看落盘日志收集功能
        response = multi_project_steps.step_check_disk_log_collection(project_name=create_multi_project)
        # 获取功能状态
        status = response.json()['metadata']['labels']['logging.kubesphere.io/logsidecar-injection']
        # 验证功能开启成功
        assert status == 'enabled'

    @allure.story('项目设置-高级设置')
    @allure.title('落盘日志收集-关闭')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.skipif(commonFunction.get_components_status_of_cluster('logging') is False, reason='集群未开启logging功能')
    def test_disk_log_collection_close(self, create_multi_workspace, create_multi_project):
        # 开启落盘日志收集功能
        multi_project_steps.step_set_disk_log_collection(project_name=create_multi_project, set='enabled')
        time.sleep(2)
        # 关闭落盘日志收集功能
        multi_project_steps.step_set_disk_log_collection(project_name=create_multi_project, set='disabled')
        # 查看落盘日志收集功能
        response = multi_project_steps.step_check_disk_log_collection(project_name=create_multi_project)
        # 获取功能状态
        status = response.json()['metadata']['labels']['logging.kubesphere.io/logsidecar-injection']
        # 验证功能开启成功
        assert status == 'disabled'

    @allure.story('概览')
    @allure.title('查询多集群项目的监控信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_project_metrics(self, create_multi_workspace, create_multi_project):
        clusters = cluster_steps.step_get_cluster_name()
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 获取720分钟之前的戳
        before_timestamp = commonFunction.get_before_timestamp(datetime.now(), 720)
        # 查询每个项目最近12h的监控信息
        for name in clusters:
            i = 0
            while i < 180:
                response = multi_project_steps.step_get_project_metrics_in_multi_project(cluster_name=name,
                                                                                         project_name=create_multi_project,
                                                                                         start_time=before_timestamp,
                                                                                         end_time=now_timestamp,
                                                                                         step='4320s', times=str(10))
                try:
                    # 获取结果中的数据类型
                    metric_type = response.json()['results'][0]['data']['resultType']
                    if metric_type:
                        # 验证数据类型正确
                        assert metric_type == 'matrix'
                        break
                except Exception as e:
                    print(e)
                time.sleep(1)
                i += 1

    @allure.story('概览')
    @allure.title('查询多集群项目的abnormalworkloads')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_project_abnormal_workloads(self, create_multi_workspace, create_multi_project):
        clusters = cluster_steps.step_get_cluster_name()
        for name in clusters:
            # 查询多集群项目的abnormalworkloads
            response = multi_project_steps.step_get_project_abnormalworkloads_in_multi_project(
                cluster_name=name,
                project_name=create_multi_project)
            # 验证查询成功
            assert 'persistentvolumeclaims' in response.json()['data']

    @allure.story('概览')
    @allure.title('查询多集群项目的federatedlimitranges')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_project_federated_limit_ranges(self, create_multi_workspace, create_multi_project):
        # 查询多集群项目的federatedlimitranges
        response = multi_project_steps.step_get_project_federatedlimitranges(project_name=create_multi_project)
        # 获取查询结果中的kind
        kind = response.json()['kind']
        # 验证kind正确
        assert kind == 'FederatedLimitRangeList'

    @allure.story('概览')
    @allure.title('查询多集群项目的workloads')
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_project_workloads(self, create_multi_workspace, create_multi_project):
        response = multi_project_steps.step_get_workloads_in_multi_project(project_name=create_multi_project)
        # 验证查询成功
        assert response.json()['totalItems'] >= 0


if __name__ == "__main__":
    pytest.main(['-s', 'test_multiClusterProject.py'])  # -s参数是为了显示用例的打印信息。 -q参数只显示结果，不显示过程
