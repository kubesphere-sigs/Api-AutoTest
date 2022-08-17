# -- coding: utf-8 --
import pytest
import allure
import sys
import time

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from fixtures.platform import create_user, create_role
from common.getData import DoexcleByPandas
from common import commonFunction
from step import platform_steps
from common.getHeader import get_header


@allure.feature('系统账户管理')
class TestUser(object):
    # 从文件中读取用例信息
    parametrize = DoexcleByPandas().get_data_from_yaml(filename='../data/system_user.yaml')

    @allure.title('{title}')  # 设置用例标题
    # 将用例信息以参数化的方式传入测试方法
    @pytest.mark.parametrize('id,url,params,data, story, title,method,severity,condition,except_result', parametrize)
    def test_user(self, id, url, params, data, story, title, method, severity, condition, except_result):

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
        # 执行yaml中的用例
        commonFunction.request_resource(url, params, data, story, title, method, severity, condition, except_result)

    @allure.story('编辑用户')
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title('测试修改用户信息')
    def test_edit_user(self, create_user):
        email_new = 'test' + str(commonFunction.get_random()) + '@yunify.com'
        role_new = 'users-manager'
        description = 'test'
        time.sleep(3)
        version = platform_steps.step_get_user_version(create_user)  # 获取创建用户的resourceVersion
        # 编辑用户信息的email地址
        r = platform_steps.step_edit_user(create_user, role_new, description, version, email_new)
        email_actual = ''
        try:
            # 获取修改后的email
            email_actual = r.json()['spec']['email']
        except Exception as e:
            print(e)
        # 验证修改用户后的邮箱信息
        assert email_actual == email_new

    @allure.story('用户')
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title('{title}')
    @pytest.mark.parametrize('role, title',
                             [('workspaces-manager', '使用系统的内置角色workspaces-manager创建用户，查看用户详情，然后使用新用户登陆ks,最后删除用户'),
                              ('users-manager', '使用系统的内置角色users-manager创建用户，查看用户详情，然后使用新用户登陆ks,最后删除用户'),
                              ('platform-regular', '使用系统的内置角色platform-regular创建用户，查看用户详情，然后使用新用户登陆ks,最后删除用户'),
                              ('platform-admin', '使用系统的内置角色platform-admin创建用户，查看用户详情，然后使用新用户登陆ks,最后删除用户'),
                              ])
    def test_login_with_new_user(self, role, title):
        user_name = 'test' + str(commonFunction.get_random())
        # 创建用户
        platform_steps.step_create_user(user_name, role)
        # 等待创建的用户被激活
        time.sleep(3)
        # 查看用户详情
        re = platform_steps.step_get_user_info(user_name)
        # 验证用户的状态为active
        status = re.json()['items'][0]['status']['state']
        with pytest.assume:
            assert status == 'Active'
        # 获取并校验用户的角色
        user_role = re.json()['items'][0]['metadata']['annotations']['iam.kubesphere.io/globalrole']
        with pytest.assume:
            assert user_role == role
        # 登陆ks
        headers = platform_steps.step_get_headers(user_name, 'P@88w0rd')
        # 验证headers获取成功
        with pytest.assume:
            assert headers
        # 删除用户
        platform_steps.step_delete_user(user_name)

    @allure.story('用户')
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title('{title}')
    @pytest.mark.parametrize('type, title',
                             [('user', '修改密码，然后使用修改后的密码登陆ks'),
                              ('admin', '使用admin账号修改用户密码，然后使用修改后的密码登陆ks')])
    def test_modify_user_pwd_by_admin(self, type, title, create_user):
        # 等待创建的用户被激活
        time.sleep(3)
        # 使用新创建的用户登陆，并获取headers
        try:
            headers = platform_steps.step_get_headers(create_user, pwd='P@88w0rd')
        except Exception as e:
            print(e)
            print("新创建的用户登陆失败")
        # 修改用户密码
        new_pwd = 'Admin@123'
        if type == 'admin':
            response = platform_steps.step_modify_user_pwd(user_name=create_user, headers=get_header(), new_pwd=new_pwd)
        elif type == 'user':
            response = platform_steps.step_modify_user_pwd(user_name=create_user, headers=headers, new_pwd=new_pwd)
        # 验证密码修改成功
        with pytest.assume:
            assert response.json()['message'] == 'success'
        time.sleep(3)
        # 使用新创建的用户登陆，并获取headers
        headers_new = platform_steps.step_get_headers(user_name=create_user, pwd=new_pwd)
        assert headers_new

    @allure.story('用户')
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title('用户历史登陆时间')
    def test_user_login_history(self, create_user):
        # 等待创建的用户被激活
        time.sleep(3)
        # 验证用户还未登陆
        res = platform_steps.step_get_user_info(create_user)
        with pytest.assume:
            assert 'lastLoginTime' not in res.json()['items'][0]['status']
        # 使用新创建的用户登陆，并获取headers
        try:
            platform_steps.step_get_headers(create_user, pwd='P@88w0rd')
        except Exception as e:
            print(e)
            print("新创建的用户登陆失败")
        # 验证登陆成功
        time.sleep(3)
        i = 0
        while i < 60:
            try:
                # 查询新用户信息
                res = platform_steps.step_get_user_info(create_user)
                if res.json()['items'][0]['status']:
                    break
            except Exception as e:
                print(e)
                time.sleep(1)
                i += 1
        # 验证已有登陆时间信息
        assert 'lastLoginTime' in res.json()['items'][0]['status']


if __name__ == "__main__":
    pytest.main(['-s', 'test_user.py'])  # -s参数是为了显示用例的打印信息。 -q参数只显示结果，不显示过程
