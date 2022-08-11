# -- coding: utf-8 --
import pytest
from pytest import assume
from common import commonFunction
from common.commonFunction import *
from common.commonFunction import get_ippool_status
from common.getData import *
from step import ippool_steps, workspace_steps, project_steps

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用


@allure.feature('ippool')
@pytest.mark.skipif(get_ippool_status() is False, reason='ippool未开启不执行')
@pytest.mark.skipif(commonFunction.check_multi_cluster() is True, reason='多集群环境下不执行')
class TestIpPool(object):
    if commonFunction.check_multi_cluster() is True:
        # 如果为单集群环境，则不会collect该class的所有用例。 __test__ = False
        __test__ = False
    else:
        __test__ = True

    ippool_name = 'ippool-' + str(get_random())
    cidr = random_ip() + '/24'
    ws_name = 'test-ippool-ws' + str(get_random())
    pro_name = 'test-ippool-pro' + str(get_random())
    parametrize = DoexcleByPandas().get_data_from_yaml(filename='../data/ippool.yaml')

    def setup_class(self):
        des = ''
        ippool_steps.step_create_ippool(ippool_name=self.ippool_name, cidr=self.cidr, description=des)
        workspace_steps.step_create_workspace(self.ws_name)
        project_steps.step_create_project(ws_name=self.ws_name, project_name=self.pro_name)

    def teardown_class(self):
        project_steps.step_delete_project(self.ws_name, self.pro_name)
        workspace_steps.step_delete_workspace(self.ws_name)
        ippool_steps.step_delete_ippool(self.ippool_name)

    @pytest.fixture()
    def create_ippool(self):
        ippool_name = 'ippool-' + str(get_random())
        cidr = random_ip() + '/24'
        description = ' '
        # 创建ippool
        ippool_steps.step_create_ippool(ippool_name, cidr, description)
        yield ippool_name
        # 删除ippool
        ippool_steps.step_delete_ippool(ippool_name)

    @allure.title('{title}')
    @pytest.mark.parametrize('id,url, params, data, story, title, method, severity, condition, except_result', parametrize)
    def test_ippool(self, id, url, params, data, story, title, method, severity, condition, except_result):
        allure.dynamic.story(story)  # 动态生成模块
        allure.dynamic.severity(severity)  # 动态生成用例等级
        targets = commonFunction.replace_str(url, params, data, title, condition, except_result,
                                             actual_value='${ippool_name}', expect_value=self.ippool_name)
        targets_new = commonFunction.replace_str(targets[0], targets[1], targets[2], targets[3],
                                                 targets[4], targets[5], actual_value='${cidr}', expect_value=self.cidr)

        request_resource(targets_new[0], targets_new[1], targets_new[2], story, targets_new[3], method, severity,
                         targets_new[4], targets_new[5])

    @allure.title('创建ippool')
    @allure.severity('critical')
    def test_create_ippool(self, create_ippool):
        synced = ''
        i = 0
        while i < 60:
            try:
                res = ippool_steps.step_search_by_name(create_ippool)
                synced = res.json()['items'][0]['status']['synced']
                if synced:
                    break
            except Exception as e:
                print(e)
                i += 1
                time.sleep(1)
        with assume:
            assert synced is True

    @allure.title('给ippool分配企业空间')
    @allure.severity('critical')
    def test_assign_ws(self, create_ippool):
        # 给ippool分配企业空间
        ippool_steps.step_assign_ws(create_ippool, self.ws_name)
        r_new = ippool_steps.step_search_by_name(create_ippool)
        pytest.assume(r_new.json()['items'][0]['metadata']['labels']['kubesphere.io/workspace'] == self.ws_name)

    @allure.title('给已分配企业空间的ippool分配企业空间')
    @allure.severity('normal')
    def test_assign_ws_ippool(self):
        ippool = 'ippool-' + str(get_random())
        cidr = random_ip() + '/24'
        description = ''
        ws_name_new = 'test-ws-' + str(get_random())
        workspace_steps.step_create_workspace(ws_name_new)
        ippool_steps.step_create_ippool(ippool, cidr, description)
        # 给ippool分配企业空间
        ippool_steps.step_assign_ws(ippool, self.ws_name)
        # 再次给ippool分配企业空间
        ippool_steps.step_assign_ws(ippool, ws_name_new)
        r_new = ippool_steps.step_search_by_name(ippool)
        pytest.assume(r_new.json()['items'][0]['metadata']['labels']['kubesphere.io/workspace'] == ws_name_new)
        # 删除ippool
        ippool_steps.step_delete_ippool(ippool)
        # 删除企业空间
        workspace_steps.step_delete_workspace(ws_name_new)

    @allure.title('给已被使用的ippool分配企业空间')
    @allure.severity('normal')
    def test_assign_ws_ippool_again(self, create_ippool):
        deploy_name = 'deploy-' + str(get_random())
        container_name = 'test-ippool-' + str(get_random())
        # 分配企业空间
        ippool_steps.step_assign_ws(create_ippool, self.ws_name)
        # 创建部署
        ippool_steps.step_create_deploy(create_ippool, deploy_name, container_name, self.pro_name)
        sleep(15)
        # 创建新的企业空间
        ws_name_new = 'test-ws-' + str(get_random())
        workspace_steps.step_create_workspace(ws_name_new)
        # 给ippool分配企业空间
        re = ippool_steps.step_assign_ws(create_ippool, ws_name_new)
        project_steps.step_delete_workload(self.pro_name, 'deployments', deploy_name)
        sleep(5)
        workspace_steps.step_delete_workspace(ws_name_new)
        sleep(5)

    @allure.title('删除ippool')
    @allure.severity('critical')
    def test_delete_ippool(self, create_ippool):
        # 删除ippool
        ippool_steps.step_delete_ippool(create_ippool)
        # 查询已删除的ippool
        time.sleep(5)
        res = ippool_steps.step_search_by_name(create_ippool)
        assert res.json()['totalItems'] == 0

    @allure.title('删除已分配企业空间的ippool')
    @allure.severity('critical')
    def test_delete_ippool_assign_ws(self, create_ippool):
        # 分配企业空间
        ippool_steps.step_assign_ws(create_ippool, self.ws_name)
        # 删除ippool
        ippool_steps.step_delete_ippool(create_ippool)
        time.sleep(3)
        # 查询已删除的ippool
        res = ippool_steps.step_search_by_name(create_ippool)
        assert res.json()['totalItems'] == 0

    @allure.title('删除后创建相同的ippool')
    @allure.severity('critical')
    def test_create_ippool_again(self):
        ippool_name = 'ippool-' + str(get_random())
        cidr = random_ip() + '/24'
        description = ' '
        # 创建ippool
        ippool_steps.step_create_ippool(ippool_name, cidr, description)
        # 验证创建成功
        time.sleep(5)
        res = ippool_steps.step_search_by_name(ippool_name)
        pytest.assume(res.json()['items'][0]['status']['synced'] is True)
        # 删除ippool
        ippool_steps.step_delete_ippool(ippool_name)
        # 查询被删除的ippool，验证删除成功
        i = 0
        while i < 60:
            try:
                re = ippool_steps.step_search_by_name(ippool_name)
                if re.json()['totalItems'] == 0:
                    break
            except Exception as e:
                print(e)
                time.sleep(1)
                i += 1
        # 再次创建相同的ippool
        ippool_steps.step_create_ippool(ippool_name, cidr, description)
        # 验证创建成功
        k = 0
        while k < 60:
            try:
                res = ippool_steps.step_search_by_name(ippool_name)
                if res.json()[0]:
                    break
            except Exception as e:
                print(e)
                time.sleep(1)
                k += 1
        pytest.assume(res.json()['items'][0]['status']['synced'] is True)
        # 删除创建的ippool
        ippool_steps.step_delete_ippool(ippool_name)

    @allure.title('删除已使用的ippool')
    @allure.severity('critical')
    def test_delete_ippool_used(self, create_ippool):
        deploy_name = 'deploy-' + str(get_random())
        container_name = 'test-ippool-' + str(get_random())
        # 分配企业空间
        ippool_steps.step_assign_ws(create_ippool, self.ws_name)
        # 创建部署
        ippool_steps.step_create_deploy(create_ippool, deploy_name, container_name, self.pro_name)
        # 等待部署创建成功
        i = 0
        while i < 180:
            try:
                response = project_steps.step_get_workload(self.pro_name, 'deployments', 'name=' + deploy_name)
                readyReplicas = response.json()['items'][0]['status']['readyReplicas']
                replicas = response.json()['items'][0]['status']['replicas']
                if readyReplicas == replicas:
                    break
            except Exception as e:
                print(e)
                i += 3
                time.sleep(3)

        # 删除ippool
        r = ippool_steps.step_delete_ippool(create_ippool)
        pytest.assume(r.json()['reason'] == 'ippool is in use, please remove the workload before deleting')
        # 删除部署
        project_steps.step_delete_workload(self.pro_name, 'deployments', deploy_name)
        sleep(15)

    @allure.title('创建部署并分配ippool')
    @allure.severity('critical')
    def test_assign_deploy_ippool(self, create_ippool):
        deploy_name = 'deploy-' + str(get_random())
        container_name = 'test-ippool-' + str(get_random())
        # 创建企业空间
        ws_name = 'test-ws' + str(get_random())
        workspace_steps.step_create_workspace(ws_name)
        # 创建项目
        pro_name = 'test-pro' + str(get_random())
        project_steps.step_create_project(ws_name, pro_name)
        # 将ippool分配到企业空间
        ippool_steps.step_assign_ws(create_ippool, ws_name)
        # 创建部署
        ippool_steps.step_create_deploy(create_ippool, deploy_name, container_name, pro_name)
        sleep(15)
        res = project_steps.step_get_deployment(pro_name, 'deployments')
        # 验证部署创建成功
        pytest.assume('unavailableReplicas' not in res.json()['items'][0]['status'])
        # 查询ippool部署
        rr = ippool_steps.step_get_job(create_ippool)
        # 验证部署名称正确
        pytest.assume(rr.json()['items'][0]['metadata']['labels']['app'] == deploy_name)
        # 删除部署
        project_steps.step_delete_workload(pro_name, 'deployments', deploy_name)
        # 删除项目
        project_steps.step_delete_project(ws_name, pro_name)
        # 删除企业空间
        workspace_steps.step_delete_workspace(ws_name)

    @allure.title('测试ippool数量')
    @allure.severity('critical')
    def test_ippool_num(self, create_ippool):
        # 分配企业空间
        ippool_steps.step_assign_ws(create_ippool, self.ws_name)
        deploy_name = 'deploy-' + str(get_random())
        container_name = 'container-' + str(get_random())
        # 创建工作负载
        ippool_steps.step_create_deploy(create_ippool, deploy_name, container_name, self.pro_name)
        # 等待工作负载创建成功
        i = 0
        while i < 180:
            try:
                response = project_steps.step_get_workload(self.pro_name, 'deployments', 'name=' + deploy_name)
                readyReplicas = response.json()['items'][0]['status']['readyReplicas']
                replicas = response.json()['items'][0]['status']['replicas']
                if readyReplicas == replicas:
                    break
            except Exception as e:
                print(e)
                i += 3
                time.sleep(3)
        r = ippool_steps.step_search_by_name(create_ippool)
        num = r.json()['items'][0]['status']['allocations']
        num_new = ippool_steps.step_get_ws_ippool_number(create_ippool, self.ws_name)
        # 验证ippool使用数量正确
        pytest.assume(num == num_new == 1)
        ws_num = ippool_steps.step_get_used_ws_number(create_ippool)
        # 验证使用ippool的企业空间数量
        pytest.assume(ws_num == 1)
        # 删除部署
        project_steps.step_delete_workload(self.pro_name, 'deployments', deploy_name)
        sleep(10)
        re = ippool_steps.step_search_by_name(create_ippool)
        num = re.json()['items'][0]['status']['allocations']
        num_new = ippool_steps.step_get_ws_ippool_number(create_ippool, self.ws_name)
        # 验证ippool使用数量正确
        pytest.assume(num == num_new)
        ws_num_new = ippool_steps.step_get_used_ws_number(create_ippool)
        # 验证使用ippool的企业空间数量
        pytest.assume(ws_num_new == 0)

    @allure.title('查询ippool的容器组')
    @allure.severity('critical')
    def test_search_ippool_pod(self, create_ippool):
        deploy_name = 'deploy-' + str(get_random())
        container_name = 'test-ippool-' + str(get_random())
        # 使用新建的ippool创建部署
        ippool_steps.step_create_deploy(create_ippool, deploy_name, container_name, self.pro_name)
        sleep(15)
        res = project_steps.step_get_deployment(self.pro_name, 'deployments')
        # 验证部署创建成功
        pytest.assume('unavailableReplicas' not in res.json()['items'][0]['status'])
        r = ippool_steps.step_get_job(create_ippool)
        # 获取pod名称
        pod_name = r.json()['items'][0]['metadata']['name']
        # 精确查询存在的pod
        re = ippool_steps.step_search_pod(pod_name, create_ippool)
        pytest.assume(re.status_code == 200)
        # 模糊查询存在的pod
        re = ippool_steps.step_search_pod(deploy_name, create_ippool)
        pytest.assume(re.json()['totalItems'] == 1)
        # 查询不存在的pod
        re = ippool_steps.step_search_pod(pod_name='ss', ippool_name=create_ippool)
        pytest.assume(re.json()['totalItems'] == 0)
        # 删除部署
        project_steps.step_delete_workload(self.pro_name, 'deployments', deploy_name)


if __name__ == '__main__':
    pytest.main(['-vs', 'test_ippool.py'])
