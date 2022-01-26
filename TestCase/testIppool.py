import sys
from time import sleep

import allure
import pytest
from common.commonFunction import *

from common.commonFunction import get_ippool_status
from common.getData import *
from step import ippool_steps, workspace_steps, project_steps

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用


@allure.feature('ippool')
@pytest.mark.skipif(get_ippool_status() is False, reason='ippool未开启不执行')
class Test_ippool:
    ippool_name = 'ippool-test'
    cidr = '192.168.100.0/24'
    ws_name = 'test-ippool-ws'
    pro_name = 'test-ippool-pro'

    def setup_class(self):
        des = ''
        ippool_steps.step_create_ippool(ippool_name=self.ippool_name, cidr=self.cidr, description=des)
        workspace_steps.step_create_workspace(self.ws_name)
        project_steps.step_create_project(ws_name=self.ws_name, project_name=self.pro_name)

    def teardown_class(self):
        project_steps.step_delete_project(self.ws_name, self.pro_name)
        workspace_steps.step_delete_workspace(self.ws_name)
        ippool_steps.step_delete_ippool(ippool_name=self.ippool_name)

    @allure.title('{title}')
    @pytest.mark.parametrize('id,url, params, data, story, title, method, severity, condition, except_result',
                             DoexcleByPandas().get_data_for_pytest(filename='../data/data.xlsx', sheet_name='ippool'))
    def test_ippool(self, id, url, params, data, story, title, method, severity, condition, except_result):
        allure.dynamic.story(story)  # 动态生成模块
        allure.dynamic.severity(severity)  # 动态生成用例等级
        request_resource(url, params, data, story, title, method, severity, condition, except_result)

    @allure.title('创建ippool')
    @allure.severity('critical')
    def test_create_ippool(self):
        ippool_name = 'ippool-' + str(get_random())
        cidr = '192.168.101.0/24'
        description = ' '
        ippool_steps.step_create_ippool(ippool_name, cidr, description)
        res = ippool_steps.step_search_by_name(ippool_name)
        synced = res.json()['items'][0]['status']['synced']
        assert synced is True
        response = ippool_steps.step_delete_ippool(ippool_name)
        assert response.status_code == 200

    @allure.title('给ippool分配企业空间')
    @allure.severity('critical')
    def test_assign_ws(self):
        ippool_name = 'ippool-' + str(get_random())
        cidr = '192.168.103.0/24'
        description = ''
        ippool_steps.step_create_ippool(ippool_name, cidr, description)
        r = ippool_steps.step_assign_ws(ippool_name, self.ws_name)
        r_new = ippool_steps.step_search_by_name(ippool_name)
        assert r_new.json()['items'][0]['metadata']['labels']['kubesphere.io/workspace'] == self.ws_name
        ippool_steps.step_delete_ippool(ippool_name)

    @allure.title('给已分配企业空间的ippool分配企业空间')
    @allure.severity('normal')
    def test_assign_ws_ippool(self):
        ippool = 'ippool-' + str(get_random())
        cidr = '192.168.104.0/24'
        description = ''
        ws_name_new = 'test-ws-' + str(get_random())
        workspace_steps.step_create_workspace(ws_name_new)
        ippool_steps.step_create_ippool(ippool, cidr, description)
        # 给ippool分配企业空间
        ippool_steps.step_assign_ws(ippool, self.ws_name)
        # 再次给ippool分配企业空间
        ippool_steps.step_assign_ws(ippool, ws_name_new)
        r_new = ippool_steps.step_search_by_name(ippool)
        assert r_new.json()['items'][0]['metadata']['labels']['kubesphere.io/workspace'] == ws_name_new
        ippool_steps.step_delete_ippool(ippool)
        workspace_steps.step_delete_workspace(ws_name_new)

    @allure.title('删除ippool')
    @allure.severity('critical')
    def test_delete_ippool(self):
        ippool_name = 'ippool-' + str(get_random())
        cidr = '192.168.105.0/24'
        description = ''
        # 创建ippool
        ippool_steps.step_create_ippool(ippool_name, cidr, description)
        # 删除ippool
        r = ippool_steps.step_delete_ippool(ippool_name)
        # 查询已删除的ippool
        res = ippool_steps.step_search_by_name(ippool_name)
        assert res.json()['totalItems'] == 0

    @allure.title('删除已分配企业空间的ippool')
    @allure.severity('critical')
    def test_delete_ippool_assign_ws(self):
        ippool_name = 'ippool-' + str(get_random())
        cidr = '192.168.102.0/24'
        description = ' '
        # 创建ippool
        ippool_steps.step_create_ippool(ippool_name, cidr, description)
        # 分配企业空间
        ippool_steps.step_assign_ws(ippool_name, self.ws_name)
        # 删除企业空间
        r = ippool_steps.step_delete_ippool(ippool_name)
        assert r.status_code == 200
        # 查询已删除的ippool
        res = ippool_steps.step_search_by_name(ippool_name)
        assert res.json()['totalItems'] == 0

    @allure.title('删除已使用的ippool')
    @allure.severity('critical')
    def test_delete_ippool_used(self):
        ippool_name = 'ippool-' + str(get_random())
        ippool = '[\"' + ippool_name + '\"]'
        deploy_name = 'deploy-' + str(get_random())
        container_name = 'test-ippool-' + str(get_random())
        cidr = '192.168.106.0/24'
        description = ''
        # 创建ippool
        ippool_steps.step_create_ippool(ippool_name, cidr, description)
        # 分配企业空间
        ippool_steps.step_assign_ws(ippool_name, self.ws_name)
        # 创建部署
        ippool_steps.step_create_deploy(ippool, deploy_name, container_name, self.pro_name)
        sleep(15)
        # 删除ippool
        r = ippool_steps.step_delete_ippool(ippool_name)
        assert r.json()['reason'] == 'ippool is in use, please remove the workload before deleting'
        # 删除部署
        r = project_steps.step_delete_workload(self.pro_name, 'deployments', deploy_name)
        sleep(15)
        res = ippool_steps.step_delete_ippool(ippool_name)
        assert res.status_code == 200

    @allure.title('创建部署分配ippool')
    @allure.severity('critical')
    def test_assign_deploy_ippool(self):
        ippool_name = '[\"' + self.ippool_name + '\"]'
        deploy_name = 'deploy-' + str(get_random())
        container_name = 'test-ippool-' + str(get_random())
        # 创建部署
        ippool_steps.step_create_deploy(ippool_name, deploy_name, container_name, self.pro_name)
        sleep(15)
        res = project_steps.step_get_deployment(self.pro_name, 'deployments')
        # 验证部署创建成功
        assert 'unavailableReplicas' not in res.json()['items'][0]['status']
        # 查询ippool部署
        rr = ippool_steps.step_get_job(self.ippool_name)
        # 验证部署名称正确
        assert rr.json()['items'][0]['metadata']['labels']['app'] == deploy_name
        # 删除部署
        project_steps.step_delete_workload(self.pro_name, 'deployments', deploy_name)
        sleep(15)

    @allure.title('测试ippool数量')
    @allure.severity('critical')
    def test_ippool_num(self):
        ippool_name = 'ippool-' + str(get_random())
        cider = '192.100.110.0/24'
        describe = ''
        # 创建ippool
        ippool_steps.step_create_ippool(ippool_name, cider, describe)
        # 分配企业空间
        ippool_steps.step_assign_ws(ippool_name, self.ws_name)
        ippool = '[\"' + ippool_name + '\"]'
        deploy_name = 'deploy-' + str(get_random())
        container_name = 'container-' + str(get_random())
        # 创建工作负载
        ippool_steps.step_create_deploy(ippool, deploy_name, container_name, self.pro_name)
        sleep(15)
        r = ippool_steps.step_search_by_name(ippool_name)
        num = r.json()['items'][0]['status']['allocations']
        num_new = ippool_steps.step_get_ws_ippool_number(ippool_name, self.ws_name)
        # 验证ippool使用数量正确
        assert num == num_new == 1
        ws_num = ippool_steps.step_get_used_ws_number(ippool_name)
        # 验证使用ippool的企业空间数量
        assert ws_num == 1
        # 删除部署
        project_steps.step_delete_workload(self.pro_name, 'deployments', deploy_name)
        sleep(10)
        re = ippool_steps.step_search_by_name(ippool_name)
        num = re.json()['items'][0]['status']['allocations']
        num_new = ippool_steps.step_get_ws_ippool_number(ippool_name, self.ws_name)
        # 验证ippool使用数量正确
        assert num == num_new
        ws_num_new = ippool_steps.step_get_used_ws_number(ippool_name)
        # 验证使用ippool的企业空间数量
        assert ws_num_new == 0
        ippool_steps.step_delete_ippool(ippool_name)

    @allure.title('查询ippool的容器组')
    @allure.severity('critical')
    def test_search_ippool_pod(self):
        ippool = '[\"' + self.ippool_name + '\"]'
        deploy_name = 'deploy-' + str(get_random())
        container_name = 'test-ippool-' + str(get_random())
        # 创建ippool
        ippool_steps.step_create_deploy(ippool, deploy_name, container_name, self.pro_name)
        sleep(15)
        res = project_steps.step_get_deployment(self.pro_name, 'deployments')
        # 验证部署创建成功
        assert 'unavailableReplicas' not in res.json()['items'][0]['status']
        r = ippool_steps.step_get_job(self.ippool_name)
        # 获取pod名称
        pod_name = r.json()['items'][0]['metadata']['name']
        # 精确查询存在的pod
        re = ippool_steps.step_search_pod(pod_name, self.ippool_name)
        assert re.status_code == 200
        # 模糊查询存在的pod
        re = ippool_steps.step_search_pod(deploy_name, self.ippool_name)
        assert re.json()['totalItems'] == 1
        # 查询不存在的pod
        re = ippool_steps.step_search_pod(pod_name='ss', ippool_name=self.ippool_name)
        assert re.json()['totalItems'] == 0
        # 删除部署
        project_steps.step_delete_workload(self.pro_name, 'deployments', deploy_name)
        sleep(5)


if __name__ == '__main__':
    pytest.main(['-vs', 'test_ippool.py'])
