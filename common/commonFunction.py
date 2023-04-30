import requests
import sys
import yaml
import json
import random
from step import multi_cluster_steps, cluster_steps, multi_project_steps
import time
import datetime
from common.getHeader import get_header, get_header_for_patch
import allure
from common.getConfig import get_apiserver
from common.getData import DoexcleByPandas
from time import sleep

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

env_url = get_apiserver()


# 创建系统用户
@allure.step('创建系统用户')
def step_create_user(user_name):
    """
    :param user_name: 系统用户的名称
    """
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/users'
    data = {"apiVersion": "iam.kubesphere.io/v1alpha2",
            "kind": "User",
            "metadata": {"name": user_name,
                         "annotations": {"kubesphere.io/creator": "admin"}
                         },
            "spec": {"email": "stevewen@yunify.com",
                     "password": "P@88w0rd"}
            }
    requests.post(url, headers=get_header(), data=json.dumps(data))


@allure.step('登录ks,并将token写入config_new.yaml')
def step_login(server, user='admin'):
    yaml_path = '../config/token.yaml'
    header = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/90.0.4430.212 Safari/537.36",
              "connection": "close",
              "verify": "false"}
    data = {
        'username': user,
        'password': 'P@88w0rd',
        'grant_type': 'password',
        'client_id': 'kubesphere',
        'client_secret': 'kubesphere'
    }
    url = server + '/oauth/token'
    try:
        r = requests.post(url=url, headers=header, data=data)
        if r.status_code == 200:
            token = r.json()['access_token']
        else:
            raise Exception('get token failed!')
    except requests.exceptions.ConnectionError as e:
        print('Error', e.args)

    ks_token = 'Bearer ' + token
    t_data = {
        "token": ks_token
    }
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data=t_data, stream=f, allow_unicode=True)


# 获取系统用户的resourceversion
def get_user_version():
    """
    :return: 系统第一个用户的resourceversion
    """
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/users'
    r = requests.get(url, headers=get_header())
    return r.json()['items'][0]['metadata']['resourceVersion']


# 删除系统用户
def delete_user(user_name):
    """
    :param user_name: 系统用户的名称
    """
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/users/' + user_name
    requests.delete(url, headers=get_header())


# 创建系统角色
def create_role(role_name):
    """
    :param role_name: 系统角色名称
    :return: 创建的系统角色的resourceversion
    """
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/globalroles'
    data = {"apiVersion": "iam.kubesphere.io/v1alpha2",
            "kind": "GlobalRole",
            "rules": [],
            "metadata": {"name": role_name,
                         "annotations": {"kubesphere.io/description": "新建角色",
                                         "iam.kubesphere.io/aggregation-roles": "[\"role-template-manage-clusters\","
                                                                                "\"role-template-view-clusters\","
                                                                                "\"role-template-view-basic\"]",
                                         "kubesphere.io/creator": "admin"}
                         }
            }
    r = requests.post(url, headers=get_header(), data=json.dumps(data))
    return r.json()['metadata']['resourceVersion']


# 获取系统角色的resourceversion
def get_role_version():
    """
    :return: 系统第一个角色的resourceversion
    """
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/globalroles'
    r = requests.get(url, headers=get_header())
    return r.json()['items'][0]['metadata']['resourceVersion']


# 删除系统角色
def delete_role(role_name):
    """
    :param role_name: 系统角色的名称
    """
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/globalroles/' + role_name
    requests.delete(url, headers=get_header())


# 创建企业空间
def create_workspace(ws_name):
    """
    :param ws_name: 企业空间的名称
    """
    url = env_url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces'
    data = {"apiVersion": "tenant.kubesphere.io/v1alpha2",
            "kind": "WorkspaceTemplate",
            "metadata": {"name": ws_name,
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"template": {"spec": {"manager": "admin"}}}}
    requests.post(url, headers=get_header(), data=json.dumps(data))


# 删除企业空间
def delete_workspace(ws_name):
    """
    :param ws_name: 企业空间的名称
    """
    url = env_url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name
    requests.delete(url, headers=get_header())


# 创建企业空间的角色
def create_ws_role(ws_name, ws_role_name):
    """
    :param ws_name: 企业空间的名称
    :param ws_role_name: 企业空间的角色的名称
    """
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/workspaceroles'
    data = {"apiVersion": "iam.kubesphere.io/v1alpha2",
            "kind": "WorkspaceRole",
            "rules": [],
            "metadata": {"name": ws_role_name,
                         "annotations": {"iam.kubesphere.io/aggregation-roles": "[\"role-template-view-basic\"]",
                                         "kubesphere.io/creator": "admin"}
                         }
            }
    requests.post(url, headers=get_header(), data=json.dumps(data))


# 删除企业空间的角色
def delete_ws_role(ws_name, ws_role_name):
    """
    :param ws_name: 企业空间的名称
    :param ws_role_name: 企业空间角色的名称
    """
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/workspaceroles/' + ws_role_name
    requests.delete(url, headers=get_header())


# 邀请用户到企业空间
def ws_invite_user(ws_name, user_name, ws_role):
    """
    :param ws_name: 企业空间的名称
    :param user_name: 系统用户的名称
    :param ws_role: 企业空间的角色
    """
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/workspacemembers'
    data = [{"username": user_name, "roleRef": ws_role}]
    requests.post(url, headers=get_header(), data=json.dumps(data))


# 创建devops工程
def create_devops(ws_name, devops_name):
    """
    :param ws_name: 企业空间的名称
    :param devops_name: devops工程的名称
    :return:
    """
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/workspaces/' + ws_name + '/devops'
    data = {"metadata": {"generateName": devops_name,
                         "labels": {"kubesphere.io/workspace": devops_name},
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "kind": "DevOpsProject",
            "apiVersion": "devops.kubesphere.io/v1alpha3"}
    r = requests.post(url, headers=get_header(), data=json.dumps(data))
    return r.json()['metadata']['name']


# 获取devops工程的resourceversion
def get_devops_resource_version(devops_name, devops_role_name):
    """
    :param devops_name: devops工程的名称
    :param devops_role_name: devops工程的角色的名称
    :return:
    """
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/devops/' + devops_name + '/roles?name=' + devops_role_name + '&sortBy=createTime&limit=10&annotation=kubesphere.io%2Fcreator'
    r = requests.get(url, headers=get_header())
    return r.json()['items'][0]['metadata']['resourceVersion']


# 创建project
def create_project(ws_name, project_name):
    """
    :param ws_name: 企业空间名称
    :param project_name: 项目名称
    """
    url = env_url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/namespaces'
    data = {"apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {"name": project_name,
                         "labels": {"kubesphere.io/workspace": "wx-ws"},
                         "annotations": {"kubesphere.io/creator": "admin"}
                         }
            }
    requests.post(url, headers=get_header(), data=json.dumps(data))


# 删除项目
def delete_project(ws_name, project_name):
    """

    :param ws_name: 企业空间名称
    :param project_name: 项目名称
    """
    url = env_url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/namespaces/' + project_name
    requests.delete(url=url, headers=get_header())


# 在project项目中获取指定角色的resourceversion
def get_project_role_version(project_nmae, project_rloe_name):
    """
    :param project_nmae: 项目名称
    :param project_rloe_name: 项目角色名称
    :return:
    """
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + project_nmae + '/roles?name=' + project_rloe_name
    r = requests.get(url, headers=get_header())
    return r.json()['items'][0]['metadata']['resourceVersion']


# 获取appstore中应用的app_id
def get_app_id(key):
    url = env_url + '/kapis/openpitrix.io/v1/apps??orderBy=create_time&paging=limit%3D12%2Cpage%3D2&conditions=status%3Dactive%2Crepo_id%3Drepo-helm&reverse=true'
    url2 = env_url + '/kapis/openpitrix.io/v1/apps??orderBy=create_time&paging=limit%3D12%2Cpage%3D1&conditions=status%3Dactive%2Crepo_id%3Drepo-helm&reverse=true'
    r = requests.get(url, headers=get_header())  # 获取app的id和name，将其组合成一个字典
    r2 = requests.get(url2, headers=get_header())  # 获取app的id和name，将其组合成一个字典
    item_name = []
    item_id = []

    items = r.json()['items']
    for item in items:
        item_name.append(item['name'])
        item_id.append(item['app_id'])

    items2 = r2.json()['items']
    for item in items2:
        item_name.append(item['name'])
        item_id.append(item['app_id'])
    dic = dict(zip(item_name, item_id))
    return dic[key]


# 获取appstore中应用的version_id
def get_app_version(app_id):
    url = env_url + '/kapis/openpitrix.io/v1/apps/' + app_id
    r = requests.get(url, headers=get_header())
    return r.json()['latest_app_version']['version_id']


# 获取应用模板中获取version_id
def get_app_versions(ws_name, app_id):
    versions = []
    url = env_url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/apps/' + app_id + '/versions?orderBy=sequence&paging=limit%3D10%2Cpage%3D1&conditions=status%3Ddraft%7Csubmitted%7Crejected%7Cin-review%7Cpassed%7Cactive%7Csuspended&reverse=true'
    r = requests.get(url=url, headers=get_header())
    # print(r.json()['items'])
    for item in r.json()['items']:
        # print(item['version_id'])
        versions.append(item['version_id'])

    return versions


# 获取没有version的应用模板的app_id
def get_app_id_noversion(ws_name, app_name):
    url = env_url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/apps?paging=limit%3D10%2Cpage%3D1&conditions=status%3Ddraft%7Cactive%7Csuspended%7Cpassed%2Ckeyword%3D' + app_name
    r = requests.get(url=url, headers=get_header())
    return r.json()['items'][0]['app_id']


# 获取应用商店管理/应用商店中所有的应用的app_id
def get_apps_id():
    apps = []
    for page in (1, 2):
        url = env_url + '/kapis/openpitrix.io/v1/apps?orderBy=create_time&paging=limit%3D10%2Cpage%3D' + str(
            page) + '&conditions=status%3Dactive%7Csuspended%2Crepo_id%3Drepo-helm&reverse=true'
        r = requests.get(url, get_header())
        for item in r.json()['items']:
            apps.append(item['app_id'])
    return apps


# 获取应用商店管理/应用商店页面，所有应用的分类id
def get_app_category():
    app_categorys = []
    for page in (1, 2):
        url = env_url + '/kapis/openpitrix.io/v1/apps?orderBy=create_time&paging=limit%3D10%2Cpage%3D' + str(
            page) + '&conditions=status%3Dactive%7Csuspended%2Crepo_id%3Drepo-helm&reverse=true'
        r = requests.get(url, get_header())
        for item in r.json()['items']:
            for app_category in item['category_set']:
                app_categorys.append(app_category['category_id'])

    for i in app_categorys:
        print(i)


# 生成随机数字，用于拼接名称
def get_random():
    num = random.randint(1, 10000000000)
    return num


# 获取x分钟之前的10位时间戳
def get_before_timestamp(now_time, minutes):
    """
    :param now_time: 当前时间 datetime.datetime.now()
    :return: 多少分钟之前的10位时间戳
    :param minutes: 需要计算多少分钟之前的时间戳
    """
    # 获取当前时间
    now_reduce = now_time - datetime.timedelta(minutes=minutes)
    # 转换成时间数组
    time_array = time.strptime(str(now_reduce)[0:19], "%Y-%m-%d %H:%M:%S")
    # 转换成时间戳
    before_timestamp = str(time.mktime(time_array))[0:10]
    return before_timestamp


# 获取当前日期的时间戳
def get_timestamp():
    now = datetime.datetime.now()
    time_array = time.strptime(str(now)[0:10], "%Y-%m-%d")
    # 转换成时间戳
    time_stamp = str(time.mktime(time_array))[0:10]
    return time_stamp


# 获取当前日期
def get_today():
    now = datetime.datetime.now()
    return str(now)[0:10]


# 获取指定时间的时间戳
def get_custom_timestamp(day, clock):
    return time.mktime(time.strptime(day + ' ' + clock, '%Y-%m-%d %H:%M:%S'))


# 获取x天前日期的时间戳
def get_before_timestamp_day(day):
    before = (datetime.datetime.now() - datetime.timedelta(days=day))
    # 转换为其他字符串格式
    other_style_time = time.strptime(str(before)[0:10], "%Y-%m-%d")
    # 转换成时间戳
    time_stamp = str(time.mktime(other_style_time))[0:10]
    return time_stamp


# 获取集群所有服务组件的状态
def get_component_health_of_cluster(namespace_actual):
    if check_multi_cluster() is True:
        # 获取多集群环境的host集群的名称
        host_name = multi_cluster_steps.step_get_host_cluster_name()
        url = env_url + '/kapis/clusters/' + host_name + '/resources.kubesphere.io/v1alpha2/components'
    else:
        url = env_url + '/kapis/resources.kubesphere.io/v1alpha2/components'
    response = requests.get(url=url, headers=get_header())
    # 获取集群的组件数量
    components_count = len(response.json())
    not_ready_namespace = []
    for i in range(0, components_count):
        # 获取组件的名称及namespace
        component_name = response.json()[i]['name']
        namespace = response.json()[i]['namespace']
        # 获取组件的健康状态
        healthy_backends = response.json()[i]['healthyBackends']
        total_backends = response.json()[i]['totalBackends']
        if healthy_backends != total_backends:
            print('NameSpace: ' + namespace + '  组件：' + component_name + '状态异常！')
            not_ready_namespace.append(namespace)
    if namespace_actual in not_ready_namespace:
        return False
    else:
        return True


# 获取集群的组件开启情况
def get_components_status_of_cluster(component):
    url = env_url + '/apis/installer.kubesphere.io/v1alpha1/clusterconfigurations'
    response = requests.get(url=url, headers=get_header())
    # 获取组件的配置信息
    spec = response.json()['items'][0]['spec']
    # 获取组件信息
    if component == 'openpitrix':
        component_status = spec[component]['store']['enabled']
    elif component == 'network':
        component_status = spec[component]['networkpolicy']['enabled']
    elif component == 'whizard':
        component_status = spec['monitoring']['whizard']['enabled']
    elif component == 'kubeedge':
        component_status = spec['edgeruntime']['kubeedge']['enabled']
    else:
        component_status = spec[component]['enabled']
    return component_status


# 获取多集群环境中各个集群的组件开启情况
def get_components_status_of_multi_cluster(cluster_name, component):
    url = env_url + '/apis/clusters/' + cluster_name + '/installer.kubesphere.io/v1alpha1/clusterconfigurations'
    response = requests.get(url=url, headers=get_header())
    # 获取组件的配置信息
    spec = response.json()['items'][0]['spec']
    # 获取组件信息
    if component == 'openpitrix':
        component_status = spec[component]['store']['enabled']
    elif component == 'network':
        component_status = spec[component]['networkpolicy']['enabled']
    else:
        component_status = spec[component]['enabled']
    return component_status


# 判断环境是否开启多集群功能
def check_multi_cluster():
    url = env_url + '/apis/installer.kubesphere.io/v1alpha1/clusterconfigurations'
    response = requests.get(url=url, headers=get_header())
    # 查询多集群功能是否启用
    try:
        multicluster_status = response.json()['items'][0]['status']['multicluster']['status']
        if multicluster_status == 'enabled':
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False


# 获取ippool组件状态
def get_ippool_status():
    url = env_url + '/apis/installer.kubesphere.io/v1alpha1/clusterconfigurations'
    response = requests.get(url=url, headers=get_header())
    te = response.json()['items'][0]['spec']['network']['ippool']['type']
    if te == 'calico':
        return True
    else:
        return False


# 测试方法、发起请求、结果校验
def request_resource(url, params, data, story, title, method, severity, condition, except_result):
    if 'http' not in url:
        if params != '':
            url_new = env_url + url + '?' + params
        else:
            url_new = env_url + url
    else:
        if params != '':
            url_new = url + '?' + params
        else:
            url_new = url
    if method == 'get':
        # 测试get方法
        r = requests.get(url_new, headers=get_header())

    elif method == 'post':
        # 测试post方法
        data = eval(data)
        r = requests.post(url_new, headers=get_header(), data=json.dumps(data))

    elif method == 'patch':
        # 测试patch方法
        data = eval(data)
        r = requests.patch(url_new, headers=get_header_for_patch(), data=json.dumps(data))

    elif method == 'delete':
        # 测试delete方法
        r = requests.delete(url_new, headers=get_header())

    # 将校验条件和预期结果参数化
    time.sleep(1)
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
                                 '用例请求的URL地址: ' + str(url_new) + '\n'
                                                                        '用例使用的请求数据: ' + str(data) + '\n'
                                                                                                             '用例模块: ' + story + '\n'
                                                                                                                                    '用例标题: ' + title + '\n'
                                                                                                                                                           '用例的请求方式: ' + method + '\n '
                                                                                                                                                                                         '用例优先级: ' + severity + '\n'
                                                                                                                                                                                                                     '用例的校验条件: ' + str(
            condition) + '\n'
                         '用例的实际结果: ' + str(condition_new) + '\n'
                                                                   '用例的预期结果: ' + str(except_result)
    )


# 替换字符串中的指定内容
def replace_str(*targets, actual_value, expect_value):
    target_new = []
    for target in targets:
        # 将参数转换为字符类型，然后判断其是否由数字组成
        if str(target).isdigit() is True:
            target_new.append(int(target))
        elif target != '' and isinstance(target, str):
            target_new.append(target.replace(actual_value, expect_value))
        else:
            target_new.append('')
    return target_new


# 创建随机ip
def random_ip():
    m = random.randint(0, 255)
    n = random.randint(0, 255)
    x = random.randint(0, 255)
    y = random.randint(0, 255)
    return str(m) + '.' + str(n) + '.' + str(x) + '.' + str(y)


# 查询csi-qingcloud组件
def get_sc_qingcloud():
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/deployments?name=csi-qingcloud&sortBy=updateTime&limit=10'
    r = requests.get(url=url, headers=get_header())
    if r.json()['totalItems'] == 0:
        return False
    elif r.json()['totalItems'] == 1:
        i = 0
        while i < 120:
            r1 = requests.get(url=url, headers=get_header())
            if r1.json()['items'][0]['status']['readyReplicas'] == r1.json()['items'][0]['status']['replicas']:
                break
            sleep(3)
            i = i + 3
        if r1.json()['items'][0]['status']['readyReplicas'] == r1.json()['items'][0]['status']['replicas']:
            return True
        else:
            return False


# 查询多集群csi-qingcloud组件
def get_multi_cluster_sc_qingcloud():
    if check_multi_cluster() is False:
        return False
    else:
        cluster_name = multi_cluster_steps.step_get_host_cluster_name()
        url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/deployments?name=csi-qingcloud&sortBy=updateTime&limit=10'
        r = requests.get(url=url, headers=get_header())
        if r.json()['totalItems'] == 0:
            return False
        elif r.json()['totalItems'] == 1:
            i = 0
            while i < 120:
                r1 = requests.get(url=url, headers=get_header())
                if r1.json()['items'][0]['status']['readyReplicas'] == r1.json()['items'][0]['status']['replicas']:
                    break
                sleep(3)
                i = i + 3
            if r1.json()['items'][0]['status']['readyReplicas'] == r1.json()['items'][0]['status']['replicas']:
                return True
            else:
                return False


# 读取excle数据，并将其写入yaml文件
def write_data_excle_to_yaml(filename, sheet_name):
    # 从excle中读取数据
    p = DoexcleByPandas().get_data_for_pytest(filename, sheet_name)
    # 将数据写入yaml
    with open('../data/storage.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(data=p, stream=f, allow_unicode=True)


# 获取测试环境信息
def write_environment_info():
    # 判断集群类型，是否为多集群
    cluster_type = check_multi_cluster()
    # 如果是单集群环境
    if cluster_type is False:
        response = cluster_steps.step_get_cluster_info()
        # 测试环境信息
        env = {
            "TEST_URL": env_url,
            "KS_VERSION": response.json()['gitVersion'],
            "K8S_VERSION": response.json()['kubernetes']['gitVersion'],
            "PLATFORM": response.json()['platform']
        }
    # 如果是多集群环境
    else:
        response = multi_cluster_steps.step_get_cluster()
        # 获取集群数量
        cluster_count = response.json()['totalItems']
        # 获取所有集群的名称
        cluster_names = []
        for i in range(cluster_count):
            cluster_names.append(response.json()['items'][i]['metadata']['name'])
        env = {
            "TEST_URL": env_url,
            "CLUSTER_NAME": cluster_names,
        }
    # 将测试环境信息写入yaml文件
    with open('../environment.properties', 'w', encoding='utf-8') as f:
        yaml.dump(env, f, sort_keys=False)


# 在多集群环境，验证非联邦项目的工作负载状态为ready
def check_workload_ready_in_multi(cluster_name, project_name, resource_type, resource_name):
    i = 0
    while i < 180:
        # 获取多集群环境中的工作负载
        response = multi_cluster_steps.step_get_app_workload_detail(cluster_name, project_name, resource_type,
                                                                    resource_name)
        # 判断工作负载的状态是否为ready
        if 'unavailableReplicas' not in response.json()['items'][0]['status']:
            return True
        else:
            sleep(3)
            i = i + 3


# 在多集群环境，验证非联邦项目的工作负载不存在
def check_workload_not_exist_in_multi(cluster_name, project_name, resource_type, resource_name):
    i = 0
    while i < 180:
        # 获取多集群环境中的工作负载
        response = multi_cluster_steps.step_get_app_workload_detail(cluster_name, project_name, resource_type,
                                                                    resource_name)
        # 判断工作负载不存在
        if response.status_code == 404:
            return True
        else:
            sleep(3)
            i = i + 3


# 在多集群环境，验证联邦项目的工作负载状态为ready
def check_workload_ready_in_multi_federated(cluster_name, project_name, resource_type, resource_name, replicas):
    i = 0
    while i < 180:
        response = multi_project_steps.step_get_workload_in_multi_project(cluster_name, project_name, resource_type, resource_name)
        try:
            ready_replicas = response.json()['status']['readyReplicas']
            if ready_replicas == replicas:
                return True
        except Exception as e:
            print(e)
        time.sleep(5)
        i += 5
    return False
