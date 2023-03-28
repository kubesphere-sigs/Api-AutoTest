# -- coding: utf-8 --
import pytest
import allure
import sys
import time

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from common.getData import DoexcleByPandas
from common.logFormat import log_format
from common import commonFunction
from step import app_steps, cluster_steps, workspace_steps, multi_project_steps, multi_workspace_steps


@allure.feature('遍历部署AppStore的所有应用')
@pytest.mark.skipif(commonFunction.get_components_status_of_cluster('openpitrix') is False, reason='集群未开启openpitrix功能')
@pytest.mark.skipif(commonFunction.check_multi_cluster() is False, reason='单集群环境下不执行')
class TestAppStore(object):
    # 如果为单集群环境，则不会collect该class的所有用例。 __test__ = False
    __test__ = False
    # __test__ = commonFunction.check_multi_cluster()

    ws_name = 'test-deploy-from-appstore' + str(commonFunction.get_random())  # 在excle中读取的用例此名称，不能修改。
    alias_name = 'for app store'
    description = '在多集群企业空间部署app store 中的应用'
    project_name = 'project-for-test-deploy-app-from-appstore' + str(commonFunction.get_random())  # 在excle中读取的用例此名称，不能修改。
    log_format()  # 配置日志格式
    # 从文件中读取用例信息
    parametrize = DoexcleByPandas().get_data_from_yaml(filename='../data/appstore.yaml')
    # 获取host集群的名称
    host_name = multi_project_steps.step_get_host_name()

    # 所有用例执行之前执行该方法
    def setup_class(self):
        # 获取集群名称
        clusters = cluster_steps.step_get_cluster_name()
        # 创建一个多集群企业空间（包含所有的集群）
        multi_workspace_steps.step_create_multi_ws(self.ws_name, self.alias_name, self.description, clusters)
        # 在企业空间的host集群上创建一个项目
        multi_project_steps.step_create_project_for_cluster(cluster_name=self.host_name, ws_name=self.ws_name,
                                                            project_name=self.project_name)

    # 所有用例执行完之后执行该方法
    def teardown_class(self):
        # 删除创建的项目
        multi_project_steps.step_delete_project_from_cluster(cluster_name='host', ws_name=self.ws_name,
                                                             project_name=self.project_name)
        # 删除创建的企业空间
        workspace_steps.step_delete_workspace(self.ws_name)

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
        # 部署应用
        app_steps.step_deploy_app_from_app_store_multi(cluster_name=self.host_name, ws_name=self.ws_name,
                                                       project_name=self.project_name, app_id=app_id, name=name,
                                                       version_id=version_id, conf=conf)
        i = 0
        while i < 600:
            # 查看应用部署情况
            response = app_steps.step_get_app_status_multi(self.host_name, self.ws_name, self.project_name, name)
            # 获取应用状态
            status = response.json()['items'][0]['cluster']['status']
            if status == 'active':
                print('应用部署耗时:' + str(i) + '秒')
                break
            elif status == 'failed':
                print('应用部署失败')
                break
            else:
                time.sleep(1)
                i = i + 1
        # 使用已经存在的应用名称部署应用
        response = app_steps.step_deploy_app_from_app_store_multi(cluster_name=self.host_name, ws_name=self.ws_name,
                                                                  project_name=self.project_name, app_id=app_id,
                                                                  name=name, version_id=version_id, conf=conf)
        # 获取部署结果
        result = response.text
        # 在应用列表查询部署的应用
        response = app_steps.step_get_deployed_app_multi(self.host_name, self.ws_name, self.project_name, name)
        # 获取应用的cluster_id
        cluster_id = response.json()['items'][0]['cluster']['cluster_id']
        # 删除应用
        app_steps.step_delete_app_multi(self.host_name, self.ws_name, self.project_name, cluster_id)
        # 验证部署结果
        assert result == 'release ' + name + ' exists\n'

    @allure.title('从应用商店部署应用时使用不符合规则的名称')
    @allure.severity(allure.severity_level.NORMAL)
    def test_deployment_mongdb_wrong_nmae(self):
        app_id = app_steps.step_get_app_id()['MongoDB']
        version_id = app_steps.step_get_app_version()['MongoDB']
        name = 'MONGO' + str(commonFunction.get_random())
        conf = "image:\n  init:\n    repository: mikefarah/yq\n    tag: 2.4.1\n    pullPolicy: IfNotPresent\n  " \
               "mongo:\n    repository: mongo\n    tag: 4.2.1\n    pullPolicy: IfNotPresent\nimagePullSecrets: [" \
               "]\nnameOverride: ''\nfullnameOverride: ''\npersistence:\n  size: 5Gi\nextraConfigurations: {" \
               "}\nrootUsername: admin\nrootPassword: password\nservice:\n  type: ClusterIP\n  port: " \
               "27017\nresources: {}\nnodeSelector: {}\ntolerations: []\naffinity: {}\n "
        # 部署应用
        app_steps.step_deploy_app_from_app_store_multi(cluster_name=self.host_name, ws_name=self.ws_name,
                                                       project_name=self.project_name, app_id=app_id, name=name,
                                                       version_id=version_id, conf=conf)
        # 查看应用部署情况
        response = app_steps.step_get_app_status_multi(self.host_name, self.ws_name, self.project_name, name)
        # 获取应用状态
        status = response.json()['items'][0]['cluster']['status']
        pytest.assume(status == 'failed')

        # 在应用列表查询部署的应用
        response = app_steps.step_get_deployed_app_multi(self.host_name, self.ws_name, self.project_name, name)
        # 获取应用的cluster_id
        cluster_id = response.json()['items'][0]['cluster']['cluster_id']
        # 删除应用
        app_steps.step_delete_app_multi(self.host_name, self.ws_name, self.project_name, cluster_id)

    @allure.title('{title}')  # 设置用例标题
    # 将用例信息以参数化的方式传入测试方法
    @pytest.mark.parametrize('id,app_name,conf,story,title,severity,except_result', parametrize)
    def test_deploy_from_appstore(self, id, app_name, conf, story, title, severity, except_result):

        allure.dynamic.story(story)  # 动态生成模块
        allure.dynamic.severity(severity)  # 动态生成用例等级

        app_id = app_steps.step_get_app_id()[app_name]
        version_id = app_steps.step_get_app_version()[app_name]
        name = app_name.lower().replace(' ', '') + str(commonFunction.get_random())
        # 部署示例应用
        app_steps.step_deploy_app_from_app_store_multi(cluster_name=self.host_name, ws_name=self.ws_name,
                                                       project_name=self.project_name, app_id=app_id, name=name,
                                                       version_id=version_id, conf=conf)
        i = 0
        while i < 300:
            # 查看应用部署情况
            response = app_steps.step_get_app_status_multi(self.host_name, self.ws_name, self.project_name, name)
            # 获取应用状态
            status = response.json()['items'][0]['cluster']['status']
            if status == 'active':
                print('应用部署耗时:' + str(i) + '秒')
                break
            elif status == 'failed':
                print('应用部署失败')
                break
            else:
                time.sleep(1)
                i = i + 1
        # 验证应用运行成功
        pytest.assume(status == 'active')
        # 在应用列表查询部署的应用
        response = app_steps.step_get_deployed_app_multi(self.host_name, self.ws_name, self.project_name, name)
        # 获取应用的cluster_id
        cluster_id = response.json()['items'][0]['cluster']['cluster_id']
        # 删除应用
        app_steps.step_delete_app_multi(self.host_name, self.ws_name, self.project_name, cluster_id)
        # 验证应用删除成功
        j = 0
        while j < 60:
            r = app_steps.step_get_deployed_app_multi(self.host_name, self.ws_name, self.project_name, name)
            count = r.json()['total_count']
            if count == 0:
                print('删除应用耗时:' + str(j) + '秒')
                break
            else:
                time.sleep(1)
                j += 1
        assert count == 0


if __name__ == "__main__":
    pytest.main(['-s', 'test_appStore.py'])  # -s参数是为了显示用例的打印信息。 -q参数只显示结果，不显示过程


