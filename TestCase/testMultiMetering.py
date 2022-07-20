import pytest
import allure
import sys
from common import commonFunction
from step import multi_meter_steps
import random

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用


@allure.feature('计量计费')
@pytest.mark.skipif(commonFunction.check_multi_cluster() is False, reason='单集群环境下不执行')
class TestMetering(object):
    # 如果为单集群环境，则不会collect该class的所有用例。 __test__ = False
    __test__ = commonFunction.check_multi_cluster()

    @allure.story('集群资源消费情况')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('step, title',
                             [('3600', '查看集群截止到昨天的消费情况，时间间隔为1小时'),
                              ('7200', '查看集群截止到昨天的消费情况，时间间隔为2小时'),
                              ('14400', '查看集群截止到昨天的消费情况，时间间隔为4小时'),
                              ('28800', '查看集群截止到昨天的消费情况，时间间隔为7小时'),
                              ('86400', '查看集群截止到昨天的消费情况，时间间隔为1天')
                              ])
    def test_get_cluster_consumption_by_yesterday(self, step, title):
        # 获取多集群环境的集群名称
        response = multi_meter_steps.step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取当前日期的时间戳
            now_timestamp = commonFunction.get_timestamp()
            # 获取7天之前的时间戳
            before_timestamp = commonFunction.get_before_timestamp_day(7)
            # 获取截止到昨天的最近7天的消费历史
            re = multi_meter_steps.step_get_cluster_consumption_history(type='cluster', start_time=before_timestamp,
                                                                        end_time=now_timestamp,
                                                                        step=step, cluster_name=cluster_name)
            # 获取查询结果的数据类型
            for j in range(0, 5):
                try:
                    result_type = re.json()['results'][j]['data']['resultType']
                    # 验证数据类型为matrix
                    assert result_type == 'matrix'
                    # 获取趋势图数据的时间间隔
                    time_1 = re.json()['results'][j]['data']['result'][0]['values'][0][0]
                    time_2 = re.json()['results'][j]['data']['result'][0]['values'][1][0]
                    time_interval = time_2 - time_1
                    # 验证时间间隔正确
                    assert time_interval == int(step)
                except Exception as e:
                    print(e)
                    print('集群无资源消费信息')
                    break

    @allure.story('集群资源消费情况')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('metric_name, title',
                             [('meter_node_cpu_usage', '查看所有节点的cpu消费情况'),
                              ('meter_node_memory_usage_wo_cache', '查看所有节点的内存消费情况'),
                              ('meter_node_pvc_bytes_total', '查看所有节点的pvc消费情况'),
                              ('meter_node_net_bytes_received', '查看所有节点的网络流入消费情况'),
                              ('meter_node_net_bytes_transmitted', '查看所有节点的网络流出消费情况')
                              ])
    def test_get_node_consumption(self, metric_name, title):
        # 获取多集群环境的集群名称
        response = multi_meter_steps.step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询集群的节点信息
            re = multi_meter_steps.step_get_node_info(cluster_name)
            # 获取集群节点的数量
            count = re.json()['totalItems']
            # 获取节点的名称
            for j in range(0, count):
                try:
                    name = re.json()['items'][j]['metadata']['name']
                    # 查看节点的消费信息
                    r = multi_meter_steps.step_get_node_consumption(metric_name, name)
                    # 获取metric_name
                    metric = r.json()['results'][j]['metric_name']
                    # 验证metric正确
                    assert metric == metric_name
                except Exception as e:
                    print(e)
                    print('节点无资源消费信息')
                    break

    @allure.story('集群资源消费情况')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('step, title',
                             [('3600', '查看所有节点截止到昨天的消费情况，时间间隔为1小时'),
                              ('7200', '查看所有节点截止到昨天的消费情况，时间间隔为2小时'),
                              ('14400', '查看所有节点截止到昨天的消费情况，时间间隔为4小时'),
                              ('28800', '查看所有节点截止到昨天的消费情况，时间间隔为8小时'),
                              ('86400', '查看所有节点截止到昨天的消费情况，时间间隔为1天')
                              ])
    def test_get_node_consumption_by_yesterday(self, step, title):
        # 获取多集群环境的集群名称
        response = multi_meter_steps.step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取当前日期的时间戳
            now_timestamp = commonFunction.get_timestamp()
            # 获取7天之前的时间戳
            before_timestamp = commonFunction.get_before_timestamp_day(7)
            # 查询集群的节点信息
            re = multi_meter_steps.step_get_node_info(cluster_name)
            # 获取集群节点的数量
            count = re.json()['totalItems']
            # 获取节点的名称
            for j in range(0, count):
                name = re.json()['items'][j]['metadata']['name']
                # 获取截止到昨天的最近7天的消费历史
                r = multi_meter_steps.step_get_node_consumption_history(cluster_name=cluster_name, start_time=before_timestamp,
                                                                        end_time=now_timestamp, step=step, name=name)
                # 获取查询结果的数据类型
                for k in range(0, 5):
                    try:
                        result_type = r.json()['results'][k]['data']['resultType']
                        # 验证数据类型为matrix
                        assert result_type == 'matrix'
                        # 获取趋势图数据的时间间隔
                        time_1 = r.json()['results'][k]['data']['result'][0]['values'][0][0]
                        time_2 = r.json()['results'][k]['data']['result'][0]['values'][1][0]
                        time_interval = time_2 - time_1
                        # 验证时间间隔正确
                        assert time_interval == int(step)
                    except Exception as e:
                        print(e)
                        print('集群：' + cluster_name + ' 节点: ' + name + '无历史资源消费信息')
                        break

    @allure.story('集群资源消费情况')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('metric_name, title',
                             [('meter_pod_cpu_usage', '查看所有pod的cpu消费情况'),
                              ('meter_pod_memory_usage_wo_cache', '查看所有pod的内存消费情况'),
                              ('meter_pod_pvc_bytes_total', '查看所有pod的pvc消费情况'),
                              ('meter_pod_net_bytes_received', '查看所有pod的网络流入消费情况'),
                              ('meter_pod_net_bytes_transmitted', '查看所有pod的网络流出消费情况')
                              ])
    def test_get_pod_consumption(self, metric_name, title):
        # 获取多集群环境的集群名称
        response = multi_meter_steps.step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询集群的节点信息
            re = multi_meter_steps.step_get_node_info(cluster_name)
            # 获取集群节点的数量
            count = re.json()['totalItems']
            # 获取节点的名称
            for j in range(0, count):
                try:
                    name = re.json()['items'][j]['metadata']['name']
                    # 查询pod的消费信息
                    r = multi_meter_steps.step_get_pod_consumption(cluster_name=cluster_name, node_name=name, metric=metric_name)
                    # 获取metric_name
                    metric = r.json()['results'][0]['metric_name']
                    # 验证metric正确
                    assert metric == metric_name
                except Exception as e:
                    print(e)
                    print('节点：' + name + '无pod资源消费信息')
                    break

    @allure.story('集群资源消费情况')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_pod_consumption_by_yesterday(self):
        step = random.choice(['3600', '7200', '14400', '28800', '86400'])
        title = '查看所有pod截止到昨天的消费情况，时间间隔为' + str(int(step)/60/60) + '小时'
        allure.dynamic.title(title)
        # 获取当前日期的时间戳
        now_timestamp = commonFunction.get_timestamp()
        # 获取7天之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp_day(7)
        # 获取多集群环境的集群名称
        response = multi_meter_steps.step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询集群所有的节点
            res = multi_meter_steps.step_get_node_info(cluster_name)
            # 获取集群的节点数量
            node_count = res.json()['totalItems']
            # 获取节点的名称
            for m in range(0, node_count):
                node_name = res.json()['items'][m]['metadata']['name']
                # 查询每个节点的pod信息
                re = multi_meter_steps.step_get_pod_info(cluster_name, node_name)
                # 获取每个节点的pod数量
                pod_count = re.json()['totalItems']
                for j in range(0, pod_count):
                    # 获取每个pod的名称
                    pod_name = re.json()['items'][j]['metadata']['name']
                    # 查询pod截止到昨天最近7天的消费情况
                    r = multi_meter_steps.step_get_pod_consumption_history(cluster_name, node_name, before_timestamp,
                                                                           now_timestamp, step, pod_name)
                    # 获取每个指标的消费历史数据的时间间隔
                    for k in range(0, 4):
                        try:
                            time_1 = r.json()['results'][k]['data']['result'][0]['values'][0][0]
                            time_2 = r.json()['results'][k]['data']['result'][0]['values'][1][0]
                            time_interval = time_2 - time_1
                            # 验证时间间隔正确
                            assert time_interval == int(step)
                        except Exception as e:
                            print(e)
                            print('集群：' + cluster_name + ' 节点' + node_name + ' pod:' + pod_name + ' 没有历史消费数据')
                            break

    @allure.story('企业空间资源消费情况')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('step, title',
                             [('3600', '查看所有企业空间截止到昨天的消费情况，时间间隔为1小时'),
                              ('7200', '查看所有企业空间截止到昨天的消费情况，时间间隔为2小时'),
                              ('14400', '查看所有企业空间截止到昨天的消费情况，时间间隔为4小时'),
                              ('28800', '查看所有企业空间截止到昨天的消费情况，时间间隔为7小时'),
                              ('86400', '查看所有企业空间截止到昨天的消费情况，时间间隔为1天')
                              ])
    def test_get_workspace_consumption_by_yesterday(self, step, title):
        # 获取当前日期的时间戳
        now_timestamp = commonFunction.get_timestamp()
        # 获取7天之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp_day(7)
        # 查询企业空间信息
        response = multi_meter_steps.step_get_workspace_info()
        # 获取企业空间的数量
        ws_count = response.json()['totalItems']
        # 获取企业空间的名称
        for i in range(0, ws_count):
            ws_name = response.json()['items'][i]['metadata']['name']
            # 获取企业空间的集群情况
            if ws_name != 'system-workspace':
                cluster_count = len(response.json()['items'][i]['spec']['placement']['clusters'])
                for k in range(0, cluster_count):
                    cluster_name = response.json()['items'][i]['spec']['placement']['clusters'][k]['name']
                    # 查询企业空间的历史消费信息
                    r = multi_meter_steps.step_get_workspace_consumption_history(cluster_name, ws_name, before_timestamp,
                                                                                 now_timestamp, step)
                    # 查询每个指标的消费历史数据
                    for j in range(0, 5):
                        try:
                            # 获取数据类型
                            result_type = r.json()['results'][j]['data']['resultType']
                            # 验证数据类型为matrix
                            assert result_type == 'matrix'
                            # 获取并验证数据的时间间隔
                            time_1 = r.json()['results'][j]['data']['result'][0]['values'][0][0]
                            time_2 = r.json()['results'][j]['data']['result'][0]['values'][1][0]
                            time_interval = time_2 - time_1
                            assert time_interval == int(step)
                        except Exception as e:
                            print(e)
                            print('企业空间：' + ws_name + ' 在集群 ' + cluster_name + ' 没有资源历史消费信息')
                            break
            else:
                # 获取多集群环境的集群名称
                response = multi_meter_steps.step_get_cluster()
                # 获取集群的数量
                cluster_count = response.json()['totalItems']
                for n in range(0, cluster_count):
                    # 获取每个集群的名称
                    cluster_name = response.json()['items'][n]['metadata']['name']
                    r = multi_meter_steps.step_get_workspace_consumption_history(cluster_name, ws_name, before_timestamp,
                                                                                 now_timestamp, step)
                    # 查询每个指标的消费历史数据
                    for j in range(0, 5):
                        try:
                            # 获取数据类型
                            result_type = r.json()['results'][j]['data']['resultType']
                            # 验证数据类型为matrix
                            assert result_type == 'matrix'
                            # 获取并验证数据的时间间隔
                            time_1 = r.json()['results'][j]['data']['result'][0]['values'][0][0]
                            time_2 = r.json()['results'][j]['data']['result'][0]['values'][1][0]
                            time_interval = time_2 - time_1
                            assert time_interval == int(step)
                        except Exception as e:
                            print(e)
                            print('企业空间：' + ws_name + ' 在集群 ' + cluster_name + ' 没有资源历史消费信息')
                            break

    @allure.story('企业空间资源消费情况')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('metric, title',
                             [('meter_namespace_cpu_usage', '按cpu查看企业空间所有项目最近1h的消费情况'),
                              ('meter_namespace_memory_usage_wo_cache', '按memoory查看企业空间所有项目最近1h的消费情况'),
                              ('meter_namespace_pvc_bytes_total', '按pvc查看企业空间所有项目最近1h的消费情况'),
                              ('meter_namespace_net_bytes_received', '按网络流入查看企业空间所有项目最近1h的消费情况'),
                              ('meter_namespace_net_bytes_transmitted', '按网络流出查看企业空间所有项目最近1h的消费情况'),
                              ])
    def test_get_project_consumption(self, metric, title):
        # 查询企业空间信息
        response = multi_meter_steps.step_get_workspace_info()
        # 获取企业空间的数量
        ws_count = response.json()['totalItems']
        # 获取企业空间的名称
        for i in range(0, ws_count):
            ws_name = response.json()['items'][i]['metadata']['name']
            if ws_name != 'system-workspace':
                cluster_count = len(response.json()['items'][i]['spec']['placement']['clusters'])
                for k in range(0, cluster_count):
                    cluster_name = response.json()['items'][i]['spec']['placement']['clusters'][k]['name']
                    # 查询每个企业空间的项目信息
                    re = multi_meter_steps.step_get_project_info(cluster_name, ws_name)
                    # 获取项目的数量
                    project_count = re.json()['totalItems']
                    project_names = []
                    # 获取企业空间中项目的名称
                    for j in range(0, project_count):
                        project_name = re.json()['items'][j]['metadata']['name']
                        project_names.append(project_name)
                    # 查询每个项目最近1h的资源消费信息
                    if len(project_names) > 0:
                        r = multi_meter_steps.step_get_project_consumption(metric, project_names)
                        # 获取查询结果中的metric_name
                        metric_name = r.json()['results'][0]['metric_name']
                        # 验证metric_name正确
                        assert metric_name == metric
                    else:
                        print('企业空间：' + ws_name + '没有项目')
            else:
                # 获取多集群环境的集群名称
                response = multi_meter_steps.step_get_cluster()
                # 获取集群的数量
                cluster_count = response.json()['totalItems']
                for n in range(0, cluster_count):
                    # 获取每个集群的名称
                    cluster_name = response.json()['items'][n]['metadata']['name']
                    # 查询每个企业空间的项目信息
                    re = multi_meter_steps.step_get_project_info(cluster_name, ws_name)
                    # 获取项目的数量
                    project_count = re.json()['totalItems']
                    project_names = []
                    # 获取企业空间中项目的名称
                    for j in range(0, project_count):
                        project_name = re.json()['items'][j]['metadata']['name']
                        project_names.append(project_name)
                    # 查询每个项目最近1h的资源消费信息
                    if len(project_names) > 0:
                        r = multi_meter_steps.step_get_project_consumption(metric, project_names)
                        # 获取查询结果中的metric_name
                        metric_name = r.json()['results'][0]['metric_name']
                        # 验证metric_name正确
                        assert metric_name == metric
                    else:
                        print('企业空间：' + ws_name + '没有项目')

    @allure.story('企业空间资源消费情况')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('step, title',
                             [('3600', '查看所有企业空间的所有项目截止到昨天的消费情况，时间间隔为1小时'),
                              ('7200', '查看所有企业空间的所有项目截止到昨天的消费情况，时间间隔为2小时'),
                              ('14400', '查看所有企业空间的所有项目截止到昨天的消费情况，时间间隔为4小时'),
                              ('28800', '查看所有企业空间的所有项目截止到昨天的消费情况，时间间隔为7小时'),
                              ('86400', '查看所有企业空间的所有项目截止到昨天的消费情况，时间间隔为1天')
                              ])
    def test_get_project_consumption_by_yesterday(self, step, title):
        # 获取当前日期的时间戳
        now_timestamp = commonFunction.get_timestamp()
        # 获取7天之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp_day(7)
        # 查询企业空间信息
        response = multi_meter_steps.step_get_workspace_info()
        # 获取企业空间的数量
        ws_count = response.json()['totalItems']
        # 获取企业空间的名称
        for i in range(0, ws_count):
            ws_name = response.json()['items'][i]['metadata']['name']
            # 查询每个企业空间的项目信息
            if ws_name != 'system-workspace':
                cluster_count = len(response.json()['items'][i]['spec']['placement']['clusters'])
                for k in range(0, cluster_count):
                    cluster_name = response.json()['items'][i]['spec']['placement']['clusters'][k]['name']
                    re = multi_meter_steps.step_get_project_info(cluster_name, ws_name)
                    # 获取项目的数量
                    project_count = re.json()['totalItems']
                    # 获取企业空间中项目的名称
                    for j in range(0, project_count):
                        project_name = re.json()['items'][j]['metadata']['name']
                        # 查询项目截止到昨天最近7天的资源消费历史
                        r = multi_meter_steps.step_get_project_consumption_history(cluster_name, project_name,
                                                                                   before_timestamp, now_timestamp, step)
                        for m in range(1, 5):
                            try:
                                # 获取并验证查询结果中每个指标的数据类型
                                result_type = r.json()['results'][m]['data']['resultType']
                                assert result_type == 'matrix'
                                # 获取并验证查询结果中每个指标的时间间隔
                                time_1 = r.json()['results'][m]['data']['result'][0]['values'][0][0]
                                time_2 = r.json()['results'][m]['data']['result'][0]['values'][1][0]
                                time_interval = time_2 - time_1
                                assert time_interval == int(step)
                            except Exception as e:
                                print(e)
                                print('企业空间：' + ws_name + '的项目 ' + project_name + '没有历史消费信息')
                                break
            else:
                # 获取多集群环境的集群名称
                response = multi_meter_steps.step_get_cluster()
                # 获取集群的数量
                cluster_count = response.json()['totalItems']
                for n in range(0, cluster_count):
                    # 获取每个集群的名称
                    cluster_name = response.json()['items'][n]['metadata']['name']
                    re = multi_meter_steps.step_get_project_info(cluster_name, ws_name)
                    # 获取项目的数量
                    project_count = re.json()['totalItems']
                    # 获取企业空间中项目的名称
                    for j in range(0, project_count):
                        project_name = re.json()['items'][j]['metadata']['name']
                        # 查询项目截止到昨天最近7天的资源消费历史
                        r = multi_meter_steps.step_get_project_consumption_history(cluster_name, project_name,
                                                                                   before_timestamp, now_timestamp, step)
                        for m in range(1, 5):
                            try:
                                # 获取并验证查询结果中每个指标的数据类型
                                result_type = r.json()['results'][m]['data']['resultType']
                                assert result_type == 'matrix'
                                # 获取并验证查询结果中每个指标的时间间隔
                                time_1 = r.json()['results'][m]['data']['result'][0]['values'][0][0]
                                time_2 = r.json()['results'][m]['data']['result'][0]['values'][1][0]
                                time_interval = time_2 - time_1
                                assert time_interval == int(step)
                            except Exception as e:
                                print(e)
                                print('企业空间：' + ws_name + '的项目 ' + project_name + '没有历史消费信息')
                                break

    @allure.story('企业空间资源消费情况')
    @allure.title('查询所有项目最近1h消费的资源信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_hierarchy_consumption(self):
        # 查询企业空间信息
        response = multi_meter_steps.step_get_workspace_info()
        # 获取企业空间的数量
        ws_count = response.json()['totalItems']
        # 获取企业空间的名称
        for i in range(0, ws_count):
            ws_name = response.json()['items'][i]['metadata']['name']
            # 查询每个企业空间的项目信息
            if ws_name != 'system-workspace':
                cluster_count = len(response.json()['items'][i]['spec']['placement']['clusters'])
                for k in range(0, cluster_count):
                    cluster_name = response.json()['items'][i]['spec']['placement']['clusters'][k]['name']
                    re = multi_meter_steps.step_get_project_info(cluster_name, ws_name)
                    # 获取项目的数量
                    project_count = re.json()['totalItems']
                    # 获取企业空间中项目的名称
                    for j in range(0, project_count):
                        project_name = re.json()['items'][j]['metadata']['name']
                        # 查询最近1h消费的资源信息
                        r = multi_meter_steps.step_get_hierarchy_consumption(cluster_name, ws_name, project_name)
                        # 验证资源查询成功
                        assert r.status_code == 200
            else:
                # 获取多集群环境的集群名称
                response = multi_meter_steps.step_get_cluster()
                # 获取集群的数量
                cluster_count = response.json()['totalItems']
                for n in range(0, cluster_count):
                    # 获取每个集群的名称
                    cluster_name = response.json()['items'][n]['metadata']['name']
                    re = multi_meter_steps.step_get_project_info(cluster_name, ws_name)
                    # 获取项目的数量
                    project_count = re.json()['totalItems']
                    # 获取企业空间中项目的名称
                    for j in range(0, project_count):
                        project_name = re.json()['items'][j]['metadata']['name']
                        # 查询最近1h消费的资源信息
                        r = multi_meter_steps.step_get_hierarchy_consumption(cluster_name, ws_name, project_name)
                        # 验证资源查询成功
                        assert r.status_code == 200

    @allure.story('企业空间资源消费情况')
    @allure.title('{title}')
    @pytest.mark.parametrize('step, title',
                             [('3600', '查询所有项目下包含的资源截止到昨天的最近7天的资源消费历史数据，时间间隔为1小时'),
                              ('7200', '查询所有项目下包含的资源截止到昨天的最近7天的资源消费历史数据，时间间隔为2小时'),
                              ('14400', '查询所有项目下包含的资源截止到昨天的最近7天的资源消费历史数据，时间间隔为4小时'),
                              ('28800', '查询所有项目下包含的资源截止到昨天的最近7天的资源消费历史数据，时间间隔为7小时'),
                              ('86400', '查询所有项目下包含的资源截止到昨天的最近7天的资源消费历史数据，时间间隔为1天')
                              ])
    def test_get_hierarchy_consumption_history(self, step, title):
        # 获取当前日期的时间戳
        now_timestamp = commonFunction.get_timestamp()
        # 获取7天之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp_day(7)
        # 查询企业空间信息
        response = multi_meter_steps.step_get_workspace_info()
        # 获取企业空间的数量
        ws_count = response.json()['totalItems']
        # 获取企业空间的名称
        for i in range(0, ws_count):
            ws_name = response.json()['items'][i]['metadata']['name']
            # 查询每个企业空间的项目信息
            if ws_name != 'system-workspace':
                cluster_count = len(response.json()['items'][i]['spec']['placement']['clusters'])
                for g in range(0, cluster_count):
                    cluster_name = response.json()['items'][i]['spec']['placement']['clusters'][g]['name']
                    re = multi_meter_steps.step_get_project_info(cluster_name, ws_name)
                    # 获取项目的数量
                    project_count = re.json()['totalItems']
                    # 获取企业空间中项目的名称
                    for j in range(0, project_count):
                        project_name = re.json()['items'][j]['metadata']['name']
                        # 查询最近1h消费的资源信息
                        r = multi_meter_steps.step_get_hierarchy_consumption(cluster_name, ws_name, project_name)
                        hierarchy_list = ['apps', 'daemonsets', 'deployments', 'openpitrixs', 'statefulsets']
                        for k in hierarchy_list:
                            if r.json()[k] is not None:
                                hierarchy = r.json()[k]
                                for key in hierarchy.keys():
                                    # 查询资源截止到昨天的最近7天消费历史
                                    rep = multi_meter_steps.step_get_hierarchy_consumption_history(cluster_name, project_name,
                                                                                                   before_timestamp, now_timestamp,
                                                                                                   step, key, k)
                                    # 获取查询结果中所有指标的数据类型
                                    for m in range(0, 4):
                                        try:
                                            result_type = rep.json()['results'][m]['data']['resultType']
                                            # 验证数据类型正确
                                            assert result_type == 'matrix'
                                            # 获取并验证查询结果中每个指标的时间间隔
                                            time_1 = rep.json()['results'][m]['data']['result'][0]['values'][0][0]
                                            time_2 = rep.json()['results'][m]['data']['result'][0]['values'][1][0]
                                            time_interval = time_2 - time_1
                                            assert time_interval == int(step)
                                        except Exception as e:
                                            print(e)
                                            print('项目：' + project_name + ' 资源类型：' + k + ' 资源名称：' + key + ' 无历史消费信息')
                                            break
            else:
                # 获取多集群环境的集群名称
                response = multi_meter_steps.step_get_cluster()
                # 获取集群的数量
                cluster_count = response.json()['totalItems']
                for n in range(0, cluster_count):
                    # 获取每个集群的名称
                    cluster_name = response.json()['items'][n]['metadata']['name']
                    re = multi_meter_steps.step_get_project_info(cluster_name, ws_name)
                    # 获取项目的数量
                    project_count = re.json()['totalItems']
                    # 获取企业空间中项目的名称
                    for j in range(0, project_count):
                        project_name = re.json()['items'][j]['metadata']['name']
                        # 查询最近1h消费的资源信息
                        r = multi_meter_steps.step_get_hierarchy_consumption(cluster_name, ws_name, project_name)
                        hierarchy_list = ['apps', 'daemonsets', 'deployments', 'openpitrixs', 'statefulsets']
                        for k in hierarchy_list:
                            if r.json()[k] is not None:
                                hierarchy = r.json()[k]
                                for key in hierarchy.keys():
                                    # 查询资源截止到昨天的最近7天消费历史
                                    rep = multi_meter_steps.step_get_hierarchy_consumption_history(cluster_name, project_name,
                                                                                                   before_timestamp, now_timestamp,
                                                                                                   step, key, k)
                                    # 获取查询结果中所有指标的数据类型
                                    for m in range(0, 4):
                                        try:
                                            result_type = rep.json()['results'][m]['data']['resultType']
                                            # 验证数据类型正确
                                            assert result_type == 'matrix'
                                            # 获取并验证查询结果中每个指标的时间间隔
                                            time_1 = rep.json()['results'][m]['data']['result'][0]['values'][0][0]
                                            time_2 = rep.json()['results'][m]['data']['result'][0]['values'][1][0]
                                            time_interval = time_2 - time_1
                                            assert time_interval == int(step)
                                        except Exception as e:
                                            print(e)
                                            print('项目：' + project_name + ' 资源类型：' + k + ' 资源名称：' + key + ' 无历史消费信息')
                                            break