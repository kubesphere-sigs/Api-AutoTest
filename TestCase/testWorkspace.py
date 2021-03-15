import requests
import pytest
import json
import allure
import sys
import time
sys.path.append('../')  #将项目路径加到搜索路径中，使得自定义模块可以引用

import logging
from config import config
from common.getData import DoexcleByPandas
from common.getHeader import get_header, get_header_for_patch
from common.logFormat import log_format
from common import commonFunction


@allure.feature('企业空间角色&用户管理')
class TestWorkSpace(object):
    user_name = 'test-user'
    ws_name = 'test-ws1'
    ws_name1 = 'auto-wx-ws'
    ws_role_name = ws_name + '-viewer'
    log_format()  #配置日志格式
    #从文件中读取用例信息
    parametrize = DoexcleByPandas().get_data_for_pytest(filename='../data/data.xlsx', sheet_name='workspace')

    #所有用例执行之前执行该方法
    def setup_class(self):
        commonFunction.create_user(self.user_name)  #创建一个用户
        commonFunction.create_workspace(self.ws_name)  #创建一个企业空间
        commonFunction.create_workspace(self.ws_name1)  # 创建一个企业空间,供excle文件中的用例使用
        time.sleep(3)
    # 所有用例执行完之后执行该方法
    def teardown_class(self):
        time.sleep(10)
        commonFunction.delete_workspace(self.ws_name)  # 删除创建的企业空间
        commonFunction.delete_workspace(self.ws_name1)  #删除供excle中用例使用的企业空间
        commonFunction.delete_user(self.user_name)  # 删除创建的用户

    @allure.title('{title}')  # 设置用例标题
    @allure.severity(allure.severity_level.CRITICAL)  # 设置用例优先级
    #将用例信息以参数化的方式传入测试方法
    @pytest.mark.parametrize('id,url,data,story,title,method,severity,condition,except_result', parametrize)
    def test_ws(self, id, url, data, story, title, method, severity, condition, except_result):

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
            #测试get方法
            r = requests.get(url, headers=get_header())

        elif method == 'post':
            #测试post方法
            data = eval(data)
            r = requests.post(url, headers=get_header(), data=json.dumps(data))

        elif method == 'patch':
            # 测试patch方法
            data = eval(data)
            print(data)
            r = requests.patch(url, headers=get_header_for_patch(), data=json.dumps(data))

        elif method == 'delete':
            #测试delete方法
            r = requests.delete(url, headers=get_header())

        #将校验条件和预期结果参数化
        if condition != 'nan':
            condition_new = eval(condition)  #将字符串转化为表达式
            if isinstance(condition_new, str):
                #判断表达式的结果是否为字符串，如果为字符串格式，则去掉其首尾的空格
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
    @allure.title('在企业空间编辑角色的权限信息')
    @allure.severity('critical')
    def test_edit_ws_role(self):

        authority = '["role-template-view-basic","role-template-create-projects"]'  #修改目标角色的权限信息
        time.sleep(1)  #由于新建的角色和系统自动生成的角色的生成时间是一致。后面获取角色的resourceversion是按时间排序获取的。因此在创建企业空间后sleep 1s
        commonFunction.create_ws_role(self.ws_name, self.ws_role_name)  #在企业空间创建角色
        version = commonFunction.get_ws_role_version(self.ws_name)  #获取该角色的resourceversion
        #修改角色的url地址
        url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/workspaces/' + self.ws_name + '/workspaceroles/' + self.ws_role_name
        #修改目标角色的数据
        data = {"apiVersion": "iam.kubesphere.io/v1alpha2",
                "kind": "WorkspaceRole",
                "metadata": {"name": self.ws_role_name,
                             "labels": {"kubesphere.io/workspace": self.ws_name},
                             "annotations": {"iam.kubesphere.io/aggregation-roles": "[\"role-template-view-basic\","
                                                                                    "\"role-template-create-projects\"]",
                                             "kubesphere.io/creator": "admin"},
                             "resourceVersion": version
                             }
                }
        #修改角色权限
        r = requests.put(url, headers=get_header(), data=json.dumps(data))
        #验证修改角色权限后的权限信息
        assert r.json()['metadata']['annotations']['iam.kubesphere.io/aggregation-roles'] == authority
        # 在日志中打印出实际结果
        logging.info('reality_result:' + str(r.json()['metadata']['annotations']['iam.kubesphere.io/aggregation-roles']))

    @allure.title('在企业空间邀请存在的新成员')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_ws_invite_user(self):

        #邀请企业空间成员的URL地址
        url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/workspaces/' + self.ws_name + '/workspacemembers'
        #邀请成员的信息
        data = [{"username": self.user_name, "roleRef": self.ws_role_name}]
        #邀请成员
        r = requests.post(url, headers=get_header(), data=json.dumps(data))
        #验证邀请后的成员名称
        assert r.json()[0]['username'] == self.user_name
        # 在日志中打印出实际结果
        logging.info('reality_result:' + str(r.json()[0]['username']))

    @allure.title('在企业空间编辑邀请成员的角色')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_ws_edit_invite_user(self):

        ws_role_new = self.ws_name + '-admin'  #修改的新角色
        commonFunction.ws_invite_user(self.ws_name, self.user_name, self.ws_role_name)  #将创建的用户邀请到创建的企业空间
        #修改企业空间成员角色的url地址
        url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/workspaces/' + self.ws_name + '/workspacemembers/' + self.user_name
        #修改的目标数据
        data = {"username": self.user_name,
                "roleRef": ws_role_new}
        #修改成员角色
        r = requests.put(url, headers=get_header(), data=json.dumps(data))
        #验证修改后的角色名称
        assert r.json()['roleRef'] == ws_role_new
        # 在日志中打印出实际结果
        logging.info('actual_result:' + str(r.json()['roleRef']))

    @allure.title('在企业空间删除邀请的成员')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_ws_delete_invite_user(self):

        commonFunction.ws_invite_user(self.ws_name, self.user_name, self.ws_role_name)  #将创建的用户邀请到创建的企业空间
        #删除邀请成员的url地址
        url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/workspaces/' + self.ws_name + '/workspacemembers/' + self.user_name
        #删除邀请成员
        r = requests.delete(url, headers=get_header())

        #验证实际结果为'success
        assert r.json()['message'] == 'success'

        # 在日志中打印出实际结果
        logging.info('actual_result:' + str(r.json()['message']))

if __name__ == "__main__":
    pytest.main(['-s', 'testWorkspace.py'])  # -s参数是为了显示用例的打印信息。 -q参数只显示结果，不显示过程






