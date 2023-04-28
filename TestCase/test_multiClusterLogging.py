# -- coding: utf-8 --
import pytest
import allure
import sys
import time
import random
from common import commonFunction
from datetime import datetime
from step import toolbox_steps, multi_cluster_steps


sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用


@allure.feature('日志查询')
@pytest.mark.skipif(commonFunction.get_components_status_of_cluster('logging') is False, reason='集群未开启logging功能')
class TestLogSearch(object):
    __test__ = commonFunction.check_multi_cluster()
    cluster_host_name = ''

    def setup_class(self):
        # 获取host集群的名称
        self.cluster_host_name = multi_cluster_steps.step_get_host_cluster_name()

    @allure.story('日志总量')
    @allure.title('验证当天的日志总量与最近12小时的日志总量关系正确')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_total_logs(self):
        # 获取当前时间的10位时间戳
        now_time = datetime.now()
        now_timestamp = str(datetime.timestamp(now_time))[0:10]
        # 获取当前日期的时间戳
        day_timestamp = commonFunction.get_timestamp()
        # 查询当天的日志总量信息
        response = toolbox_steps.step_get_log(day_timestamp, now_timestamp, self.cluster_host_name)
        # 获取收集日志的容器数量
        pod_count = response.json()['statistics']['containers']
        # 获取收集到的日志数量
        log_counts = response.json()['statistics']['logs']
        # 验证容器数量大于0
        with pytest.assume:
            assert pod_count > 0
        # 查询最近12小时的日志变化趋势
        interval = '30m'   # 时间间隔 30分钟
        # 获取12小时之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp(now_time, 720)
        re = toolbox_steps.step_get_logs_trend(before_timestamp, now_timestamp, interval, self.cluster_host_name)
        # 获取最近12小时的日志总量
        logs_count = re.json()['histogram']['total']
        # 验证今日日志总量和最近12小时日志总量的关系,获取当前日期
        today = commonFunction.get_today()
        # 获取当天12点的时间戳
        tamp = commonFunction.get_custom_timestamp(today, '12:00:00')
        if int(now_timestamp) > int(tamp):   # 如果当前时间大于12点，则当天的日志总数大于等于最近12小时的日志总数
            assert log_counts >= logs_count
        elif int(now_timestamp) < int(tamp):  # 如果当前时间小于12点，则当天的日志总数小于等于最近12小时的日志总数
            assert logs_count >= log_counts
        else:                                # 如果当前时间等于12点，则当天的日志总数等于最近12小时的日志总数
            assert logs_count == log_counts

    @allure.story('日志总量')
    @allure.title('验证最近 12 小时日志总量正确')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_logs_12h(self):
        # 时间间隔,单位是秒
        interval = '30m'
        # 获取当前时间的10位时间戳
        now_time = datetime.now()
        now_timestamp = str(datetime.timestamp(now_time))[0:10]
        # 获取12小时之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp(now_time, 720)
        # 查询最近 12 小时日志总数变化趋势
        response = toolbox_steps.step_get_logs_trend(before_timestamp, now_timestamp, interval, self.cluster_host_name)
        # 获取日志总量
        logs_count = response.json()['histogram']['total']
        # 获取日志趋势图中的横坐标数量
        count = len(response.json()['histogram']['histograms'])
        # 获取日志趋势图中的每个时间段的日志数量之和
        logs_count_actual = 0
        for i in range(0, count):
            number = response.json()['histogram']['histograms'][i]['count']
            logs_count_actual += number
        # 验证接口返回的日志总数和趋势图中日志的总数一致
        assert logs_count == logs_count_actual

    @allure.story('日志总量')
    @allure.title('查询最近 12 小时日志总数变化趋势,验证时间间隔正确')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_logs_trend(self):
        # 时间间隔
        interval = '30m'
        # 获取当前时间的10位时间戳
        now_time = datetime.now()
        now_timestamp = str(datetime.timestamp(now_time))[0:10]
        # 获取12小时之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp(now_time, 720)
        # 查询最近 12 小时日志总数变化趋势
        response = toolbox_steps.step_get_logs_trend(before_timestamp, now_timestamp, interval, self.cluster_host_name)
        # 获取查询结果数据中的时间间隔
        time_1 = response.json()['histogram']['histograms'][0]['time']
        time_2 = response.json()['histogram']['histograms'][1]['time']
        time_interval = (time_2 - time_1) / 1000 / 60  # 换算成分钟
        # 验证时间间隔正确
        assert time_interval == int(interval[:2])

    @allure.story('日志查询规则')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(('search_rule', 'title'),
                             [('namespaces=kubesphere', '按项目精确查询日志趋势'),
                              ('log_query=error', '按关键字查询日志趋势'),
                              ('workloads=ks', '按工作负载精确查询日志趋势'),
                              ('pods=ks', '按容器组精确查询日志趋势'),
                              ('containers=ks', '按容器精确查询日志趋势'),
                              ('namespace_query=kubesphere', '按项目精确查询日志趋势'),
                              ('workload_query=ks', '按工作负载精确查询日志趋势'),
                              ('pod_query=ks', '按容器组精确查询日志趋势'),
                              ('container_query=ks', '按容器精确查询日志趋势')
                              ])
    def test_get_logs_trend_by_search(self, search_rule, title):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 按不同条件查询日志
        response = toolbox_steps.step_get_logs_trend_by_search(search_rule, now_timestamp, self.cluster_host_name)
        # 获取查询结果中的总日志条数
        log_count = response.json()['histogram']['total']
        # 验证查询成功
        assert log_count >= 0

    @allure.story('日志查询规则')
    @allure.title('按关键字查询日志的详情信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_logs_by_keyword(self):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 按关键字查询日志详情信息
        response = toolbox_steps.step_get_logs_by_keyword('error', now_timestamp, self.cluster_host_name)
        # 获取查询到的日志数量
        logs_count = response.json()['query']['total']
        # 验证查询成功
        assert logs_count >= 0

    @allure.story('日志查询规则')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(('query_rule', 'title'),
                             [('Exact Query', '按项目精确查询日志的详情信息'),
                              ('Fuzzy Query', '按项目模糊查询日志的详情信息')
                              ])
    def test_get_logs_by_project(self, query_rule, title):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 按项目查询日志详情信息
        response = toolbox_steps.step_get_logs_by_project(query_rule, 'kube', now_timestamp, self.cluster_host_name)
        # 获取查询到的日志数量
        logs_count = response.json()['query']['total']
        # 验证查询成功
        assert logs_count >= 0

    @allure.story('日志查询规则')
    @allure.title('{title}')
    @pytest.mark.parametrize(('query_rule', 'title'),
                             [('Exact Query', '按工作负载精确查询日志的详情信息'),
                              ('Fuzzy Query', '按工作负载模糊查询日志的详情信息')
                              ])
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_logs_by_workload(self, query_rule, title):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 按工作负载查询日志详情信息
        response = toolbox_steps.step_get_logs_by_workload(query_rule, 'kube', now_timestamp, self.cluster_host_name)
        # 获取查询到的日志数量
        logs_count = response.json()['query']['total']
        # 验证查询成功
        assert logs_count >= 0

    @allure.story('日志查询规则')
    @allure.title('{title}')
    @pytest.mark.parametrize(('query_rule', 'title'),
                             [('Exact Query', '按容器组精确查询日志的详情信息'),
                              ('Fuzzy Query', '按容器组模糊查询日志的详情信息')
                              ])
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_logs_by_pod(self, query_rule, title):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 按容器组查询日志详情信息
        response = toolbox_steps.step_get_logs_by_pod(query_rule, 'kube', now_timestamp, self.cluster_host_name)
        # 获取查询到的日志数量
        logs_count = response.json()['query']['total']
        # 验证查询成功
        assert logs_count >= 0

    @allure.story('日志查询规则')
    @allure.title('{title}')
    @pytest.mark.parametrize(('query_rule', 'title'),
                             [('Exact Query', '按容器精确查询日志的详情信息'),
                              ('Fuzzy Query', '按容器模糊查询日志的详情信息')
                              ])
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_logs_by_container(self, query_rule, title):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 按容器查询日志详情信息
        response = toolbox_steps.step_get_logs_by_container(query_rule, 'kube', now_timestamp, self.cluster_host_name)
        # 获取查询到的日志数量
        logs_count = response.json()['query']['total']
        # 验证查询成功
        assert logs_count >= 0

    @allure.story('日志查询规则')
    @allure.title('{title}')
    @pytest.mark.parametrize(('limit', 'interval', 'title'),
                             [(10, '1m', '按时间范围查询最近10分钟日志的详情信息'),
                              (180, '6m', '按容器模糊查询最近3小时日志的详情信息'),
                              (1440, '48m', '按容器模糊查询最近一天日志的详情信息')
                              ])
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_logs_by_time_limit(self, limit, interval, title):
        # 获取当前时间的10位时间戳（结束时间）
        now_time = datetime.now()
        now_timestamp = str(datetime.timestamp(now_time))[0:10]
        # 获取开始时间
        start_time = commonFunction.get_before_timestamp(now_time, limit)
        # 按时间范围查询容器日志
        res = toolbox_steps.step_get_logs_by_time(interval, start_time, now_timestamp, self.cluster_host_name)
        log_num = res.json()['query']['total']
        # 验证查询成功
        assert log_num >= 0

    @allure.story("集群设置/日志接收器")
    @allure.title('查看日志接收器中的容器日志')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_log_receiver_log(self):
        # 查询日志接收器/容器日志
        response = multi_cluster_steps.step_get_log_receiver(self.cluster_host_name, 'logging')
        # 获取日志接收器的数量
        log_receiver_num = len(response.json()['items'])
        # 如果存在日志收集器则执行后续操作
        if log_receiver_num > 0:
            # 获取接收器类型和启用状态
            component = response.json()['items'][0]['metadata']['labels']['logging.kubesphere.io/component']
            enabled = response.json()['items'][0]['metadata']['labels']['logging.kubesphere.io/enabled']
            # 校验接收器类型和启用状态，启用状态默认为开启
            with pytest.assume:
                assert component == 'logging'
                assert enabled == 'true'
        else:
            print('日志接收器不存在，无法执行后续操作')

    @allure.story('集群设置/日志接收器')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('type, log_type, title',
                             [('fluentd', 'logging', '为容器日志添加日志接收器fluentd，并验证添加成功'),
                              ('kafka', 'logging', '为容器日志添加日志接收器kafka，并验证添加成功'),
                              ('es', 'logging', '为容器日志添加日志接收器elasticsearch，并验证添加成功')
                              ])
    def test_add_log_receiver_logging(self, type, log_type, title):
        # 添加日志收集器
        log_receiver_name = 'test' + str(commonFunction.get_random()) + '-' + type
        multi_cluster_steps.step_add_log_receiver(self.cluster_host_name, type, log_type, log_receiver_name)
        # 查看日志收集器
        response = multi_cluster_steps.step_get_log_receiver(self.cluster_host_name, log_type)
        # 获取日志收集器的数量
        log_receiver_num = len(response.json()['items'])
        # 获取所有日志收集器的名称
        log_receiver_actual = []
        for i in range(log_receiver_num):
            log_receiver_actual.append(response.json()['items'][i]['metadata']['name'])
        # 验证日志接收器添加成功
        with pytest.assume:
            assert log_receiver_name in log_receiver_actual
        # 删除创建的日志接收器
        multi_cluster_steps.step_delete_log_receiver(self.cluster_host_name, log_receiver_name)

    @allure.story('集群设置/日志接收器')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('type, log_type, title',
                             [('fluentd', 'logging', '将容器日志的日志接收器fluentd状态更改为false'),
                              ('es', 'logging', '将容器日志的日志接收器es状态更改为false'),
                              ('kafka', 'logging', '将容器日志的日志接收器kafka状态更改为false')
                              ])
    def test_modify_log_receiver_logging_status(self, type, log_type, title):
        # 添加日志收集器
        log_receiver_name = 'test' + str(commonFunction.get_random()) + '-' + type
        multi_cluster_steps.step_add_log_receiver(self.cluster_host_name, type, log_type, log_receiver_name)
        # 查看日志接收器详情
        multi_cluster_steps.step_get_log_receiver_detail(self.cluster_host_name, log_receiver_name)
        # 更改日志接收器状态
        multi_cluster_steps.step_modify_log_receiver_status(self.cluster_host_name, log_receiver_name, 'false')
        # 查看日志接受器详情并验证更改成功
        re = multi_cluster_steps.step_get_log_receiver_detail(self.cluster_host_name, log_receiver_name)
        status = re.json()['metadata']['labels']['logging.kubesphere.io/enabled']
        with pytest.assume:
            assert status == 'false'
        # 删除创建的日志接收器
        multi_cluster_steps.step_delete_log_receiver(self.cluster_host_name, log_receiver_name)

    @allure.story('集群设置/日志接收器')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('type, log_type, title',
                             [
                                 ('es', 'logging', '修改容器日志的日志接受器elasticsearch的服务地址'),
                                 ('kafka', 'logging', '修改容器日志的日志接受器kafka的服务地址'),
                                 ('fluentd', 'logging', '修改容器日志的日志接受器fluentd的服务地址')
                             ])
    def test_modify_log_receiver_logging_address(self, type, log_type, title):
        # 添加日志收集器
        log_receiver_name = 'test' + str(commonFunction.get_random()) + '-' + type
        multi_cluster_steps.step_add_log_receiver(self.cluster_host_name, type, log_type, log_receiver_name)
        # 修改日志接收器的服务地址
        host = commonFunction.random_ip()
        port = random.randint(1, 65535)
        multi_cluster_steps.step_modify_log_receiver_address(type, self.cluster_host_name, log_receiver_name, host, port)
        # 查看日志接受器详情并验证修改成功
        spec = multi_cluster_steps.step_get_log_receiver_detail(self.cluster_host_name, log_receiver_name).json()['spec']
        with pytest.assume:
            assert str(host) in str(spec)
        with pytest.assume:
            assert str(port) in str(spec)
        # 删除创建的日志接收器
        multi_cluster_steps.step_delete_log_receiver(self.cluster_host_name, log_receiver_name)

    @allure.story('集群设置/日志接收器')
    @allure.title('添加同名的日志接收器')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('type, log_type, title',
                             [
                                 ('es', 'logging', '添加同名的日志接收器elasticsearch'),
                                 ('kafka', 'logging', '添加同名的日志接收器kafka'),
                                 ('fluentd', 'logging', '添加同名的日志接收器fluentd')
                             ])
    def test_add_log_receiver_logging_same_name(self, type, log_type, title):
        # 添加日志收集器
        log_receiver_name = 'test' + str(commonFunction.get_random()) + '-' + type
        multi_cluster_steps.step_add_log_receiver(self.cluster_host_name, type, log_type, log_receiver_name)
        # 添加同名的日志收集器
        response = multi_cluster_steps.step_add_log_receiver(self.cluster_host_name, type, log_type, log_receiver_name)
        # 验证添加失败
        with pytest.assume:
            assert response.json()['status'] == 'Failure'
            assert response.json()['message'] == 'outputs.logging.kubesphere.io \"' + log_receiver_name + '\" already exists'
        # 删除创建的日志接收器
        multi_cluster_steps.step_delete_log_receiver(self.cluster_host_name, log_receiver_name)


if __name__ == '__main__':
    pytest.main(["-s", "test_multi_cluster_logging.py"])