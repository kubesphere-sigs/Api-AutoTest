import requests
import pytest
import json
import allure
import sys

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from config import config
from common.getData import DoexcleByPandas
from common.getHeader import get_header, get_header_for_patch
from common.logFormat import log_format
from common import commonFunction
from math import ceil


@allure.step('获取指定应用分类的category_id')
def step_get_category_id_by_name(category_name):
    """
    :param category_name: 分类名称
    :return: 分类的category_id
    """
    url = config.url + '/kapis/openpitrix.io/v1/categories'
    r = requests.get(url=url, headers=get_header())
    # 获取分类的数量
    count = r.json()['total_count']
    name = []
    id = []
    for i in range(count):
        name.append(r.json()['items'][i]['category_id'])
        id.append(r.json()['items'][i]['name'])
    name_id = dict(zip(id, name))
    return name_id[category_name]


@allure.step('获取所有应用分类的category_id')
def step_get_categories_id():
    url = config.url + '/kapis/openpitrix.io/v1/categories'
    r = requests.get(url=url, headers=get_header())
    # 获取分类的数量
    count = r.json()['total_count']
    categories_id = []
    for i in range(count):
        categories_id.append(r.json()['items'][i]['category_id'])

    return categories_id


@allure.step('新建应用分类')
def step_create_category(cate_name):
    url = config.url + '/kapis/openpitrix.io/v1/categories'
    data = {"name": cate_name,
            "description": "documentation",
            "locale": "{}"
            }
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.title('向应用分类中添加应用')
def step_app_to_category(app_id, cat_id):
    url = config.url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/'
    data = {"category_id": cat_id}
    response = requests.patch(url, headers=get_header_for_patch(), data=json.dumps(data))
    return response


@allure.step('删除分类')
def step_delete_app_category(cate_id):
    url = config.url + '/kapis/openpitrix.io/v1/categories/' + cate_id
    r = requests.delete(url, headers=get_header())
    return r.text.strip()


@allure.step('删除不包含应用的分类')
def step_delete_category(cate_id):
    url = config.url + '/kapis/openpitrix.io/v1/categories/' + cate_id
    response = requests.delete(url, headers=get_header())
    return response


@allure.step('修改分类信息')
def step_change_category(cate_id, new_name):
    url = config.url + '/kapis/openpitrix.io/v1/categories/' + cate_id
    data = {"name": new_name,
            "description": "documentation",
            "locale": "{}"
            }
    requests.patch(url, headers=get_header_for_patch(), data=json.dumps(data))


@allure.step('获取应用商店管理/应用商店中所有的应用的app_id')
def step_get_apps_id():
    page = 1
    url = config.url + '/kapis/openpitrix.io/v1/apps?orderBy=create_time&paging=limit%3D10%2Cpage%3D' + str(page) + '&conditions=status%3Dactive%7Csuspended%2Crepo_id%3Drepo-helm&reverse=true'
    # 获取应用总数量
    r = requests.get(url=url, headers=get_header())
    count = r.json()['total_count']
    # 获取页数
    pages = ceil(count/10)
    apps = []
    for page in range(1, pages+1):
        r = requests.get(url, get_header())
        for item in r.json()['items']:
            apps.append(item['app_id'])
    return apps


@allure.step('查看应用的详情信息')
def step_get_app_detail(app_id):
    url = config.url + '/kapis/openpitrix.io/v1/apps/' + app_id
    response = requests.get(url=url, headers=get_header())
    return response


@allure.feature('应用商店管理')
@pytest.mark.skipif(commonFunction.get_component_health_of_cluster('') is False, reason='')
@pytest.mark.skipif(commonFunction.get_components_status_of_cluster('openpitrix') is False, reason='集群未开启openpitrix功能')
@pytest.mark.skipif(commonFunction.check_multi_cluster() is True, reason='多集群环境下不执行')
class TestManageAppStore(object):
    ws_name = 'test-appstore-manage'  # 在excle中读取的用例此名称，不能修改。
    project_name = 'project-for-test-appstore-manage'  # 在excle中读取的用例此名称，不能修改。
    log_format()  # 配置日志格式
    # 从文件中读取用例信息
    parametrize = DoexcleByPandas().get_data_for_pytest(filename='../data/data.xlsx', sheet_name='manageapps')

    @allure.title('{title}')  # 设置用例标题
    @allure.severity(allure.severity_level.CRITICAL)  # 设置用例优先级
    # 将用例信息以参数化的方式传入测试方法
    @pytest.mark.parametrize('id,url,data, story, title,method,severity,condition,except_result', parametrize)
    def test_manage_app_store(self, id, url, data, story, title, method, severity, condition, except_result):

        '''
        :param id: 用例编号
        :param url: 用例请求的URL地址
        :param data: 用例使用的请求数据
        :param title: 用例标题
        :param method: 用例的请求方式
        :param severity: 用例优先级
        :param condition: 用例的校验条件
        :param except_result: 用例的预期结果
        '''

        allure.dynamic.story(story)  # 动态生成模块
        allure.dynamic.severity(severity)  # 动态生成用例等级

        # test开头的测试函数
        url = config.url + url
        if method == 'get':
            # 测试get方法
            r = requests.get(url, headers=get_header())

        elif method == 'post':
            # 测试post方法
            data = eval(data)
            r = requests.post(url, headers=get_header(), data=json.dumps(data))

        elif method == 'patch':
            # 测试patch方法
            data = eval(data)
            r = requests.patch(url, headers=get_header_for_patch(), data=json.dumps(data))

        elif method == 'delete':
            # 测试delete方法
            r = requests.delete(url, headers=get_header())

        # 将校验条件和预期结果参数化
        if condition != '':
            condition_new = eval(condition)  # 将字符串转化为表达式
            if isinstance(condition_new, str):
                # 判断表达式的结果是否为字符串，如果为字符串格式，则去掉其首尾的空格
                assert condition_new.strip() == except_result
            else:
                assert condition_new == except_result

        # 将用例中的内容打印在报告中
        print(
            '用例编号: ' + str(id) + '\n'
                                 '用例请求的URL地址: ' + str(url) + '\n'
                                                             '用例使用的请求数据: ' + str(data) + '\n'
                                                                                         '用例模块: ' + story + '\n'
                                                                                                            '用例标题: ' + title + '\n'
                                                                                                                               '用例的请求方式: ' + method + '\n'
                                                                                                                                                      '用例优先级: ' + severity + '\n'
                                                                                                                                                                             '用例的校验条件: ' + str(
                condition) + '\n'
                             '用例的实际结果: ' + str(condition_new) + '\n'
                                                                '用例的预期结果: ' + str(except_result)
        )

    @allure.story('应用分类')
    @allure.title('删除不包含应用的分类')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_category(self):
        # 新建应用分类
        category_name = 'category' + str(commonFunction.get_random())
        response = step_create_category(category_name)
        # 获取创建分类的category_id
        category_id = response.json()['category_id']
        # 删除分类
        step_delete_category(category_id)
        # 查询所有分类的category_id
        categories_id = step_get_categories_id()
        # 验证被删除分类的category_id不存在
        assert category_id not in categories_id

    @allure.story('应用分类')
    @allure.title('修改分类信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_change_category(self):
        old_name = 'category' + str(commonFunction.get_random())
        new_name = 'category' + str(commonFunction.get_random())
        # 新建应用分类
        response = step_create_category(old_name)
        # 获取新建分类的category_id
        category_id = response.json()['category_id']
        # 修改分类名称为test-wx3
        step_change_category(category_id, new_name)
        # 验证修改成功，使用修改后的名称查询category_id
        category_id_new = step_get_category_id_by_name(new_name)
        assert category_id == category_id_new
        # 删除分类
        step_delete_category(category_id)

    @allure.story('应用商店')
    @allure.title('查看所有内置应用的详情信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_check_apps_detail(self):
        # 获取应用商店管理/应用商店页面，所有应用的app_id
        apps_id = step_get_apps_id()
        # 查看所有应用的详情信息，并验证查询成功
        for app_id in apps_id:
            response = step_get_app_detail(app_id)
            assert response.json()['app_id'] == app_id

    @allure.story('应用分类')
    @allure.title('删除包含应用的分类')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_app_category(self):
        category_name = 'category' + str(commonFunction.get_random())
        # 新建应用分类
        response = step_create_category(category_name)
        # 获取新建分类的category_id
        category_id = response.json()['category_id']
        # 获取应用商店页面所有应用的app_id
        apps_id = step_get_apps_id()
        # print(apps_id)
        # 向分类test-wx中添加所有内置应用
        for app_id in apps_id:
            step_app_to_category(app_id, category_id)
        # 删除分类
        result = step_delete_app_category(category_id)
        # 验证删除结果
        assert result == 'category ' + category_name + ' owns application'
        # 获取未分类的category_id
        uncategorized_id = step_get_category_id_by_name('uncategorized')
        # 将所有的内置应用移动到未分类中
        for app_id in apps_id:
            step_app_to_category(app_id, uncategorized_id)
        # 删除新建的分类
        step_delete_category(category_id)


if __name__ == "__main__":
    pytest.main(['-s', 'testAppStoreManage.py'])  # -s参数是为了显示用例的打印信息。 -q参数只显示结果，不显示过程
