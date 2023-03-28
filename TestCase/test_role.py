# -- coding: utf-8 --
import time
import pytest
import allure
import sys
sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from common.getData import DoexcleByPandas
from common import commonFunction
from step import platform_steps


@allure.feature('平台角色管理')
class TestRole(object):
    authority_platform_self_provisioner = '["role-template-create-workspaces"]'
    authority_platform_regular = '["role-template-view-app-templates"]'
    authority_admin = '["role-template-manage-clusters","role-template-view-clusters","role-template-view-roles",' \
                      '"role-template-manage-roles","role-template-view-roles","role-template-view-workspaces",' \
                      '"role-template-manage-workspaces","role-template-manage-users","role-template-view-roles",' \
                      '"role-template-view-users","role-template-manage-app-templates",' \
                      '"role-template-view-app-templates","role-template-manage-platform-settings"]'

    # 从文件中读取用例信息
    parametrize = DoexcleByPandas().get_data_from_yaml(filename='../data/system_role.yaml')

    @allure.title('{title}')  # 设置用例标题
    # 将用例信息以参数化的方式传入测试方法
    @pytest.mark.parametrize('id,url,params,data, story, title,method,severity,condition,except_result', parametrize)
    def test_role(self, id, url, params, data, story, title, method, severity, condition, except_result):

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
        # 执行excel中的用例
        commonFunction.request_resource(url, params, data, story, title, method, severity, condition, except_result)

    '''
        以下用例由于存在较多的前置条件，不便于从excle中获取信息，故使用一个方法一个用例的方式
    '''

    @allure.story('编辑角色')
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title('编辑角色权限')
    def test_edit_role(self, create_role):
        authority = '["role-template-view-clusters","role-template-view-basic"]'
        # 查询角色并获取version
        response = platform_steps.step_get_role_info(create_role)
        version = response.json()['items'][0]['metadata']['resourceVersion']
        r = platform_steps.step_edit_role_authority(create_role, version, authority)
        # 验证编辑后的角色权限
        assert r.json()['metadata']['annotations']['iam.kubesphere.io/aggregation-roles'] == authority

    @allure.story('编辑角色')
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title('查询不存在的角色')
    def test_query_not_exist_role(self):
        # 构建角色名称
        role_name = 'role' + str(commonFunction.get_random())
        # 查询角色
        response = platform_steps.step_get_role_info(role_name)
        # 验证查询结果为空
        assert response.json()['totalItems'] == 0

    @allure.story('角色详情')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('role_name, title, authority',
                             [
                                 ('platform-self-provisioner', '查询角色platform-self-provisioner的权限列表', authority_platform_self_provisioner),
                                 ('platform-regular', '查询角色platform_regular的权限列表', authority_platform_regular),
                                 ('platform-admin', '查询角色platform-admin的权限列表', authority_admin)
                             ])
    def test_query_role_permission_list(self, role_name, title, authority):
        # 查询权限列表
        authority_list = platform_steps.step_get_role_authority(role_name)
        # 验证权限正确
        assert authority == authority_list

    @allure.story('角色详情')
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title('查询角色授权用户')
    def test_query_role_authorized_user(self, create_role, create_user):
        time.sleep(3)
        # 查询角色授权用户
        res = platform_steps.step_get_role_user(create_role)
        # 验证用户数量
        with pytest.assume:
            assert res.json()['totalItems'] == 1
        # 验证用户名称
        assert res.json()['items'][0]['metadata']['name'] == create_user

    @allure.story('角色列表')
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title('删除已关联用户的角色')
    def test_delete_role_authorized(self, create_user, create_role):
        time.sleep(3)
        # 删除角色
        response = platform_steps.step_delete_user(create_role)
        with pytest.assume:
            assert response.text == 'users.iam.kubesphere.io "' + create_role + '" not found\n'

    @allure.story('角色详情')
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title('添加无任何权限的角色')
    def test_create_role_no_authority(self, create_role):
        # 查询角色的权限信息
        response = platform_steps.step_get_role_info(create_role)
        authority = response.json()['items'][0]['metadata']['annotations']['iam.kubesphere.io/aggregation-roles']
        assert authority == '["role-template-view-basic"]'

    @allure.story('角色详情')
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title('添加有权限的角色')
    def test_create_role_with_authority(self):
        authority = '["role-template-manage-clusters","role-template-view-clusters","role-template-manage-roles","role-template-view-roles","role-template-view-users","role-template-view-basic"]'
        role_name = 'role' + str(commonFunction.get_random())
        # 创建角色
        platform_steps.step_create_role(role_name, authority)
        # 查询角色的权限信息
        response = platform_steps.step_get_role_info(role_name)
        authority_actual = response.json()['items'][0]['metadata']['annotations']['iam.kubesphere.io/aggregation-roles']
        with pytest.assume:
            assert authority_actual == authority
        # 删除角色
        platform_steps.step_delete_role(role_name)


if __name__ == "__main__":
    pytest.main(['-s', 'test_role.py'])  # -s参数是为了显示用例的打印信息。 -q参数只显示结果，不显示过程
