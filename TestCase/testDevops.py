import requests
import pytest
import json
import allure
import sys
import base64

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

import time
from urllib import parse
from common.getHeader import get_header
from common import commonFunction
from step import devops_steps, platform_steps, workspace_steps, toolbox_steps, project_steps
from step import workspace_steps
from common.getConfig import get_config

env_url = get_config()['env']['url']


@allure.feature('DevOps')
@pytest.mark.skipif(commonFunction.get_component_health_of_cluster('kubesphere-devops-system') is False,
                    reason='集群devops功能未准备好')
@pytest.mark.skipif(commonFunction.get_components_status_of_cluster('devops') is False, reason='集群未开启devops功能')
@pytest.mark.skipif(commonFunction.check_multi_cluster() is True, reason='多集群环境下不执行')
class TestDevOps(object):
    user_name = 'wx-user' + str(commonFunction.get_random())
    user_role = 'users-manager' + str(commonFunction.get_random())
    ws_name = 'ws-dev' + str(commonFunction.get_random())
    dev_name = 'wx-dev' + str(commonFunction.get_random())
    ws_role_name = ws_name + '-viewer' + str(commonFunction.get_random())
    dev_role_name = 'wx-dev-role' + str(commonFunction.get_random())
    dev_name_new = ''

    # 所有用例执行之前执行该方法
    def setup_class(self):
        platform_steps.step_create_user(self.user_name, self.user_role)  # 创建一个用户
        workspace_steps.step_create_workspace(self.ws_name)  # 创建一个企业空间
        commonFunction.ws_invite_user(self.ws_name, self.user_name, self.ws_name + '-viewer')  # 将创建的用户邀请到企业空间
        devops_steps.step_create_devops(self.ws_name, self.dev_name)  # 创建一个devops工程
        response = devops_steps.step_get_devopinfo(self.ws_name, self.dev_name)
        self.dev_name_new = response.json()['items'][0]['metadata']['name']

    # 所有用例执行完之后执行该方法
    def teardown_class(self):
        # 获取devops工程的id
        response = devops_steps.step_get_devopinfo(self.ws_name, self.dev_name)
        dev_name_new = response.json()['items'][0]['metadata']['name']
        devops_steps.step_delete_devops(ws_name=self.ws_name, devops_name=dev_name_new)  # 删除创建的devops工程
        workspace_steps.step_delete_workspace(self.ws_name)  # 删除创建的工作空间
        platform_steps.step_delete_user(self.user_name)  # 删除创建的用户

    '''
    以下用例由于存在较多的前置条件，不便于从excle中获取信息，故使用一个方法一个用例的方式
    '''

    @allure.story('devops项目')
    @allure.title('创建devops工程,然后将其删除')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_devops(self):
        devops_name = 'test-devops' + str(commonFunction.get_random())
        # 创建devops工程
        devops_steps.step_create_devops(self.ws_name, devops_name)
        # 查询devops工程
        response = devops_steps.step_get_devopinfo(self.ws_name, devops_name)
        # 获取devops工程的别名
        devops_name_new = response.json()['items'][0]['metadata']['name']
        # 获取devops的数量
        count = response.json()['totalItems']
        # 验证数量正确
        assert count == 1
        # 删除创建的devops工程
        devops_steps.step_delete_devops(self.ws_name, devops_name_new)
        time.sleep(5)
        # 查询devops工程
        re = devops_steps.step_get_devopinfo(self.ws_name, devops_name)
        # 获取devops的数量
        count = re.json()['totalItems']
        # 验证数量正确
        assert count == 0

    @allure.story('devops项目')
    @allure.title('精确查询存在的devops工程')
    @allure.severity(allure.severity_level.NORMAL)
    def test_search_devops(self):
        # 查询前置条件中创建的devops工程
        devops_name = devops_steps.step_search_devops(ws_name=self.ws_name, condition=self.dev_name)
        # 验证查询结果
        assert devops_name == self.dev_name_new

    @allure.story('devops项目')
    @allure.title('模糊查询存在的devops工程')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_search_devops(self):
        # 查询前置条件中创建的devops工程
        condition = 'dev'
        devops_name = devops_steps.step_search_devops(ws_name=self.ws_name, condition=condition)
        # 验证查询结果
        assert condition in devops_name

    @allure.story('devops项目')
    @allure.title('查询不存在的devops工程')
    @allure.severity(allure.severity_level.NORMAL)
    def test_search_devops_no(self):
        # 查询前置条件中创建的devops工程
        condition = 'devops-test'
        result = devops_steps.step_search_devops(ws_name=self.ws_name, condition=condition)
        # 验证查询结果
        assert result == 0

    @allure.story('工程管理-基本信息')
    @allure.title('编辑信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_modify_devopsinfo(self):
        # 获取devops的详细信息
        re = devops_steps.step_get_devopinfo(self.ws_name, self.dev_name_new)
        data = re.json()['items'][0]
        name = '我是别名'
        data['metadata']['annotations']['kubesphere.io/alias-name'] = name
        data['metadata']['annotations']['kubesphere.io/description'] = 'wobushi'
        # 修改devops的别名和描述信息
        alias_name = devops_steps.step_modify_devinfo(self.ws_name, self.dev_name_new, data)
        # 校验修改后的别名
        assert alias_name == name

    @allure.story('工程管理-凭证')
    @allure.title('创建账户凭证')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_account_credential(self):
        url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + self.dev_name_new + '/credentials'
        name = 'test' + str(commonFunction.get_random())
        description = '我是描述信息'
        username = 'dXNlcm5hbWU='
        password = 'cGFzc3dvcmQ='

        data = {"apiVersion": "v1", "kind": "Secret",
                "metadata": {"namespace": self.dev_name_new,
                             "labels": {"app": name},
                             "annotations": {"kubesphere.io/description": description,
                                             "kubesphere.io/creator": "admin"},
                             "name": name},
                "type": "credential.devops.kubesphere.io/basic-auth",
                "data": {"username": username, "password": password
                         }
                }
        r = requests.post(url=url, headers=get_header(), data=json.dumps(data))
        # 验证新建的凭证的type
        assert r.json()['type'] == 'credential.devops.kubesphere.io/basic-auth'
        # 删除凭证
        devops_steps.step_delete_credential(self.dev_name_new, name)

    @allure.story('工程管理-凭证')
    @allure.title('创建SSH凭证')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_ssh_credential(self):
        url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + self.dev_name_new + '/credentials'
        name = 'test' + str(commonFunction.get_random())
        username = 'cXdl'
        private_key = 'YXNk'

        data = {"apiVersion": "v1", "kind": "Secret",
                "metadata": {"namespace": self.dev_name_new,
                             "labels": {"app": name}, "annotations": {"kubesphere.io/creator": "admin"}, "name": name},
                "type": "credential.devops.kubesphere.io/ssh-auth",
                "data": {"username": username, "private_key": private_key}}
        r = requests.post(url=url, headers=get_header(), data=json.dumps(data))
        # 验证新建的凭证的type
        assert r.json()['type'] == 'credential.devops.kubesphere.io/ssh-auth'
        # 删除凭证
        devops_steps.step_delete_credential(self.dev_name_new, name)

    @allure.story('工程管理-凭证')
    @allure.title('创建secret_text凭证')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_secret_text_credential(self):
        url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + self.dev_name_new + '/credentials'
        name = 'test' + str(commonFunction.get_random())
        description = '我是描述信息'
        secret = 'cXdlYXNk'
        data = {"apiVersion": "v1", "kind": "Secret",
                "metadata": {"namespace": self.dev_name_new, "labels": {"app": name},
                             "annotations": {"kubesphere.io/description": description,
                                             "kubesphere.io/creator": "admin"}, "name": name},
                "type": "credential.devops.kubesphere.io/secret-text", "data": {"secret": secret}}
        r = requests.post(url=url, headers=get_header(), data=json.dumps(data))
        # 验证新建的凭证的type
        assert r.json()['type'] == 'credential.devops.kubesphere.io/secret-text'
        # 删除凭证
        devops_steps.step_delete_credential(self.dev_name_new, name)

    @allure.story('工程管理-凭证')
    @allure.title('创建kubeconfig凭证')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_kubeconfig_credential(self):
        url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + self.dev_name_new + '/credentials'
        name = 'test' + str(commonFunction.get_random())
        description = '我是描述信息'
        data = {"apiVersion": "v1", "kind": "Secret",
                "metadata": {"namespace": self.dev_name_new, "labels": {"app": name},
                             "annotations": {"kubesphere.io/description": description,
                                             "kubesphere.io/creator": "admin"}, "name": name},
                "type": "credential.devops.kubesphere.io/kubeconfig",
                "data": {
                    "content": "YXBpVmVyc2lvbjogdjEKY2x1c3RlcnM6Ci0gY2x1c3RlcjoKICAgIGNlcnRpZmljYXRlLWF1dGhvcml0eS1kYXRhOiBMUzB0TFMxQ1JVZEpUaUJEUlZKVVNVWkpRMEZVUlMwdExTMHRDazFKU1VONVJFTkRRV0pEWjBGM1NVSkJaMGxDUVVSQlRrSm5hM0ZvYTJsSE9YY3dRa0ZSYzBaQlJFRldUVkpOZDBWUldVUldVVkZFUlhkd2NtUlhTbXdLWTIwMWJHUkhWbnBOUWpSWVJGUkplRTFFUlhkT1ZFRjVUWHBKZVU1R2IxaEVWRTE0VFVSRmQwMTZRWGxOZWtsNVRrWnZkMFpVUlZSTlFrVkhRVEZWUlFwQmVFMUxZVE5XYVZwWVNuVmFXRkpzWTNwRFEwRlRTWGRFVVZsS1MyOWFTV2gyWTA1QlVVVkNRbEZCUkdkblJWQkJSRU5EUVZGdlEyZG5SVUpCUzBaaENuaEpVRFJOZWxoNksxRjBTMUYwT0hRNWRVRjNiR05hU1VSMFVXUjBRekl2TVdoRFIyWjZjVEpSTkN0VEwwSndiamxaVG1kblZFeDJXR3hVTjBkNmVGWUtkRk56TjFsRVNsbHFaak5pYUhsNmFHWjNXazVIWmtGU2MwUk9NazVRWVVaRE1XcEhNMmxCV2tOWUwwTldWblY2WXpsV1YzbzFRMjhyUlhsR0wxUjJlQXB2Y0RaMWIzUmhXR2syYlM5emVVWk5SMVExY1RablVIaDFSSE51YWpaaFNIaFJWRkEzVDB0S1dFcGhPRGdyUVVSVGFUTkhNMDFZVEd0YWRuWnZNVlpoQ2xKcVZtVnRhRTU1TDBSNWIxbE9ORWRKUkN0eE5sZzFLemRVUVZGNWRtTTBaV3BNZUdGVk5HSk9WRzl6ZEhCb1lUZEZjWE5XVHk5ak5qTkpRWGQ1VFhRS09YVkVUVUppYTJkbGRHWlJhVUp6Y0dKVWRVeEhSbWN5UW1OamMyVnFaalJ3V0haaFZtaG5WMnhTVXpOWWIyMDVXU3R0VW5oM2EwaFRZa3BoZEdwdk5ncFNZUzlXTkVWVVVEQjZXSE0xTjJSdmFVY3dRMEYzUlVGQllVMXFUVU5GZDBSbldVUldVakJRUVZGSUwwSkJVVVJCWjB0clRVRTRSMEV4VldSRmQwVkNDaTkzVVVaTlFVMUNRV1k0ZDBSUldVcExiMXBKYUhaalRrRlJSVXhDVVVGRVoyZEZRa0ZKSzFOcWIwOTVMMlpzVGpacVdtMWxRVWg2WlhOUmFuaG5NM01LZWpjMGNtaHZTMmswYVRFeVdDOVBORzFCY0hGc1RtRTBZV1pFVERKV1N6RTVjbVpIZDNaSVYwMW1TalJaU1d0ak5VczFjMHRzU21SblJuRXlaRnBFTVFwSU56WlZkakowVTAxdGNVOXJWVlZDY1RWQkwydHhPWFZ2YUhwMGNGTTJSM3BVUTFVNEwza3hZMHRWYWpoMWJETjZhVVpvSzJKSmMzaHRWa1pxWmpaVENsWjNZbWQ2WlRZd09XTTVaelJNVkZWUVJHWmFkVGxSTWpaaWJtWXdLM3BwWVZjMGVYTlBibWhzYXl0b1RGUm1UM0ZGT1UxSVRYVnVVbTh5SzJwVFdqRUtlWEF6WTNwbVRrRklSM3BDZUU1SFZUWmtja1I0ZVhZNVUzRTFaa1ZaVEhsS05FRTFiSEUxTlVaeFdVRlBWV1F4U3pkRlJXUmtSbFpPUmtaRVdtZE9SZ3BOYkhjMFMwWlRkVGxJTkVWNVFrMVVOa3BRVUUxaE1saG1WemwyU1ROUFZIbEJLeTlxYlhOS2MyaHFaMlJpU0dVcmJUaGtiVnBRZW00elVUMEtMUzB0TFMxRlRrUWdRMFZTVkVsR1NVTkJWRVV0TFMwdExRbz0KICAgIHNlcnZlcjogaHR0cHM6Ly9rdWJlcm5ldGVzLmRlZmF1bHQuc3ZjCiAgbmFtZToga3ViZXJuZXRlcwpjb250ZXh0czoKLSBjb250ZXh0OgogICAgY2x1c3Rlcjoga3ViZXJuZXRlcwogICAgbmFtZXNwYWNlOiBkZWZhdWx0CiAgICB1c2VyOiBhZG1pbgogIG5hbWU6IGFkbWluQGt1YmVybmV0ZXMKY3VycmVudC1jb250ZXh0OiBhZG1pbkBrdWJlcm5ldGVzCmtpbmQ6IENvbmZpZwpwcmVmZXJlbmNlczoge30KdXNlcnM6Ci0gbmFtZTogYWRtaW4KICB1c2VyOgogICAgdG9rZW46IGV5SmhiR2NpT2lKU1V6STFOaUlzSW10cFpDSTZJblE1YmpoMlJqWlNhSEJpYm01QlZsQjBZVU10TWw4d04xTTVRMjFVZVd0ellqWXliMmxRU1ZWb2NVVWlmUS5leUpwYzNNaU9pSnJkV0psY201bGRHVnpMM05sY25acFkyVmhZMk52ZFc1MElpd2lhM1ZpWlhKdVpYUmxjeTVwYnk5elpYSjJhV05sWVdOamIzVnVkQzl1WVcxbGMzQmhZMlVpT2lKcmRXSmxjM0JvWlhKbExYTjVjM1JsYlNJc0ltdDFZbVZ5Ym1WMFpYTXVhVzh2YzJWeWRtbGpaV0ZqWTI5MWJuUXZjMlZqY21WMExtNWhiV1VpT2lKcmRXSmxjM0JvWlhKbExYUnZhMlZ1TFRSa2JqZHJJaXdpYTNWaVpYSnVaWFJsY3k1cGJ5OXpaWEoyYVdObFlXTmpiM1Z1ZEM5elpYSjJhV05sTFdGalkyOTFiblF1Ym1GdFpTSTZJbXQxWW1WemNHaGxjbVVpTENKcmRXSmxjbTVsZEdWekxtbHZMM05sY25acFkyVmhZMk52ZFc1MEwzTmxjblpwWTJVdFlXTmpiM1Z1ZEM1MWFXUWlPaUkzTm1JMFltWXpPQzAyTURoa0xUUmtPV1V0T1dZeU9DMHpaVE5rTm1ReFptSmtZekVpTENKemRXSWlPaUp6ZVhOMFpXMDZjMlZ5ZG1salpXRmpZMjkxYm5RNmEzVmlaWE53YUdWeVpTMXplWE4wWlcwNmEzVmlaWE53YUdWeVpTSjkuR1VGOW1GYzlkQWpLdm5MMDNOMHlLWlNtUk1IT2VWQlBhUTBpT0xBYTZ6Zl9ZbmN6TmpmTHJvU2txWVNGdU1WSDdXSTNYejQ2QWdLalBKZXA0NGtHbTVQbVE3MldHY2hwTkhuek82TGNWUkhQMV9TZDBqUDVKRDdKaktMN1ZyQ3lQb2l6b2VFMi1EM3V5QWxybXN1cGV0bnJWYVM1OVctcXkzZ1pWdGt1Z1BHQ2NBcGlMOHp0M2xsVC03dVlWN1RWcEFIUkFCTEQ2eFJSM3gxdnk5N3NUTXl4S2NoRjMxa3M3a0ZUdmJkRHZjeV93ZUtoWm5RTmRWWkllNDQwTktLYmFpRHotS3dzRks4UzZzMzZpRkowdWwyd1NTaWZCcG96aENmY2JIMGV4NTZkTFZyVFlMRWFoS2JWTEJSbUpDRGZUbTUzY2VndXExYXlNZUVuUTBkQU5nCg=="}}

        r = requests.post(url=url, headers=get_header(), data=json.dumps(data))
        # 验证新建的凭证的type
        assert r.json()['type'] == 'credential.devops.kubesphere.io/kubeconfig'
        # 删除凭证
        devops_steps.step_delete_credential(self.dev_name_new, name)

    @allure.story('工程管理-凭证')
    @allure.title('精确查询存在的凭证')
    @allure.severity(allure.severity_level.NORMAL)
    def test_search_credential(self):
        # 创建ssh凭证
        credential_name = 'ssh' + str(commonFunction.get_random())
        devops_steps.step_create_ssh_credential(self.dev_name_new, credential_name)
        # 查询之前用例创建的SSH凭证
        condition = credential_name
        result = devops_steps.step_search_credential(devops_name=self.dev_name_new, condition=condition)
        # 校验查询结果
        assert result == condition
        # 删除凭证
        devops_steps.step_delete_credential(self.dev_name_new, credential_name)

    @allure.story('工程管理-凭证')
    @allure.title('模糊查询存在的凭证')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_search_credential(self):
        # 创建ssh凭证
        credential_name = 'ssh' + str(commonFunction.get_random())
        devops_steps.step_create_ssh_credential(self.dev_name_new, credential_name)
        # 查询之前创建的凭证
        condition = credential_name
        result = devops_steps.step_search_credential(devops_name=self.dev_name_new, condition=condition)
        # 校验查询结果
        assert condition in result
        # 删除凭证
        devops_steps.step_delete_credential(self.dev_name_new, credential_name)

    @allure.story('工程管理-凭证')
    @allure.title('查询不存在的凭证')
    @allure.severity(allure.severity_level.NORMAL)
    def test_search_credential_no(self):
        # 查询之前用例创建的SSH凭证
        condition = 'test321'
        result = devops_steps.step_search_credential(devops_name=self.dev_name_new, condition=condition)
        # 校验查询结果
        assert result == 0

    @allure.story('工程管理-凭证')
    @allure.title('删除凭证')
    def test_delete_credential(self):
        credential_name = 'testdelete' + str(commonFunction.get_random())
        # 获取创建的devops工程的别名
        response = devops_steps.step_get_devopinfo(self.ws_name, self.dev_name)
        dev_name_new = response.json()['items'][0]['metadata']['name']
        # 创建凭证
        username = 'd2VueGlueGlu'      
        password = 'd2VueGluMTIzNDU2'
        devops_steps.step_create_account_credential(dev_name_new, credential_name, username, password)
        # 查询创建的凭证
        response = devops_steps.step_get_credential(dev_name_new, credential_name)
        print(response.text)
        # 获取凭证的数量
        count = response.json()['totalItems']
        # 验证凭证的数量正确
        assert count == 1
        # 删除凭证
        devops_steps.step_delete_credential(dev_name_new, credential_name)
        # 查询创建的凭证
        response = devops_steps.step_get_credential(dev_name_new, credential_name)
        # 获取凭证的数量
        count = response.json()['totalItems']
        # 验证凭证的数量正确
        assert count == 0

    @allure.story('工程管理-工程角色')
    @allure.title('查看devops工程默认的所有角色')
    @allure.title('查看devops工程默认的所有角色')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_role_all(self):
        r = devops_steps.step_get_role(self.dev_name_new, '')
        assert r.json()['totalItems'] == 3  # 验证初始的角色数量为3

    @allure.story('工程管理-工程角色')
    @allure.title('查找devops工程指定的角色')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_role_one(self):
        role_name = 'viewer'
        r = devops_steps.step_get_role(self.dev_name_new, role_name)
        assert r.json()['items'][0]['metadata']['name'] == role_name  # 验证查询的角色结果为viewer

    @allure.story('工程管理-工程角色')
    @allure.title('查找devops工程中不存在的角色')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_role_none(self):
        role_name = 'no-exist'
        r = devops_steps.step_get_role(self.dev_name_new, role_name)
        assert r.json()['totalItems'] == 0  # 验证查询到的结果为空

    @allure.story('工程管理-工程角色')
    @allure.title('模糊查找devops工程中的角色')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_role_fuzzy(self):
        url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/devops/' + self.dev_name_new + \
              '/roles?name=admi&sortBy=createTime&limit=10&annotation=kubesphere.io%2Fcreator'
        r = requests.get(url, headers=get_header())
        assert r.json()['totalItems'] == 1  # 验证查询到的结果数量为2
        # 验证查找到的角色
        assert r.json()['items'][0]['metadata']['name'] == 'admin'

    @allure.story('工程管理-工程角色')
    @allure.title('在devops工程中创建角色')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_role_create(self):
        url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + self.dev_name_new + '/roles'
        data = {"apiVersion": "rbac.authorization.k8s.io/v1",
                "kind": "Role",
                "metadata": {"namespace": self.dev_name_new,
                             "name": self.dev_role_name,
                             "annotations": {"iam.kubesphere.io/aggregation-roles": "[\"role-template-view-pipelines\","
                                                                                    "\"role-template-view-credentials\","
                                                                                    "\"role-template-view-basic\"]",
                                             "kubesphere.io/creator": "admin"}
                             },
                "rules": []
                }
        r = requests.post(url, headers=get_header(), data=json.dumps(data))
        assert r.json()['metadata']['name'] == self.dev_role_name  # 验证新建的角色名称

    @allure.story('工程管理-工程角色')
    @allure.title('在devops工程中创建角色-角色名称为空')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_role_create_name_none(self):
        url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + self.dev_name_new + '/roles'
        data = {"apiVersion": "rbac.authorization.k8s.io/v1",
                "kind": "Role",
                "metadata": {"namespace": self.dev_name_new,
                             "name": '',
                             "annotations": {"iam.kubesphere.io/aggregation-roles": "[\"role-template-view-pipelines\","
                                                                                    "\"role-template-view-credentials\","
                                                                                    "\"role-template-view-basic\"]",
                                             "kubesphere.io/creator": "admin"}
                             },
                "rules": []
                }
        r = requests.post(url, headers=get_header(), data=json.dumps(data))
        # 验证创建角色失败的异常提示信息
        assert r.text.strip() == 'Role.rbac.authorization.k8s.io "" is invalid: metadata.name: Required value: name or generateName is required'

    @pytest.mark.skip(reason='用例的执行结果应当为false。接口没有对角色的名称做限制')
    @allure.story('工程管理-工程角色')
    @allure.title('在devops工程中创建角色-名称中包含大写字母')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_role_create_name(self):
        # 获取创建的devops工程的别名
        response = devops_steps.step_get_devopinfo(self.ws_name, self.dev_name)
        dev_name_new = response.json()['items'][0]['metadata']['name']
        devops_role_name = 'Wx'
        url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + dev_name_new + '/roles'
        data = {"apiVersion": "rbac.authorization.k8s.io/v1",
                "kind": "Role",
                "metadata": {"namespace": dev_name_new,
                             "name": devops_role_name,
                             "annotations": {"iam.kubesphere.io/aggregation-roles": "[\"role-template-view-pipelines\","
                                                                                    "\"role-template-view-credentials\","
                                                                                    "\"role-template-view-basic\"]",
                                             "kubesphere.io/creator": "admin"}
                             },
                "rules": []
                }
        r = requests.post(url, headers=get_header(), data=json.dumps(data))
        print(r.text)

    @pytest.mark.skip(reason='用例的执行结果应当为false。接口没有对角色的名称做限制')
    @allure.story('工程管理-工程角色')
    @allure.title('在devops工程中创建角色-名称中包含非分隔符("-")的特殊符号')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_role_create_name1(self):
        # 获取创建的devops工程的别名
        response = devops_steps.step_get_devopinfo(self.ws_name, self.dev_name)
        dev_name_new = response.json()['items'][0]['metadata']['name']
        devops_role_name = 'W@x'
        url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + dev_name_new + '/roles'
        data = {"apiVersion": "rbac.authorization.k8s.io/v1",
                "kind": "Role",
                "metadata": {"namespace": dev_name_new,
                             "name": devops_role_name,
                             "annotations": {"iam.kubesphere.io/aggregation-roles": "[\"role-template-view-pipelines\","
                                                                                    "\"role-template-view-credentials\","
                                                                                    "\"role-template-view-basic\"]",
                                             "kubesphere.io/creator": "admin"}
                             },
                "rules": []
                }
        r = requests.post(url, headers=get_header(), data=json.dumps(data))
        print(r.text)

    @pytest.mark.skip(reason='用例的执行结果应当为false。接口没有对角色的名称做限制')
    @allure.story('工程管理-工程角色')
    @allure.title('在devops工程中创建角色-名称以分隔符("-")开头')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_role_create_name2(self):
        # 获取创建的devops工程的别名
        response = devops_steps.step_get_devopinfo(self.ws_name, self.dev_name)
        dev_name_new = response.json()['items'][0]['metadata']['name']
        devops_role_name = '-Wx'
        url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + dev_name_new + '/roles'
        data = {"apiVersion": "rbac.authorization.k8s.io/v1",
                "kind": "Role",
                "metadata": {"namespace": dev_name_new,
                             "name": devops_role_name,
                             "annotations": {"iam.kubesphere.io/aggregation-roles": "[\"role-template-view-pipelines\","
                                                                                    "\"role-template-view-credentials\","
                                                                                    "\"role-template-view-basic\"]",
                                             "kubesphere.io/creator": "admin"}
                             },
                "rules": []
                }
        r = requests.post(url, headers=get_header(), data=json.dumps(data))
        print(r.text)

    @pytest.mark.skip(reason='用例的执行结果应当为false。接口没有对角色的名称做限制')
    @allure.story('工程管理-工程角色')
    @allure.title('在devops工程中创建角色-名称以分隔符("-")结尾')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_role_create_name3(self):
        # 获取创建的devops工程的别名
        response = devops_steps.step_get_devopinfo(self.ws_name, self.dev_name)
        dev_name_new = response.json()['items'][0]['metadata']['name']
        devops_role_name = 'Wx-'
        url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + dev_name_new + '/roles'
        data = {"apiVersion": "rbac.authorization.k8s.io/v1",
                "kind": "Role",
                "metadata": {"namespace": dev_name_new,
                             "name": devops_role_name,
                             "annotations": {"iam.kubesphere.io/aggregation-roles": "[\"role-template-view-pipelines\","
                                                                                    "\"role-template-view-credentials\","
                                                                                    "\"role-template-view-basic\"]",
                                             "kubesphere.io/creator": "admin"}
                             },
                "rules": []
                }
        r = requests.post(url, headers=get_header(), data=json.dumps(data))
        print(r.text)

    @allure.story('工程管理-工程角色')
    @allure.title('在devops工程中编辑角色基本信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_role_edit_info(self):
        # 创建角色
        role_name = 'test-role' + str(commonFunction.get_random())
        devops_steps.step_create_role(self.dev_name_new, role_name)
        # 编辑角色的基本信息
        alias = '测试别名test'
        description = '测试描述test'
        r = devops_steps.step_edit_role_info(self.dev_name_new, role_name, alias, description)
        assert r.json()['metadata']['annotations']['kubesphere.io/alias-name'] == alias  # 验证修改后的别名
        assert r.json()['metadata']['annotations']['kubesphere.io/description'] == description  # 验证修改后的描述信息
        # 删除创建的角色
        devops_steps.step_delete_role(self.dev_name_new, role_name)

    @allure.story('工程管理-工程角色')
    @allure.title('在devops工程中编辑角色的权限信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_role_edit_authority(self):
        # 创建角色
        role_name = 'test-role' + str(commonFunction.get_random())
        devops_steps.step_create_role(self.dev_name_new, role_name)
        # 获取角色的resourceVersion
        resourceVersion = commonFunction.get_devops_resourceVersion(self.dev_name_new, role_name)
        # 编辑角色的权限
        authority = '["role-template-view-pipelines","role-template-view-credentials","role-template-view-basic","role-template-manage-pipelines"]'
        annotations = {"iam.kubesphere.io/aggregation-roles": authority,
                                             "kubesphere.io/alias-name": "我是别名",
                                             "kubesphere.io/creator": "admin",
                                             "kubesphere.io/description": "我是描述信息"}

        response = devops_steps.step_edit_role_authority(self.dev_name_new, role_name, annotations, resourceVersion)
        assert response.json()['metadata']['annotations']['iam.kubesphere.io/aggregation-roles'] == authority  # 验证修改后的权限信息
        # 删除创建的devops角色
        devops_steps.step_delete_role(self.dev_name_new, role_name)

    @allure.story('工程管理-工程角色')
    @allure.title('在devops工程中删除角色,并验证删除成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_role_delete(self):
        # 创建角色
        role_name = 'test-role' + str(commonFunction.get_random())
        devops_steps.step_create_role(self.dev_name_new, role_name)
        # 精确查询创建的角色
        count = devops_steps.step_get_role(self.dev_name_new, role_name).json()['totalItems']
        # 验证角色创建成功
        assert count == 1
        # 删除角色
        devops_steps.step_delete_role(self.dev_name_new, role_name)
        time.sleep(10)
        # 精确查询创建的角色
        count1 = devops_steps.step_get_role(self.dev_name_new, role_name).json()['totalItems']
        # 验证角色删除成功
        assert count1 == 0

    @allure.story('工程管理-工程成员')
    @allure.title('查看devops工程默认的所有用户')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_user_all(self):
        url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/devops/' + self.dev_name_new + '/members?sortBy=createTime&limit=10'
        r = requests.get(url, headers=get_header())
        assert r.json()['items'][0]['metadata']['name'] == 'admin'  # 验证默认的用户仅有admin

    @allure.story('工程管理-工程成员')
    @allure.title('查找devops工程指定的用户')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_user_one(self):
        user_condition = 'admin'
        url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/devops/' + self.dev_name_new + '/members?name=' + user_condition + '&sortBy=createTime&limit=10'
        r = requests.get(url, headers=get_header())
        assert r.json()['items'][0]['metadata']['name'] == 'admin'  # 验证查找的结果为admin

    @allure.story('工程管理-工程成员')
    @allure.title('模糊查找devops工程的用户')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_user_fuzzy(self):
        user_condition = 'ad'
        url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/devops/' + self.dev_name_new + '/members?name=' + user_condition + '&sortBy=createTime&limit=10'
        r = requests.get(url, headers=get_header())
        assert r.json()['items'][0]['metadata']['name'] == 'admin'  # 验证查找的结果为admin

    @allure.story('工程管理-工程成员')
    @allure.title('查找devops工程不存在的用户')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_user_none(self):
        user_condition = 'wx-ad'
        url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/devops/' + self.dev_name_new + '/members?name=' + user_condition + '&sortBy=createTime&limit=10'
        r = requests.get(url, headers=get_header())
        assert r.json()['totalItems'] == 0  # 验证查找的结果为空

    @allure.story('工程管理-工程成员')
    @allure.title('邀请用户到devops工程')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_invite_user(self):
        url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/devops/' + self.dev_name_new + '/members'
        data = [{"username": self.user_name,
                 "roleRef": "viewer"}]
        r = requests.post(url, headers=get_header(), data=json.dumps(data))
        assert r.json()[0]['username'] == self.user_name  # 验证邀请后的用户名称

    @pytest.mark.skip(reason='用例的执行结果应当为false。接口没有对不存在的用户做限制')
    @allure.story('工程管理-工程成员')
    @allure.title('邀请不存在的用户到devops工程')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_invite_none_user(self):
        # 获取创建的devops工程的别名
        response = devops_steps.step_get_devopinfo(self.ws_name, self.dev_name)
        dev_name_new = response.json()['items'][0]['metadata']['name']
        url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/devops/' + dev_name_new + '/members'
        data = [{"username": 'wxqw',
                 "roleRef": "viewer"}]
        r = requests.post(url, headers=get_header(), data=json.dumps(data))
        print(r.text)

    @allure.story('工程管理-工程成员')
    @allure.title('编辑devops工程成员的角色')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_edit_user(self):
        url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/devops/' + self.dev_name_new + '/members/' + self.user_name
        data = {"username": self.user_name,
                "roleRef": "operator"}
        r = requests.put(url, headers=get_header(), data=json.dumps(data))
        assert r.json()['roleRef'] == 'operator'  # 验证修改后的用户角色

    @allure.story('工程管理-工程成员')
    @allure.title('删除devops工程的成员')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_delete_user(self):
        url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/devops/' + self.dev_name_new + '/members/' + self.user_name
        r = requests.delete(url, headers=get_header())
        assert r.json()['message'] == 'success'  # 验证删除成功

    @allure.story('流水线')
    @allure.title('基于github创建多分支流水线, 已启用发现tag分支')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_pipeline_base_github_with_tag(self):
        credential_name = 'github' + str(commonFunction.get_random())
        pipeline_name = 'github' + str(commonFunction.get_random())
        patch = 'Jenkinsfile-online'    # 脚本路径
        # 获取创建的devops工程的别名
        response = devops_steps.step_get_devopinfo(self.ws_name, self.dev_name)
        dev_name_new = response.json()['items'][0]['metadata']['name']
        # 创建凭证
        username = 'YWRtaW4='
        password = 'Z2hwX2RsVUpBNm1wRmg3VFFRVWtLVTBkMzBNYTNZbEplUTIzUm5jNw=='
        devops_steps.step_create_account_credential(dev_name_new, credential_name, username, password)
        # 创建流水线
        devops_steps.step_create_pipeline_base_github(self.dev_name, dev_name_new, pipeline_name,
                                                      credential_name, patch, True)
        # 等待流水线分支拉取成功
        time.sleep(40)
        # 获取流水线的健康状态
        weatherScore = devops_steps.step_get_pipeline_weather(dev_name_new, pipeline_name)
        # 获取流水线的分支数量
        branch_count = devops_steps.step_get_pipeline_branch(dev_name_new, pipeline_name)
        # 验证流水线的状态和分支数量正确
        assert weatherScore == 100
        assert branch_count == 22
        # 删除创建的流水线
        devops_steps.step_delete_pipeline(dev_name_new, pipeline_name)
        # 删除凭证
        devops_steps.step_delete_credential(dev_name_new, credential_name)

    @allure.story('流水线')
    @allure.title('基于github创建多分支流水线, 已停用发现tag分支')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_pipeline_base_github_no_tag(self):
        credential_name = 'github' + str(commonFunction.get_random())
        pipeline_name = 'github' + str(commonFunction.get_random())
        patch = 'Jenkinsfile-online'  # 脚本路径
        # 获取创建的devops工程的别名
        response = devops_steps.step_get_devopinfo(self.ws_name, self.dev_name)
        dev_name_new = response.json()['items'][0]['metadata']['name']
        # 创建凭证
        username = 'YWRtaW4='
        password = 'Z2hwX2RsVUpBNm1wRmg3VFFRVWtLVTBkMzBNYTNZbEplUTIzUm5jNw=='
        devops_steps.step_create_account_credential(dev_name_new, credential_name, username, password)
        # 创建流水线
        devops_steps.step_create_pipeline_base_github(self.dev_name, dev_name_new, pipeline_name,
                                                      credential_name, patch, False)
        # 等待流水线分支拉取成功
        time.sleep(30)
        # 获取流水线的健康状态
        weatherScore = devops_steps.step_get_pipeline_weather(dev_name_new, pipeline_name)
        # 获取流水线的分支数量
        branch_count = devops_steps.step_get_pipeline_branch(dev_name_new, pipeline_name)
        # 验证流水线的状态和分支数量正确
        assert weatherScore == 100
        assert branch_count == 12
        # 删除创建的流水线
        devops_steps.step_delete_pipeline(dev_name_new, pipeline_name)
        # 删除凭证
        devops_steps.step_delete_credential(dev_name_new, credential_name)

    @allure.story('流水线')
    @allure.title('基于gitlab公用仓库创建多分支流水线')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_pipeline_base_gitlab_public(self):
        pipeline_name = 'gitlab' + str(commonFunction.get_random())
        # 获取创建的devops工程的别名
        response = devops_steps.step_get_devopinfo(self.ws_name, self.dev_name)
        dev_name_new = response.json()['items'][0]['metadata']['name']
        # 基于gitlab创建流水线
        devops_steps.step_create_pipeline_base_gitlab(self.dev_name, dev_name_new, pipeline_name, False)
        # 等待流水线分支拉取成功
        time.sleep(60)
        # 获取流水线的健康状态
        weatherScore = devops_steps.step_get_pipeline_weather(dev_name_new, pipeline_name)
        # 获取流水线的分支数量
        branch_count = devops_steps.step_get_pipeline_branch(dev_name_new, pipeline_name)
        # 验证流水线的状态和分支数量正确
        assert weatherScore == 100
        assert branch_count == 1
        # 删除创建的流水线
        devops_steps.step_delete_pipeline(dev_name_new, pipeline_name)

    @allure.story('流水线')
    @allure.title('maven流水线实例')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_maven(self):
        credential_name = 'dockerhub-wx'
        credential_name1 = 'wx'
        pipeline_name = 'gitlab' + str(commonFunction.get_random())
        # 获取创建的devops工程的别名
        response = devops_steps.step_get_devopinfo(self.ws_name, self.dev_name)
        dev_name_new = response.json()['items'][0]['metadata']['name']
        # 创建用户名和密码凭证
        username = 'd2VueGlueGlu'
        password = 'd2VueGluMTIzNDU2'
        devops_steps.step_create_account_credential(dev_name_new, credential_name, username, password)
        # 创建kubeconfig类型凭证
        kubeconfig = toolbox_steps.step_get_kubeconfig()
        content = base64.b64encode(kubeconfig.encode("utf-8")).decode("utf-8")  # 将kubeconfig编码成base64,然后转换成str类型
        devops_steps.step_create_kubeconfig_credential(dev_name_new, credential_name1, content)
        # 使用图形化方式创建流水线并获取resourceVersion
        r = devops_steps.step_create_pipeline(self.dev_name, dev_name_new, pipeline_name)
        resourceVersion = r.json()['metadata']['resourceVersion']
        # 查看流水线详情并获取spechash和uid
        r1 = devops_steps.step_get_pipeline(dev_name_new, pipeline_name)
        spechash = r1.json()['items'][0]['metadata']['annotations']["pipeline.devops.kubesphere.io/spechash"]
        uid = r1.json()['items'][0]['metadata']['uid']
        # 编辑jenkinsfile
        # 从jenkinsfile文件中读取jenkinsfile信息
        with open('../data/jenkinsfile') as file_object:
            contents = file_object.read()
        # 将jenkinsfile编码为encodeURIComponent
        jenkinsfile = parse.quote(contents)
        # 1、checkScriptCompile
        devops_steps.step_edit_jenkinsfile_checkScriptCompile(dev_name_new, pipeline_name, jenkinsfile)
        # 2、put
        devops_steps.step_edit_jenkinsfile_put(dev_name_new, uid, pipeline_name, resourceVersion, contents, spechash)
        # 3、tojson
        devops_steps.step_edit_jenkinsfile_tojson(jenkinsfile)

        # 创建流水线编译所需的ns
        project_steps.step_create_project(self.ws_name, project_name='kubesphere-sample-dev')

        # 运行pipeline
        devops_steps.step_run_pipeline(dev_name_new, pipeline_name)











if __name__ == "__main__":
    pytest.main(['-s', 'testDevops.py'])  # -s参数是为了显示用例的打印信息。 -q参数只显示结果，不显示过程
