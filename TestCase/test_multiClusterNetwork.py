# -- coding: utf-8 --
import pytest
import sys
import allure
import time
from common import commonFunction
from common.commonFunction import get_ippool_status, get_random, random_ip, request_resource
from common.getData import DoexcleByPandas
from step import network_steps, project_steps, multi_cluster_steps, multi_workspace_steps

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用


@allure.feature('网络')
@pytest.mark.skipif(get_ippool_status() is False, reason='ippool未开启不执行')
@pytest.mark.skipif(commonFunction.check_multi_cluster() is False, reason='单集群环境下不执行')
class TestNetwork(object):
    if commonFunction.check_multi_cluster() is False:
        # 如果为单集群环境，则不会collect该class的所有用例。 __test__ = False
        __test__ = False
    else:
        __test__ = True

    ippool_name = 'ippool-' + str(get_random())
    ip = random_ip()
    ws_name = 'test-network-multi-ws' + str(get_random())
    pro_name = 'test-network-multi-pro' + str(get_random())
    parametrize = DoexcleByPandas().get_data_from_yaml(filename='../data/network.yaml')
    # 获取host集群的名称
    cluster_name = multi_cluster_steps.step_get_host_cluster_name()

    def setup_class(self):
        # 创建ippool
        network_steps.step_create_ippool(ippool_name=self.ippool_name, ip=self.ip, cluster_name=self.cluster_name)
        # 创建多集群workspace
        multi_workspace_steps.step_create_multi_ws(self.ws_name, self.cluster_name)
        # 创建多集群project
        multi_workspace_steps.step_create_project(self.cluster_name, self.ws_name, self.pro_name)

    def teardown_class(self):
        # 删除多集群项目
        multi_workspace_steps.step_delete_multi_project(self.pro_name)
        # 删除多集群workspace
        multi_workspace_steps.step_delete_workspace(self.ws_name)
        # 删除ippool
        network_steps.step_delete_ippool(self.ippool_name, self.cluster_name)

    @allure.title('{title}')
    @pytest.mark.parametrize('cid,url, params, data, story, title, method, severity, condition, except_result',
                             parametrize)
    def test_ippool(self, cid, url, params, data, story, title, method, severity, condition, except_result):
        allure.dynamic.story(story)  # 动态生成模块
        allure.dynamic.severity(severity)  # 动态生成用例等级
        targets = commonFunction.replace_str(url, params, data, title, condition, except_result,
                                             actual_value='${ippool_name}', expect_value=self.ippool_name)
        targets_new = commonFunction.replace_str(targets[0], targets[1], targets[2], targets[3],
                                                 targets[4], targets[5], actual_value='${cidr}',
                                                 expect_value=self.ip + '/24')

        request_resource(targets_new[0], targets_new[1], targets_new[2], story, targets_new[3], method, severity,
                         targets_new[4], targets_new[5])

    @allure.story('Ip pool')
    @allure.title('创建ippool')
    @allure.severity('critical')
    def test_create_ippool(self, ip_pool_name, ip_address):
        # 创建ippool
        network_steps.step_create_ippool(ippool_name=ip_pool_name, ip=ip_address, cluster_name=self.cluster_name)
        synced = ''
        i = 0
        while i < 60:
            try:
                res = network_steps.step_search_by_name(ip_pool_name, self.cluster_name)
                synced = res.json()['items'][0]['status']['synced']
                if synced:
                    break
            except Exception as e:
                print(e)
                i += 1
                time.sleep(1)
        with pytest.assume:
            assert synced is True
        # 删除创建的ippool
        network_steps.step_delete_ippool(ip_pool_name, self.cluster_name)

    @allure.story('Ip pool')
    @allure.title('{title}')
    @allure.severity('normal')
    @pytest.mark.parametrize('title,mask,blockSize,status_code',
                             [('创建ippool-掩码=块大小', 31, 31, 201),
                              ('创建ippool-掩码>块大小', 31, 30, 403),
                              ('创建ippool-掩码<块大小', 30, 31, 201),
                              ('创建ippool-块大小=32', 31, 32, 201),
                              ('创建ippool-块大小>32', 31, 33, 403)])
    def test_create_ippool_with_mask_block_size(self, title, mask, blockSize, status_code, ip_pool_name, ip_address):
        # 创建ippool
        r = network_steps.step_create_ippool(ip_pool_name, ip_address, mask=mask, blockSize=blockSize, cluster_name=self.cluster_name)
        with pytest.assume:
            assert r.status_code == status_code
        # 删除创建的ippool
        if r.status_code == 201:
            network_steps.step_delete_ippool(ip_pool_name, self.cluster_name)

    @allure.story('Ip pool')
    @allure.title('创建同名ippool')
    @allure.severity('normal')
    def test_create_ippool_with_same_name(self, ip_address):
        r = network_steps.step_create_ippool(ippool_name=self.ippool_name, ip=ip_address, cluster_name=self.cluster_name)
        with pytest.assume:
            assert r.json()['message'] == 'ippools.network.kubesphere.io "' + self.ippool_name + '" already exists'

    @allure.story('Ip pool')
    @allure.title('修改ippool的描述信息')
    @allure.severity('normal')
    @pytest.mark.parametrize('create_multi_ippool', [cluster_name], indirect=True)
    def test_update_ippool_desc(self, create_multi_ippool):
        # # 获取ippool的信息
        r = network_steps.step_search_by_name(create_multi_ippool, self.cluster_name)
        spec = r.json()['items'][0]['spec']
        id = r.json()['items'][0]['metadata']['labels']['ippool.network.kubesphere.io/id']
        # 修改ippool的描述信息
        network_steps.step_update_ippool(id, create_multi_ippool, spec, description='test', cluster_name=self.cluster_name)
        # 获取修改后的ippool的信息
        res = network_steps.step_search_by_name(create_multi_ippool, self.cluster_name)
        description = res.json()['items'][0]['metadata']['annotations']['kubesphere.io/description']
        with pytest.assume:
            assert description == 'test'

    @allure.story('Ip pool')
    @allure.title('修改ippool的别名')
    @allure.severity('normal')
    @pytest.mark.parametrize('create_multi_ippool', [cluster_name], indirect=True)
    def test_update_ippool_alias(self, create_multi_ippool):
        # 获取ippool的信息
        r = network_steps.step_search_by_name(create_multi_ippool, cluster_name=self.cluster_name)
        spec = r.json()['items'][0]['spec']
        id = r.json()['items'][0]['metadata']['labels']['ippool.network.kubesphere.io/id']
        # 修改ippool的别名
        network_steps.step_update_ippool(id, create_multi_ippool, spec, alias='test', cluster_name=self.cluster_name)
        # 获取修改后的ippool的信息
        res = network_steps.step_search_by_name(create_multi_ippool, cluster_name=self.cluster_name)
        alias = res.json()['items'][0]['metadata']['annotations']['kubesphere.io/alias-name']
        with pytest.assume:
            assert alias == 'test'

    @allure.story('Ip pool')
    @allure.title('创建cidr交叉的ippool')
    @allure.severity('normal')
    def test_create_ippool_with_same_cidr(self, ip_pool_name, ip_address):
        # 创建ippool
        network_steps.step_create_ippool(ippool_name=ip_pool_name, ip=ip_address, cluster_name=self.cluster_name)
        # 创建cidr交叉的ippool
        ippool_name_new = 'ippool-' + str(get_random())
        r = network_steps.step_create_ippool(ippool_name=ippool_name_new, ip=ip_address, cluster_name=self.cluster_name)
        # 断言创建失败
        with pytest.assume:
            assert r.status_code == 403
        # 删除创建的ippool
        network_steps.step_delete_ippool(ip_pool_name, cluster_name=self.cluster_name)

    @allure.story('Ip pool')
    @allure.title('给ippool分配企业空间')
    @allure.severity('critical')
    @pytest.mark.parametrize('create_multi_ippool', [cluster_name], indirect=True)
    def test_assign_ws(self, create_multi_ippool):
        # 给ippool分配企业空间
        network_steps.step_assign_ws(create_multi_ippool, self.ws_name, cluster_name=self.cluster_name)
        r_new = network_steps.step_search_by_name(create_multi_ippool, cluster_name=self.cluster_name)
        with pytest.assume:
            assert r_new.json()['items'][0]['metadata']['labels']['kubesphere.io/workspace'] == self.ws_name

    @allure.story('Ip pool')
    @allure.title('给已分配企业空间但未使用的ippool分配企业空间')
    @allure.severity('normal')
    @pytest.mark.parametrize('create_multi_ippool', [cluster_name], indirect=True)
    def test_assign_ws_ippool(self, create_multi_ippool, create_multi_workspace):
        # 给ippool分配企业空间
        network_steps.step_assign_ws(create_multi_ippool, create_multi_workspace, cluster_name=self.cluster_name)
        # 再次给ippool分配企业空间
        network_steps.step_assign_ws(create_multi_ippool, self.ws_name, cluster_name=self.cluster_name)
        r_new = network_steps.step_search_by_name(create_multi_ippool, cluster_name=self.cluster_name)
        # 获取ippool被分配的企业空间的名称
        ws_name_actual = r_new.json()['items'][0]['metadata']['labels']['kubesphere.io/workspace']
        with pytest.assume:
            assert ws_name_actual == self.ws_name

    @allure.story('Ip pool')
    @allure.title('删除ippool')
    @allure.severity('critical')
    @pytest.mark.parametrize('create_multi_ippool', [cluster_name], indirect=True)
    def test_delete_ippool(self, create_multi_ippool):
        # 删除ippool
        network_steps.step_delete_ippool(create_multi_ippool, cluster_name=self.cluster_name)
        # 查询已删除的ippool
        time.sleep(8)
        res = network_steps.step_search_by_name(create_multi_ippool, cluster_name=self.cluster_name)
        assert res.json()['totalItems'] == 0

    @allure.story('Ip pool')
    @allure.title('删除已分配企业空间的ippool')
    @allure.severity('critical')
    @pytest.mark.parametrize('create_multi_ippool', [cluster_name], indirect=True)
    def test_delete_ippool_assign_ws(self, ws_name, create_multi_ippool, create_multi_workspace):
        # 分配企业空间
        network_steps.step_assign_ws(create_multi_ippool, create_multi_workspace, cluster_name=self.cluster_name)
        # 删除ippool
        network_steps.step_delete_ippool(create_multi_ippool, cluster_name=self.cluster_name)
        time.sleep(3)
        # 查询已删除的ippool
        res = network_steps.step_search_by_name(create_multi_ippool, cluster_name=self.cluster_name)
        with pytest.assume:
            assert res.json()['totalItems'] == 0

    @allure.story('Ip pool')
    @allure.title('删除后创建相同的ippool')
    @allure.severity('critical')
    @pytest.mark.parametrize('create_multi_ippool', [cluster_name], indirect=True)
    def test_create_ippool_again(self, ip_pool_name, ip_address, create_multi_ippool):
        # 验证创建成功
        time.sleep(5)
        res = network_steps.step_search_by_name(create_multi_ippool, cluster_name=self.cluster_name)
        with pytest.assume:
            assert res.json()['items'][0]['status']['synced'] is True
        # 删除ippool
        network_steps.step_delete_ippool(create_multi_ippool, cluster_name=self.cluster_name)
        # 查询被删除的ippool，验证删除成功
        i = 0
        while i < 60:
            try:
                re = network_steps.step_search_by_name(create_multi_ippool, cluster_name=self.cluster_name)
                if re.json()['totalItems'] == 0:
                    break
            except Exception as e:
                print(e)
                time.sleep(1)
                i += 1
        # 再次创建相同的ippool
        network_steps.step_create_ippool(ip_pool_name, ip_address, cluster_name=self.cluster_name)
        # 验证创建成功
        k = 0
        while k < 60:
            try:
                res = network_steps.step_search_by_name(ip_pool_name, cluster_name=self.cluster_name)
                if res.json()[0]:
                    break
            except Exception as e:
                print(e)
                time.sleep(1)
                k += 1
        with pytest.assume:
            assert res.json()['items'][0]['status']['synced'] is True

    @allure.story('Ip pool')
    @allure.title('删除已使用的ippool')
    @allure.severity('critical')
    @pytest.mark.parametrize('create_multi_ippool', [cluster_name], indirect=True)
    def test_delete_ippool_used(self, create_multi_ippool, deploy_name, container_name):
        # 分配企业空间
        network_steps.step_assign_ws(create_multi_ippool, self.ws_name, cluster_name=self.cluster_name)
        # 创建工作负载
        network_steps.step_create_deploy_use_ip_pool_multi(create_multi_ippool, deploy_name, container_name,
                                                           self.pro_name, self.cluster_name)
        # 等待工作负载创建成功
        workload_status = commonFunction.check_workload_ready_in_multi(self.cluster_name, self.pro_name, 'deployments',
                                                                       deploy_name)
        if workload_status:
            # 删除ippool
            r = network_steps.step_delete_ippool(create_multi_ippool)
            with pytest.assume:
                assert r.json()['reason'] == 'ippool is in use, please remove the workload before deleting'
            # 删除部署
            project_steps.step_delete_workload(self.pro_name, 'deployments', deploy_name)
            # 等待部署删除成功
            commonFunction.check_workload_not_exist_in_multi(self.cluster_name, self.pro_name, 'deployments',
                                                             deploy_name)
        else:
            print('部署创建失败')

    @allure.story('Ip pool')
    @allure.title('测试ippool数量')
    @allure.severity('critical')
    @pytest.mark.parametrize('create_multi_ippool', [cluster_name], indirect=True)
    def test_ippool_num(self, deploy_name, container_name, create_multi_ippool):
        # 将ippool分配到企业空间
        network_steps.step_assign_ws(create_multi_ippool, self.ws_name, self.cluster_name)
        # 创建工作负载
        network_steps.step_create_deploy_use_ip_pool_multi(create_multi_ippool, deploy_name, container_name, self.pro_name, self.cluster_name)
        # 等待工作负载创建成功
        workload_status = commonFunction.check_workload_ready_in_multi(self.cluster_name, self.pro_name, 'deployments',
                                                                       deploy_name)
        if workload_status:
            r = network_steps.step_search_by_name(create_multi_ippool, cluster_name=self.cluster_name)
            num = r.json()['items'][0]['status']['allocations']
            num_new = network_steps.step_get_ws_ippool_number(create_multi_ippool, self.ws_name, cluster_name=self.cluster_name)
            # 验证ippool使用数量正确
            with pytest.assume:
                assert num == num_new == 1
            ws_num = network_steps.step_get_used_ws_number(create_multi_ippool, cluster_name=self.cluster_name)
            # 验证使用ippool的企业空间数量
            with pytest.assume:
                assert ws_num == 1
            # 删除部署
            project_steps.step_delete_workload(self.pro_name, 'deployments', deploy_name)
            # 等待部署删除成功
            commonFunction.check_workload_not_exist_in_multi(self.cluster_name, self.pro_name, 'deployments',
                                                             deploy_name)
        else:
            print('部署创建失败')

    @allure.story('Ip pool')
    @allure.title('查询ippool的容器组')
    @allure.severity('critical')
    @pytest.mark.parametrize('create_multi_ippool', [cluster_name], indirect=True)
    def test_search_ippool_pod(self, deploy_name, container_name, create_multi_ippool):
        # 将ippool分配到企业空间
        network_steps.step_assign_ws(create_multi_ippool, self.ws_name, self.cluster_name)
        # 使用新建的ippool创建部署
        network_steps.step_create_deploy_use_ip_pool_multi(create_multi_ippool, deploy_name, container_name, self.pro_name, self.cluster_name)
        # 等待部署创建成功
        workload_status = commonFunction.check_workload_ready_in_multi(self.cluster_name, self.pro_name, 'deployments', deploy_name)
        if workload_status:
            r = network_steps.step_get_job(create_multi_ippool, cluster_name=self.cluster_name)
            # 获取pod名称
            pod_name = r.json()['items'][0]['metadata']['name']
            # 精确查询存在的pod
            re = network_steps.step_search_pod(pod_name, create_multi_ippool)
            with pytest.assume:
                assert re.status_code == 200
            # 模糊查询存在的pod
            re = network_steps.step_search_pod(deploy_name, create_multi_ippool)
            with pytest.assume:
                assert re.json()['totalItems'] == 1
            # 查询不存在的pod
            re = network_steps.step_search_pod(pod_name='ss', ippool_name=create_multi_ippool)
            with pytest.assume:
                assert re.json()['totalItems'] == 0
            # 删除部署
            project_steps.step_delete_workload(self.pro_name, 'deployments', deploy_name)
            # 等待部署删除成功
            commonFunction.check_workload_not_exist_in_multi(self.cluster_name, self.pro_name, 'deployments', deploy_name)
        else:
            print('部署创建失败')

    @allure.story('Ip pool')
    @allure.title('禁用未分配企业空间的Ippool')
    @allure.severity('critical')
    @pytest.mark.parametrize('create_multi_ippool', [cluster_name], indirect=True)
    def test_disable_ippool(self, create_multi_ippool):
        # 禁用ippool
        res = network_steps.step_disable_ippool(create_multi_ippool, cluster_name=self.cluster_name)
        # 验证ippool禁用成功
        with pytest.assume:
            assert res.json()['spec']['disabled'] == True

    @allure.story('Ip pool')
    @allure.title('启用已分配企业空间的Ippool')
    @allure.severity('critical')
    @pytest.mark.parametrize('create_multi_ippool', [cluster_name], indirect=True)
    def test_disable_ippool_with_ws(self, create_multi_ippool):
        # 将ippool分配到企业空间
        network_steps.step_assign_ws(create_multi_ippool, self.ws_name, self.cluster_name)
        # 禁用ippool
        network_steps.step_disable_ippool(create_multi_ippool, cluster_name=self.cluster_name)
        # 查询ippool
        res = network_steps.step_search_by_name(create_multi_ippool, cluster_name=self.cluster_name)
        # 验证ippool禁用成功
        with pytest.assume:
            assert res.json()['items'][0]['spec']['disabled'] == True

    @allure.story('Ip pool')
    @allure.title('启用已禁用的Ippool')
    @allure.severity('critical')
    @pytest.mark.parametrize('create_multi_ippool', [cluster_name], indirect=True)
    def test_enable_ippool(self, create_multi_ippool):
        # 禁用ippool
        network_steps.step_disable_ippool(create_multi_ippool, cluster_name=self.cluster_name)
        # 启用ippool
        res = network_steps.step_enable_ippool(create_multi_ippool, cluster_name=self.cluster_name)
        # 验证ippool启用成功
        with pytest.assume:
            assert res.json()['spec']['disabled'] == False

    @allure.story('Ip pool')
    @allure.title('禁用ippool后，删除ippool')
    @allure.severity('critical')
    @pytest.mark.parametrize('create_multi_ippool', [cluster_name], indirect=True)
    def test_delete_disable_ippool(self, create_multi_ippool):
        # 禁用ippool
        network_steps.step_disable_ippool(create_multi_ippool, cluster_name=self.cluster_name)
        # 删除ippool
        res = network_steps.step_delete_ippool(create_multi_ippool, cluster_name=self.cluster_name)
        # 验证删除成功
        with pytest.assume:
            assert res.status_code == 200

    @allure.story('Ip pool')
    @allure.title('启用ippool后，删除ippool')
    @allure.severity('normal')
    @pytest.mark.parametrize('create_multi_ippool', [cluster_name], indirect=True)
    def test_delete_enable_ippool(self, create_multi_ippool):
        # 禁用ippool
        network_steps.step_disable_ippool(create_multi_ippool, cluster_name=self.cluster_name)
        # 启用ippool
        network_steps.step_enable_ippool(create_multi_ippool, cluster_name=self.cluster_name)
        # 删除ippool
        res = network_steps.step_delete_ippool(create_multi_ippool, cluster_name=self.cluster_name)
        # 验证删除成功
        with pytest.assume:
            assert res.status_code == 200

    @allure.story('Ip pool')
    @allure.title('禁用ippool，并迁移到企业空间相同的ippool')
    @allure.severity('critical')
    @pytest.mark.parametrize('create_multi_ippool', [cluster_name], indirect=True)
    def test_disable_ippool_and_move_to_same_ws(self, create_multi_ippool):
        # 将ippool分配到企业空间
        network_steps.step_assign_ws(create_multi_ippool, self.ws_name, self.cluster_name)
        # 创建另一个ippool
        new_ip_pool_name = create_multi_ippool + 'test'
        new_ip_address = commonFunction.random_ip()
        network_steps.step_create_ippool(new_ip_pool_name, new_ip_address, cluster_name=self.cluster_name)
        # 将ippool分配到相同的企业空间
        network_steps.step_assign_ws(new_ip_pool_name, self.ws_name)
        # 禁用ippool
        network_steps.step_disable_ippool(create_multi_ippool, self.cluster_name)
        # 迁移ippool
        res = network_steps.step_migrate_ippool(create_multi_ippool, new_ip_pool_name, self.cluster_name)
        with pytest.assume:
            assert res.json()['message'] == 'success'
        # 删除ippool
        network_steps.step_delete_ippool(new_ip_pool_name)

    @allure.story('Ip pool')
    @allure.title('禁用ippool，并迁移到企业空间不同的ippool')
    @allure.severity('critical')
    @pytest.mark.parametrize('create_multi_ippool', [cluster_name], indirect=True)
    def test_disable_ippool_and_move_to_diff_ws(self, ws_name, create_multi_ippool, create_multi_workspace):
        # 将ippool分配到企业空间
        network_steps.step_assign_ws(create_multi_ippool, self.ws_name, self.cluster_name)
        # 创建另一个ippool
        new_ip_pool_name = create_multi_ippool + 'test'
        new_ip_address = commonFunction.random_ip()
        network_steps.step_create_ippool(new_ip_pool_name, new_ip_address, cluster_name=self.cluster_name)
        # 将ippool分配到不同的企业空间
        network_steps.step_assign_ws(new_ip_pool_name, create_multi_workspace)
        # 禁用ippool
        network_steps.step_disable_ippool(create_multi_ippool, self.cluster_name)
        # 迁移ippool
        res = network_steps.step_migrate_ippool(create_multi_ippool, new_ip_pool_name, self.cluster_name)
        with pytest.assume:
            assert res.status_code == 400
        # 删除ippool
        network_steps.step_delete_ippool(new_ip_pool_name)

    @allure.story('Network policy')
    @allure.title('创建网络策略')
    @allure.severity('critical')
    def test_create_network_policy(self, create_project, create_network_policy):
        # 查询网络策略
        res = network_steps.step_search_network_policy(create_project, create_network_policy)
        # 获取网络策略的名称
        network_policy_name = res.json()['items'][0]['metadata']['name']
        # 验证网络策略创建成功
        with pytest.assume:
            assert network_policy_name == create_network_policy

    @allure.story('Network policy')
    @allure.title('查询网络策略')
    @allure.severity('normal')
    @pytest.mark.parametrize('title, pro_name, network_policy_name',
                             [('查询全部的网络策略', '', ''),
                              ('查询指定名称的网络策略', '', 'true'),
                              ('查询指定项目的网络策略', 'true', ''),
                              ('查询指定名称和项目的网络策略', 'true', 'true')
                              ])
    def test_search_network_policy(self, title, pro_name, network_policy_name, create_project, create_network_policy):
        # 判断是否指定名称和项目
        if network_policy_name == 'true' and pro_name == '':
            network_policy_name = create_network_policy
        elif network_policy_name == 'true' and pro_name == 'true':
            network_policy_name = create_network_policy
            pro_name = create_project
        elif network_policy_name == '' and pro_name == 'true':
            pro_name = create_project
        # 查询网络策略
        res = network_steps.step_search_network_policy(pro_name, network_policy_name)
        # 验证网络策略查询成功
        with pytest.assume:
            assert res.json()['totalItems'] >= 1

    @allure.story('Network policy')
    @allure.title('删除网络策略')
    @allure.severity('critical')
    def test_delete_network_policy(self, create_project, create_network_policy):
        # 删除网络策略
        network_steps.step_delete_network_policy(create_project, create_network_policy)
        # 查询网络策略
        res = network_steps.step_search_network_policy(create_project, create_network_policy)
        # 验证网络策略删除成功
        with pytest.assume:
            assert res.json()['totalItems'] == 0

    @allure.story('Network policy')
    @allure.title('更新网络策略')
    @allure.severity('normal')
    def test_update_network_policy(self, create_project, create_network_policy):
        # 更新网络策略
        alias = 'alias-' + str(get_random())
        description = 'description-' + str(get_random())
        network_steps.step_update_network_policy(create_project, create_network_policy, alias, description)
        # 查询网络策略
        res = network_steps.step_search_network_policy(create_project, create_network_policy)
        # 验证网络策略更新成功
        with pytest.assume:
            assert res.json()['items'][0]['metadata']['annotations']['kubesphere.io/alias-name'] == alias
            assert res.json()['items'][0]['metadata']['annotations']['kubesphere.io/description'] == description

    @allure.story('Network policy')
    @allure.title('查看网络策略的详情信息')
    @allure.severity('normal')
    def test_get_network_policy_detail(self, create_project, create_network_policy):
        # 查询网络策略
        res = network_steps.step_get_network_policy_detail(create_project, create_network_policy)
        # 验证网络策略查询成功
        with pytest.assume:
            assert res.json()['metadata']['name'] == create_network_policy


if __name__ == '__main__':
    pytest.main(['-vs', 'test_network.py'])
