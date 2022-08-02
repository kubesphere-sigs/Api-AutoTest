# -- coding: utf-8 --
import pytest
import allure
import sys

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from common.getData import DoexcleByPandas
from common import commonFunction
from step import app_steps, workspace_steps


@allure.feature('应用商店管理')
@pytest.mark.skipif(commonFunction.get_components_status_of_cluster('openpitrix') is False, reason='集群未开启openpitrix功能')
class TestManageAppStore(object):
    if commonFunction.check_multi_cluster() is True:
        # 如果为单集群环境，则不会collect该class的所有用例。 __test__ = False
        __test__ = False
    else:
        __test__ = True

    # 从文件中读取用例信息
    parametrize = DoexcleByPandas().get_data_from_yaml(filename='../data/manageapps.yaml')

    @allure.story('应用分类')
    @allure.title('删除不包含应用的分类')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_category(self):
        # 新建应用分类
        category_name = 'category' + str(commonFunction.get_random())
        response = app_steps.step_create_category(category_name)
        # 获取创建分类的category_id
        category_id = response.json()['category_id']
        # 删除分类
        app_steps.step_delete_category(category_id)
        # 查询所有分类的category_id
        categories_id = app_steps.step_get_categories_id()
        # 验证被删除分类的category_id不存在
        assert category_id not in categories_id

    @allure.story('应用分类')
    @allure.title('修改分类信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_change_category(self):
        old_name = 'category' + str(commonFunction.get_random())
        new_name = 'category' + str(commonFunction.get_random())
        # 新建应用分类
        response = app_steps.step_create_category(old_name)
        # 获取新建分类的category_id
        category_id = response.json()['category_id']
        # 修改分类名称
        app_steps.step_change_category(category_id, new_name)
        # 验证修改成功，使用修改后的名称查询category_id
        category_id_new = app_steps.step_get_category_id_by_name(new_name)
        assert category_id == category_id_new
        # 删除分类
        app_steps.step_delete_category(category_id)

    @allure.story('应用商店')
    @allure.title('查看所有内置应用的详情信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_check_apps_detail(self):
        # 获取应用商店管理/应用商店页面，所有应用的app_id
        apps_id = app_steps.step_get_apps_id()
        # 查看所有应用的详情信息，并验证查询成功
        for app_id in apps_id:
            response = app_steps.step_get_app_detail(app_id)
            assert response.json()['app_id'] == app_id

    @allure.story('应用分类')
    @allure.title('删除包含应用的分类')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_app_category(self):
        # 创建企业空间
        ws_name = 'ws-for-test-app-store-manage' + str(commonFunction.get_random())
        workspace_steps.step_create_workspace(ws_name)
        version = 'v0.1 [v1.0]'  # 部署的应用的版本名称
        update_log = 'test'  # 部署应用的更新日志
        app_name = 'test-app' + str(commonFunction.get_random())  # 应用模版名称
        # 创建应用模板
        app_steps.step_create_app_template(ws_name, app_name)
        # 获取应用的app_id和version_id
        response = app_steps.step_get_app_template(ws_name, app_name)
        app_id = response.json()['items'][0]['app_id']
        version_id = response.json()['items'][0]['latest_app_version']['version_id']
        # 应用模版提交审核
        app_steps.step_app_template_submit(app_id, version_id, version, update_log)
        # 应用审核通过
        app_steps.step_app_pass(app_id, version_id)
        # 发布模板到应用商店
        app_steps.step_release(app_id, version_id)
        category_name = 'category' + str(commonFunction.get_random())
        # 新建应用分类
        response = app_steps.step_create_category(category_name)
        # 获取新建分类的category_id
        category_id = response.json()['category_id']
        # 获取应用商店页面所有应用的app_id
        # apps_id = app_steps.step_get_apps_id()
        # 向分类中添加新上架的应用
        app_steps.step_app_to_category(app_id + '-store', category_id)
        # 删除分类
        result = app_steps.step_delete_app_category(category_id)
        # 验证删除结果
        assert result == 'category ' + category_name + ' owns application'
        # 下架新上架的应用
        app_steps.step_suspend_app(app_id)
        # 删除新建的分类
        app_steps.step_delete_category(category_id)

    @allure.title('{title}')  # 设置用例标题
    # 将用例信息以参数化的方式传入测试方法
    @pytest.mark.parametrize('id,url,params,data, story, title,method,severity,condition,except_result', parametrize)
    def test_manage_app_store(self, id, url, params, data, story, title, method, severity, condition, except_result):

        """
        :param id: 用例编号
        :param url: 用例请求的URL地址
        :param data: 用例使用的请求数据
        :param title: 用例标题
        :param method: 用例的请求方式
        :param severity: 用例优先级
        :param condition: 用例的校验条件
        :param except_result: 用例的预期结果
        """

        allure.dynamic.story(story)  # 动态生成模块
        allure.dynamic.severity(severity)  # 动态生成用例等级
        commonFunction.request_resource(url, params, data, story, title, method, severity, condition, except_result)


if __name__ == "__main__":
    pytest.main(['-s', 'testAppStoreManage.py'])  # -s参数是为了显示用例的打印信息。 -q参数只显示结果，不显示过程
