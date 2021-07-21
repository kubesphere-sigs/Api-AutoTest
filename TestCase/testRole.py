import pytest
import allure
import sys

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from common.getData import DoexcleByPandas
from common import commonFunction
from step import platform_steps


@allure.feature('系统角色管理')
class TestRole(object):
    # 从文件中读取用例信息
    parametrize = DoexcleByPandas().get_data_for_pytest(filename='../data/data.xlsx', sheet_name='system_role')

    @allure.title('{title}')  # 设置用例标题
    @allure.severity(allure.severity_level.CRITICAL)  # 设置用例优先级
    # 将用例信息以参数化的方式传入测试方法
    @pytest.mark.parametrize('id,url,params,data, story, title,method,severity,condition,except_result', parametrize)
    def test_role(self, id, url, params, data, story, title, method, severity, condition, except_result):

        '''
        :param id: 用例编号
        :param url: 用例请求的URL地址
        :param data: 用例使用的请求数据
        :param title: 用例标题
        :param method: 用例的请求方式
        :param severity: 用例优先级
        :param condition: 用例的校验条件
        :param except_result: 用例的预期结果
        '''

        allure.dynamic.story(story)  # 动态生成模块
        allure.dynamic.severity(severity)  # 动态生成用例等级
        # 执行excel中的用例
        commonFunction.request_resource(url, params, data, story, title, method, severity, condition, except_result)

    '''
        以下用例由于存在较多的前置条件，不便于从excle中获取信息，故使用一个方法一个用例的方式
    '''

    @allure.story('编辑角色')
    @allure.severity('critical')
    @allure.title('测试编辑角色权限')
    def test_edit_role(self):
        role_name = 'role' + str(commonFunction.get_random())
        authority = '["role-template-view-clusters","role-template-view-basic"]'
        platform_steps.step_create_role(role_name)  # 创建角色
        # 查询角色并获取version
        response = platform_steps.step_get_role_info(role_name)
        version = response.json()['items'][0]['metadata']['resourceVersion']
        r = platform_steps.step_edit_role_authority(role_name, version, authority)
        try:
            # 验证编辑后的角色权限
            assert r.json()['metadata']['annotations']['iam.kubesphere.io/aggregation-roles'] == authority
        finally:
            platform_steps.step_delete_role(role_name)  # 删除新建的角色

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


if __name__ == "__main__":
    pytest.main(['-s', 'testRole.py'])  # -s参数是为了显示用例的打印信息。 -q参数只显示结果，不显示过程
