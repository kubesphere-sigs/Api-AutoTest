from time import sleep

import allure
import pytest
from common import commonFunction
from common.commonFunction import get_random, request_resource
from common.getData import DoexcleByPandas
from step import workspace_steps, project_steps, storage_steps
from fixtures.storage import create_sc


@allure.feature('storage')
@pytest.mark.skipif(commonFunction.check_multi_cluster() is True, reason='多集群环境下不执行')
@pytest.mark.skipif(commonFunction.get_sc_qingcloud() is False, reason='csi-qingcloud存储插件不存在')
class TestStorage:
    if commonFunction.check_multi_cluster() is True:
        # 如果为单集群环境，则不会collect该class的所有用例。 __test__ = False
        __test__ = False
    else:
        __test__ = True

    sc_name = 'test-sc'
    sc_name1 = 'test-vsc'
    ws_name = 'ws-' + str(get_random())
    pro_ws_name = 'ws-pro-' + str(get_random())
    allowVolumeExpansion = True
    volume_name = 'volume-' + str(get_random())
    project_name = pro_ws_name
    work_name = 'deploy-test'
    container_name = 'container'
    image = 'nginx'
    replicas = 1
    ports = [{"name": "tcp-80", "protocol": "TCP", "containerPort": 80}]
    volumemount = [{"name": sc_name1, "readOnly": False, "mountPath": "/data"}]
    volume_info = [{"name": sc_name1, "persistentVolumeClaim": {"claimName": volume_name}}]
    strategy = {"type": "RollingUpdate", "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"}}

    # 所有用例执行之前执行该方法
    def setup_class(self):
        workspace_steps.step_create_workspace(ws_name=self.ws_name)
        project_steps.step_create_project(ws_name=self.ws_name, project_name=self.pro_ws_name)
        storage_steps.create_sc(sc_name=self.sc_name, expansion=self.allowVolumeExpansion)
        storage_steps.create_sc(sc_name=self.sc_name1, expansion=self.allowVolumeExpansion)
        storage_steps.step_create_volume(project_name=self.pro_ws_name, volume_name=self.volume_name,
                                         sc_name=self.sc_name1)
        project_steps.step_create_deploy(project_name=self.pro_ws_name, work_name=self.work_name,
                                         container_name=self.container_name,
                                         image=self.image, replicas=self.replicas, ports=self.ports,
                                         volumemount=self.volumemount,
                                         volume_info=self.volume_info, strategy=self.strategy)
        i = 0
        while i < 150:
            r = project_steps.step_get_volume(self.pro_ws_name, self.volume_name)
            if str(r.json()['items'][0]['status']['phase']) == 'Bound':
                break
            sleep(1)
            i = i + 1
        assert str(r.json()['items'][0]['status']['phase']) == 'Bound'

    def teardown_class(self):
        project_steps.step_delete_project(ws_name=self.ws_name, project_name=self.pro_ws_name)
        workspace_steps.step_delete_workspace(ws_name=self.ws_name)
        project_steps.step_delete_workload(project_name=self.pro_ws_name, type='deployments', work_name=self.work_name)
        project_steps.step_delete_volume(project_name=self.pro_ws_name, volume_name=self.volume_name)
        storage_steps.delete_sc(sc_name=self.sc_name)
        storage_steps.delete_sc(sc_name=self.sc_name1)
        storage_steps.delete_vsc(vsc_name=self.sc_name1)
        storage_steps.delete_vsc(vsc_name=self.sc_name)

    @allure.title('{title}')
    @pytest.mark.parametrize('id,url, params, data, story, title, method, severity, condition, except_result',
                             DoexcleByPandas().get_data_from_yaml('../data/storage.yaml'))
    def test_storage(self, id, url, params, data, story, title, method, severity, condition, except_result):
        allure.dynamic.story(story)  # 动态生成模块
        allure.dynamic.severity(severity)  # 动态生成用例等级
        targets = commonFunction.replace_str(url, params, data, title, condition, except_result,
                                             actual_value='${sc_name}', expect_value=self.sc_name)
        request_resource(targets[0], targets[1], targets[2], story, targets[3], method, severity,
                         targets[4], targets[5])

    @allure.story("存储-存储类")
    @allure.title('设置卷操作')
    @allure.severity('normal')
    def test_set_volume_operations(self, create_sc):
        ex = True
        allow_clone = 'false'
        allow_snapshot = 'false'
        storage_steps.set_volume_operations(create_sc, ex, allow_clone, allow_snapshot)
        # 查看存储类详细信息
        re = storage_steps.get_sc_info(create_sc)
        # 验证设置成功
        pytest.assume(re.json()['metadata']['annotations']['storageclass.kubesphere.io/allow-clone'] == 'false')
        pytest.assume(re.json()['metadata']['annotations']['storageclass.kubesphere.io/allow-snapshot'] == 'false')

    @allure.story("存储-存储类")
    @allure.title('设置默认类')
    @allure.severity('normal')
    def test_set_default_sc(self):
        ex1 = 'true'
        storage_steps.set_default_sc('local', 'false')
        storage_steps.set_default_sc(self.sc_name, ex1)
        # 查询存储类
        re = storage_steps.search_sc_by_name(self.sc_name)
        # 验证设置成功
        assert re.json()['items'][0]['metadata']['annotations'][
                   'storageclass.beta.kubernetes.io/is-default-class'] == 'true'
        storage_steps.set_default_sc(self.sc_name, 'false')
        storage_steps.set_default_sc('local', 'true')

    @allure.story("存储-存储类")
    @allure.title('存储类的存储卷信息')
    @allure.severity('normal')
    def test_sc_pvc(self, create_sc):
        ex = True
        # 创建存储卷
        volume_name = 'volume-' + str(get_random())
        storage_steps.step_create_volume(self.pro_ws_name, create_sc, volume_name)
        # 查询存储类已有存储卷信息
        re = storage_steps.search_volume_by_sc(create_sc)
        # 查询存储卷数量
        num = storage_steps.search_sc_by_name(create_sc).json()['items'][0]['metadata']['annotations'][
            'kubesphere.io/pvc-count']
        # 验证存储卷存在以及数量正确
        pytest.assume(re.json()['items'][0]['metadata']['name'] == volume_name)
        pytest.assume(num == '1')
        # 删除存储卷
        project_steps.step_delete_volume(self.pro_ws_name, volume_name)
        # 查询存储卷数量
        num1 = storage_steps.search_sc_by_name(create_sc).json()['items'][0]['metadata']['annotations'][
            'kubesphere.io/pvc-count']
        # 查询存储类已有存储卷信息
        re = storage_steps.search_volume_by_sc(create_sc)
        # 验证存储卷不存在以及数量正确
        pytest.assume(re.json()['totalItems'] == 0)
        pytest.assume(num1 == '0')

    @allure.story("存储-存储类")
    @allure.title('查询存储类已有存储卷')
    @allure.severity('normal')
    def test_search_pvc(self):
        # 创建存储卷
        volume_name = 'volume-' + str(get_random())
        storage_steps.step_create_volume(self.pro_ws_name, self.sc_name, volume_name)
        # 精确查询已有存储卷
        r = storage_steps.search_volume(self.sc_name, volume_name)
        assert r.json()['items'][0]['metadata']['name'] == volume_name
        # 模糊查询存在的存储卷
        re = storage_steps.search_volume(self.sc_name, 'volume')
        assert re.json()['items'][0]['metadata']['name'] == volume_name
        # 查询不存在的存储卷
        response = storage_steps.search_volume(self.sc_name, 'ff')
        assert response.json()['totalItems'] == 0
        # 删除存储卷
        project_steps.step_delete_volume(self.pro_ws_name, volume_name)

    @allure.story("存储-卷快照类")
    @allure.title('创建卷快照类')
    @allure.severity('normal')
    def test_create_vsc(self):
        vsc_name = 'vsc-' + str(get_random())
        diver = 'disk.csi.qingcloud.com'
        policy = 'Delete'
        # 创建卷快照类
        storage_steps.create_vsc(vsc_name, diver, policy)
        # 验证创建成功
        r = storage_steps.search_vsc_by_name(vsc_name)
        assert r.json()['totalItems'] == 1
        # 删除卷快照类
        storage_steps.delete_vsc(vsc_name)

    @allure.story("存储-卷快照类")
    @allure.title('编辑卷快照类信息')
    @allure.severity('normal')
    def test_set_vsc_info(self):
        vsc_name = self.sc_name
        r = storage_steps.search_vsc_by_name(vsc_name)
        driver = r.json()['items'][0]['driver']
        policy = r.json()['items'][0]['deletionPolicy']
        creationtime = r.json()['items'][0]['metadata']['creationTimestamp']
        time = r.json()['items'][0]['metadata']['managedFields'][0]['time']
        generation = r.json()['items'][0]['metadata']['generation']
        version = r.json()['items'][0]['metadata']['resourceVersion']
        uid = r.json()['items'][0]['metadata']['uid']
        alias_name = 'test-alias-name'
        des = 'test-describe'
        # 设置别名和描述信息
        storage_steps.set_vsc(vsc_name, driver, policy, creationtime, time,
                              generation, version, uid, alias_name, des)
        # 验证别名设置成功
        res = storage_steps.search_vsc_by_name(vsc_name)
        pytest.assume(res.json()['items'][0]['metadata']['annotations']['kubesphere.io/alias-name'] == alias_name)
        # 验证描述信息设置成功
        pytest.assume(res.json()['items'][0]['metadata']['annotations']['kubesphere.io/description'] == des)

    @allure.story("存储-卷快照类")
    @allure.title('验证卷快照类的卷快照数量')
    @allure.severity('normal')
    def test_get_vs_by_vsc(self):
        vs_name = 'snapshot-' + str(get_random())
        vsc_name = self.sc_name1
        volume_name = self.volume_name
        i = 0
        # 创建卷快照
        storage_steps.create_volume_snapshots(self.pro_ws_name, vs_name, vsc_name, volume_name)
        # 验证存储卷快照状态为准备就绪，最长等待时间为150s
        while i < 150:
            r1 = storage_steps.search_vs_by_name(vs_name)
            # 存储卷快照的状态为布尔值，故先将结果转换我字符类型
            try:
                if str(r1.json()['items'][0]['status']['readyToUse']) == 'True':
                    break
            except Exception as e:
                print(e)
            sleep(1)
            i = i + 1
        assert str(r1.json()['items'][0]['status']['readyToUse']) == 'True'
        # 查询卷快照类
        r = storage_steps.search_vsc_by_name(vsc_name)
        # 判断快照数量
        assert r.json()['items'][0]['metadata']['annotations']['kubesphere.io/snapshot-count'] == '1'
        # 删除已有卷快照
        storage_steps.delete_vs(self.pro_ws_name, vs_name)
        j = 0
        while j < 150:
            r2 = storage_steps.search_vs_by_name(vs_name)
            if r2.json()['totalItems'] == 0:
                break
            sleep(1)
            j = j + 1
        assert r2.json()['totalItems'] == 0
        # 查询卷快照类
        r = storage_steps.search_vsc_by_name(vsc_name)
        # 判断快照数量
        assert r.json()['items'][0]['metadata']['annotations']['kubesphere.io/snapshot-count'] == '0'

    @allure.story("存储-卷快照类")
    @allure.title('查询卷快照类的卷快照')
    @allure.severity('normal')
    def test_search_vs_by_vsc(self):
        vs_name = 'snapshot-' + str(get_random())
        vsc_name = self.sc_name1
        volume_name = self.volume_name
        i = 0
        # 创建卷快照
        storage_steps.create_volume_snapshots(self.pro_ws_name, vs_name, vsc_name, volume_name)
        # 验证存储卷快照状态为准备就绪，最长等待时间为150s
        while i < 150:
            r1 = storage_steps.search_vs_by_name(vs_name)
            # 存储卷快照的状态为布尔值，故先将结果转换我字符类型
            try:
                if str(r1.json()['items'][0]['status']['readyToUse']) == 'True':
                    break
            except Exception as e:
                print(e)
            sleep(1)
            i = i + 1
        assert str(r1.json()['items'][0]['status']['readyToUse']) == 'True'
        # 查询快照类的快照
        re = storage_steps.get_vs_for_vsc(vsc_name)
        # 验证名称正确
        assert re.json()['items'][0]['metadata']['name'] == vs_name
        # 精确查询已有快照
        res1 = storage_steps.search_vs_for_vsc(vsc_name, vs_name)
        assert res1.json()['items'][0]['metadata']['name'] == vs_name
        # 模糊查询已有快照
        res2 = storage_steps.search_vs_for_vsc(vsc_name, 'snapshot-')
        assert res2.json()['items'][0]['metadata']['name'] == vs_name
        # 查询不存在的快照
        res2 = storage_steps.search_vs_for_vsc(vsc_name, 'kk')
        assert res2.json()['totalItems'] == 0
        # 删除卷快照
        storage_steps.delete_vs(self.pro_ws_name, vs_name)
        j = 0
        while j < 150:
            r2 = storage_steps.search_vs_by_name(vs_name)
            if r2.json()['totalItems'] == 0:
                break
            sleep(1)
            j = j + 1
        assert r2.json()['totalItems'] == 0

    @allure.story("存储-卷快照")
    @allure.title('创建快照')
    @allure.severity('normal')
    def test_create_snapshots(self):
        vs_name = 'snapshot-' + str(get_random())
        vsc_name = self.sc_name1
        volume_name = self.volume_name
        i = 0
        # 创建卷快照
        storage_steps.create_volume_snapshots(self.pro_ws_name, vs_name, vsc_name, volume_name)
        # 验证存储卷快照状态为准备就绪，最长等待时间为150s
        while i < 150:
            r1 = storage_steps.search_vs_by_name(vs_name)
            # 存储卷快照的状态为布尔值，故先将结果转换我字符类型
            try:
                if str(r1.json()['items'][0]['status']['readyToUse']) == 'True':
                    break
            except Exception as e:
                print(e)
            sleep(1)
            i = i + 1
        print("创建存储卷快照耗时:" + str(i) + '秒')
        assert str(r1.json()['items'][0]['status']['readyToUse']) == 'True'
        storage_steps.delete_vs(self.pro_ws_name, vsc_name)
        # 删除卷快照
        storage_steps.delete_vs(self.pro_ws_name, vs_name)
        j = 0
        while j < 150:
            r2 = storage_steps.search_vs_by_name(vs_name)
            if r2.json()['totalItems'] == 0:
                break
            sleep(1)
            j = j + 1
        assert r2.json()['totalItems'] == 0

    @allure.story("存储-卷快照")
    @allure.title('创建同名的快照')
    @allure.severity('normal')
    def test_create_same_snapshots(self):
        vs_name = 'snapshot-' + str(get_random())
        vsc_name = self.sc_name1
        volume_name = self.volume_name
        i = 0
        # 创建卷快照
        storage_steps.create_volume_snapshots(self.pro_ws_name, vs_name, vsc_name, volume_name)
        # 验证存储卷快照状态为准备就绪，最长等待时间为150s
        while i < 150:
            r1 = storage_steps.search_vs_by_name(vs_name)
            # 存储卷快照的状态为布尔值，故先将结果转换我字符类型
            try:
                if str(r1.json()['items'][0]['status']['readyToUse']) == 'True':
                    break
            except Exception as e:
                print(e)
            sleep(1)
            i = i + 1
        print("创建存储卷快照耗时:" + str(i) + '秒')
        # 再次创建同名的快照
        res = storage_steps.create_volume_snapshots(self.pro_ws_name, vs_name, vsc_name, volume_name)
        assert res.json()['message'] == 'volumesnapshots.snapshot.storage.k8s.io "' + vs_name + '" already exists'
        # 删除已有卷快照
        storage_steps.delete_vs(self.pro_ws_name, vs_name)
        j = 0
        while j < 150:
            r2 = storage_steps.search_vs_by_name(vs_name)
            if r2.json()['totalItems'] == 0:
                break
            sleep(1)
            j = j + 1
        assert r2.json()['totalItems'] == 0

    @allure.story("存储-卷快照")
    @allure.title('查询卷快照')
    @allure.severity('normal')
    def test_search_snapshots(self):
        vs_name = 'snapshot-' + str(get_random())
        vsc_name = self.sc_name1
        volume_name = self.volume_name
        i = 0
        # 创建卷快照
        storage_steps.create_volume_snapshots(self.pro_ws_name, vs_name, vsc_name, volume_name)
        # 验证存储卷快照状态为准备就绪，最长等待时间为150s
        while i < 150:
            r1 = storage_steps.search_vs_by_name(vs_name)
            # 存储卷快照的状态为布尔值，故先将结果转换我字符类型
            try:
                if str(r1.json()['items'][0]['status']['readyToUse']) == 'True':
                    break
            except Exception as e:
                print(e)
            sleep(1)
            i = i + 1
        print("创建存储卷快照耗时:" + str(i) + '秒')
        # 精确查询存在的快照
        r = storage_steps.search_vs_by_name(vs_name)
        assert r.json()['items'][0]['metadata']['name'] == vs_name
        # 模糊查询存在的快照
        r1 = storage_steps.search_vs_by_name('snapshot')
        assert r1.json()['items'][0]['metadata']['name'] == vs_name
        # 查询不存在的快照
        r2 = storage_steps.search_vs_by_name('kk')
        assert r2.json()['totalItems'] == 0
        # 删除已有卷快照
        storage_steps.delete_vs(self.pro_ws_name, vs_name)
        j = 0
        while j < 150:
            r2 = storage_steps.search_vs_by_name(vs_name)
            if r2.json()['totalItems'] == 0:
                break
            sleep(1)
            j = j + 1
        assert r2.json()['totalItems'] == 0

    @allure.story("存储-卷快照")
    @allure.title('使用卷快照创建存储卷')
    @allure.severity('normal')
    def test_create_volume_by_snapshots(self):
        vs_name = 'snapshot-' + str(get_random())
        vsc_name = self.sc_name1
        volume_name = self.volume_name
        volume = 'pvc-' + str(get_random())
        # 获取存储类
        sc_name = storage_steps.search_volume_by_name(volume_name).json()['items'][0]['spec']['storageClassName']
        i = 0
        # 创建卷快照
        storage_steps.create_volume_snapshots(self.pro_ws_name, vs_name, vsc_name, volume_name)
        # 验证存储卷快照状态为准备就绪，最长等待时间为150s
        while i < 150:
            r1 = storage_steps.search_vs_by_name(vs_name)
            # 存储卷快照的状态为布尔值，故先将结果转换我字符类型
            try:
                if str(r1.json()['items'][0]['status']['readyToUse']) == 'True':
                    break
            except Exception as e:
                print(e)
            sleep(1)
            i = i + 1
        print("创建存储卷快照耗时:" + str(i) + '秒')
        # 创建存储卷
        storage_steps.create_volumne_by_vs(self.pro_ws_name, volume, sc_name)
        # 查询存储卷已存在，验证创建成功
        res = storage_steps.search_volume_by_name(volume)
        assert res.json()['items'][0]['status']['phase'] == 'Pending'
        # 删除存储卷
        project_steps.step_delete_volume(self.pro_ws_name, volume)
        # 删除已有卷快照
        storage_steps.delete_vs(self.pro_ws_name, vs_name)
        j = 0
        while j < 150:
            r2 = storage_steps.search_vs_by_name(vs_name)
            if r2.json()['totalItems'] == 0:
                break
            sleep(1)
            j = j + 1
        assert r2.json()['totalItems'] == 0

    @allure.story("存储-卷快照")
    @allure.title('使用卷快照创建同名存储卷')
    @allure.severity('normal')
    def test_create_same_volume_by_snapshots(self):
        vs_name = 'snapshot-' + str(get_random())
        vsc_name = self.sc_name1
        volume_name = self.volume_name
        # 获取存储类
        sc_name = storage_steps.search_volume_by_name(volume_name).json()['items'][0]['spec']['storageClassName']
        i = 0
        # 创建卷快照
        storage_steps.create_volume_snapshots(self.pro_ws_name, vs_name, vsc_name, volume_name)
        # 验证存储卷快照状态为准备就绪，最长等待时间为150s
        while i < 150:
            r1 = storage_steps.search_vs_by_name(vs_name)
            # 存储卷快照的状态为布尔值，故先将结果转换我字符类型
            try:
                if str(r1.json()['items'][0]['status']['readyToUse']) == 'True':
                    break
            except Exception as e:
                print(e)
            sleep(1)
            i = i + 1
        print("创建存储卷快照耗时:" + str(i) + '秒')
        # 创建存储卷
        res = storage_steps.create_volumne_by_vs(self.pro_ws_name, volume_name, sc_name)
        # 验证报错信息正确
        assert res.json()['message'] == 'persistentvolumeclaims "'+volume_name+'" already exists'
        # 删除已有卷快照
        storage_steps.delete_vs(self.pro_ws_name, vs_name)
        j = 0
        while j < 150:
            r2 = storage_steps.search_vs_by_name(vs_name)
            if r2.json()['totalItems'] == 0:
                break
            sleep(1)
            j = j + 1
        assert r2.json()['totalItems'] == 0