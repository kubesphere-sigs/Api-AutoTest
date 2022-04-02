import pytest
import allure
import sys
import time

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from common.getData import DoexcleByPandas
from common import commonFunction
from step import platform_steps
from common.getHeader import get_header


@allure.feature('系统账户管理')
class TestUser(object):
    # 从文件中读取用例信息
    parametrize = DoexcleByPandas().get_data_for_pytest(filename='../data/data.xlsx', sheet_name='system_user')

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
        # 执行excel中的用例
        commonFunction.request_resource(url, params, data, story, title, method, severity, condition, except_result)

    '''
        以下用例由于存在较多的前置条件，不便于从excle中获取信息，故使用一个方法一个用例的方式
    '''

    @allure.story('编辑用户')
    @allure.severity('critical')
    @allure.title('测试修改用户信息')
    def test_edit_user(self):
        user_name = 'wx123'
        role = 'workspaces-manager'
        email_new = 'stevewen12345@yunify.com'
        role_new = 'users-manager'
        description = 'test'
        platform_steps.step_create_user(user_name, role)  # 创建用户
        time.sleep(3)
        version = platform_steps.step_get_user_version(user_name)  # 获取创建用户的resourceVersion
        # 编辑用户信息的email地址
        r = platform_steps.step_edit_user(user_name, role_new, description, version, email_new)
        try:
            # 获取修改后的email
            email_actual = r.json()['spec']['email']
        except Exception as e:
            print(e)
        # 验证修改用户后的邮箱信息
        assert email_actual == email_new
        platform_steps.step_delete_user(user_name)  # 删除新建的用户

    @allure.story('用户')
    @allure.severity('critical')
    @allure.title('遍历使用系统所有的内置角色创建用户，查看用户详情，然后使用新用户登陆ks,最后删除用户')
    def test_login_with_new_user(self):
        roles = ['workspaces-manager', 'users-manager', 'platform-regular', 'platform-admin']
        for role in roles:
            user_name = 'test' + str(commonFunction.get_random())
            # 创建用户
            platform_steps.step_create_user(user_name, role)
            # 等待创建的用户被激活
            time.sleep(3)
            # 查看用户详情
            re = platform_steps.step_get_user_info(user_name)
            # 验证用户的状态为active
            status = re.json()['items'][0]['status']['state']
            assert status == 'Active'
            # 获取并校验用户的角色
            user_role = re.json()['items'][0]['metadata']['annotations']['iam.kubesphere.io/globalrole']
            assert user_role == role
            # 登陆ks
            headers = platform_steps.step_get_headers(user_name, 'P@88w0rd')
            # 验证headers获取成功
            assert headers
            # 删除用户
            platform_steps.step_delete_user(user_name)

    @allure.story('用户')
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title('{title}')
    @pytest.mark.parametrize('type, title',
                             [('user', '修改密码，然后使用修改后的密码登陆ks'),
                              ('admin', '使用admin账号修改用户密码，然后使用修改后的密码登陆ks')])
    def test_modify_user_pwd_by_admin(self, type, title):
        # 创建用户
        user_name = 'modify' + str(commonFunction.get_random())
        role = 'users-manager'
        platform_steps.step_create_user(user_name, role)
        # 等待创建的用户被激活
        time.sleep(3)
        # 使用新创建的用户登陆，并获取headers
        try:
            headers = platform_steps.step_get_headers(user_name, pwd='P@88w0rd')
        except Exception as e:
            print(e)
            print("新创建的用户登陆失败")
        # 修改用户密码
        new_pwd = 'Admin@123'
        if type == 'admin':
            response = platform_steps.step_modify_user_pwd(user_name=user_name, headers=get_header(), new_pwd=new_pwd)
        elif type == 'user':
            response = platform_steps.step_modify_user_pwd(user_name=user_name, headers=headers, new_pwd=new_pwd)
        # 验证密码修改成功
        assert response.json()['message'] == 'success'
        time.sleep(3)
        # 使用新创建的用户登陆，并获取headers
        headers_new = platform_steps.step_get_headers(user_name=user_name, pwd=new_pwd)
        assert headers_new
        # 删除创建的用户
        platform_steps.step_delete_user(user_name)

    @allure.story('用户')
    @allure.severity('critical')
    @allure.title('用户历史登陆时间')
    def test_user_login_history(self):
        user_name = 'modify' + str(commonFunction.get_random())
        role = 'platform-admin'
        platform_steps.step_create_user(user_name, role)
        # 等待创建的用户被激活
        time.sleep(3)
        # 验证用户还未登陆
        res = platform_steps.step_get_user_info(user_name)
        assert 'lastLoginTime' not in res.json()['items'][0]['status']
        # 使用新创建的用户登陆，并获取headers
        try:
            headers = platform_steps.step_get_headers(user_name, pwd='P@88w0rd')
        except Exception as e:
            print(e)
            print("新创建的用户登陆失败")
        # 验证登陆成功
        assert headers
        # 查询新用户信息
        res = platform_steps.step_get_user_info(user_name)
        # 验证已有登陆时间信息
        assert 'lastLoginTime' in res.json()['items'][0]['status']
        # 删除用户
        platform_steps.step_delete_user(user_name)


if __name__ == "__main__":
    pytest.main(['-s', 'testUser.py'])  # -s参数是为了显示用例的打印信息。 -q参数只显示结果，不显示过程
