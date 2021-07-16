import requests
import pytest
import allure
import sys
from config import config
from common.getHeader import get_header
from common import commonFunction
import time

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用


@allure.step('查询集群的操作审计总量')
def step_get_audits(start_time, end_time):
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/auditing/events?operation=statistics' \
                       '&start_time=' + start_time + '&end_time=' + end_time + '&interval=30m'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群操作审计总数的变化趋势')
def step_get_audits_trend(start_time, end_time):
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/auditing/events?operation=histogram&' \
                       'start_time=' + start_time + '&end_time=' + end_time + '&interval=30m'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('按不同条件查询集群审计总数的变化趋势')
def step_get_events_trend_by_search(search_rule, end_time):
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/auditing/events?operation=histogram&' \
                       'start_time=0&end_time=' + end_time + '&interval=1d&' + search_rule
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('按不同条件查询审计的信息')
def step_get_audits_by_search(search_rule, end_time):
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/auditing/events?operation=query&from=0&size=50&' \
                       '' + search_rule + '&start_time=0&end_time=' + end_time + '&interval=1d'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.feature('操作审计')
@pytest.mark.skipif(commonFunction.get_component_health_of_cluster('') is False, reason='')
@pytest.mark.skipif(commonFunction.get_components_status_of_cluster('auditing') is False, reason='集群未开启auditing功能')
class TestAuditingOperatingSearch(object):

    @allure.story('审计总量')
    @allure.title('验证当天的操作审计总量正确')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_total_audits(self):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 获取当前日期的时间戳
        day_timestamp = commonFunction.get_timestamp()
        # 查询当天的操作审计总量信息
        response = step_get_audits(day_timestamp, now_timestamp)
        # 获取收集审计的资源数量
        resources_count = response.json()['statistics']['resources']
        # 获取收集到的日志数量
        event_counts = response.json()['statistics']['events']
        # 验证资源数量数量大于0
        assert resources_count > 0
        # 查询最近当天审计总数变化趋势
        re = step_get_audits_trend(day_timestamp, now_timestamp)
        # 获取趋势图的横坐标数量
        count = len(re.json()['histogram']['buckets'])
        # 获取每个时间段的操作审计数量之和
        audit_count_actual = 0
        for i in range(0, count):
            number = re.json()['histogram']['buckets'][i]['count']
            audit_count_actual += number
        # 验证接口返回的总量信息和趋势图中的数量之和一致
        assert event_counts == audit_count_actual

    @allure.story('审计总量')
    @allure.title('验证最近 12 小时操作审计总数正确')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_audits_12h(self):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 获取12小时之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp(720)
        # 查询最近 12 小时审计总数变化趋势
        response = step_get_audits_trend(before_timestamp, now_timestamp)
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
        now_timestamp = str(time.time())[0:10]
        # 获取12小时之前的时间戳
        before_timestamp = commonFunction.get_before_timestamp(720)
        # 查询最近 12 小时审计总数变化趋势
        response = step_get_audits_trend(before_timestamp, now_timestamp)
        # 获取查询结果数据中的时间间隔
        time_1 = response.json()['histogram']['buckets'][0]['time']
        time_2 = response.json()['histogram']['buckets'][1]['time']
        time_interval = (time_2 - time_1)/1000  # 换算成秒
        # 验证时间间隔正确
        assert time_interval == int(interval)

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
        response = step_get_events_trend_by_search(search_rule, now_timestamp)
        # 获取查询结果中的总审计条数
        log_count = response.json()['histogram']['total']
        # 验证查询成功
        assert log_count >= 0

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
        now_timestamp = str(time.time())[0:10]
        # 按关键字查询日志详情信息
        response = step_get_audits_by_search(search_rule, now_timestamp)
        # 获取查询到的审计数量
        logs_count = response.json()['query']['total']
        # 验证查询成功
        assert logs_count >= 0


