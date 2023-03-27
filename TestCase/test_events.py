# -- coding: utf-8 --
import pytest
import allure
import sys
import time
import random
from datetime import datetime
from common import commonFunction
from step import toolbox_steps, cluster_steps


sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用


@allure.feature('事件查询')
@pytest.mark.skipif(commonFunction.get_components_status_of_cluster('events') is False, reason='集群未开启events功能')
class TestEventSearch(object):
    if commonFunction.check_multi_cluster() is True:
        # 如果为多集群环境，则不会collect该class的所有用例。 __test__ = False
        __test__ = False
    else:
        __test__ = True

    @allure.story('事件总量')
    @allure.title('验证当天的事件总量与最近12小时的事件总量的关系正确')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_total_events(self):
        # 获取当前时间的10位时间戳
        now_time = datetime.now()
        now_timestamp = str(datetime.timestamp(now_time))[0:10]
        # 获取当前日期的时间戳
        day_timestamp = commonFunction.get_timestamp()
        # 查询当天的事件总量信息
        response = toolbox_steps.step_get_event(day_timestamp, now_timestamp)
        # 获取收集事件的资源数量
        resources_count = response.json()['statistics']['resources']
        # 获取收集到的事件数量
        event_counts = response.json()['statistics']['events']
        # 验证事件数量大于0
        pytest.assume(resources_count > 0)
        # 获取最近12小时的事件趋势图
        interval = '30m'  # 时间间隔 30分钟
        # 获取12小时之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp(now_time, 720)
        re = toolbox_steps.step_get_events_trend(before_timestamp, now_timestamp, interval)
        # 获取最近12小时的事件总量
        event_count = re.json()['histogram']['total']
        # 验证今日事件总量和最近12小时事件总量的关系,获取当前日期
        today = commonFunction.get_today()
        # 获取当天12点的时间戳
        tamp = commonFunction.get_custom_timestamp(today, '12:00:00')
        if int(now_timestamp) > int(tamp):  # 如果当前时间大于12点，则当天的事件总数大于等于最近12小时的事件总数
            assert event_counts >= event_count
        elif int(now_timestamp) < int(tamp):  # 如果当前时间小于12点，则当天的事件总数小于等于最近12小时的事件总数
            assert event_count >= event_counts
        else:  # 如果当前时间等于12点，则当天的事件总数等于最近12小时的事件总数
            assert event_count == event_counts
        # 获取当天的事件趋势图
        interval = '1h'  # 时间间隔
        re = toolbox_steps.step_get_events_trend(day_timestamp, now_timestamp, interval)
        # 获取趋势图的横坐标数量
        count = len(re.json()['histogram']['buckets'])
        # 获取每个时间段的事件数量之和
        events_count_actual = 0
        for i in range(0, count):
            number = re.json()['histogram']['buckets'][i]['count']
            events_count_actual += number
        # 验证接口返回的事件数量和趋势图中的事件之和一致
        assert events_count_actual == event_counts

    @allure.story('事件总量')
    @allure.title('验证最近 12 小时事件总数正确')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_events_12h(self):
        # 时间间隔,单位是秒
        interval = '30m'
        # 获取当前时间的10位时间戳
        now_time = datetime.now()
        now_timestamp = str(datetime.timestamp(now_time))[0:10]
        # 获取12小时之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp(now_time, 720)
        # 查询最近 12 小时事件总数变化趋势
        response = toolbox_steps.step_get_events_trend(before_timestamp, now_timestamp, interval)
        # 获取事件总量
        events_count = response.json()['histogram']['total']
        # 获取趋势图的横坐标数量
        count = len(response.json()['histogram']['buckets'])
        # 获取每个时间段的事件数量之和
        events_count_actual = 0
        for i in range(0, count):
            number = response.json()['histogram']['buckets'][i]['count']
            events_count_actual += number
        # 验证接口返回的事件数量和趋势图中的事件之和一致
        assert events_count_actual == events_count

    @allure.story('事件总量')
    @allure.title('查询最近 12 小时事件总数变化趋势')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_events_trend(self):
        # 时间间隔,单位是秒
        interval = '30m'
        # 获取当前时间的10位时间戳
        now_time = datetime.now()
        now_timestamp = str(datetime.timestamp(now_time))[0:10]        # 获取12小时之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp(now_time, 720)
        # 查询最近 12 小时事件总数变化趋势
        response = toolbox_steps.step_get_events_trend(before_timestamp, now_timestamp, interval)
        # 获取查询结果数据中的时间间隔
        time_1 = response.json()['histogram']['buckets'][0]['time']
        try:
            time_2 = response.json()['histogram']['buckets'][1]['time']
            time_interval = (time_2 - time_1) / 1000  # 换算成秒
            # 验证时间间隔正确
            assert time_interval == int(interval)
        except Exception as e:
            print(e)
            print('只有半个小时内的数据即一个时间段')

    @allure.story('事件查询规则')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize(('search_rule', 'title'),
                             [('message_search=test', '按消息查询事件趋势'),
                              ('workspace_search=sys', '按企业空间模糊查询事件趋势'),
                              ('workspace_filter=sys', '按企业空间精确查询事件趋势'),
                              ('involved_object_namespace_filter=kube', '按项目精确查询事件趋势'),
                              ('involved_object_namespace_search=kube', '按项目模糊查询事件趋势'),
                              ('involved_object_kind_filter=deployment', '按资源类型查询事件趋势'),
                              ('involved_object_name_filter=kube', '按资源名称精确查询事件趋势'),
                              ('involved_object_name_search=kube', '按资源名称模糊查询事件趋势'),
                              ('reason_filter=Failed', '按原因精确查询事件趋势'),
                              ('reason_search=Failed', '按原因模糊查询事件趋势'),
                              ('type_filter=Warning', '按类别精确查询事件趋势'),
                              ('type_search=Warning', '按类别模糊查询事件趋势'),
                              ('reason_search=Failed', '按原因模糊查询事件趋势')
                              ])
    def test_get_events_trend_by_search(self, search_rule, title):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 按不同条件查询事件
        response = toolbox_steps.step_get_events_trend_by_search(search_rule, now_timestamp)
        # 获取查询结果中的总事件条数
        log_count = response.json()['histogram']['total']
        # 验证查询成功
        assert log_count >= 0

    @allure.story('事件查询规则')
    @allure.title('{title}')
    @pytest.mark.parametrize(('search_rule', 'title'),
                             [('message_search=error', '按消息查询事件趋势'),
                              ('workspace_search=sys', '按企业空间模糊查询事件趋势'),
                              ('workspace_filter=sys', '按企业空间精确查询事件趋势'),
                              ('involved_object_namespace_filter=kube', '按项目精确查询事件趋势'),
                              ('involved_object_namespace_search=kube', '按项目模糊查询事件趋势'),
                              ('involved_object_kind_filter=deployment', '按资源类型查询事件趋势'),
                              ('involved_object_name_filter=kube', '按资源名称精确查询事件趋势'),
                              ('involved_object_name_search=kube', '按资源名称模糊查询事件趋势'),
                              ('reason_filter=Failed', '按原因精确查询事件趋势'),
                              ('reason_search=Failed', '按原因模糊查询事件趋势'),
                              ('type_filter=Warning', '按类别精确查询事件趋势'),
                              ('type_search=Warning', '按类别模糊查询事件趋势'),
                              ('reason_search=Failed', '按原因模糊查询事件趋势')
                              ])
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_events_by_search(self, search_rule, title):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 按关键字查询事件详情信息
        response = toolbox_steps.step_get_events_by_search(search_rule, now_timestamp)
        # 获取查询到的事件数量
        logs_count = response.json()['query']['total']
        # 验证查询成功
        assert logs_count >= 0

    @allure.story('事件查询规则')
    @allure.title('{title}')
    @pytest.mark.parametrize(('limit', 'interval', 'title'),
                             [(10, '1m', '按时间范围查询最近10分钟事件趋势'),
                              (180, '6m', '按时间范围查询最近3小时事件趋势'),
                              (1440, '48m', '按时间范围查询最近一天事件趋势')
                              ])
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_events_by_time_limit(self, limit, interval, title):
        # 获取当前时间的10位时间戳
        now_time = datetime.now()
        now_timestamp = str(datetime.timestamp(now_time))[0:10]
        # 获取开始时间
        start_time = commonFunction.get_before_timestamp(now_time, limit)
        # 按时间范围查询事件
        res = toolbox_steps.step_get_events_by_time(interval, start_time, now_timestamp)
        event_num = res.json()['query']['total']
        # 验证查询成功
        assert event_num >= 0

    @allure.story("集群设置")
    @allure.title('查看默认情况下日志接收器中的资源事件')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_log_receiver_event(self):
        # 查询日志接收器/资源事件
        response = cluster_steps.step_get_log_receiver('events')
        # 判断是否存在日志接收器
        items = response.json()['items']
        # 验证日志接收器不存在
        pytest.assume(not items)

    @allure.story('集群设置/日志接收器')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('type, log_type, title',
                             [
                                 ('fluentd', 'events', '为资源事件添加日志接受器，并验证添加成功'),
                                 ('kafka', 'events', '为资源事件添加日志接受器，并验证添加成功')
                             ])
    def test_add_log_receiver_events(self, type, log_type, title):
        # 添加日志收集器
        cluster_steps.step_add_log_receiver(type, log_type)
        # 查看日志收集器
        response = cluster_steps.step_get_log_receiver(log_type)
        log_receiver_name = response.json()['items'][0]['metadata']['name']
        # 验证日志接收器添加成功
        with pytest.assume:
            assert log_receiver_name == 'forward-' + log_type
        # 删除创建的日志接收器
        cluster_steps.step_delete_log_receiver(log_receiver_name)

    @allure.story('集群设置/日志接收器')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('log_type, title',
                             [
                                 ('events', '将资源事件的日志接受器状态更改为false')
                             ])
    def test_modify_log_receiver_events_status(self, log_type, title):
        # 添加日志收集器
        cluster_steps.step_add_log_receiver('fluentd', log_type)
        # 查看日志收集器，并获取新增日志接收器名称
        response = cluster_steps.step_get_log_receiver(log_type)
        log_receiver_name = response.json()['items'][0]['metadata']['name']
        # 查看日志接收器详情
        cluster_steps.step_get_log_receiver_detail(log_receiver_name)
        # 更改日志接收器状态
        cluster_steps.step_modify_log_receiver_status(log_receiver_name, 'false')
        # 查看日志接受器详情并验证更改成功
        re = cluster_steps.step_get_log_receiver_detail(log_receiver_name)
        status = re.json()['metadata']['labels']['logging.kubesphere.io/enabled']
        pytest.assume(status == 'false')
        # 删除创建的日志接收器
        cluster_steps.step_delete_log_receiver(log_receiver_name)

    @allure.story('集群设置/日志接收器')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('log_type, title',
                             [
                                 ('events', '修改资源事件的日志接受器的服务地址')
                             ])
    def test_modify_log_receiver_events_address(self, log_type, title):
        # 添加日志收集器
        cluster_steps.step_add_log_receiver('fluentd', log_type)
        # 查看日志收集器，并获取新增日志接收器名称
        response = cluster_steps.step_get_log_receiver(log_type)
        log_receiver_name = response.json()['items'][0]['metadata']['name']
        # 查看日志接收器详情
        cluster_steps.step_get_log_receiver_detail(log_receiver_name)
        # 修改日志接收器的服务地址
        host = commonFunction.random_ip()
        port = random.randint(1, 65535)
        cluster_steps.step_modify_log_receiver_address(log_receiver_name, host, port)
        # 查看日志接受器详情并验证修改成功
        re = cluster_steps.step_get_log_receiver_detail(log_receiver_name)
        host_actual = re.json()['spec']['forward']['host']
        port_actual = re.json()['spec']['forward']['port']
        pytest.assume(host_actual == host)
        pytest.assume(port_actual == port)
        # 删除创建的日志接收器
        cluster_steps.step_delete_log_receiver(log_receiver_name)


if __name__ == "__main__":
    pytest.main(['-s', 'test_events.py'])  # -s参数是为了显示用例的打印信息。 -q参数只显示结果，不显示过程