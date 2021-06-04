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
from common.logFormat import log_format
from common import commonFunction


@allure.step('部署指定应用')
def step_deployment_app(project_name, app_id, app_version_id, name, conf):
    """
    :param project_name: 项目名称
    :param app_id: 应用id
    :param app_version_id: 应用版本号
    :param name: 部署时的应用名称
    :param conf: 应用的镜像信息
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/undefined/clusters/default/namespaces/' + project_name + '/applications'
    data = {"app_id": app_id,
            "name": name,
            "version_id": app_version_id,
            "conf": conf +
                    "Name: " + name + "\nDescription: ''\nWorkspace: " + project_name + "\n"}
    r = requests.post(url, headers=get_header(), data=json.dumps(data))
    # 验证部署应用请求成功
    assert r.json()['message'] == 'success'


@allure.step('查看指定应用信息')
def step_get_app_status(ws_name, project_name, app_name):
    """
    :param ws_name: 企业空间
    :param project_name: 项目名称
    :param app_name: 应用名称
    :return: 应用状态
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/namespaces/' + project_name + '/applications?conditions=keyword%3D' + app_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在应用列表中查看应用是否存在')
def step_get_app_count(ws_name, project_name, app_name):
    """
    :param ws_name: 企业空间
    :param project_name: 项目名称
    :param app_name: 应用名称
    :return:
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/clusters/default/namespaces/' + project_name + '/applications' \
                                                                                                                          '?conditions=status%3Dactive%7Cstopped%7Cpending%7Csuspended%2Ckeyword%3D' + app_name + '&paging=limit%3D10%2Cpage%3D1&orderBy=status_time&reverse=true'
    r = requests.get(url=url, headers=get_header())
    return r.json()['total_count']


@allure.step('在应用列表获取指定应用的cluster_id')
def step_get_deployed_app(ws_name, project_name, app_name):
    """
    :param ws_name: 企业空间
    :param project_name: 项目名称
    :param app_name: 应用名称
    :return: 应用的cluster_id
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/namespaces/' + project_name + '/applications?conditions=keyword%3D' + app_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('删除应用列表指定的应用')
def step_delete_app(ws_name, project_name, cluster_id):
    """
    :param ws_name: 企业空间
    :param project_name: 项目名称
    :param cluster_id: 部署后的应用的id
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/namespaces/' + project_name + '/applications/' + cluster_id
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('获取appstore中应用的app_id')
def step_get_app_id():
    url = config.url + '/kapis/openpitrix.io/v1/apps??orderBy=create_time&paging=limit%3D12%2Cpage%3D2&conditions=status%3Dactive%2Crepo_id%3Drepo-helm&reverse=true'
    url2 = config.url + '/kapis/openpitrix.io/v1/apps??orderBy=create_time&paging=limit%3D12%2Cpage%3D1&conditions=status%3Dactive%2Crepo_id%3Drepo-helm&reverse=true'
    r = requests.get(url, headers=get_header())  # 获取app的id和name，将其组合成一个字典
    r2 = requests.get(url2, headers=get_header())  # 获取app的id和name，将其组合成一个字典
    item_name = []
    item_app_id = []
    items = r.json()['items']
    for item in items:
        item_name.append(item['name'])
        item_app_id.append(item['app_id'])
    items2 = r2.json()['items']
    for item in items2:
        item_name.append(item['name'])
        item_app_id.append(item['app_id'])
    dic = dict(zip(item_name, item_app_id))
    return dic


@allure.step('获取appstore中所有应用的name, app_id, version_id')
def step_get_app_version():
    url = config.url + '/kapis/openpitrix.io/v1/apps??orderBy=create_time&paging=limit%3D12%2Cpage%3D2&conditions=status%3Dactive%2Crepo_id%3Drepo-helm&reverse=true'
    url2 = config.url + '/kapis/openpitrix.io/v1/apps??orderBy=create_time&paging=limit%3D12%2Cpage%3D1&conditions=status%3Dactive%2Crepo_id%3Drepo-helm&reverse=true'
    r = requests.get(url, headers=get_header())  # 获取app的id和name，将其组合成一个字典
    r2 = requests.get(url2, headers=get_header())  # 获取app的id和name，将其组合成一个字典
    item_name = []
    item_version_id = []
    items = r.json()['items']
    for item in items:
        item_name.append(item['name'])
        item_version_id.append(item['latest_app_version']['version_id'])
    items2 = r2.json()['items']
    for item in items2:
        item_name.append(item['name'])
        item_version_id.append(item['latest_app_version']['version_id'])
    dic = dict(zip(item_name, item_version_id))
    return dic


@allure.step('从应用商店部署应用')
def step_deploy_app_from_app_store(ws_name, project_name, app_id, name, version_id, conf):
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/namespaces/' + project_name + '/applications'
    data = {
        "app_id": app_id,
        "name": name,
        "version_id": version_id,
        "conf": conf
    }
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.feature('遍历部署AppStore的所有应用')
class TestAppStore(object):
    ws_name = 'test-deploy-from-appstore'  # 在excle中读取的用例此名称，不能修改。
    project_name = 'project-for-test-deploy-app-from-appstore'  # 在excle中读取的用例此名称，不能修改。
    log_format()  # 配置日志格式
    # 从文件中读取用例信息
    parametrize = DoexcleByPandas().get_data_for_pytest(filename='../data/data.xlsx', sheet_name='appstore')

    # 所有用例执行之前执行该方法
    def setup_class(self):
        commonFunction.create_workspace(self.ws_name)  # 创建一个企业空间
        commonFunction.create_project(ws_name=self.ws_name, project_name=self.project_name)  # 创建一个项目

    # 所有用例执行完之后执行该方法
    def teardown_class(self):
        commonFunction.delete_project(self.ws_name, self.ws_name)  # 删除创建的项目
        commonFunction.delete_workspace(self.ws_name)  # 删除创建的企业空间

    @allure.title('从应用商店部署应用时使用已经存在的名称')
    @allure.severity(allure.severity_level.NORMAL)
    def test_deployment_mongdb(self):
        app_id = step_get_app_id()['MongoDB']
        version_id = step_get_app_version()['MongoDB']
        name = 'mongdb' + str(commonFunction.get_random())
        conf = "image:\n  init:\n    repository: mikefarah/yq\n    tag: 2.4.1\n    pullPolicy: IfNotPresent\n  " \
               "mongo:\n    repository: mongo\n    tag: 4.2.1\n    pullPolicy: IfNotPresent\nimagePullSecrets: [" \
               "]\nnameOverride: ''\nfullnameOverride: ''\npersistence:\n  size: 5Gi\nextraConfigurations: {" \
               "}\nrootUsername: admin\nrootPassword: password\nservice:\n  type: ClusterIP\n  port: " \
               "27017\nresources: {}\nnodeSelector: {}\ntolerations: []\naffinity: {}\n "
        # 部署示例应用
        step_deploy_app_from_app_store(ws_name=self.ws_name, project_name=self.project_name, app_id=app_id, name=name,
                                       version_id=version_id, conf=conf)
        i = 0
        while i < 600:
            # 查看应用部署情况
            response = step_get_app_status(self.ws_name, self.project_name, name)
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
        response = step_deploy_app_from_app_store(ws_name=self.ws_name, project_name=self.project_name, app_id=app_id,
                                                  name=name, version_id=version_id, conf=conf)
        # 获取部署结果
        result = response.text
        # 在应用列表查询部署的应用
        response = step_get_deployed_app(self.ws_name, self.project_name, name)
        # 获取应用的cluster_id
        cluster_id = response.json()['items'][0]['cluster']['cluster_id']
        # 删除应用
        step_delete_app(self.ws_name, self.project_name, cluster_id)
        # 验证部署结果
        assert result == 'release ' + name + ' exists\n'

    @allure.title('从应用商店部署应用时使用不符合规则的名称')
    @allure.severity(allure.severity_level.NORMAL)
    def test_deployment_mongdb_wrong_nmae(self):
        app_id = step_get_app_id()['MongoDB']
        version_id = step_get_app_version()['MongoDB']
        name = 'MONGO' + str(commonFunction.get_random())
        conf = "image:\n  init:\n    repository: mikefarah/yq\n    tag: 2.4.1\n    pullPolicy: IfNotPresent\n  " \
               "mongo:\n    repository: mongo\n    tag: 4.2.1\n    pullPolicy: IfNotPresent\nimagePullSecrets: [" \
               "]\nnameOverride: ''\nfullnameOverride: ''\npersistence:\n  size: 5Gi\nextraConfigurations: {" \
               "}\nrootUsername: admin\nrootPassword: password\nservice:\n  type: ClusterIP\n  port: " \
               "27017\nresources: {}\nnodeSelector: {}\ntolerations: []\naffinity: {}\n "
        # 部署示例应用
        step_deploy_app_from_app_store(ws_name=self.ws_name, project_name=self.project_name, app_id=app_id, name=name,
                                       version_id=version_id, conf=conf)
        # 查看应用部署情况
        response = step_get_app_status(self.ws_name, self.project_name, name)
        # 获取应用状态
        status = response.json()['items'][0]['cluster']['status']
        assert status == 'failed'

        # 在应用列表查询部署的应用
        response = step_get_deployed_app(self.ws_name, self.project_name, name)
        # 获取应用的cluster_id
        cluster_id = response.json()['items'][0]['cluster']['cluster_id']
        # 删除应用
        step_delete_app(self.ws_name, self.project_name, cluster_id)

    @allure.title('{title}')  # 设置用例标题
    @allure.severity(allure.severity_level.CRITICAL)  # 设置用例优先级
    # 将用例信息以参数化的方式传入测试方法
    @pytest.mark.parametrize('id,app_name,conf, story, title,severity,except_result', parametrize)
    def test_ws_role_user(self, id, app_name, conf, story, title, severity, except_result):

        allure.dynamic.story(story)  # 动态生成模块
        allure.dynamic.severity(severity)  # 动态生成用例等级

        app_id = step_get_app_id()[app_name]
        version_id = step_get_app_version()[app_name]
        name = app_name.lower().replace(' ', '') + str(commonFunction.get_random())
        conf = conf
        # 部署示例应用
        step_deploy_app_from_app_store(ws_name=self.ws_name, project_name=self.project_name, app_id=app_id, name=name,
                                       version_id=version_id, conf=conf)
        i = 0
        while i < 600:
            # 查看应用部署情况
            response = step_get_app_status(self.ws_name, self.project_name, name)
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
        assert status == 'active'
        # 在应用列表查询部署的应用
        response = step_get_deployed_app(self.ws_name, self.project_name, name)
        # 获取应用的cluster_id
        cluster_id = response.json()['items'][0]['cluster']['cluster_id']
        # 删除应用
        step_delete_app(self.ws_name, self.project_name, cluster_id)
        # 验证应用删除成功
        j = 0
        while j < 60:
            r = step_get_deployed_app(self.ws_name, self.project_name, name)
            count = r.json()['total_count']
            if count == 0:
                print('删除应用耗时:' + str(j) + '秒')
                break
            else:
                time.sleep(1)
                j += 1
        assert count == 0


if __name__ == "__main__":
    pytest.main(['-vs', 'testAppStore.py'])  # -s参数是为了显示用例的打印信息。 -q参数只显示结果，不显示过程
