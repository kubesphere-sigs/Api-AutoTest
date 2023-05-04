import allure
import pytest
from common import commonFunction
from common.commonFunction import get_random, request_resource
from common.getData import DoexcleByPandas
from step import multi_cluster_storages_step, multi_cluster_steps, multi_workspace_steps, multi_project_steps, \
    cluster_steps


@allure.feature('多集群存储')
@pytest.mark.skipif(commonFunction.check_multi_cluster() is False, reason='单集群环境下不执行')
@pytest.mark.skipif(commonFunction.get_multi_cluster_sc_qingcloud() is False, reason='csi-qingcloud存储插件不存在')
class TestMultiClusterStorage:
    # 如果为单集群环境，则不会collect该class的所有用例。 __test__ = False
    __test__ = commonFunction.check_multi_cluster()

    cluster_name = multi_cluster_steps.step_get_host_cluster_name()
    sc_name = 'test-multi-cluster-sc' + str(get_random())
    ws_name = 'multi-ws-' + str(get_random())
    pro_ws_name = 'multi-ws-pro-' + str(get_random())
    allow_volume_expansion = True
    diver = 'disk.csi.qingcloud.com'
    policy = 'Delete'

    def setup_class(self):
        # 创建多集群工作空间
        multi_workspace_steps.step_create_multi_ws(ws_name=self.ws_name, cluster_names=self.cluster_name)
        # 多集群环境下在host集群创建项目
        multi_project_steps.step_create_project_in_ws(self.ws_name, self.cluster_name, self.pro_ws_name)
        # 多集群环境下在host集群创建存储类
        multi_cluster_storages_step.step_create_sc(cluster_name=self.cluster_name, sc_name=self.sc_name,
                                                   expansion=self.allow_volume_expansion)
        # 多集群环境下在host集群创建卷快照类
        multi_cluster_storages_step.step_create_vsc(self.cluster_name, self.sc_name, self.diver, self.policy)

    def teardown_class(self):
        # 删除创建的卷快照类
        multi_cluster_storages_step.delete_vsc(cluster_name=self.cluster_name, vsc_name=self.sc_name)
        # 删除创建的存储类
        multi_cluster_storages_step.delete_sc(cluster_name=self.cluster_name, sc_name=self.sc_name)
        # 删除创建的项目
        multi_project_steps.step_delete_project_in_ws(self.ws_name, self.cluster_name, self.pro_ws_name)
        # 删除创建的工作空间
        multi_workspace_steps.step_delete_workspace(ws_name=self.ws_name)

    @allure.title('{title}')
    @pytest.mark.parametrize('id,url, params, data, story, title, method, severity, condition, except_result',
                             DoexcleByPandas().get_data_from_yaml(filename='../data/multi_cluster_storage.yaml'))
    def test_storage(self, id, url, params, data, story, title, method, severity, condition, except_result):
        allure.dynamic.story(story)  # 动态生成模块
        allure.dynamic.severity(severity)  # 动态生成用例等级
        # 替换yaml中的参数
        targets = commonFunction.replace_str(url, params, data, title, condition, except_result,
                                             actual_value='${sc_name}', expect_value=self.sc_name)
        targets_new = commonFunction.replace_str(targets[0], targets[1], targets[2], targets[3],
                                                 targets[4], targets[5], actual_value='${cluster_name}',
                                                 expect_value=self.cluster_name)
        request_resource(targets_new[0], targets_new[1], targets_new[2], story, targets_new[3], method, severity,
                         targets_new[4], targets_new[5])

    @allure.story("存储类")
    @allure.title('{title}')
    @allure.severity('normal')
    @pytest.mark.parametrize('title, ex, allow_clone, allow_snapshot', [
        ('设置卷操作-开启卷扩展、克隆、创建快照', True, 'true', 'true'),
        ('设置卷操作-开启卷扩展、关闭克隆和创建快照', True, 'false', 'false'),
        ('设置卷操作-开启卷扩展、关闭克隆、开启创建快照', True, 'false', 'true'),
        ('设置卷操作-开启卷扩展、开启克隆、关闭创建快照', True, 'true', 'false'),
        ('设置卷操作-关闭卷扩展、开启克隆和创建快照', False, 'true', 'true'),
        ('设置卷操作-关闭卷扩展、克隆、创建快照', False, 'false', 'false'),
        ('设置卷操作-关闭卷扩展、开启克隆、关闭创建快照', False, 'true', 'false'),
        ('设置卷操作-关闭卷扩展、关闭克隆、开启创建快照', False, 'false', 'true')])
    def test_set_volume_operations(self, create_multi_cluster_sc, title, ex, allow_clone, allow_snapshot):
        multi_cluster_storages_step.set_volume_operations(self.cluster_name, create_multi_cluster_sc, ex, allow_clone,
                                                          allow_snapshot)
        # 查看存储类详细信息
        re = multi_cluster_storages_step.get_sc_info(self.cluster_name, create_multi_cluster_sc)
        # 验证设置成功
        with pytest.assume:
            assert re.json()['metadata']['annotations']['storageclass.kubesphere.io/allow-clone'] == allow_clone
            assert re.json()['metadata']['annotations']['storageclass.kubesphere.io/allow-snapshot'] == allow_snapshot

    @allure.story("存储类")
    @allure.title('设置为默认存储类')
    @allure.severity('normal')
    def test_set_default_sc(self):
        # 获取集群的默认存储类
        default_sc = cluster_steps.step_get_cluster_default_storage_class(self.cluster_name)
        ex = 'true'
        # 将创建的存储类设置为默认存储类，并将原默认存储类设置为非默认
        multi_cluster_storages_step.set_default_sc(self.cluster_name, default_sc, 'false')
        multi_cluster_storages_step.set_default_sc(self.cluster_name, self.sc_name, ex)
        # 查询存储类
        re = multi_cluster_storages_step.search_sc_by_name(self.cluster_name, self.sc_name)
        # 验证设置成功
        assert re.json()['items'][0]['metadata']['annotations'][
                   'storageclass.beta.kubernetes.io/is-default-class'] == 'true'
        # 将原默认存储类设置为默认，并将创建的存储类设置为非默认存储类
        multi_cluster_storages_step.set_default_sc(self.cluster_name, self.sc_name, 'false')
        multi_cluster_storages_step.set_default_sc(self.cluster_name, default_sc, 'true')

    @allure.story("存储类")
    @allure.title('验证存储类的持久卷声明数量正确')
    @allure.severity('normal')
    def test_sc_pvc(self, create_multi_cluster_sc):
        # 创建存储卷
        volume_name = 'volume-' + str(get_random())
        multi_cluster_storages_step.step_create_pvc(self.cluster_name, self.pro_ws_name, create_multi_cluster_sc,
                                                    volume_name)
        # 查询存储类已有存储卷信息
        re = multi_cluster_storages_step.search_volume_by_sc(self.cluster_name, create_multi_cluster_sc)
        # 查询存储卷数量
        num = \
            multi_cluster_storages_step.search_sc_by_name(self.cluster_name, create_multi_cluster_sc).json()['items'][
                0][
                'metadata'][
                'annotations'][
                'kubesphere.io/pvc-count']
        # 验证存储卷存在以及数量正确
        with pytest.assume:
            assert re.json()['items'][0]['metadata']['name'] == volume_name
        with pytest.assume:
            assert num == '1'
        # 删除存储卷
        multi_cluster_storages_step.delete_volume(self.cluster_name, self.pro_ws_name, volume_name)
        # 查询存储卷数量
        num1 = \
            multi_cluster_storages_step.search_sc_by_name(self.cluster_name, create_multi_cluster_sc).json()['items'][
                0][
                'metadata'][
                'annotations'][
                'kubesphere.io/pvc-count']
        # 查询存储类已有存储卷信息
        re = multi_cluster_storages_step.search_volume_by_sc(self.cluster_name, create_multi_cluster_sc)
        # 验证存储卷不存在以及数量正确
        with pytest.assume:
            assert re.json()['totalItems'] == 0
        with pytest.assume:
            assert num1 == '0'

    @allure.story("存储类")
    @allure.title('查询存储类已有存储卷')
    @allure.severity('normal')
    def test_search_pvc(self):
        # 创建存储卷
        volume_name = 'volume-' + str(get_random())
        multi_cluster_storages_step.step_create_pvc(self.cluster_name, self.pro_ws_name, self.sc_name, volume_name)
        # 精确查询已有存储卷
        r = multi_cluster_storages_step.search_volume(self.cluster_name, self.sc_name, volume_name)
        assert r.json()['items'][0]['metadata']['name'] == volume_name
        # 模糊查询存在的存储卷
        re = multi_cluster_storages_step.search_volume(self.cluster_name, self.sc_name, 'volume')
        assert re.json()['items'][0]['metadata']['name'] == volume_name
        # 查询不存在的存储卷
        response = multi_cluster_storages_step.search_volume(self.cluster_name, self.sc_name, 'ff')
        assert response.json()['totalItems'] == 0
        # 删除存储卷
        multi_cluster_storages_step.delete_volume(self.cluster_name, self.pro_ws_name, volume_name)
