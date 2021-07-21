import pytest
import allure
import sys
import time
from common.getData import DoexcleByPandas

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from common import commonFunction
from step import app_steps, cluster_steps, workspace_steps, project_steps


@allure.feature('应用管理')
@pytest.mark.skipif(commonFunction.get_component_health_of_cluster('') is False, reason='')
@pytest.mark.skipif(commonFunction.get_components_status_of_cluster('openpitrix') is False, reason='集群未开启openpitrix功能')
class TestAppTemplate(object):
    ws_name = 'test-app'  # 在读取execle中的测试用例时，使用到了ws_name
    project_name = 'project-for-test-app' + str(commonFunction.get_random())
    alias_name = 'for app store'
    description = '在多集群企业空间部署app store 中的应用'

    # 所有用例执行之前执行该方法
    def setup_class(self):
        if commonFunction.check_multi_cluster() is False:
            workspace_steps.step_create_workspace(self.ws_name)  # 创建一个企业空间
            project_steps.step_create_project(ws_name=self.ws_name, project_name=self.project_name)  # 创建一个项目
        else:
            # 获取集群名称
            clusters = cluster_steps.step_get_cluster_name()
            # 创建一个多集群企业空间（包含所有的集群）
            workspace_steps.step_create_multi_ws(self.ws_name, self.alias_name, self.description,
                                 clusters)
            # 在企业空间的host集群上创建一个项目
            project_steps.step_create_project_for_cluster(cluster_name='host', ws_name=self.ws_name,
                                                          project_name=self.project_name)

    # 所有用例执行完之后执行该方法
    def teardown_class(self):
        if commonFunction.check_multi_cluster() is False:
            project_steps.step_delete_project(self.ws_name, self.project_name)  # 删除创建的项目
            workspace_steps.step_delete_workspace(self.ws_name)  # 删除创建的企业空间
        else:
            # 删除创建的项目
            project_steps.step_delete_project_from_cluster(cluster_name='host', ws_name=self.ws_name,
                                                           project_name=self.project_name)
            # 删除创建的企业空间
            workspace_steps.step_delete_workspace(self.ws_name)

    parametrize = DoexcleByPandas().get_data_for_pytest(filename='../data/data.xlsx', sheet_name='appmanage')

    @allure.title('{title}')  # 设置用例标题
    # 将用例信息以参数化的方式传入测试方法
    @pytest.mark.parametrize('id,url,params,data,story,title,method,severity,condition,except_result', parametrize)
    def test_app_repo(self, id, url, params, data, story, title, method, severity, condition, except_result):

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
        commonFunction.request_resource(url, params, data, story, title, method, severity, condition, except_result)

    @allure.story('应用管理-应用仓库')
    @allure.title('使用正确的信息新建应用仓库')
    @allure.severity(allure.severity_level.BLOCKER)
    def test_add_app_repository(self):
        repo_name = 'repo' + str(commonFunction.get_random())  # 仓库名称
        repo_url = 'https://helm-chart-repo.pek3a.qingstor.com/kubernetes-charts/'  # 仓库的url信息
        # 添加仓库
        app_steps.step_add_app_repository(self.ws_name, repo_name, repo_url)
        # 查询列表，并获取查询到的仓库的id、名称
        response = app_steps.step_get_app_repository(self.ws_name, repo_name)
        repo_id = response.json()['items'][0]['repo_id']
        name = response.json()['items'][0]['name']
        # 等待应用仓库同步成功，最长等待时间60s
        i = 0
        while i < 60:
            # 获取应用仓库的状态
            re = app_steps.step_get_app_repository(self.ws_name, repo_name)
            status = re.json()['items'][0]['status']
            if status == 'successful':
                print('应用仓库同步耗时：' + str(i))
                break
            time.sleep(2)
            i = i + 2
        # 删除应用仓库
        app_steps.step_delete_app_repo(self.ws_name, repo_id)
        # 验证仓库添加成功
        assert name == repo_name

    @allure.story('应用管理-应用仓库')
    @allure.title('按名称精确查询应用仓库')
    def test_get_app_repository(self):
        repo_name = 'repo' + str(commonFunction.get_random())  # 仓库名称
        repo_url = 'https://helm-chart-repo.pek3a.qingstor.com/kubernetes-charts/'  # 仓库的url信息
        # 添加仓库
        app_steps.step_add_app_repository(self.ws_name, repo_name, repo_url)
        # 查询列表，并获取创建的仓库的名称和id
        response = app_steps.step_get_app_repository(self.ws_name, repo_name)
        repo_id = response.json()['items'][0]['repo_id']
        name = response.json()['items'][0]['name']
        # 删除应用仓库
        app_steps.step_delete_app_repo(self.ws_name, repo_id)
        # 验证查询的结果正确
        assert name == repo_name

    @allure.story('应用管理-应用仓库')
    @allure.title('删除应用仓库并验证删除成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_app_repository(self):
        repo_name = 'repo' + str(commonFunction.get_random())  # 仓库名称
        repo_url = 'https://helm-chart-repo.pek3a.qingstor.com/kubernetes-charts/'  # 仓库的url信息
        # 添加仓库
        app_steps.step_add_app_repository(self.ws_name, repo_name, repo_url)
        # 查询列表，并获取查询到的仓库的repo_id
        response = app_steps.step_get_app_repository(self.ws_name, repo_name)
        repo_id = response.json()['items'][0]['repo_id']
        # 等待仓库同步成功
        time.sleep(10)
        # 删除应用仓库
        app_steps.step_delete_app_repo(self.ws_name, repo_id)
        # 查询列表，验证删除成功
        time.sleep(10)  # 等待删除成功
        response = app_steps.step_get_app_repository(self.ws_name, repo_name)
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
        response = app_steps.step_delete_app_repo(self.ws_name, repo_id)
        # 验证删除结果
        assert response.json()['message'] == 'success'

    @allure.story('应用管理-应用模板')
    @allure.title('发布应用模板到商店，然后将应用下架，再重新上架，最后下架应用')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_suspend_app_template(self):
        version = 'v0.1 [v1.0]'  # 部署的应用的版本名称
        update_log = 'test'  # 部署应用的更新日志
        app_name = 'test-app' + str(commonFunction.get_random())  # 应用模版名称
        # 创建应用模板
        app_steps.step_create_app_template(self.ws_name, app_name)
        # 获取应用的app_id和version_id
        response = app_steps.step_get_app_template(self.ws_name, app_name)
        app_id = response.json()['items'][0]['app_id']
        version_id = response.json()['items'][0]['latest_app_version']['version_id']
        # 应用模版提交审核
        app_steps.step_app_template_submit(app_id, version_id, version, update_log)
        # 应用审核通过
        app_steps.step_app_pass(app_id, version_id)
        # 发布模板到应用商店
        app_steps.step_release(app_id, version_id)
        # 下架应用
        app_steps.step_suspend_app(app_id)
        # 重新上架应用
        app_steps.step_app_recover(app_id, version_id)
        # 下架应用
        app_steps.step_suspend_app(app_id)
        # 获取应用模版中所有的版本version
        versions = app_steps.step_get_app_versions(self.ws_name, app_id)
        # 删除应用版本
        app_steps.step_delete_version(app_name, versions)
        time.sleep(5)  # 等待版本删除完成后，再删除模版
        # 删除应用模板
        re = app_steps.step_delete_app_template(self.ws_name, app_id)
        # 验证删除成功
        assert re.json()['message'] == 'success'

    @allure.story('应用管理-应用模板')
    @allure.title('应用审核不通过,然后重新提交审核，最后审核通过')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_app_check_reject(self):
        version = 'v0.1 [v1.0]'  # 部署的应用的版本名称
        update_log = 'test'  # 部署应用的更新日志
        app_name = 'test-app' + str(commonFunction.get_random())  # 应用模版名称
        # 创建应用模板
        app_steps.step_create_app_template(self.ws_name, app_name)
        # 获取应用的app_id和version_id
        response = app_steps.step_get_app_template(self.ws_name, app_name)
        app_id = response.json()['items'][0]['app_id']
        version_id = response.json()['items'][0]['latest_app_version']['version_id']
        # 应用模板提交审核
        app_steps.step_app_template_submit(app_id, version_id, version, update_log)
        # 应用审核不通过
        app_steps.step_app_reject(app_id, version_id)
        # 应用模板提交审核
        app_steps.step_app_template_submit(app_id, version_id, version, update_log)
        # 应用审核通过
        app_steps.step_app_pass(app_id, version_id)
        # 查看应用审核记录
        app_steps.step_audit_records(app_id, version_id)
        # 获取应用模版中所有的版本version
        versions = app_steps.step_get_app_versions(self.ws_name, app_id)
        # 删除应用版本
        app_steps.step_delete_version(app_id, versions)
        # 删除应用模板
        re = app_steps.step_delete_app_template(self.ws_name, app_id)
        # 验证应用模版删除成功
        assert re.json()['message'] == 'success'

    @allure.story('应用管理-应用模板')
    @allure.title('创建应用模板后添加版本')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_add_version(self):
        app_name = 'test-app' + str(commonFunction.get_random())  # 应用模版名称
        # 创建应用模板
        app_steps.step_create_app_template(self.ws_name, app_name)
        # 获取应用的app_id和version_id
        response = app_steps.step_get_app_template(self.ws_name, app_name)
        app_id = response.json()['items'][0]['app_id']
        # 添加应用版本
        app_steps.step_add_version(self.ws_name, app_id)
        # 获取应用模版中所有的版本version
        versions = app_steps.step_get_app_versions(self.ws_name, app_id)
        # 删除应用版本
        app_steps.step_delete_version(app_id, versions)
        # 删除应用模板
        re = app_steps.step_delete_app_template(self.ws_name, app_id)
        # 验证应用模版删除成功
        assert re.json()['message'] == 'success'

    @allure.story('应用-应用模板')
    @allure.title('从应用模版部署新应用')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_deployment_app_form_template(self):
        app_name = 'test-app' + str(commonFunction.get_random())
        # 创建应用模板
        app_steps.step_create_app_template(self.ws_name, app_name)
        # 获取应用模版的app_id和version_id
        response = app_steps.step_get_app_template(self.ws_name, app_name)
        app_id = response.json()['items'][0]['app_id']
        version_id = response.json()['items'][0]['latest_app_version']['version_id']
        # 部署应用模版
        name = app_name + 'test-app'  # 应用名称
        re = app_steps.step_deploy_template(self.ws_name, self.project_name, app_id, name, version_id)
        # 验证部署结果
        message = re.json()['message']
        assert message == 'success'
        # 在项目的应用列表中验证部署的应用运行正常,最长等待时间300s
        i = 0
        while i < 300:
            r = app_steps.step_get_app_status(self.ws_name, self.project_name, app_name)
            status = r.json()['items'][0]['cluster']['status']
            if status == 'active':
                print('应用部署耗时:' + str(i) + '秒')
                break
            time.sleep(10)
            i = i + 10
        assert status == 'active'
        # 获取部署的应用的cluster_id
        r = app_steps.step_get_app(self.ws_name, self.project_name, app_name)
        cluster_id = r.json()['items'][0]['cluster']['cluster_id']
        # 删除创建的应用
        app_steps.step_delete_app(self.ws_name, self.project_name, cluster_id)
        # 在应用列表中查询创建的应用，验证删除成功
        time.sleep(5)  # 等待删除时间
        re = app_steps.step_get_app(self.ws_name, self.project_name, app_name)
        # 获取查询的结果
        count = re.json()['total_count']
        # 获取应用模版中所有的版本version
        versions = app_steps.step_get_app_versions(self.ws_name, app_id)
        app_steps.step_delete_version(app_id, versions)  # 删除应用版本
        app_steps.step_delete_app_template(self.ws_name, app_name)  # 删除应用模板
        assert count == 0

    @allure.story('应用-应用模板')
    @allure.title('从应用商店部署新应用')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_deployment_app_form_appstore(self):
        version = 'v0.1 [v1.0]'  # 部署的应用的版本名称
        update_log = 'test'  # 部署应用的更新日志
        app_name = 'test-app' + str(commonFunction.get_random())  # 应用模版名称
        # 创建应用模板
        app_steps.step_create_app_template(self.ws_name, app_name)
        # 获取应用的app_id和version_id
        response = app_steps.step_get_app_template(self.ws_name, app_name)
        app_id = response.json()['items'][0]['app_id']
        version_id = response.json()['items'][0]['latest_app_version']['version_id']
        # 应用模版提交审核
        app_steps.step_app_template_submit(app_id, version_id, version, update_log)
        # 应用审核通过
        app_steps.step_app_pass(app_id, version_id)
        # 发布模板到应用商店
        app_steps.step_release(app_id, version_id)
        # 部署应用
        name = app_name + 'test-app'  # 应用名称
        res = app_steps.step_deploy_template(self.ws_name, self.project_name, app_id, name, version_id)
        # 验证部署结果
        message = res.json()['message']
        assert message == 'success'
        # 在项目的应用列表中验证部署的应用运行正常,最长等待时间300s
        i = 0
        while i < 300:
            r = app_steps.step_get_app_status(self.ws_name, self.project_name, app_name)
            status = r.json()['items'][0]['cluster']['status']
            if status == 'active':
                print('应用部署耗时:' + str(i) + '秒')
                break
            time.sleep(10)
            i = i + 10
        # 获取部署的应用的cluster_id
        re = app_steps.step_get_app(self.ws_name, self.project_name, app_name)
        cluster_id = re.json()['items'][0]['cluster']['cluster_id']
        # 删除创建的应用
        app_steps.step_delete_app(self.ws_name, self.project_name, cluster_id)
        # 在应用列表中查询创建的应用，验证删除成功
        time.sleep(5)  # 等待删除时间
        r = app_steps.step_get_app(self.ws_name, self.project_name, app_name)
        count = r.json()['total_count']
        assert count == 0
        # 下架应用
        app_steps.step_suspend_app(app_id)

    @allure.story('应用-应用模板')
    @allure.title('按名称精确查询部署的应用')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_app(self):
        app_name = 'test-app' + str(commonFunction.get_random())
        # 创建应用模板
        app_steps.step_create_app_template(self.ws_name, app_name)
        # 获取应用模版的app_id和version_id
        response = app_steps.step_get_app_template(self.ws_name, app_name)
        app_id = response.json()['items'][0]['app_id']
        version_id = response.json()['items'][0]['latest_app_version']['version_id']
        # 部署应用模版
        name = app_name + 'test-app'  # 应用名称
        res = app_steps.step_deploy_template(self.ws_name, self.project_name, app_id, name, version_id)
        # 验证部署结果
        message = res.json()['message']
        assert message == 'success'
        # 获取部署的应用的name和cluster_id
        r = app_steps.step_get_app(self.ws_name, self.project_name, name)
        name_actual = r.json()['items'][0]['cluster']['name']
        # 验证应用的名称正确
        assert name_actual == name
        cluster_id = r.json()['items'][0]['cluster']['cluster_id']
        # 删除创建的应用
        app_steps.step_delete_app(self.ws_name, self.project_name, cluster_id)
        # 在应用列表中查询创建的应用，验证删除成功
        time.sleep(5)  # 等待删除时间
        re = app_steps.step_get_app(self.ws_name, self.project_name, app_name)
        # 获取查询结果
        count = re.json()['total_count']
        # 获取应用模版中所有的版本version
        versions = app_steps.step_get_app_versions(self.ws_name, app_id)
        app_steps.step_delete_version(app_id, versions)  # 删除应用版本
        app_steps.step_delete_app_template(self.ws_name, app_name)  # 删除应用模板
        assert count == 0

    @allure.story('应用管理-应用模版')
    @allure.title('在应用模版中精确查询存在的模版')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_app_template(self):
        # 创建应用模版
        app_name = 'test-app' + str(commonFunction.get_random())
        app_steps.step_create_app_template(self.ws_name, app_name)
        # 查询指定的应用模版
        response = app_steps.step_get_app_template(self.ws_name, app_name)
        # 获取查询结果
        name = response.json()['items'][0]['name']
        # 获取创建的模版的app_id
        app_id = response.json()['items'][0]['app_id']
        # 获取应用模版中所有的版本version
        versions = app_steps.step_get_app_versions(self.ws_name, app_id)
        # 删除应用版本
        app_steps.step_delete_version(app_name, versions)
        # 删除创建的应用模版
        app_steps.step_delete_app_template(self.ws_name, app_id)
        # 验证查询结果
        assert name == app_name

    @allure.story('应用管理-应用模版')
    @allure.title('在不删除应用版本的情况下删除应用模版')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_template_with_version(self):
        # 创建应用模版
        app_name = 'test-app' + str(commonFunction.get_random())
        app_steps.step_create_app_template(self.ws_name, app_name)
        # 查询创建的应用模版
        response = app_steps.step_get_app_template(self.ws_name, app_name)
        # 获取创建的模版的app_id
        app_id = response.json()['items'][0]['app_id']
        # 删除创建的应用模版
        re = app_steps.step_delete_app_template(self.ws_name, app_id)
        # 获取接口返回信息
        message = re.text
        # 验证接口响应信息
        assert message == 'app ' + app_id + ' has some versions not deleted\n'


if __name__ == "__main__":
    pytest.main(['-s', 'testAppManage.py'])  # -s参数是为了显示用例的打印信息。 -q参数只显示结果，不显示过程


