import requests
import pytest
import json
import allure
import sys
import random
import time
from common.getData import DoexcleByPandas

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from config import config
from common.getHeader import get_header, get_header_for_patch
from common import commonFunction


@allure.step('创建应用模板')
def step_create_app_template(ws_name, app_name):
    """
    :param ws_name: 企业空间名称
    :param app_name: 应用模版名称
    :return:
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/apps'
    data = {"version_type": "helm",
            "name": app_name,
            "version_package": "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"
            }
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('查询指定的应用模版')
def step_get_app_template(ws_name, app_name):
    """
    :param ws_name: 企业空间名称
    :param app_name: 应用名称
    :return:
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/apps?conditions=keyword%3D' + app_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('部署应用')
def step_deploy_template(ws_name, project_name, app_id, name, version_id):
    """
    :param ws_name: 企业空间名称
    :param project_name: 项目名称
    :param app_id: 应用id
    :param name: 部署应用的名称
    :param version_id: 应用的版本号
    :return:
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + \
          '/clusters/default/namespaces/' + project_name + '/applications'
    data = {"app_id": app_id,
            "name": name,
            "version_id": version_id,
            "conf": "affinity: {}\napiserver: 'https://kubernetes.default.svc:443'\nemqxAddressType: ip\nemqxConfig:\n "
                    " EMQX_MANAGEMENT__LISTENER__HTTP: '8080'\nemqxLicneseSecretName: null\nimage: "
                    "'emqx/emqx:latest'\nimagePullPolicy: IfNotPresent\ningress:\n  annotations: {}\n  enabled: "
                    "false\n  hosts:\n    - chart-example.local\n  path: /\n  tls: []\nnamespace: "
                    "default\nnodeSelector: {}\npersistence:\n  accessMode: ReadWriteOnce\n  enabled: false\n  size: "
                    "20Mi\nreplicas: 3\nresources: {}\nservice:\n  type: ClusterIP\ntolerations: []\n"}

    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('查看应用状态')
def step_get_app_status(ws_name, project_name, app_name):
    """
    :param ws_name: 企业空间名称
    :param project_name: 项目名称
    :param app_name: 应用名称
    :return:
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/namespaces/' + project_name + '/applications?conditions=keyword%3D' + app_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看指定应用')
def step_get_app(ws_name, project_name, app_name):
    """
    :param ws_name: 企业空间名称
    :param project_name: 项目名称
    :param app_name: 应用名称
    :return:
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/namespaces/' + project_name + '/applications?conditions=keyword%3D' + app_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('删除部署的应用')
def step_delete_app(ws_name, project_name, cluster_id):
    """
    :param ws_name: 企业空间名称
    :param project_name: 项目名称
    :param cluster_id: 集群id
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/clusters/default/namespaces/' + project_name + '/applications/' + cluster_id

    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('应用模板提交审核')
def step_app_template_submit(app_id, version_id, version, update_log):
    """
    :param app_id: 应用的id
    :param version_id: 应用的版本id
    :param version: 部署时应用的版本名称
    :param update_log: 部署时应用的更新日志
    :return:
    """
    url1 = config.url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/versions/' + version_id + '/'
    url2 = config.url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/versions/' + version_id + '/action'
    data1 = {"name": version,
             "description": update_log}
    data2 = {"action": "submit"}
    requests.patch(url1, headers=get_header_for_patch(), data=json.dumps(data1))
    response = requests.post(url2, headers=get_header(), data=json.dumps(data2))
    return response


@allure.step('应用模板撤销审核')
def step_app_template_submit_cancle(app_id, version_id):
    """
    :param app_id: 应用id
    :param version_id: 应用的版本id
    """
    url = config.url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/versions/' + version_id + '/action'
    data = {"action": "cancel"}
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('应用审核--通过')
def step_app_pass(app_id, version_id):
    """
    :param app_id: 应用id
    :param version_id: 应用的版本id
    """
    url = config.url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/versions/' + version_id + '/action'
    data = {"action": "pass"}
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('应用审核--不通过')
def step_app_reject(app_id, version_id):
    """
    :param app_id: 应用id
    :param version_id: 应用的版本id
    """
    url = config.url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/versions/' + version_id + '/action'
    data = {"action": "reject", "message": "test-reject"}
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('发布应用商店')
def step_release(app_id, version_id):
    """
    :param app_id: 应用id
    :param version_id: 应用的版本id
    """
    url = config.url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/versions/' + version_id + '/action'
    data = {"action": "release"}
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('下架应用')
def step_suspend_app(app_id):
    """
    :param app_id: 应用id
    """
    url = config.url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/action'
    data = {"action": "suspend"}
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('重新上架')
def step_app_recover(app_id, version_id):
    """
    :param app_id: 应用id
    :param version_id: 应用的版本id
    """
    url = config.url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/versions/' + version_id + '/action'
    data = {"action": "recover"}
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('查看应用审核记录')
def step_audit_records(app_id, version_id):
    """
    :param app_id: 应用id
    :param version_id: 应用的版本id
    """
    url = config.url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/versions/' + version_id + '/audits?'
    response = requests.get(url, get_header())
    return response


@allure.step('添加版本')
def step_add_version(ws_name, app_id):
    """
    :param ws_name: 企业空间名称
    :param app_id: 应用id
    :return:
    """
    # 获取应用的app_id和version_id
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/apps/' + app_id + '/versions'
    data = {"type": "helm",
            "package": "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"}
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('获取应用模板中所有版本的version_id')
def step_get_app_versions(ws_name, app_id):
    """
    :param ws_name: 企业空间名称
    :param app_id: 应用id
    :return:
    """
    versions = []
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/apps/' + app_id + '/versions?orderBy=sequence&paging=limit%3D10%2Cpage%3D1&conditions=status%3Ddraft%7Csubmitted%7Crejected%7Cin-review%7Cpassed%7Cactive%7Csuspended&reverse=true'
    r = requests.get(url=url, headers=get_header())
    for item in r.json()['items']:
        versions.append(item['version_id'])
    return versions


@allure.step('删除版本')
def step_delete_version(app_id, versions):
    """
    :param app_id: 应用id
    :param versions: 应用的版本信息
    """
    for version in versions:
        url = config.url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/versions/' + version + '/'
        data = {}
        r = requests.delete(url, headers=get_header(), data=json.dumps(data))  # 删除应用版本
        assert r.json()['message'] == 'success'


@allure.step('删除应用模板')
def step_delete_app_template(ws_name, app_id):
    """
    :param ws_name: 企业空间名称
    :param app_id: 应用id
    :return:
    """
    data = {}
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/apps/' + app_id + '/'
    response = requests.delete(url, headers=get_header(), data=json.dumps(data))  # 删除应用模板
    return response


@allure.step('添加仓库')
def step_add_app_repository(ws_name, rpo_name, rpo_url):
    """
    :param ws_name: 企业空间
    :param rpo_name: 应用仓库名称
    :param rpo_url: 应用仓库地址
    :return: 应用仓库的repo_id
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/repos'
    data = {"name": rpo_name,
            "repoType": "Helm",
            "type": "https",
            "visibility": "public",
            "credential": "{}",
            "providers": ["kubernetes"],
            "url": rpo_url,
            "app_default_status": "active"
            }
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('查询应用仓库列表指定仓库')
def step_get_app_reposity(ws_name, rpo_name):
    """
    :param ws_name: 企业空间
    :param rpo_name: 应用仓库名称
    :return: 应用仓库的repo_id
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/repos?conditions=keyword%3D' + rpo_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('删除应用仓库')
def step_delete_app_repo(ws_name, repo_id):
    """
    :param ws_name: 企业空间名称
    :param repo_id: 仓库id
    :return:
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/repos/' + repo_id + '/'
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.feature('应用管理')
class TestAppTemplate(object):
    ws_name = 'test-app'  # 在读取excle中的测试用例时，使用到了ws_name
    project_name = 'project-for-test-app'

    # 所有用例执行之前执行该方法
    def setup_class(self):
        commonFunction.create_workspace(self.ws_name)  # 创建一个企业空间
        commonFunction.create_project(ws_name=self.ws_name, project_name=self.project_name)  # 创建一个项目

    # 所有用例执行完之后执行该方法
    def teardown_class(self):
        commonFunction.delete_project(self.ws_name, self.project_name)  # 删除创建的项目
        commonFunction.delete_workspace(self.ws_name)  # 删除创建的企业空间

    parametrize = DoexcleByPandas().get_data_for_pytest(filename='../data/data.xlsx', sheet_name='appmanage')

    @allure.title('{title}')  # 设置用例标题
    # 将用例信息以参数化的方式传入测试方法
    @pytest.mark.parametrize('id,url,data,story,title,method,severity,condition,except_result', parametrize)
    def test_app_repo(self, id, url, data, story, title, method, severity, condition, except_result):

        """
        :param id: 用例编号
        :param url: 用例请求的URL地址
        :param data: 用例使用的请求数据
        :param story: 用例模块
        :param title: 用例标题
        :param method: 用例的请求方式
        :param severity: 用例优先级
        :param condition: 用例的校验条件
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

    @allure.story('应用管理-应用仓库')
    @allure.title('使用正确的信息新建应用仓库')
    @allure.severity(allure.severity_level.BLOCKER)
    def test_add_app_repository(self):
        repo_name = 'repo' + str(commonFunction.get_random())  # 仓库名称
        repo_url = 'https://helm-chart-repo.pek3a.qingstor.com/kubernetes-charts/'  # 仓库的url信息
        # 添加仓库
        step_add_app_repository(self.ws_name, repo_name, repo_url)
        # 查询列表，并获取查询到的仓库的id、名称
        response = step_get_app_reposity(self.ws_name, repo_name)
        repo_id = response.json()['items'][0]['repo_id']
        name = response.json()['items'][0]['name']
        # 等待应用仓库同步成功，最长等待时间60s
        i = 0
        while i < 60:
            # 获取应用仓库的状态
            re = step_get_app_reposity(self.ws_name, repo_name)
            status = re.json()['items'][0]['status']
            if status == 'successful':
                print('应用仓库同步耗时：' + str(i))
                break
            time.sleep(2)
            i = i + 2
        # 删除应用仓库
        step_delete_app_repo(self.ws_name, repo_id)
        # 验证仓库添加成功
        assert name == repo_name

    @allure.story('应用管理-应用仓库')
    @allure.title('按名称精确查询应用仓库')
    def test_get_app_repository(self):
        repo_name = 'repo' + str(commonFunction.get_random())  # 仓库名称
        repo_url = 'https://helm-chart-repo.pek3a.qingstor.com/kubernetes-charts/'  # 仓库的url信息
        # 添加仓库
        step_add_app_repository(self.ws_name, repo_name, repo_url)
        # 查询列表，并获取创建的仓库的名称和id
        response = step_get_app_reposity(self.ws_name, repo_name)
        repo_id = response.json()['items'][0]['repo_id']
        name = response.json()['items'][0]['name']
        # 删除应用仓库
        step_delete_app_repo(self.ws_name, repo_id)
        # 验证查询的结果正确
        assert name == repo_name

    @allure.story('应用管理-应用仓库')
    @allure.title('删除应用仓库并验证删除成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_app_repository(self):
        repo_name = 'repo' + str(commonFunction.get_random())  # 仓库名称
        repo_url = 'https://helm-chart-repo.pek3a.qingstor.com/kubernetes-charts/'  # 仓库的url信息
        # 添加仓库
        step_add_app_repository(self.ws_name, repo_name, repo_url)
        # 查询列表，并获取查询到的仓库的repo_id
        response = step_get_app_reposity(self.ws_name, repo_name)
        repo_id = response.json()['items'][0]['repo_id']
        # 等待仓库同步成功
        time.sleep(10)
        # 删除应用仓库
        step_delete_app_repo(self.ws_name, repo_id)
        # 查询列表，验证删除成功
        time.sleep(10)  # 等待删除成功
        response = step_get_app_reposity(self.ws_name, repo_name)
        count = response.json()['total_count']
        # 验证仓库删除成功
        assert count == 0

    @allure.story('应用管理-应用仓库')
    @allure.title('删除不存在的应用仓库')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_app_repository_no(self):
        # 验证删除的应用仓库不存在
        repo_id = 'qwe'
        # 删除应用仓库
        response = step_delete_app_repo(self.ws_name, repo_id)
        # 验证删除结果
        assert response.json()['message'] == 'success'

    @allure.story('应用管理-应用模板')
    @allure.title('发布应用模板到商店，然后将应用下架，再重新上架，最后下架应用')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_suspend_app_template(self):
        version = 'v0.1 [v1.0]'  # 部署的应用的版本名称
        update_log = 'test'  # 部署应用的更新日志
        app_name = 'app' + str(commonFunction.get_random())  # 应用模版名称
        # 创建应用模板
        step_create_app_template(self.ws_name, app_name)
        # 获取应用的app_id和version_id
        response = step_get_app_template(self.ws_name, app_name)
        app_id = response.json()['items'][0]['app_id']
        version_id = response.json()['items'][0]['latest_app_version']['version_id']
        # 应用模版提交审核
        step_app_template_submit(app_id, version_id, version, update_log)
        # 应用审核通过
        step_app_pass(app_id, version_id)
        # 发布模板到应用商店
        step_release(app_id, version_id)
        # 下架应用
        step_suspend_app(app_id)
        # 重新上架应用
        step_app_recover(app_id, version_id)
        # 下架应用
        step_suspend_app(app_id)
        # 获取应用模版中所有的版本version
        versions = step_get_app_versions(self.ws_name, app_id)
        # 删除应用版本
        step_delete_version(app_name, versions)
        time.sleep(5)  # 等待版本删除完成后，再删除模版
        # 删除应用模板
        re = step_delete_app_template(self.ws_name, app_id)
        print(re.text)
        # 验证删除成功
        assert re.json()['message'] == 'success'

    @allure.story('应用管理-应用模板')
    @allure.title('应用审核不通过,然后重新提交审核，最后审核通过')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_app_check_reject(self):
        version = 'v0.1 [v1.0]'  # 部署的应用的版本名称
        update_log = 'test'  # 部署应用的更新日志
        app_name = 'app' + str(commonFunction.get_random())  # 应用模版名称
        # 创建应用模板
        step_create_app_template(self.ws_name, app_name)
        # 获取应用的app_id和version_id
        response = step_get_app_template(self.ws_name, app_name)
        app_id = response.json()['items'][0]['app_id']
        version_id = response.json()['items'][0]['latest_app_version']['version_id']
        # 应用模板提交审核
        step_app_template_submit(app_id, version_id, version, update_log)
        # 应用审核不通过
        step_app_reject(app_id, version_id)
        # 应用模板提交审核
        step_app_template_submit(app_id, version_id, version, update_log)
        # 应用审核通过
        step_app_pass(app_id, version_id)
        # 查看应用审核记录
        step_audit_records(app_id, version_id)
        # 获取应用模版中所有的版本version
        versions = step_get_app_versions(self.ws_name, app_id)
        # 删除应用版本
        step_delete_version(app_id, versions)
        # 删除应用模板
        re = step_delete_app_template(self.ws_name, app_id)
        # 验证应用模版删除成功
        assert re.json()['message'] == 'success'

    @allure.story('应用管理-应用模板')
    @allure.title('创建应用模板后添加版本')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_add_version(self):
        app_name = 'app' + str(commonFunction.get_random())  # 应用模版名称
        # 创建应用模板
        step_create_app_template(self.ws_name, app_name)
        # 获取应用的app_id和version_id
        response = step_get_app_template(self.ws_name, app_name)
        app_id = response.json()['items'][0]['app_id']
        # 添加应用版本
        step_add_version(self.ws_name, app_name)
        # 获取应用模版中所有的版本version
        versions = step_get_app_versions(self.ws_name, app_id)
        # 删除应用版本
        step_delete_version(app_id, versions)
        # 删除应用模板
        re = step_delete_app_template(self.ws_name, app_id)
        # 验证应用模版删除成功
        assert re.json()['message'] == 'success'

    @allure.story('应用-应用模板')
    @allure.title('从应用模版部署新应用')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_deployment_app_form_template(self):
        app_name = 'app' + str(commonFunction.get_random())
        # 创建应用模板
        step_create_app_template(self.ws_name, app_name)
        # 获取应用模版的app_id和version_id
        response = step_get_app_template(self.ws_name, app_name)
        app_id = response.json()['items'][0]['app_id']
        version_id = response.json()['items'][0]['latest_app_version']['version_id']
        # 部署应用模版
        name = app_name + 'app'  # 应用名称
        re = step_deploy_template(self.ws_name, self.project_name, app_id, name, version_id)
        # 验证部署结果
        message = re.json()['message']
        assert message == 'success'
        # 在项目的应用列表中验证部署的应用运行正常,最长等待时间600s
        i = 0
        while i < 600:
            r = step_get_app_status(self.ws_name, self.project_name, app_name)
            status = r.json()['items'][0]['cluster']['status']
            if status == 'active':
                print('应用部署耗时:' + str(i) + '秒')
                break
            time.sleep(10)
            i = i + 10
        assert status == 'active'
        # 获取部署的应用的cluster_id
        r = step_get_app(self.ws_name, self.project_name, app_name)
        cluster_id = r.json()['items'][0]['cluster']['cluster_id']
        # 删除创建的应用
        step_delete_app(self.ws_name, self.project_name, cluster_id)
        # 在应用列表中查询创建的应用，验证删除成功
        time.sleep(5)  # 等待删除时间
        re = step_get_app(self.ws_name, self.project_name, app_name)
        # 获取查询的结果
        count = re.json()['total_count']
        # 获取应用模版中所有的版本version
        versions = step_get_app_versions(self.ws_name, app_id)
        step_delete_version(app_id, versions)  # 删除应用版本
        step_delete_app_template(self.ws_name, app_name)  # 删除应用模板
        assert count == 0

    @allure.story('应用-应用模板')
    @allure.title('从应用商店部署新应用')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_deployment_app_form_appstore(self):
        version = 'v0.1 [v1.0]'  # 部署的应用的版本名称
        update_log = 'test'  # 部署应用的更新日志
        app_name = 'app' + str(commonFunction.get_random())  # 应用模版名称
        print(app_name)
        # 创建应用模板
        step_create_app_template(self.ws_name, app_name)
        # 获取应用的app_id和version_id
        response = step_get_app_template(self.ws_name, app_name)
        app_id = response.json()['items'][0]['app_id']
        version_id = response.json()['items'][0]['latest_app_version']['version_id']
        # 应用模版提交审核
        step_app_template_submit(app_id, version_id, version, update_log)
        # 应用审核通过
        step_app_pass(app_id, version_id)
        # 发布模板到应用商店
        step_release(app_id, version_id)
        # 部署应用
        name = app_name + 'app'  # 应用名称
        res = step_deploy_template(self.ws_name, self.project_name, app_id, name, version_id)
        # 验证部署结果
        message = res.json()['message']
        assert message == 'success'
        # 在项目的应用列表中验证部署的应用运行正常,最长等待时间600s
        i = 0
        while i < 600:
            r = step_get_app_status(self.ws_name, self.project_name, app_name)
            status = r.json()['items'][0]['cluster']['status']
            if status == 'active':
                print('应用部署耗时:' + str(i) + '秒')
                break
            time.sleep(10)
            i = i + 10
        # 获取部署的应用的cluster_id
        re = step_get_app(self.ws_name, self.project_name, app_name)
        cluster_id = re.json()['items'][0]['cluster']['cluster_id']
        # 删除创建的应用
        step_delete_app(self.ws_name, self.project_name, cluster_id)
        # 在应用列表中查询创建的应用，验证删除成功
        time.sleep(5)  # 等待删除时间
        r = step_get_app(self.ws_name, self.project_name, app_name)
        count = r.json()['total_count']
        assert count == 0

    @allure.story('应用-应用模板')
    @allure.title('按名称精确查询部署的应用')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_app(self):
        app_name = 'app' + str(commonFunction.get_random())
        # 创建应用模板
        step_create_app_template(self.ws_name, app_name)
        # 获取应用模版的app_id和version_id
        response = step_get_app_template(self.ws_name, app_name)
        app_id = response.json()['items'][0]['app_id']
        version_id = response.json()['items'][0]['latest_app_version']['version_id']
        # 部署应用模版
        name = app_name + 'app'  # 应用名称
        res = step_deploy_template(self.ws_name, self.project_name, app_id, name, version_id)
        # 验证部署结果
        message = res.json()['message']
        assert message == 'success'
        # 获取部署的应用的name和cluster_id
        r = step_get_app(self.ws_name, self.project_name, name)
        name_actual = r.json()['items'][0]['cluster']['name']
        # 验证应用的名称正确
        assert name_actual == name
        cluster_id = r.json()['items'][0]['cluster']['cluster_id']
        # 删除创建的应用
        step_delete_app(self.ws_name, self.project_name, cluster_id)
        # 在应用列表中查询创建的应用，验证删除成功
        time.sleep(5)  # 等待删除时间
        re = step_get_app(self.ws_name, self.project_name, app_name)
        # 获取查询结果
        count = re.json()['total_count']
        # 获取应用模版中所有的版本version
        versions = step_get_app_versions(self.ws_name, app_id)
        step_delete_version(app_id, versions)  # 删除应用版本
        step_delete_app_template(self.ws_name, app_name)  # 删除应用模板
        assert count == 0

    @allure.story('应用管理-应用模版')
    @allure.title('在应用模版中精确查询存在的模版')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_app_template(self):
        # 创建应用模版
        app_name = 'app' + str(commonFunction.get_random())
        step_create_app_template(self.ws_name, app_name)
        # 查询指定的应用模版
        response = step_get_app_template(self.ws_name, app_name)
        # 获取查询结果
        name = response.json()['items'][0]['name']
        # 获取创建的模版的app_id
        app_id = response.json()['items'][0]['app_id']
        # 获取应用模版中所有的版本version
        versions = step_get_app_versions(self.ws_name, app_id)
        # 删除应用版本
        step_delete_version(app_name, versions)
        # 删除创建的应用模版
        step_delete_app_template(self.ws_name, app_id)
        # 验证查询结果
        assert name == app_name

    @allure.story('应用管理-应用模版')
    @allure.title('在不删除应用版本的情况下删除应用模版')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_template_with_version(self):
        # 创建应用模版
        app_name = 'app' + str(commonFunction.get_random())
        step_create_app_template(self.ws_name, app_name)
        # 查询创建的应用模版
        response = step_get_app_template(self.ws_name, app_name)
        # 获取创建的模版的app_id
        app_id = response.json()['items'][0]['app_id']
        # 删除创建的应用模版
        re = step_delete_app_template(self.ws_name, app_id)
        # 获取接口返回信息
        message = re.text
        # 验证接口响应信息
        assert message == 'app ' + app_id + ' has some versions not deleted\n'


if __name__ == "__main__":
    pytest.main(['-s', 'testAppManage.py'])  # -s参数是为了显示用例的打印信息。 -q参数只显示结果，不显示过程
