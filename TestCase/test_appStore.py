# -- coding: utf-8 --
import pytest
import allure
import sys
import time

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from pytest import assume
from common.getData import DoexcleByPandas
from common import commonFunction
from step import app_steps, project_steps, workspace_steps


@allure.feature('遍历部署AppStore的所有应用')
@pytest.mark.skipif(commonFunction.get_components_status_of_cluster('openpitrix') is False, reason='集群未开启openpitrix功能')
@pytest.mark.skipif(commonFunction.check_multi_cluster() is True, reason='多集群环境下不执行')
class TestAppStore(object):
    if commonFunction.check_multi_cluster() is True:
        # 如果为多集群环境，则不会collect该class的所有用例。 __test__ = False
        __test__ = False
    else:
        __test__ = True

    ws_name = 'test-deploy-from-appstore' + str(commonFunction.get_random())  # 在excle中读取的用例此名称，不能修改。
    # 在excle中读取的用例此名称，不能修改。
    project_name = 'project-for-test-deploy-app-from-appstore' + str(commonFunction.get_random())
    # 从文件中读取用例信息
    parametrize = DoexcleByPandas().get_data_from_yaml(filename='../data/appstore.yaml')

    # 所有用例执行之前执行该方法
    def setup_class(self):
        workspace_steps.step_create_workspace(self.ws_name)  # 创建一个企业空间
        project_steps.step_create_project(ws_name=self.ws_name, project_name=self.project_name)  # 创建一个项目

    # 所有用例执行完之后执行该方法
    def teardown_class(self):
        time.sleep(60)
        project_steps.step_delete_project(self.ws_name, self.ws_name)  # 删除创建的项目
        workspace_steps.step_delete_workspace(self.ws_name)  # 删除创建的企业空间

    @allure.title('从应用商店部署应用时使用已经存在的名称')
    @allure.severity(allure.severity_level.NORMAL)
    def test_deployment_mongdb(self):
        app_id = app_steps.step_get_app_id()['MongoDB']
        version_id = app_steps.step_get_app_version()['MongoDB']
        name = 'mongdb' + str(commonFunction.get_random())
        conf = "image:\n  init:\n    repository: mikefarah/yq\n    tag: 2.4.1\n    pullPolicy: IfNotPresent\n  " \
               "mongo:\n    repository: mongo\n    tag: 4.2.1\n    pullPolicy: IfNotPresent\nimagePullSecrets: [" \
               "]\nnameOverride: ''\nfullnameOverride: ''\npersistence:\n  size: 5Gi\nextraConfigurations: {" \
               "}\nrootUsername: admin\nrootPassword: password\nservice:\n  type: ClusterIP\n  port: " \
               "27017\nresources: {}\nnodeSelector: {}\ntolerations: []\naffinity: {}\n "
        # 部署示例应用
        app_steps.step_deploy_app_from_app_store(ws_name=self.ws_name, project_name=self.project_name, app_id=app_id,
                                                 name=name, version_id=version_id, conf=conf)
        i = 0
        while i < 180:
            try:
                # 查看应用部署情况
                response = app_steps.step_get_app_status(self.ws_name, self.project_name, name)
                # 获取应用状态
                status = response.json()['items'][0]['cluster']['status']
                if status == 'active':
                    print('应用部署耗时:' + str(i) + '秒')
                    break
                elif status == 'failed':
                    print('应用部署失败')
                    break
            except Exception as e:
                print(e)
            finally:
                time.sleep(10)
                i = i + 10
        # 使用已经存在的应用名称部署应用
        response = app_steps.step_deploy_app_from_app_store(ws_name=self.ws_name, project_name=self.project_name,
                                                            app_id=app_id, name=name, version_id=version_id, conf=conf)
        # 获取部署结果
        result = response.text
        # 验证部署结果
        with assume:
            assert result == 'release ' + name + ' exists\n'
        # 在应用列表查询部署的应用
        re = project_steps.step_get_app(self.ws_name, self.project_name, name)
        # 获取应用的cluster_id
        cluster_id = re.json()['items'][0]['cluster']['cluster_id']
        # 删除应用
        project_steps.step_delete_app(self.ws_name, self.project_name, cluster_id)
        # 获取项目所有的持久卷声明
        res = project_steps.step_get_pvc(self.project_name, '')
        pvc_count = res.json()['totalItems']
        if pvc_count > 0:
            for i in range(0, pvc_count):
                pvc_name = res.json()['items'][i]['metadata']['name']
                # 删除pvc
                project_steps.step_delete_pvc(self.project_name, pvc_name)
        # 等待pvc删除成功
        k = 0
        while k < 60:
            pvc_count = project_steps.step_get_pvc(self.project_name, '').json()['totalItems']
            if pvc_count == 0:
                break
            else:
                time.sleep(5)
                i += 5

    @allure.title('从应用商店部署应用时使用不符合规则的名称')
    @allure.severity(allure.severity_level.NORMAL)
    def test_deployment_mongdb_wrong_name(self):
        app_id = app_steps.step_get_app_id()['MongoDB']
        version_id = app_steps.step_get_app_version()['MongoDB']
        name = 'MONGO' + str(commonFunction.get_random())
        conf = "image:\n  init:\n    repository: mikefarah/yq\n    tag: 2.4.1\n    pullPolicy: IfNotPresent\n  " \
               "mongo:\n    repository: mongo\n    tag: 4.2.1\n    pullPolicy: IfNotPresent\nimagePullSecrets: [" \
               "]\nnameOverride: ''\nfullnameOverride: ''\npersistence:\n  size: 5Gi\nextraConfigurations: {" \
               "}\nrootUsername: admin\nrootPassword: password\nservice:\n  type: ClusterIP\n  port: " \
               "27017\nresources: {}\nnodeSelector: {}\ntolerations: []\naffinity: {}\n "
        # 部署示例应用
        app_steps.step_deploy_app_from_app_store(ws_name=self.ws_name, project_name=self.project_name,
                                                 app_id=app_id, name=name, version_id=version_id, conf=conf)
        # 查看应用部署情况
        response = project_steps.step_get_app(self.ws_name, self.project_name, name)
        # 获取应用状态
        status = response.json()['items'][0]['cluster']['status']
        with assume:
            assert status == 'failed'
        # 在应用列表查询部署的应用
        response = project_steps.step_get_app(self.ws_name, self.project_name, name)
        # 获取应用的cluster_id
        cluster_id = response.json()['items'][0]['cluster']['cluster_id']
        # 删除应用
        project_steps.step_delete_app(self.ws_name, self.project_name, cluster_id)

    @allure.title('{title}')  # 设置用例标题
    @allure.severity(allure.severity_level.CRITICAL)  # 设置用例优先级
    # 将用例信息以参数化的方式传入测试方法
    @pytest.mark.parametrize('id,app_name,conf, story, title,severity,except_result', parametrize)
    def test_deploy_app(self, id, app_name, conf, story, title, severity, except_result):

        allure.dynamic.story(story)  # 动态生成模块
        allure.dynamic.severity(severity)  # 动态生成用例等级
        app_id = app_steps.step_get_app_id()[app_name]
        version_id = app_steps.step_get_app_version()[app_name]
        name = app_name.lower().replace(' ', '-') + '-' + str(commonFunction.get_random())
        # 创建项目
        project_name = 'test-deploy-app-' + app_name.lower().replace(' ', '-') + '-' + str(commonFunction.get_random())
        project_steps.step_create_project(self.ws_name, project_name)
        # 部署示例应用
        app_steps.step_deploy_app_from_app_store(ws_name=self.ws_name, project_name=project_name,
                                                 app_id=app_id, name=name, version_id=version_id, conf=conf)
        status = ''
        i = 0
        while i < 100:
            try:
                # 查看应用部署情况
                response = project_steps.step_get_app(self.ws_name, project_name, name)
                # 获取应用状态
                status = response.json()['items'][0]['cluster']['status']
                if status == 'active':
                    print('应用部署耗时:' + str(i) + '秒')
                    break
                elif status == 'failed':
                    print('应用部署失败')
                    break
            except Exception as e:
                print(e)
            finally:
                time.sleep(20)
                i = i + 20
        # 验证应用运行成功
        with assume:
            assert status == 'active'
        # 在应用列表查询部署的应用
        response = project_steps.step_get_app(self.ws_name, project_name, name)
        # 获取应用的cluster_id
        cluster_id = response.json()['items'][0]['cluster']['cluster_id']
        # 删除应用
        project_steps.step_delete_app(self.ws_name, project_name, cluster_id)
        # 验证应用删除成功
        j = 0
        while j < 60:
            r = project_steps.step_get_app(self.ws_name, project_name, name)
            count = r.json()['total_count']
            if count == 0:
                print('删除应用耗时:' + str(j) + '秒')
                break
            else:
                time.sleep(10)
                j += 10
        try:
            # 获取项目所有的服务
            re = project_steps.step_get_service(project_name)
            count_service = re.json()['totalItems']
            if count_service > 0:
                for i in range(0, count_service):
                    service_name = re.json()['items'][i]['metadata']['name']
                    # 删除所有服务
                    project_steps.step_delete_service(project_name, service_name)
            # 获取项目所有的 statefulsets
            re = project_steps.step_get_workload(project_name, 'statefulsets', 'name='
                                                 + app_name.lower().replace(' ', '-'))
            st_count = re.json()['totalItems']
            if st_count > 0:
                for i in range(0, st_count):
                    st_name = re.json()['items'][i]['metadata']['name']
                    project_steps.step_delete_workload(project_name, 'statefulsets', st_name)
            # 获取项目所有的持久卷声明
            res = project_steps.step_get_pvc(project_name, '')
            pvc_count = res.json()['totalItems']
            if pvc_count > 0:
                for i in range(0, pvc_count):
                    pvc_name = res.json()['items'][i]['metadata']['name']
                    # 删除pvc
                    project_steps.step_delete_pvc(project_name, pvc_name)
            # 等待pvc删除成功
            k = 0
            while k < 60:
                pvc_count = project_steps.step_get_pvc(project_name, '').json()['totalItems']
                if pvc_count == 0:
                    break
                else:
                    time.sleep(5)
                    i += 5
        except Exception as e:
            print(e)
        finally:
            # 删除创建的项目
            project_steps.step_delete_project(self.ws_name, project_name)


if __name__ == "__main__":
    pytest.main(['-vs', 'test_appStore.py'])  # -s参数是为了显示用例的打印信息。 -q参数只显示结果，不显示过程
