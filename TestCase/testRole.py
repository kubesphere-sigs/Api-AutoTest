import requests
import pytest
import json
import allure
import sys

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from config import config
from common.getData import DoexcleByPandas
from common.getHeader import get_header
from common.logFormat import log_format
from common import commonFunction


@allure.step('新建角色')
def step_create_role(role_name):
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/globalroles'
    data = {"apiVersion": "iam.kubesphere.io/v1alpha2",
            "kind": "GlobalRole",
            "rules": [],
            "metadata":
                {
                    "name": role_name,
                    "annotations": {
                        "iam.kubesphere.io/aggregation-roles":
                            "[\"role-template-manage-clusters\",\"role-template-view-clusters\","
                            "\"role-template-view-basic\"]",
                        "kubesphere.io/creator": "admin"
                    }
                }
            }
    r = requests.post(url, headers=get_header(), data=json.dumps(data))
    return r


@allure.step('编辑角色权限')
def step_edit_role_authority(role_name, version, authority):
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/globalroles/' + role_name
    data = {"apiVersion": "iam.kubesphere.io/v1alpha2",
            "kind": "GlobalRole",
            "rules": [{"verbs": ["*"], "apiGroups": ["*"], "resources": ["globalroles"]},
                      {"verbs": ["get", "list", "watch"], "apiGroups": ["iam.kubesphere.io"],
                       "resources": ["globalroles"]}, {"verbs": ["get", "list", "watch"], "apiGroups": ["*"],
                                                       "resources": ["users", "users/loginrecords"]}],
            "metadata": {"name": role_name, "labels": {"kubefed.io/managed": "false"}, "annotations": {
                "iam.kubesphere.io/aggregation-roles": authority,
                "kubesphere.io/creator": "admin"}, "resourceVersion": version}}
    r = requests.put(url, headers=get_header(), data=json.dumps(data))
    return r


@allure.step('查询角色信息')
def step_get_role_info(role_name):
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/globalroles?name=' + role_name + \
                       '&annotation=kubesphere.io%2Fcreator'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('删除角色')
def step_delete_role(role_name):
    """
    :param role_name: 系统角色的名称
    """
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/globalroles/' + role_name
    response = requests.delete(url, headers=get_header())
    return response


@allure.feature('系统角色管理')
class TestRole(object):
    # 从文件中读取用例信息
    parametrize = DoexcleByPandas().get_data_for_pytest(filename='../data/data.xlsx', sheet_name='system_role')

    @allure.title('{title}')  # 设置用例标题
    @allure.severity(allure.severity_level.CRITICAL)  # 设置用例优先级
    # 将用例信息以参数化的方式传入测试方法
    @pytest.mark.parametrize('id,url,data, story, title,method,severity,condition,except_result', parametrize)
    def test_role(self, id, url, data, story, title, method, severity, condition, except_result):

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
            r = requests.patch(url, headers=get_header(), data=json.dumps(data))

        elif method == 'delete':
            # 测试delete方法
            r = requests.delete(url, headers=get_header())

        # 将校验条件和预期结果参数化
        if condition != '':
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

    '''
        以下用例由于存在较多的前置条件，不便于从excle中获取信息，故使用一个方法一个用例的方式
    '''

    @allure.story('编辑角色')
    @allure.severity('critical')
    @allure.title('测试编辑角色权限')
    def test_edit_role(self):
        role_name = 'role' + str(commonFunction.get_random())
        authority = '["role-template-view-clusters","role-template-view-basic"]'
        step_create_role(role_name)  # 创建角色
        # 查询角色并获取version
        response = step_get_role_info(role_name)
        version = response.json()['items'][0]['metadata']['resourceVersion']
        r = step_edit_role_authority(role_name, version, authority)
        try:
            # 验证编辑后的角色权限
            assert r.json()['metadata']['annotations']['iam.kubesphere.io/aggregation-roles'] == authority
        finally:
            step_delete_role(role_name)  # 删除新建的角色

    @allure.story('编辑角色')
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title('查询不存在的角色')
    def test_query_not_exist_role(self):
        # 构建角色名称
        role_name = 'role' + str(commonFunction.get_random())
        # 查询角色
        response = step_get_role_info(role_name)
        # 验证查询结果为空
        assert response.json()['totalItems'] == 0


if __name__ == "__main__":
    pytest.main(['-s', 'testRole.py'])  # -s参数是为了显示用例的打印信息。 -q参数只显示结果，不显示过程
