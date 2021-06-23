import requests
import pytest
import json
import allure
import sys
from config import config
from common.getData import DoexcleByPandas
from common.getHeader import get_header
from common import commonFunction
import random
import time
import datetime

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用


@allure.step('从工作台获取平台信息')
def step_get_base_info(start_time, end_time, step, times):
    url = config.url + '/kapis/monitoring.kubesphere.io/v1alpha3/kubesphere?start=' + start_time + \
          '&end=' + end_time + '&step=' + step + 's&times=' + times + '&metrics_filter=kubesphere_cluser_count%7C' \
          'kubesphere_workspace_count%7Ckubesphere_user_count%7Ckubesphere_app_template_count%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询平台的企业空间信息')
def step_get_ws_info():
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询平台的用户信息')
def step_get_user_info():
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/users'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询平台的应用模版信息')
def step_get_app_info():
    url = config.url + '/kapis/openpitrix.io/v1/apps?orderBy=create_time&paging=limit%3D12%2Cpage%3D1&' \
                       'conditions=status%3Dactive%2Crepo_id%3Drepo-helm&reverse=true'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.feature('工作台')
class TestWorkbench(object):

    @allure.story('平台信息')
    @allure.title('查询平台的集群数量')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_count(self):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 获取180分钟戳
        before_timestamp = commonFunction.get_before_timestamp(180)
        # 查询工作台的基本信息
        response = step_get_base_info(before_timestamp, now_timestamp, '600', '20')
        # 获取平台的集群数量
        cluster_count = response.json()['results'][0]['data']['result'][0]['value'][1]
        # 验证集群数量正确
        assert cluster_count == str(1)

    @allure.story('平台信息')
    @allure.title('查询平台的企业空间数量')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_ws_count(self):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 获取180分钟戳
        before_timestamp = commonFunction.get_before_timestamp(180)
        # 查询工作台的基本信息
        response = step_get_base_info(before_timestamp, now_timestamp, '600', '20')
        # 获取平台的workspace数量
        ws_count = response.json()['results'][1]['data']['result'][0]['value'][1]
        # 查询集群的企业空间信息，并获取企业空间数量
        r = step_get_ws_info()
        ws_count_actual = r.json()['totalItems']
        # 验证企业空间数量正确
        assert int(ws_count) == ws_count_actual

    @allure.story('平台信息')
    @allure.title('查询平台的用户数量')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_user_count(self):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 获取180分钟戳
        before_timestamp = commonFunction.get_before_timestamp(180)
        # 查询工作台的基本信息
        response = step_get_base_info(before_timestamp, now_timestamp, '600', '20')
        # 获取平台的用户数量
        user_count = response.json()['results'][2]['data']['result'][0]['value'][1]
        # 查询集群的用户信息，并获取用户数量
        r = step_get_user_info()
        user_count_actual = r.json()['totalItems']
        # 验证用户数量正确
        assert int(user_count) == user_count_actual

    @allure.story('平台信息')
    @allure.title('查询平台的应用模版数量')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_template_count(self):
        # 获取当前时间的10位时间戳
        now_timestamp = str(time.time())[0:10]
        # 获取180分钟戳
        before_timestamp = commonFunction.get_before_timestamp(180)
        # 查询工作台的基本信息
        response = step_get_base_info(before_timestamp, now_timestamp, '600', '20')
        # 获取平台的应用模版数量
        template_count = response.json()['results'][3]['data']['result'][0]['value'][1]
        # 查询集群的应用模版信息，并获取用户数量
        r = step_get_app_info()
        template_count_actual = r.json()['total_count']
        # 验证用户数量正确
        assert int(template_count) == template_count_actual