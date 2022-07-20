import pytest
import allure
import sys
import time
import random

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from common.getData import DoexcleByPandas
from common.logFormat import log_format
from common import commonFunction
from step import multi_worksapce_steps


@allure.feature('多集群环境企业空间')
@pytest.mark.skipif(commonFunction.check_multi_cluster() is False, reason='未开启多集群功能')
@pytest.mark.skipif(commonFunction.check_multi_cluster() is False, reason='单集群环境下不执行')
class TestWorkSpace(object):
    # 如果为单集群环境，则不会collect该class的所有用例。 __test__ = False
    __test__ = commonFunction.check_multi_cluster()

    user_name = 'user-for-test-ws'
    alias_name = '多集群'
    description = '用于测试多集群环境企业空间'
    ws_name = 'ws-for-test-multi-ws' + str(commonFunction.get_random())
    ws_role_name = ws_name + '-viewer-test'
    log_format()  # 配置日志格式
    # 从文件中读取用例信息
    parametrize = DoexcleByPandas().get_data_for_pytest(filename='../data/data.xlsx',
                                                        sheet_name='multi-cluster workspace')

    # 所有用例执行之前执行该方法
    def setup_class(self):
        multi_worksapce_steps.step_create_user(self.user_name)  # 创建一个用户
        # 获取集群名称
        clusters = multi_worksapce_steps.step_get_cluster_name()
        # 创建一个多集群企业空间（包含所有的集群）
        multi_worksapce_steps.step_create_multi_ws(self.ws_name + str(commonFunction.get_random()),
                             self.alias_name, self.description, clusters)
        # 创建若干个多集群企业空间（只部署在单个集群）
        if len(clusters) > 1:
            for i in range(len(clusters)):
                multi_worksapce_steps.step_create_multi_ws(self.ws_name + str(commonFunction.get_random()),
                                                           self.alias_name, self.description, clusters[i])
        # 创建一个多集群企业空间,供excle文件中的用例使用
        multi_worksapce_steps.step_create_multi_ws(self.ws_name, self.alias_name, self.description, clusters)
        time.sleep(3)

    # 所有用例执行完之后执行该方法
    def teardown_class(self):
        time.sleep(10)
        user_ws = multi_worksapce_steps.step_get_user_ws()  # 获取所有用户创建的企业空间
        for ws in user_ws:
            multi_worksapce_steps.step_delete_workspace(ws)  # 删除创建的企业空间
        multi_worksapce_steps.step_delete_user(self.user_name)  # 删除创建的用户

    @allure.title('{title}')  # 设置用例标题
    # 将用例信息以参数化的方式传入测试方法
    @pytest.mark.parametrize('id,url,params,data,story,title,method,severity,condition,except_result', parametrize)
    def test_ws(self, id, url, params, data, story, title, method, severity, condition, except_result):

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
        # 将测试用例中的变量替换成指定内容
        targets = commonFunction.replace_str(url, params, data, title, condition, except_result,
                                             actual_value='${ws_name}', expect_value=self.ws_name)
        # 使用修改过的内容进行测试
        print(targets[0])
        commonFunction.request_resource(targets[0], targets[1], targets[2], story, targets[3], method, severity,
                                        targets[4], targets[5])

    '''
    以下用例由于存在较多的前置条件，不便于从excle中获取信息，故使用一个方法一个用例的方式
    '''

    @allure.story('企业空间设置-企业角色')
    @allure.title('在企业空间编辑角色的权限信息')
    @allure.severity('critical')
    def test_edit_ws_role(self):
        # 查询企业空间
        response = multi_worksapce_steps.step_get_ws_info('')
        ws_count = response.json()['totalItems']
        for k in range(0, ws_count):
            # 获取每个企业空间的名称
            ws_name = response.json()['items'][k]['metadata']['name']
            if ws_name != 'system-workspace':
                authority_create = '["role-template-view-basic"]'  # 创建角色的权限信息
                authority_edit = '["role-template-view-basic","role-template-create-projects"]'  # 修改目标角色的权限信息
                ws_role_name = 'role' + str(commonFunction.get_random())  #创建的角色名称
                time.sleep(1)  # 由于新建的角色和系统自动生成的角色的生成时间是一致。后面获取角色的resourceversion是按时间排序获取的。因此在创建企业空间后sleep 1s
                # 在企业空间创建角色
                multi_worksapce_steps.step_create_ws_role(ws_name, ws_role_name, authority_create)
                # 查询并获取该角色的resourceversion
                re = multi_worksapce_steps.step_get_ws_role(ws_name, ws_role_name)
                version = re.json()['items'][0]['metadata']['resourceVersion']
                # 修改角色权限
                multi_worksapce_steps.step_edit_role_authory(ws_name, ws_role_name, version, authority_edit)
                # 查询并获取该角色的权限信息
                r = multi_worksapce_steps.step_get_ws_role(ws_name, ws_role_name)
                authority_actual = r.json()['items'][0]['metadata']['annotations']["iam.kubesphere.io/aggregation-roles"]
                # 验证修改角色权限后的权限信息
                assert authority_actual == authority_edit
                # 删除创建的角色
                multi_worksapce_steps.step_delete_role(ws_name, ws_role_name)

    @allure.story('企业空间设置-企业成员')
    @allure.title('在企业空间邀请存在的新成员')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_ws_invite_user(self):
        # 创建用户
        user_name = 'test' + str(commonFunction.get_random())
        multi_worksapce_steps.step_create_user(user_name)
        # 查询企业空间
        response = multi_worksapce_steps.step_get_ws_info('')
        ws_count = response.json()['totalItems']
        for k in range(0, ws_count):
            # 获取每个企业空间的名称
            ws_name = response.json()['items'][k]['metadata']['name']
            if ws_name != 'system-workspace':
                # 将用户邀请到企业空间
                ws_role_invite = ws_name + '-viewer'  # 邀请用户时赋予的角色
                multi_worksapce_steps.step_invite_user(ws_name, user_name, ws_role_invite)
                # 在企业空间中查询邀请的用户
                re = multi_worksapce_steps.step_get_ws_user(ws_name, user_name)
                # 验证邀请后的成员名称
                assert re.json()['items'][0]['metadata']['name'] == user_name
                # 将邀请的用户移除企业空间
                multi_worksapce_steps.step_delete_ws_user(ws_name, user_name)
        # 删除用户
        multi_worksapce_steps.step_delete_user(user_name)

    @allure.story('企业空间设置-企业角色')
    @allure.title('在企业空间编辑邀请成员的角色')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_ws_edit_invite_user(self):
        # 创建用户
        user_name = 'test' + str(commonFunction.get_random())
        multi_worksapce_steps.step_create_user(user_name)
        # 查询企业空间
        response = multi_worksapce_steps.step_get_ws_info('')
        ws_count = response.json()['totalItems']
        for k in range(0, ws_count):
            # 获取每个企业空间的名称
            ws_name = response.json()['items'][k]['metadata']['name']
            if ws_name != 'system-workspace':
                ws_role_create = ws_name + '-viewer'  # 邀请用户时赋予的角色
                ws_role_new = ws_name + '-admin'  # 修改的新角色
                # 将创建的用户邀请到创建的企业空间
                multi_worksapce_steps.step_invite_user(ws_name, user_name, ws_role_create)
                # 修改成员角色
                multi_worksapce_steps.step_edit_ws_user_role(ws_name, user_name, ws_role_new)
                # 查询该企业空间成员的信息
                r = multi_worksapce_steps.step_get_ws_user(ws_name, user_name)
                # 获取该成员的角色信息
                user_role = r.json()['items'][0]['metadata']['annotations']['iam.kubesphere.io/workspacerole']
                # 验证修改后的角色名称
                assert user_role == ws_role_new
                # 将邀请的用户移除企业空间
                # step_delete_ws_user(ws_name, self.user_name)
        # 删除创建的用户
        multi_worksapce_steps.step_delete_user(user_name)

    @allure.story('企业空间设置-企业成员')
    @allure.title('在企业空间删除邀请的成员并验证删除成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_ws_delete_invite_user(self):
        # 查询企业空间
        response = multi_worksapce_steps.step_get_ws_info('')
        ws_count = response.json()['totalItems']
        for k in range(0, ws_count):
            # 获取每个企业空间的名称
            ws_name = response.json()['items'][k]['metadata']['name']
            if ws_name != 'system-workspace':
                ws_role_create = ws_name + '-viewer'  # 邀请用户是赋予的角色
                # 将创建的用户邀请到创建的企业空间
                multi_worksapce_steps.step_invite_user(ws_name, self.user_name, ws_role_create)
                # 将邀请的用户移除企业空间
                multi_worksapce_steps.step_delete_ws_user(ws_name, self.user_name)
                # 查询该企业空间成员的信息
                re = multi_worksapce_steps.step_get_ws_user(ws_name, self.user_name)
                # 验证删除成功
                assert re.json()['totalItems'] == 0

    @allure.story('企业空间设置-企业组织')
    @allure.title('创建、编辑、删除企业组织')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_department(self):
        data = {"kubesphere.io/workspace-role": "wx-regular",
                "kubesphere.io/alias-name": "",
                "kubesphere.io/project-roles": "[]",
                "kubesphere.io/devops-roles": "[]",
                "kubesphere.io/creator": "admin"
                }
        # 查询企业空间
        response = multi_worksapce_steps.step_get_ws_info('')
        ws_count = response.json()['totalItems']
        for k in range(0, ws_count):
            # 获取每个企业空间的名称
            ws_name = response.json()['items'][k]['metadata']['name']
            if ws_name != 'system-workspace':
                # 创建企业组织,并获取创建的企业组织的name
                group_name = 'group' + str(commonFunction.get_random())
                res = multi_worksapce_steps.step_create_department(ws_name, group_name, data)
                name = res.json()['metadata']['name']
                # 获取所有的企业组织名称
                group_name_actual = multi_worksapce_steps.step_get_department(ws_name)
                # 校验企业组织名称，已验证企业组织创建成功
                assert group_name in group_name_actual
                # 编辑企业组织
                edit_data = {"metadata": {"annotations": {"kubesphere.io/workspace-role": "wx-regular",
                                                          "kubesphere.io/alias-name": "我是别名",
                                                          "kubesphere.io/project-roles": "[]",
                                                          "kubesphere.io/devops-roles": "[]",
                                                          "kubesphere.io/creator": "admin"}}}
                annotations = multi_worksapce_steps.step_edit_department(ws_name, name, edit_data)
                # 验证编辑后的内容
                assert "我是别名" == annotations['kubesphere.io/alias-name']
                # 删除企业组织,并获取返回信息
                re = multi_worksapce_steps.step_delete_department(ws_name, name)
                # 验证删除成功
                assert re.json()['message'] == 'success'

    @allure.story('企业空间设置-企业组织')
    @allure.title('创建重名的企业组织')
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_rename_department(self):
        # 创建企业组织
        data = {"kubesphere.io/workspace-role": "wx-regular",
                "kubesphere.io/alias-name": "",
                "kubesphere.io/project-roles": "[]",
                "kubesphere.io/devops-roles": "[]",
                "kubesphere.io/creator": "admin"
                }
        # 查询企业空间
        response = multi_worksapce_steps.step_get_ws_info('')
        ws_count = response.json()['totalItems']
        for k in range(0, ws_count):
            # 获取每个企业空间的名称
            ws_name = response.json()['items'][k]['metadata']['name']
            if ws_name != 'system-workspace':
                # 创建企业组织,并获取创建的企业组织的name
                group_name = 'group' + str(commonFunction.get_random())
                re = multi_worksapce_steps.step_create_department(ws_name, group_name, data)
                name = re.json()['metadata']['name']
                # 创建一个同名的企业组织
                re = multi_worksapce_steps.step_create_department(ws_name, group_name, data)
                # 校验接口返回信息
                assert_message = 'Operation cannot be fulfilled on groups.iam.kubesphere.io "' + group_name + \
                                 '": a group named ' + group_name + ' already exists in the workspace\n'
                assert re.text == assert_message
                # 删除创建的企业空间
                res = multi_worksapce_steps.step_delete_department(ws_name, name)
                # 验证删除成功
                res.json()['message'] == 'success'

    @allure.story('企业空间设置-企业组织')
    @allure.title('创建的企业组织名称中包含大写字母')
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_wrong_name_department(self):
        # 创建组织
        group_names = ['Test-group', 'test-Group', 'test-grouP']
        data = {"kubesphere.io/workspace-role": "wx-regular",
                "kubesphere.io/alias-name": "",
                "kubesphere.io/project-roles": "[]",
                "kubesphere.io/devops-roles": "[]",
                "kubesphere.io/creator": "admin"
                }
        # 查询企业空间
        response = multi_worksapce_steps.step_get_ws_info('')
        ws_count = response.json()['totalItems']
        for k in range(0, ws_count):
            # 获取每个企业空间的名称
            ws_name = response.json()['items'][k]['metadata']['name']
            if ws_name != 'system-workspace':
                for group_name in group_names:
                    # 获取返回信息
                    re = multi_worksapce_steps.step_create_department(self.ws_name, group_name, data)
                    assert_message = 'is invalid: [metadata.generateName: Invalid value: "' + group_name + '"'
                    # 校验接口返回信息
                    assert assert_message in re.text

    @allure.story('企业空间设置-企业组织')
    @allure.title('创建的企业组织名称中包含特殊字符')
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_wrong_name_1_department(self):
        # 创建组织
        data = {"kubesphere.io/workspace-role": "wx-regular",
                "kubesphere.io/alias-name": "",
                "kubesphere.io/project-roles": "[]",
                "kubesphere.io/devops-roles": "[]",
                "kubesphere.io/creator": "admin"
                }
        # 构建企业组织名称
        group_names = []
        for i in range(0, 9):
            group_names.append(random.choice(['@', '!', '$', '#', '%', '&', '*', '_', '+']) + 'test-group')
            group_names.append('test-group' + random.choice(['@', '!', '$', '#', '%', '&', '*', '_', '+']))
            group_names.append('test-' + random.choice(['@', '!', '$', '#', '%', '&', '*']) + 'group')
        # 查询企业空间
        response = multi_worksapce_steps.step_get_ws_info('')
        ws_count = response.json()['totalItems']
        for k in range(0, ws_count):
            # 获取每个企业空间的名称
            ws_name = response.json()['items'][k]['metadata']['name']
            if ws_name != 'system-workspace':
                for group_name in group_names:
                    res = multi_worksapce_steps.step_create_department(self.ws_name, group_name, data)
                    assert_message = 'is invalid: [metadata.generateName: Invalid value'
                    # 校验接口返回信息
                    assert assert_message in res.text

    @allure.story('企业空间设置-企业组织')
    @allure.title('创建企业组织时绑定不存在的项目')
    @allure.severity(allure.severity_level.CRITICAL)
    # 接口没有校验企业空间的角色、项目和角色是否存在
    def wx_test_create_wrong_pro_department(self):
        group_name = 'test-group'
        data = {"kubesphere.io/workspace-role": "wx-regular",
                "kubesphere.io/alias-name": "",
                "kubesphere.io/project-roles": "[{\"cluster\":\"\",\"namespace\":\"test\",\"role\":\"viewer1\"}]",
                "kubesphere.io/devops-roles": "[]",
                "kubesphere.io/creator": "admin"
                }
        # 获取返回信息
        response = multi_worksapce_steps.step_create_department(self.ws_name, group_name, data)
        print(response.text)

    @allure.story('企业空间设置-企业组织')
    @allure.title('为用户分配企业组织')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_assign_user(self):
        data = {"kubesphere.io/workspace-role": "wx-regular",
                "kubesphere.io/alias-name": "",
                "kubesphere.io/project-roles": "[]",
                "kubesphere.io/devops-roles": "[]",
                "kubesphere.io/creator": "admin"
                }
        # 查询企业空间
        response = multi_worksapce_steps.step_get_ws_info('')
        ws_count = response.json()['totalItems']
        for k in range(0, ws_count):
            # 获取每个企业空间的名称
            ws_name = response.json()['items'][k]['metadata']['name']
            if ws_name != 'system-workspace':
                group_name = 'group' + str(commonFunction.get_random())
                # 创建企业组织,并获取创建的企业组织的name
                resp = multi_worksapce_steps.step_create_department(ws_name, group_name, data)
                name = resp.json()['metadata']['name']
                # 获取该企业组织可分配的用户数量
                res = multi_worksapce_steps.step_get_user_for_department(name)
                counts = res.json()['totalItems']
                # 将指定用户绑定到指定企业组织
                re = multi_worksapce_steps.step_binding_user(self.ws_name, name, self.user_name)
                # 获取绑定后返回的用户名
                binding_user = re.json()[0]['users'][0]
                # 校验绑定的用户名称
                assert binding_user == self.user_name
                # 重新获取企业组织可分配的用户名称
                r = multi_worksapce_steps.step_get_user_for_department(name)
                counts_new = r.json()['totalItems']
                user_name = []
                for i in range(0, counts_new):
                    user_name.append(r.json()['items'][i]['metadata']['name'])
                # 验证已分配的用户不在可分配的用户列表中
                assert binding_user not in user_name

    @allure.story('企业空间设置-企业组织')
    @allure.title('将已绑定企业组织的用户再次绑定该企业组织')
    @allure.severity(allure.severity_level.CRITICAL)
    # 接口没有限制将同一个用户重复绑定到一个企业组织
    def wx_test_reassign_user(self):
        group_name = 'test2'
        data = {"kubesphere.io/workspace-role": "wx-regular",
                "kubesphere.io/alias-name": "",
                "kubesphere.io/project-roles": "[]",
                "kubesphere.io/devops-roles": "[]",
                "kubesphere.io/creator": "admin"
                }
        # 创建企业组织,并获取创建的企业组织的name
        response = multi_worksapce_steps.step_create_department(self.ws_name, group_name, data)
        name = response.json()['metadata']['name']
        # 将指定用户绑定到指定企业组织
        multi_worksapce_steps.step_binding_user(self.ws_name, name, self.user_name)
        # 将指定用户再次绑定到该企业空间
        response = multi_worksapce_steps.step_binding_user(self.ws_name, name, self.user_name)
        print(response.text)

    @allure.story('企业空间设置-企业组织')
    @allure.title('将用户从企业组织解绑')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_unbind_user(self):
        data = {"kubesphere.io/workspace-role": "wx-regular",
                "kubesphere.io/alias-name": "",
                "kubesphere.io/project-roles": "[]",
                "kubesphere.io/devops-roles": "[]",
                "kubesphere.io/creator": "admin"
                }
        # 查询企业空间
        response = multi_worksapce_steps.step_get_ws_info('')
        ws_count = response.json()['totalItems']
        for k in range(0, ws_count):
            # 获取每个企业空间的名称
            ws_name = response.json()['items'][k]['metadata']['name']
            if ws_name != 'system-workspace':
                group_name = 'group' + str(commonFunction.get_random())
                # 创建企业组织,并获取创建的企业组织的name
                res = multi_worksapce_steps.step_create_department(ws_name, group_name, data)
                name = res.json()['metadata']['name']
                # 将指定用户绑定到指定企业组织
                re = multi_worksapce_steps.step_binding_user(ws_name, name, self.user_name)
                # 获取绑定后返回的用户名
                binding_user = re.json()[0]['metadata']['name']
                # 将用户从企业组织解绑
                r = multi_worksapce_steps.step_unbind_user(ws_name=ws_name, user_name=binding_user)
                # 校验解绑结果
                assert r.json()['message'] == 'success'
                # 删除企业组织
                multi_worksapce_steps.step_delete_department(ws_name, name)

    @allure.story('企业空间设置-配额管理')
    @allure.title('编辑企业空间配额')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_edit_quota(self):
        # 查询企业空间
        response = multi_worksapce_steps.step_get_ws_info('')
        ws_count = response.json()['totalItems']
        for k in range(0, ws_count):
            # 获取每个企业空间的名称
            ws_name = response.json()['items'][k]['metadata']['name']
            # 获取企业空间的集群信息
            if ws_name != 'system-workspace':
                clusters_name = []
                res = multi_worksapce_steps.step_get_ws_info(ws_name)
                clusters = res.json()['items'][0]['spec']['placement']['clusters']
                for i in range(0, len(clusters)):
                    clusters_name.append(clusters[i]['name'])
                # 遍历集群名称，在每个集群创建项目
                for cluster in clusters_name:
                    # 初始化企业配额
                    multi_worksapce_steps.step_init_quota(cluster_name=cluster, ws_name=ws_name)
                    # 获取企业配额的resourceVersion
                    res = multi_worksapce_steps.step_get_quota_resource_version(cluster, ws_name)
                    resource_version = res.json()['metadata']['resourceVersion']
                    # 编辑企业配额
                    hard_data = {"limits.cpu": "10", "limits.memory": "100Gi",
                                 "requests.cpu": "1", "requests.memory": "1Gi"}
                    multi_worksapce_steps.step_edit_quota(ws_name=ws_name, hard_data=hard_data, cluster_name=cluster,
                                    resource_version=resource_version)
                    # 获取企业空间的配额信息
                    r = multi_worksapce_steps.step_get_ws_quota(cluster, ws_name)
                    hard_info = r.json()['spec']['quota']['hard']
                    # 校验修改后的配额信息
                    assert hard_data == hard_info

    @allure.story('项目管理')
    @allure.title('在多集群企业空间创建项目')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_project(self):
        # 查询企业空间
        response = multi_worksapce_steps.step_get_ws_info('')
        ws_count = response.json()['totalItems']
        for k in range(0, ws_count):
            # 获取每个企业空间的名称
            ws_name = response.json()['items'][k]['metadata']['name']
            # 获取企业空间的集群信息
            if ws_name != 'system-workspace':
                clusters_name = []
                res = multi_worksapce_steps.step_get_ws_info(ws_name)
                clusters = res.json()['items'][0]['spec']['placement']['clusters']
                for i in range(0, len(clusters)):
                    clusters_name.append(clusters[i]['name'])
                # 遍历集群名称，在每个集群创建项目
                for cluster in clusters_name:
                    project_name = 'test-pro' + str(commonFunction.get_random())
                    multi_worksapce_steps.step_create_project(cluster, ws_name, project_name)
                    # 查询项目并验证项目创建成功
                    re = multi_worksapce_steps.step_get_project(cluster, ws_name, project_name)
                    assert re.json()['totalItems'] == 1
                    # 删除创建的项目
                    multi_worksapce_steps.step_delete_project(cluster, ws_name, project_name)

    @allure.story('项目管理')
    @allure.title('在多集群企业空间使用重复的名称创建项目')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_project_exist_name(self):
        # 查询企业空间
        response = multi_worksapce_steps.step_get_ws_info('')
        ws_count = response.json()['totalItems']
        for k in range(0, ws_count):
            # 获取每个企业空间的名称
            ws_name = response.json()['items'][k]['metadata']['name']
            # 获取企业空间的集群信息
            if ws_name != 'system-workspace':
                clusters_name = []
                res = multi_worksapce_steps.step_get_ws_info(ws_name)
                clusters = res.json()['items'][0]['spec']['placement']['clusters']
                for i in range(0, len(clusters)):
                    clusters_name.append(clusters[i]['name'])
                # 遍历集群名称，在每个集群创建项目
                for cluster in clusters_name:
                    project_name = 'test-pro' + str(commonFunction.get_random())
                    multi_worksapce_steps.step_create_project(cluster, ws_name, project_name)
                    # 查询项目并验证项目创建成功
                    re = multi_worksapce_steps.step_get_project(cluster, ws_name, project_name)
                    assert re.json()['totalItems'] == 1
                    # 使用重复的名称创建项目
                    r = multi_worksapce_steps.step_create_project(cluster, ws_name, project_name)
                    # 验证提示信息正确
                    assert r.text == 'namespaces ' + '"' + project_name + '"' + ' already exists\n'
                    # 删除创建的项目
                    multi_worksapce_steps.step_delete_project(cluster, ws_name, project_name)

    @allure.story('项目管理')
    @allure.title('创建多集群项目,且将其部署在所有和单个集群上')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_multi_project_alone(self):
        # 查询企业空间
        response = multi_worksapce_steps.step_get_ws_info('')
        ws_count = response.json()['totalItems']
        for k in range(0, ws_count):
            # 获取每个企业空间的名称
            ws_name = response.json()['items'][k]['metadata']['name']
            # 获取企业空间的集群信息
            if ws_name != 'system-workspace':
                clusters_name = []
                re = multi_worksapce_steps.step_get_ws_info(ws_name)
                clusters = re.json()['items'][0]['spec']['placement']['clusters']
                for i in range(0, len(clusters)):
                    clusters_name.append(clusters[i]['name'])
                if len(clusters_name) > 1:
                    # 创建多集群项目,但是项目部署在单个集群上
                    for j in range(0, len(clusters_name)):
                        multi_project_name = 'multi-pro' + str(commonFunction.get_random())
                        multi_worksapce_steps.step_create_multi_project(ws_name, multi_project_name, clusters_name[j])
                        # 查询多集群项目，验证项目创建
                        re = multi_worksapce_steps.step_get_multi_project(ws_name, multi_project_name)
                        assert re.json()['totalItems'] == 1
                        # 删除多集群项目
                        multi_worksapce_steps.step_delete_multi_project(multi_project_name)
                else:
                    multi_project_name = 'multi-pro' + str(commonFunction.get_random())
                    multi_worksapce_steps.step_create_multi_project(ws_name, multi_project_name, clusters_name)
                    # 查询多集群项目，验证项目创建
                    re = multi_worksapce_steps.step_get_multi_project(ws_name, multi_project_name)
                    assert re.json()['totalItems'] == 1
                    # 删除多集群项目
                    multi_worksapce_steps.step_delete_multi_project(multi_project_name)

    @pytest.mark.skipif(commonFunction.get_components_status_of_cluster('network') is False,
                        reason='集群未开启networkpolicy功能')
    @allure.story('企业空间设置-网络策略')
    @allure.title('关闭企业空间网络隔离')
    def wx_test_off_network_lsolation(self):
        # 关闭企业空间网络隔离
        multi_worksapce_steps.step_set_network_lsolation(self.ws_name, False)
        # 验证企业空间信息
        response = multi_worksapce_steps.step_get_ws_info(self.ws_name)
        # 获取企业空间的网络隔离状态
        network_lsolation = response.json()['spec']['template']['spec']['networkIsolation']
        # 验证设置成功
        assert network_lsolation is False

    @pytest.mark.skipif(commonFunction.get_components_status_of_cluster('network') is False,
                        reason='集群未开启networkpolicy功能')
    @allure.story('企业空间设置-网络策略')
    @allure.title('开启企业空间网络隔离')
    def wx_test_enable_network_lsolation(self):
        # 关闭企业空间网络隔离
        multi_worksapce_steps.step_set_network_lsolation(self.ws_name, True)
        # 验证企业空间信息
        response = multi_worksapce_steps.step_get_ws_info(self.ws_name)
        # 获取企业空间的网络隔离状态
        network_lsolation = response.json()['spec']['template']['spec']['networkIsolation']
        # 验证设置成功
        assert network_lsolation is True


if __name__ == "__main__":
    pytest.main(['-s', 'testWorkspace.py'])  # -s参数是为了显示用例的打印信息。 -q参数只显示结果，不显示过程
