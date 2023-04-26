# -- coding: utf-8 --
import pytest
import allure
import sys

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

import time
from common import commonFunction
from step import devops_steps, workspace_steps
from step import cluster_steps, project_steps


@allure.feature('DevOps')
@pytest.mark.skipif(commonFunction.get_component_health_of_cluster('kubesphere-devops-system') is False,
                    reason='集群devops功能未准备好')
@pytest.mark.skipif(commonFunction.get_components_status_of_cluster('devops') is False, reason='集群未开启devops功能')
@pytest.mark.skipif(commonFunction.check_multi_cluster() is True, reason='多集群环境下不执行')
class TestDevOps(object):
    if commonFunction.check_multi_cluster() is True:
        # 如果为单集群环境，则不会collect该class的所有用例。 __test__ = False
        __test__ = False
    else:
        __test__ = True
    ws_name = 'ws-dev' + str(commonFunction.get_random())
    dev_name = 'test-dev' + str(commonFunction.get_random())
    dev_name_new = ''

    # 所有用例执行之前执行该方法
    def setup_class(self):
        workspace_steps.step_create_workspace(self.ws_name)  # 创建一个企业空间
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

    @allure.story('devops项目')
    @allure.title('创建devops工程,然后将其删除')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_devops(self, create_ws):
        devops_name = 'test-devops' + str(commonFunction.get_random())
        # 创建devops工程
        devops_steps.step_create_devops(create_ws, devops_name)
        # 查询devops工程
        response = devops_steps.step_get_devopinfo(create_ws, devops_name)
        # 获取devops工程的别名
        devops_name_new = response.json()['items'][0]['metadata']['name']
        # 获取devops的数量
        count = response.json()['totalItems']
        # 验证数量正确
        with pytest.assume:
            assert count == 1
        # 删除创建的devops工程
        devops_steps.step_delete_devops(create_ws, devops_name_new)
        time.sleep(5)
        # 查询devops工程
        re = devops_steps.step_get_devopinfo(create_ws, devops_name)
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
    def test_modify_devopsinfo(self, create_ws, create_devops):
        # 获取devops的详细信息
        re = devops_steps.step_get_devopinfo(create_ws, create_devops)
        data = re.json()['items'][0]
        name = '我是别名'
        data['metadata']['annotations']['kubesphere.io/alias-name'] = name
        data['metadata']['annotations']['kubesphere.io/description'] = 'wobushi'
        # 修改devops的别名和描述信息
        alias_name = devops_steps.step_modify_devinfo(create_ws, create_devops, data)
        # 校验修改后的别名
        assert alias_name == name

    @allure.story('工程管理-凭证')
    @allure.title('创建账户凭证')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_account_credential(self, create_devops):
        name = 'test' + str(commonFunction.get_random())
        username = 'dXNlcm5hbWU='
        password = 'cGFzc3dvcmQ='
        credential_type = 'basic-auth'
        data = {"username": username, "password": password}
        # 创建凭证
        response = devops_steps.step_create_credential(create_devops, name, credential_type, data)
        # 验证新建的凭证的type
        with pytest.assume:
            assert response.json()['type'] == 'credential.devops.kubesphere.io/' + credential_type
        # 删除凭证
        devops_steps.step_delete_credential(create_devops, name)

    @allure.story('工程管理-凭证')
    @allure.title('创建SSH凭证')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_ssh_credential(self, create_devops):
        name = 'test' + str(commonFunction.get_random())
        username = 'cXdl'
        private_key = 'YXNk'
        credential_type = 'ssh-auth'
        data = {"username": username, "private_key": private_key}
        # 创建凭证
        response = devops_steps.step_create_credential(create_devops, name, credential_type, data)
        # 验证新建的凭证的type
        with pytest.assume:
            assert response.json()['type'] == 'credential.devops.kubesphere.io/' + credential_type
        # 删除凭证
        devops_steps.step_delete_credential(create_devops, name)

    @allure.story('工程管理-凭证')
    @allure.title('创建secret_text凭证')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_secret_text_credential(self, create_devops):
        name = 'test' + str(commonFunction.get_random())
        secret = 'cXdlYXNk'
        credential_type = 'secret-text'
        data = {"secret": secret}
        # 创建凭证
        response = devops_steps.step_create_credential(create_devops, name, credential_type, data)
        # 验证新建的凭证的type
        with pytest.assume:
            assert response.json()['type'] == 'credential.devops.kubesphere.io/' + credential_type
        # 删除凭证
        devops_steps.step_delete_credential(create_devops, name)

    @allure.story('工程管理-凭证')
    @allure.title('创建kubeconfig凭证')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_kube_config_credential(self, create_devops):
        name = 'test' + str(commonFunction.get_random())
        credential_type = 'kubeconfig'
        data = {
            "content": "YXBpVmVyc2lvbjogdjEKY2x1c3RlcnM6Ci0gY2x1c3RlcjoKICAgIGNlcnRpZmljYXRlLWF1dGhvcml0eS1kYXRhOiBMUzB0TFMxQ1JVZEpUaUJEUlZKVVNVWkpRMEZVUlMwdExTMHRDazFKU1VONVJFTkRRV0pEWjBGM1NVSkJaMGxDUVVSQlRrSm5hM0ZvYTJsSE9YY3dRa0ZSYzBaQlJFRldUVkpOZDBWUldVUldVVkZFUlhkd2NtUlhTbXdLWTIwMWJHUkhWbnBOUWpSWVJGUkplRTFFUlhkT1ZFRjVUWHBKZVU1R2IxaEVWRTE0VFVSRmQwMTZRWGxOZWtsNVRrWnZkMFpVUlZSTlFrVkhRVEZWUlFwQmVFMUxZVE5XYVZwWVNuVmFXRkpzWTNwRFEwRlRTWGRFVVZsS1MyOWFTV2gyWTA1QlVVVkNRbEZCUkdkblJWQkJSRU5EUVZGdlEyZG5SVUpCUzBaaENuaEpVRFJOZWxoNksxRjBTMUYwT0hRNWRVRjNiR05hU1VSMFVXUjBRekl2TVdoRFIyWjZjVEpSTkN0VEwwSndiamxaVG1kblZFeDJXR3hVTjBkNmVGWUtkRk56TjFsRVNsbHFaak5pYUhsNmFHWjNXazVIWmtGU2MwUk9NazVRWVVaRE1XcEhNMmxCV2tOWUwwTldWblY2WXpsV1YzbzFRMjhyUlhsR0wxUjJlQXB2Y0RaMWIzUmhXR2syYlM5emVVWk5SMVExY1RablVIaDFSSE51YWpaaFNIaFJWRkEzVDB0S1dFcGhPRGdyUVVSVGFUTkhNMDFZVEd0YWRuWnZNVlpoQ2xKcVZtVnRhRTU1TDBSNWIxbE9ORWRKUkN0eE5sZzFLemRVUVZGNWRtTTBaV3BNZUdGVk5HSk9WRzl6ZEhCb1lUZEZjWE5XVHk5ak5qTkpRWGQ1VFhRS09YVkVUVUppYTJkbGRHWlJhVUp6Y0dKVWRVeEhSbWN5UW1OamMyVnFaalJ3V0haaFZtaG5WMnhTVXpOWWIyMDVXU3R0VW5oM2EwaFRZa3BoZEdwdk5ncFNZUzlXTkVWVVVEQjZXSE0xTjJSdmFVY3dRMEYzUlVGQllVMXFUVU5GZDBSbldVUldVakJRUVZGSUwwSkJVVVJCWjB0clRVRTRSMEV4VldSRmQwVkNDaTkzVVVaTlFVMUNRV1k0ZDBSUldVcExiMXBKYUhaalRrRlJSVXhDVVVGRVoyZEZRa0ZKSzFOcWIwOTVMMlpzVGpacVdtMWxRVWg2WlhOUmFuaG5NM01LZWpjMGNtaHZTMmswYVRFeVdDOVBORzFCY0hGc1RtRTBZV1pFVERKV1N6RTVjbVpIZDNaSVYwMW1TalJaU1d0ak5VczFjMHRzU21SblJuRXlaRnBFTVFwSU56WlZkakowVTAxdGNVOXJWVlZDY1RWQkwydHhPWFZ2YUhwMGNGTTJSM3BVUTFVNEwza3hZMHRWYWpoMWJETjZhVVpvSzJKSmMzaHRWa1pxWmpaVENsWjNZbWQ2WlRZd09XTTVaelJNVkZWUVJHWmFkVGxSTWpaaWJtWXdLM3BwWVZjMGVYTlBibWhzYXl0b1RGUm1UM0ZGT1UxSVRYVnVVbTh5SzJwVFdqRUtlWEF6WTNwbVRrRklSM3BDZUU1SFZUWmtja1I0ZVhZNVUzRTFaa1ZaVEhsS05FRTFiSEUxTlVaeFdVRlBWV1F4U3pkRlJXUmtSbFpPUmtaRVdtZE9SZ3BOYkhjMFMwWlRkVGxJTkVWNVFrMVVOa3BRVUUxaE1saG1WemwyU1ROUFZIbEJLeTlxYlhOS2MyaHFaMlJpU0dVcmJUaGtiVnBRZW00elVUMEtMUzB0TFMxRlRrUWdRMFZTVkVsR1NVTkJWRVV0TFMwdExRbz0KICAgIHNlcnZlcjogaHR0cHM6Ly9rdWJlcm5ldGVzLmRlZmF1bHQuc3ZjCiAgbmFtZToga3ViZXJuZXRlcwpjb250ZXh0czoKLSBjb250ZXh0OgogICAgY2x1c3Rlcjoga3ViZXJuZXRlcwogICAgbmFtZXNwYWNlOiBkZWZhdWx0CiAgICB1c2VyOiBhZG1pbgogIG5hbWU6IGFkbWluQGt1YmVybmV0ZXMKY3VycmVudC1jb250ZXh0OiBhZG1pbkBrdWJlcm5ldGVzCmtpbmQ6IENvbmZpZwpwcmVmZXJlbmNlczoge30KdXNlcnM6Ci0gbmFtZTogYWRtaW4KICB1c2VyOgogICAgdG9rZW46IGV5SmhiR2NpT2lKU1V6STFOaUlzSW10cFpDSTZJblE1YmpoMlJqWlNhSEJpYm01QlZsQjBZVU10TWw4d04xTTVRMjFVZVd0ellqWXliMmxRU1ZWb2NVVWlmUS5leUpwYzNNaU9pSnJkV0psY201bGRHVnpMM05sY25acFkyVmhZMk52ZFc1MElpd2lhM1ZpWlhKdVpYUmxjeTVwYnk5elpYSjJhV05sWVdOamIzVnVkQzl1WVcxbGMzQmhZMlVpT2lKcmRXSmxjM0JvWlhKbExYTjVjM1JsYlNJc0ltdDFZbVZ5Ym1WMFpYTXVhVzh2YzJWeWRtbGpaV0ZqWTI5MWJuUXZjMlZqY21WMExtNWhiV1VpT2lKcmRXSmxjM0JvWlhKbExYUnZhMlZ1TFRSa2JqZHJJaXdpYTNWaVpYSnVaWFJsY3k1cGJ5OXpaWEoyYVdObFlXTmpiM1Z1ZEM5elpYSjJhV05sTFdGalkyOTFiblF1Ym1GdFpTSTZJbXQxWW1WemNHaGxjbVVpTENKcmRXSmxjbTVsZEdWekxtbHZMM05sY25acFkyVmhZMk52ZFc1MEwzTmxjblpwWTJVdFlXTmpiM1Z1ZEM1MWFXUWlPaUkzTm1JMFltWXpPQzAyTURoa0xUUmtPV1V0T1dZeU9DMHpaVE5rTm1ReFptSmtZekVpTENKemRXSWlPaUp6ZVhOMFpXMDZjMlZ5ZG1salpXRmpZMjkxYm5RNmEzVmlaWE53YUdWeVpTMXplWE4wWlcwNmEzVmlaWE53YUdWeVpTSjkuR1VGOW1GYzlkQWpLdm5MMDNOMHlLWlNtUk1IT2VWQlBhUTBpT0xBYTZ6Zl9ZbmN6TmpmTHJvU2txWVNGdU1WSDdXSTNYejQ2QWdLalBKZXA0NGtHbTVQbVE3MldHY2hwTkhuek82TGNWUkhQMV9TZDBqUDVKRDdKaktMN1ZyQ3lQb2l6b2VFMi1EM3V5QWxybXN1cGV0bnJWYVM1OVctcXkzZ1pWdGt1Z1BHQ2NBcGlMOHp0M2xsVC03dVlWN1RWcEFIUkFCTEQ2eFJSM3gxdnk5N3NUTXl4S2NoRjMxa3M3a0ZUdmJkRHZjeV93ZUtoWm5RTmRWWkllNDQwTktLYmFpRHotS3dzRks4UzZzMzZpRkowdWwyd1NTaWZCcG96aENmY2JIMGV4NTZkTFZyVFlMRWFoS2JWTEJSbUpDRGZUbTUzY2VndXExYXlNZUVuUTBkQU5nCg=="}
        # 创建凭证
        response = devops_steps.step_create_credential(create_devops, name, credential_type, data)
        # 验证新建的凭证的type
        with pytest.assume:
            assert response.json()['type'] == 'credential.devops.kubesphere.io/' + credential_type
        # 删除凭证
        devops_steps.step_delete_credential(create_devops, name)

    @allure.story('工程管理-凭证')
    @allure.title('精确查询存在的凭证')
    @allure.severity(allure.severity_level.NORMAL)
    def test_search_credential(self, create_devops):
        # 创建ssh凭证
        credential_name = 'ssh' + str(commonFunction.get_random())
        devops_steps.step_create_ssh_credential(create_devops, credential_name)
        # 查询之前用例创建的SSH凭证
        condition = credential_name
        result = devops_steps.step_search_credential(devops_name=create_devops, condition=condition)
        # 校验查询结果
        with pytest.assume:
            assert result == condition
        # 删除凭证
        devops_steps.step_delete_credential(create_devops, credential_name)

    @allure.story('工程管理-凭证')
    @allure.title('模糊查询存在的凭证')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_search_credential(self, create_devops):
        # 创建ssh凭证
        credential_name = 'ssh' + str(commonFunction.get_random())
        devops_steps.step_create_ssh_credential(create_devops, credential_name)
        # 查询之前创建的凭证
        condition = credential_name
        result = devops_steps.step_search_credential(devops_name=create_devops, condition=condition)
        # 校验查询结果
        with pytest.assume:
            assert condition in result
        # 删除凭证
        devops_steps.step_delete_credential(create_devops, credential_name)

    @allure.story('工程管理-凭证')
    @allure.title('查询不存在的凭证')
    @allure.severity(allure.severity_level.NORMAL)
    def test_search_credential_no(self, create_devops):
        # 查询之前用例创建的SSH凭证
        condition = 'test321'
        result = devops_steps.step_search_credential(devops_name=create_devops, condition=condition)
        # 校验查询结果
        assert result == 0

    @allure.story('工程管理-凭证')
    @allure.title('删除凭证')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_credential(self, create_ws, create_devops):
        credential_name = 'testdelete' + str(commonFunction.get_random())
        # 获取创建的devops工程的别名
        response = devops_steps.step_get_devopinfo(create_ws, create_devops)
        dev_name_new = response.json()['items'][0]['metadata']['name']
        # 创建凭证
        username = 'd2VueGlueGlu'
        password = 'd2VueGluMTIzNDU2'
        devops_steps.step_create_account_credential(dev_name_new, credential_name, username, password)
        # 查询创建的凭证
        response = devops_steps.step_get_credential(dev_name_new, credential_name)
        # 获取凭证的数量
        count = response.json()['totalItems']
        # 验证凭证的数量正确
        with pytest.assume:
            assert count == 1
        # 删除凭证
        devops_steps.step_delete_credential(dev_name_new, credential_name)
        time.sleep(3)
        # 查询创建的凭证
        response = devops_steps.step_get_credential(dev_name_new, credential_name)
        # 获取凭证的数量
        count_new = response.json()['totalItems']
        # 验证凭证的数量正确
        assert count_new == 0

    @allure.story('工程管理-工程角色')
    @allure.title('查看devops工程默认的所有角色')
    @allure.severity(allure.severity_level.NORMAL)
    def test_devops_role_all(self, create_devops):
        response = devops_steps.step_get_role(create_devops, '')
        assert response.json()['totalItems'] == 3  # 验证初始的角色数量为3

    @allure.story('工程管理-工程角色')
    @allure.title('查找devops工程指定的角色')
    @allure.severity(allure.severity_level.NORMAL)
    def test_devops_role_one(self, create_devops):
        role_name = 'viewer'
        r = devops_steps.step_get_role(create_devops, role_name)
        assert r.json()['items'][0]['metadata']['name'] == role_name  # 验证查询的角色结果为viewer

    @allure.story('工程管理-工程角色')
    @allure.title('查找devops工程中不存在的角色')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_role_none(self, create_devops):
        role_name = 'no-exist'
        r = devops_steps.step_get_role(create_devops, role_name)
        assert r.json()['totalItems'] == 0  # 验证查询到的结果为空

    @allure.story('工程管理-工程角色')
    @allure.title('模糊查找devops工程中的角色')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_role_fuzzy(self, create_devops):
        response = devops_steps.step_get_role(create_devops, 'adm')
        with pytest.assume:
            assert response.json()['totalItems'] == 1  # 验证查询到的结果数量为2
        # 验证查找到的角色
        assert response.json()['items'][0]['metadata']['name'] == 'admin'

    @allure.story('工程管理-工程角色')
    @allure.title('在devops工程中创建角色')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_role_create(self, create_devops):
        # 创建角色
        role_name = 'test-role' + str(commonFunction.get_random())
        response = devops_steps.step_create_role(create_devops, role_name)
        with pytest.assume:
            assert response.json()['metadata']['name'] == role_name  # 验证新建的角色名称
        # 删除角色
        devops_steps.step_delete_role(create_devops, role_name)

    @allure.story('工程管理-工程角色')
    @allure.title('在devops工程中创建角色-角色名称为空')
    @allure.severity(allure.severity_level.NORMAL)
    def test_devops_role_create_name_none(self, create_devops):
        # 创建角色
        role_name = ''
        response = devops_steps.step_create_role(create_devops, role_name)
        # 验证创建角色失败的异常提示信息
        assert response.text.strip() == 'Role.rbac.authorization.k8s.io "" is invalid: metadata.name: Required value: name or generateName is required'

    @allure.story('工程管理-工程角色')
    @allure.title('在devops工程中编辑角色基本信息')
    @allure.severity(allure.severity_level.NORMAL)
    def test_devops_role_edit_info(self, create_devops):
        # 创建角色
        role_name = 'test-role' + str(commonFunction.get_random())
        devops_steps.step_create_role(create_devops, role_name)
        # 编辑角色的基本信息
        alias = '测试别名test'
        description = '测试描述test'
        r = devops_steps.step_edit_role_info(create_devops, role_name, alias, description)
        with pytest.assume:
            assert r.json()['metadata']['annotations']['kubesphere.io/alias-name'] == alias  # 验证修改后的别名
        with pytest.assume:
            assert r.json()['metadata']['annotations']['kubesphere.io/description'] == description  # 验证修改后的描述信息
        # 删除创建的角色
        devops_steps.step_delete_role(create_devops, role_name)

    @allure.story('工程管理-工程角色')
    @allure.title('在devops工程中编辑角色的权限信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_role_edit_authority(self, create_devops):
        # 创建角色
        role_name = 'test-role' + str(commonFunction.get_random())
        response = devops_steps.step_create_role(create_devops, role_name)
        # 获取角色的resourceVersion
        resource_version = response.json()['metadata']['resourceVersion']
        # 编辑角色的权限
        authority = '["role-template-view-pipelines","role-template-view-credentials","role-template-view-basic"]'
        annotations = {"iam.kubesphere.io/aggregation-roles": authority,
                       "kubesphere.io/alias-name": "",
                       "kubesphere.io/creator": "admin",
                       "kubesphere.io/description": ""}

        response = devops_steps.step_edit_role_authority(create_devops, role_name, annotations, resource_version)
        # 验证修改后的权限信息
        with pytest.assume:
            assert response.json()['metadata']['annotations']['iam.kubesphere.io/aggregation-roles'] == authority
        # 删除创建的devops角色
        devops_steps.step_delete_role(create_devops, role_name)

    @allure.story('工程管理-工程角色')
    @allure.title('在devops工程中删除角色,并验证删除成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_role_delete(self, create_devops):
        # 创建角色
        role_name = 'test-role' + str(commonFunction.get_random())
        devops_steps.step_create_role(create_devops, role_name)
        # 精确查询创建的角色
        count = devops_steps.step_get_role(create_devops, role_name).json()['totalItems']
        # 验证角色创建成功
        with pytest.assume:
            assert count == 1
        # 删除角色
        devops_steps.step_delete_role(create_devops, role_name)
        time.sleep(10)
        # 精确查询创建的角色
        count1 = devops_steps.step_get_role(create_devops, role_name).json()['totalItems']
        # 验证角色删除成功
        assert count1 == 0

    @allure.story('工程管理-工程成员')
    @allure.title('查看devops工程默认的所有用户')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_user_all(self, create_devops):
        # 查询成员
        response = devops_steps.step_get_member(create_devops, '')
        assert response.json()['items'][0]['metadata']['name'] == 'admin'  # 验证默认的用户仅有admin

    @allure.story('工程管理-工程成员')
    @allure.title('查找devops工程指定的用户')
    @allure.severity(allure.severity_level.NORMAL)
    def test_devops_user_one(self, create_devops):
        user_condition = 'admin'
        # 查询成员
        response = devops_steps.step_get_member(create_devops, user_condition)
        assert response.json()['items'][0]['metadata']['name'] == 'admin'  # 验证查找的结果为admin

    @allure.story('工程管理-工程成员')
    @allure.title('模糊查找devops工程的用户')
    @allure.severity(allure.severity_level.NORMAL)
    def test_devops_user_fuzzy(self, create_devops):
        user_condition = 'ad'
        # 查询成员
        response = devops_steps.step_get_member(create_devops, user_condition)
        assert response.json()['items'][0]['metadata']['name'] == 'admin'  # 验证查找的结果为admin

    @allure.story('工程管理-工程成员')
    @allure.title('查找devops工程不存在的用户')
    @allure.severity(allure.severity_level.NORMAL)
    def test_devops_user_none(self, create_devops):
        user_condition = 'wx-ad'
        # 查询成员
        response = devops_steps.step_get_member(create_devops, user_condition)
        assert response.json()['totalItems'] == 0  # 验证查找的结果为空

    @allure.story('工程管理-工程成员')
    @allure.title('邀请用户到devops工程')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_invite_user(self, create_user, create_ws, create_devops):
        role = 'viewer'
        commonFunction.ws_invite_user(create_ws, create_user, create_ws + '-viewer')  # 将创建的用户邀请到企业空间
        # 将用户邀请到devops项目
        devops_steps.step_invite_member(create_devops, create_user, role)
        response = devops_steps.step_invite_member(create_devops, create_user, role)
        assert response.json()[0]['username'] == create_user  # 验证邀请后的用户名称

    @allure.story('工程管理-工程成员')
    @allure.title('编辑devops工程成员的角色')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_edit_user(self, create_user, create_ws, create_devops):
        role_old = 'operator'
        role_new = 'viewer'
        commonFunction.ws_invite_user(create_ws, create_user, create_ws + '-viewer')  # 将创建的用户邀请到企业空间
        # 将用户邀请到devops项目
        devops_steps.step_invite_member(create_devops, create_user, role_old)
        response = devops_steps.step_edit_member(create_devops, create_user, role_new)
        assert response.json()['roleRef'] == role_new  # 验证修改后的用户角色

    @allure.story('工程管理-工程成员')
    @allure.title('删除devops工程的成员')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_devops_delete_user(self, create_user, create_ws, create_devops):
        role = 'operator'
        commonFunction.ws_invite_user(create_ws, create_user, create_ws + '-viewer')  # 将创建的用户邀请到企业空间
        # 将用户邀请到devops项目
        devops_steps.step_invite_member(create_devops, create_user, role)
        response = devops_steps.step_remove_member(create_devops, create_user)
        assert response.json()['message'] == 'success'  # 验证删除成功

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
        weather_score = 0
        branch_count = 0
        i = 0
        while i < 180:
            try:
                # 查看流水线详情
                r = devops_steps.step_get_pipeline(dev_name_new, pipeline_name)
                # 获取流水线的 jenkins-metadata
                jenkins_metadata = r.json()['items'][0]['metadata']['annotations']['pipeline.devops.kubesphere.io/jenkins-metadata']
                # 获取流水线的健康状态
                weather_score = eval(jenkins_metadata)['weatherScore']  # jenkins_metadata是str类型，使用eval将其转化为dict
                # 获取流水线的分支数量
                branch_count = eval(jenkins_metadata)['totalNumberOfBranches']  # jenkins_metadata是str类型，使用eval将其转化为dict
                if jenkins_metadata:
                    break
            except Exception as e:
                print(e)
                time.sleep(5)
                i += 5
        # 验证流水线的状态和分支数量正确
        with pytest.assume:
            assert weather_score == 100
        with pytest.assume:
            assert branch_count == 1
        # 删除创建的流水线
        devops_steps.step_delete_pipeline(dev_name_new, pipeline_name)

    @allure.story('代码仓库')
    @allure.title('基于git导入代码仓库')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_import_code_rep_by_git(self, create_devops):
        # 创建代码仓库
        name = 'test-git' + str(commonFunction.get_random())
        provider = 'git'
        url = 'https://gitee.com/linuxsuren/demo-go-http'
        devops_steps.step_import_code_repository(create_devops, name, provider, url)
        # 查询代码仓库
        response = devops_steps.step_get_code_repository(create_devops, name)
        # 获取仓库地址
        url_actual = response.json()['items'][0]['spec']['url']
        # 验证查询结果
        with pytest.assume:
            assert url == url_actual
        # 删除代码仓库
        devops_steps.step_delete_code_repository(create_devops, name)

    @allure.story('代码仓库')
    @allure.title('编辑代码仓库')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_edit_rep(self, create_devops):
        # 创建代码仓库
        name = 'test-git' + str(commonFunction.get_random())
        provider = 'git'
        url = 'https://github.com/wenxin-01/open-podcasts'
        devops_steps.step_import_code_repository(create_devops, name, provider, url)
        # 编辑代码仓库
        annotations = {"kubesphere.io/creator": "admin", "kubesphere.io/alias-name": "bieming",
                       "kubesphere.io/description": "miaoshu "}
        url_new = 'https://gitee.com/linuxsuren/demo-go-http/tree'
        devops_steps.step_edit_code_repository(create_devops, name, provider, annotations, url_new)
        # 查询代码仓库
        response = devops_steps.step_get_code_repository(create_devops, name)
        # 获取仓库地址
        url_actual = response.json()['items'][0]['spec']['url']
        # 验证查询结果
        with pytest.assume:
            assert url_new == url_actual
        # 删除代码仓库
        devops_steps.step_delete_code_repository(create_devops, name)

    @allure.story('代码仓库')
    @allure.title('删除代码仓库')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_rep(self, create_devops):
        # 创建代码仓库
        name = 'test-git' + str(commonFunction.get_random())
        provider = 'git'
        url = 'https://gitee.com/linuxsuren/demo-go-http'
        devops_steps.step_import_code_repository(create_devops, name, provider, url)
        # 模糊查询代码仓库
        response = devops_steps.step_get_code_repository(create_devops, name[:-1])
        # 获取仓库地址
        url_actual = response.json()['items'][0]['spec']['url']
        # 验证查询结果
        with pytest.assume:
            assert url == url_actual
        # 删除代码仓库
        devops_steps.step_delete_code_repository(create_devops, name)
        time.sleep(2)
        # 查询代码仓库
        re = devops_steps.step_get_code_repository(create_devops, name)
        # 验证仓库数量为0
        assert re.json()['totalItems'] == 0

    @allure.story('持续部署')
    @allure.title('创建持续部署任务')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_cd(self, create_devops, create_code_repository):
        # 创建cd任务
        cd_name = 'test-cd' + str(commonFunction.get_random())
        annotations = {"kubesphere.io/alias-name": "bieming", "kubesphere.io/description": "miaoshu",
                       "kubesphere.io/creator": "admin"}
        ns = 'test-pro' + str(commonFunction.get_random())
        path = 'manifest'
        devops_steps.step_create_cd(create_devops, cd_name, annotations, ns, create_code_repository, path)
        # 查看cd任务创建的资源
        i = 0
        count = 0
        while i < 60:
            response = cluster_steps.step_get_project_workload_by_type(ns, 'deployments')
            count = response.json()['totalItems']
            # 验证数量为1
            if count == 1:
                break
            time.sleep(10)
            i += 10
        with pytest.assume:
            assert count == 1
        # 删除cd任务并删除创建的资源
        devops_steps.step_delete_cd(create_devops, cd_name, 'true')
        time.sleep(5)
        # 删除创建的项目
        project_steps.step_delete_project_by_name(ns)

    @allure.story('持续部署')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('delete_resource, title',
                             [
                                 ('true', '删除持续部署任务,并删除创建的资源'),
                                 ('false', '删除持续部署任务,不删除创建的资源')
                             ])
    def test_delete_cd(self, create_devops, create_code_repository, delete_resource, title):
        # 创建cd任务
        cd_name = 'test-cd' + str(commonFunction.get_random())
        annotations = {"kubesphere.io/alias-name": "", "kubesphere.io/description": "", "kubesphere.io/creator": "admin"}
        ns = 'test-pro' + str(commonFunction.get_random())
        path = 'manifest'
        devops_steps.step_create_cd(create_devops, cd_name, annotations, ns, create_code_repository, path)
        # 查看cd任务创建的资源
        i = 0
        while i < 180:
            response = cluster_steps.step_get_project_workload_by_type(ns, 'deployments')
            count = response.json()['totalItems']
            # 数量不为0 表示资源创建成功
            if count != 0:
                break
            time.sleep(10)
            i += 10
        if delete_resource == 'true':
            # 删除cd任务并删除创建的资源
            devops_steps.step_delete_cd(create_devops, cd_name, 'true')
            # 等待资源删除成功
            count_deploy = 0
            i = 0
            while i < 180:
                # 查询被删除的资源并获取查询结果
                r = cluster_steps.step_get_project_workload_by_type(ns, 'deployments')
                count_deploy = r.json()['totalItems']
                if count_deploy > 0:
                    time.sleep(1)
                    i += 1
                else:
                    break
            # 验证资源删除成功
            with pytest.assume:
                assert count_deploy == 0
            # 删除项目
            project_steps.step_delete_project_by_name(ns)
        elif delete_resource == 'false':
            # 删除cd任务但不删除创建的资源
            devops_steps.step_delete_cd(create_devops, cd_name, 'false')
            # 查看创建的资源
            re = cluster_steps.step_get_project_workload_by_type(ns, 'deployments')
            count_deploy = re.json()['totalItems']
            with pytest.assume:
                assert count_deploy == 1


if __name__ == "__main__":
    pytest.main(['-s', 'test_devops.py'])  # -s参数是为了显示用例的打印信息。 -q参数只显示结果，不显示过程
