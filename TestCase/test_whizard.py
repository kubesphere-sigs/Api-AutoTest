import allure
import pytest
from common import commonFunction
from common.getData import DoexcleByPandas
from step import whizard_steps


@pytest.mark.skipif(commonFunction.get_components_status_of_cluster('whizard') is False, reason='whizard组件未安装')
@allure.feature('可观测中心')
class TestWhizard(object):
    if commonFunction.check_multi_cluster() is False:
        # 如果为单集群环境，则不会collect该class的所有用例。 __test__ = False
        __test__ = False
    else:
        __test__ = True

    # 从文件中读取用例信息
    parametrize = DoexcleByPandas().get_data_from_yaml(filename='../data/whizard.yaml')

    # 获取可观测中心显示的集群名称
    cluster_name = whizard_steps.step_get_cluster_name()
    if len(cluster_name) == 1:
        resources_filter = cluster_name[0]
    elif len(cluster_name) > 1:
        # 如果集群数量大于1，则需要将集群名称拼接成字符串，且除了第一个名称外，每个名称前面都需要加上%7C
        resources_filter = cluster_name[0]
        for i in range(1, len(cluster_name)):
            resources_filter = resources_filter + '%7C' + cluster_name[i]
    else:
        resources_filter = ''
    print(resources_filter)

    @allure.title('{title}')  # 设置用例标题
    @allure.severity(allure.severity_level.CRITICAL)  # 设置用例优先级
    # 将用例信息以参数化的方式传入测试方法
    @pytest.mark.parametrize('id,url,params,data,story,title,method,severity,condition,except_result', parametrize)
    def test_whizard(self, id, url, params, data, story, title, method, severity, condition, except_result):
        """
        :param id: 用例编号
        :param url: 用例请求的URL地址
        :param data: 用例使用的请求数据
        :param story: 用例模块
        :param title: 用例标题
        :param method: 用例的请求方式
        :param severity: 用例优先级
        :param condition: 用例的校验条件
        :param except_result: 用例的预期结果
        """

        allure.dynamic.story(story)  # 动态生成模块
        allure.dynamic.severity(severity)  # 动态生成用例等级
        # 将测试用例中的变量替换成指定内容
        targets = commonFunction.replace_str(url, params, data, condition, except_result,
                                             actual_value='${cluster_name}', expect_value=self.resources_filter)
        # 使用修改过的内容进行测试
        commonFunction.request_resource(targets[0], targets[1], targets[2], story, title, method, severity,
                                        targets[3], targets[4])

