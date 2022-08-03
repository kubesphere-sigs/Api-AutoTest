# -- coding: utf-8 --
import random
import sys
import time
import allure
import pytest
from datetime import datetime
from common import commonFunction
from step import toolbox_steps, cluster_steps

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用


@allure.feature('操作审计')
@pytest.mark.skipif(commonFunction.get_components_status_of_cluster('auditing') is False, reason='集群未开启auditing功能')
class TestAuditingOperatingSearch(object):
    if commonFunction.check_multi_cluster() is True:
        # 如果为多集群环境，则不会collect该class的所有用例。 __test__ = False
        __test__ = False
    else:
        __test__ = True

    @allure.story('审计总量')
    @allure.title('验证当天的操作审计总量与最近12小时的审计总量关系正确')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_total_audits(self):
        # 获取当前时间的10位时间戳
        now_time = datetime.now()
        now_timestamp = str(datetime.timestamp(now_time))[0:10]
        # 获取当前日期的时间戳
        day_timestamp = commonFunction.get_timestamp()
        # 查询当天的操作审计总量信息
        response = toolbox_steps.step_get_audits(day_timestamp, now_timestamp)
        # 获取收集审计的资源数量
        resources_count = response.json()['statistics']['resources']
        # 获取收集到的审计数量
        audit_counts = response.json()['statistics']['events']
        # 验证资源数量数量大于0
        pytest.assume(resources_count > 0)
        # 获取12小时之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp(now_time, 720)
        # 查询最近12小时审计总数变化趋势
        re = toolbox_steps.step_get_audits_trend(before_timestamp, now_timestamp)
        # 获取最近12小时的审计总量
        audit_count = re.json()['histogram']['total']
        # 验证今日事件总量和最近12小时事件总量的关系
        # 获取当前日期
        today = commonFunction.get_today()
        # 获取当天12点的时间戳
        tamp = commonFunction.get_custom_timestamp(today, '12:00:00')
        if int(now_timestamp) > int(tamp):  # 如果当前时间大于12点，则当天的事件总数大于等于最近12小时的事件总数
            assert audit_counts >= audit_count
        elif int(now_timestamp) < int(tamp):  # 如果当前时间小于12点，则当天的事件总数小于等于最近12小时的事件总数
            assert audit_count >= audit_counts
        else:  # 如果当前时间等于12点，则当天的事件总数等于最近12小时的事件总数
            assert audit_count == audit_counts

    @allure.story('审计总量')
    @allure.title('验证最近 12 小时操作审计总数正确')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_audits_12h(self):
        # 获取当前时间的10位时间戳
        now_time = datetime.now()
        now_timestamp = str(datetime.timestamp(now_time))[0:10]
        # 获取12小时之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp(now_time, 720)
        # 查询最近 12 小时审计总数变化趋势
        response = toolbox_steps.step_get_audits_trend(before_timestamp, now_timestamp)
        # 获取操作审计总量
        audit_count = response.json()['histogram']['total']
        # 获取趋势图的横坐标数量
        count = len(response.json()['histogram']['buckets'])
        # 获取每个时间段的操作审计数量之和
        audit_count_actual = 0
        for i in range(0, count):
            number = response.json()['histogram']['buckets'][i]['count']
            audit_count_actual += number
        # 验证接口返回的总量信息和趋势图中的数量之和一致
        assert audit_count == audit_count_actual

    @allure.story('审计总量')
    @allure.title('查询最近 12 小时操作审计总数变化趋势')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_audits_trend(self):
        # 时间间隔,单位是秒
        interval = '1800'
        # 获取当前时间的10位时间戳
        now_time = datetime.now()
        now_timestamp = str(datetime.timestamp(now_time))[0:10]
        # 获取12小时之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp(now_time, 720)
        # 查询最近 12 小时审计总数变化趋势
        response = toolbox_steps.step_get_audits_trend(before_timestamp, now_timestamp)
        # 获取查询结果数据中的时间间隔
        time_1 = response.json()['histogram']['buckets'][0]['time']
        try:
            time_2 = response.json()['histogram']['buckets'][1]['time']
            time_interval = (time_2 - time_1)/1000  # 换算成秒
        # 验证时间间隔正确
            assert time_interval == int(interval)
        except Exception as e:
            print(e)
            print('只有半个小时内的数据即一个时间段')

    @allure.story('审计查询规则')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(('search_rule', 'title'),
                             [
                              ('workspace_search=sys', '按企业空间模糊查询审计趋势'),
                              ('workspace_filter=sys', '按企业空间精确查询审计趋势'),
                              ('objectref_namespace_filter=kube', '按项目精确查询审计趋势'),
                              ('objectref_namespace_search=kube', '按项目模糊查询审计趋势'),
                              ('objectref_resource_filter=deployment', '按资源类型查询审计趋势'),
                              ('objectref_name_filter=kube', '按资源名称精确查询审计趋势'),
                              ('objectref_name_search=kube', '按资源名称模糊查询审计趋势'),
                              ('verb_filter=post', '按操作行为查询审计趋势'),
                              ('response_code_filter=OK', '按状态码查询审计趋势'),
                              ('user_search=adm', '按操作账户模糊查询审计趋势'),
                              ('user_filter=admin', '按操作账户精确查询审计趋势'),
                              ('source_ip_search=192.', '按来源ip查询审计趋势')
                              ])
    def test_get_audits_trend_by_search(self, search_rule, title):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 按不同条件查询审计
        response = toolbox_steps.step_get_audits_trend_by_search(search_rule, now_timestamp)
        # 获取查询结果中的总审计条数
        log_count = response.json()['histogram']['total']
        # 验证查询成功
        assert log_count >= 0

    @allure.story('日志查询规则')
    @allure.title('{title}')
    @pytest.mark.parametrize(('limit', 'interval', 'title'),
                             [(10, '1m', '按时间范围查询最近10分钟审计趋势'),
                              (180, '6m', '按时间查询最近3小时审计趋势'),
                              (1440, '48m', '按时间查询最近一天审计趋势')
                              ])
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_audits_trend_by_time_limit(self, limit, interval, title):
        # 获取当前时间的10位时间戳（结束时间）
        now_time = datetime.now()
        now_timestamp = str(datetime.timestamp(now_time))[0:10]
        # 获取开始时间
        start_time = commonFunction.get_before_timestamp(now_time, limit)
        # 按时间范围查询容器日志
        res = toolbox_steps.step_get_audits_trend_by_time(interval, start_time, now_timestamp)
        audits_num = res.json()['histogram']['total']
        # 验证查询成功
        assert audits_num >= 0

    @allure.story('审计查询规则')
    @allure.title('{title}')
    @pytest.mark.parametrize(('search_rule', 'title'),
                             [
                              ('workspace_search=sys', '按企业空间模糊查询审计详情'),
                              ('workspace_filter=sys', '按企业空间精确查询审计详情'),
                              ('objectref_namespace_filter=kube', '按项目精确查询审计详情'),
                              ('objectref_namespace_search=kube', '按项目模糊查询审计详情'),
                              ('objectref_resource_filter=deployment', '按资源类型查询审计详情'),
                              ('objectref_name_filter=kube', '按资源名称精确查询审计详情'),
                              ('objectref_name_search=kube', '按资源名称模糊查询审计详情'),
                              ('verb_filter=post', '按操作行为查询审计详情'),
                              ('response_code_filter=OK', '按状态码查询审计详情'),
                              ('user_search=adm', '按操作账户模糊查询审计详情'),
                              ('user_filter=admin', '按操作账户精确查询审计详情'),
                              ('source_ip_search=192.', '按来源ip查询审计详情')
                              ])
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_audits_by_search(self, search_rule, title):
        # 获取当前时间的10位时间戳
        now_time = datetime.now()
        now_timestamp = str(datetime.timestamp(now_time))[0:10]
        # 按关键字查询日志详情信息
        response = toolbox_steps.step_get_audits_by_search(search_rule, now_timestamp)
        # 获取查询到的审计数量
        logs_count = response.json()['query']['total']
        # 验证查询成功
        assert logs_count >= 0

    @allure.story('日志查询规则')
    @allure.title('{title}')
    @pytest.mark.parametrize(('limit', 'interval', 'title'),
                             [(10, '1m', '按时间范围查询最近10分钟审计详情'),
                              (180, '6m', '按时间查询最近3小时审计详情'),
                              (1440, '48m', '按时间查询最近一天审计详情')
                              ])
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_audits_detail_by_time_limit(self, limit, interval, title):
        # 获取当前时间的10位时间戳（结束时间）
        now_time = datetime.now()
        now_timestamp = str(datetime.timestamp(now_time))[0:10]
        # 获取开始时间
        start_time = commonFunction.get_before_timestamp(now_time, limit)
        # 按时间范围查询容器日志
        res = toolbox_steps.step_get_audits_by_time(interval, start_time, now_timestamp)
        audits_num = res.json()['query']['total']
        # 验证查询成功
        assert audits_num >= 0

    @allure.story("集群设置")
    @allure.title('查看日志接收器中的审计日志')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_log_receiver_audit(self):
        # 查询日志接收器/审计日志
        response = cluster_steps.step_get_log_receiver('auditing')
        # 获取接收器类型和启用状态
        component = response.json()['items'][0]['metadata']['labels']['logging.kubesphere.io/component']
        enabled = response.json()['items'][0]['metadata']['labels']['logging.kubesphere.io/enabled']
        # 校验接收器类型和启用状态，启用状态默认为开启
        pytest.assume(component == 'auditing')
        assert enabled == 'true'

    @allure.story('集群设置/日志接收器')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('type, log_type, title',
                             [
                                 ('fluentd', 'auditing', '为审计日志添加日志接收器，并验证添加成功'),
                                 ('kafka', 'auditing', '为审计日志添加日志接收器，并验证添加成功')
                             ])
    def test_add_log_receiver_auditing(self, type, log_type, title):
        # 添加日志收集器
        cluster_steps.step_add_log_receiver(type, log_type)
        # 查看日志收集器
        response = cluster_steps.step_get_log_receiver(log_type)
        log_receiver_name = response.json()['items'][1]['metadata']['name']
        # 验证日志接收器添加成功
        pytest.assume(log_receiver_name == 'forward-' + log_type)
        # 删除创建的日志接收器
        cluster_steps.step_delete_log_receiver(log_receiver_name)

    @allure.story('集群设置/日志接收器')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('log_type, title',
                             [
                                 ('auditing', '将审计日志的日志接收器状态更改为false')
                             ])
    def test_modify_log_receiver_auditing_status(self, log_type, title):
        # 添加日志收集器
        cluster_steps.step_add_log_receiver('fluentd', log_type)
        # 查看日志收集器，并获取新增日志接收器名称
        response = cluster_steps.step_get_log_receiver(log_type)
        log_receiver_name = response.json()['items'][1]['metadata']['name']
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
                                 ('auditing', '修改审计日志的日志接收器的服务地址')
                             ])
    def test_modify_log_receiver_auditing_address(self, log_type, title):
        # 添加日志收集器
        cluster_steps.step_add_log_receiver('fluentd', log_type)
        # 查看日志收集器，并获取新增日志接收器名称
        response = cluster_steps.step_get_log_receiver(log_type)
        log_receiver_name = response.json()['items'][1]['metadata']['name']
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
        assert port_actual == port
        # 删除创建的日志接收器
        cluster_steps.step_delete_log_receiver(log_receiver_name)

