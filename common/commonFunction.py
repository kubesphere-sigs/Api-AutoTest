import requests
import json
import random
from config import config
from common.getHeader import get_header
import time
import datetime


# 创建系统用户
def create_user(user_name):
    """
    :param user_name: 系统用户的名称
    """
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/users'
    data = {"apiVersion": "iam.kubesphere.io/v1alpha2",
            "kind": "User",
            "metadata": {"name": user_name,
                         "annotations": {"kubesphere.io/creator": "admin"}
                         },
            "spec": {"email": "stevewen@yunify.com",
                     "password": "P@88w0rd"}
            }
    requests.post(url, headers=get_header(), data=json.dumps(data))


# 获取系统用户的resourceversion
def get_user_version():
    """
    :return: 系统第一个用户的resourceversion
    """
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/users'
    r = requests.get(url, headers=get_header())
    return r.json()['items'][0]['metadata']['resourceVersion']


# 删除系统用户
def delete_user(user_name):
    """
    :param user_name: 系统用户的名称
    """
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/users/' + user_name
    requests.delete(url, headers=get_header())


# 创建系统角色
def create_role(role_name):
    """
    :param role_name: 系统角色名称
    :return: 创建的系统角色的resourceversion
    """
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/globalroles'
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
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/globalroles'
    r = requests.get(url, headers=get_header())
    return r.json()['items'][0]['metadata']['resourceVersion']


# 删除系统角色
def delete_role(role_name):
    """
    :param role_name: 系统角色的名称
    """
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/globalroles/' + role_name
    requests.delete(url, headers=get_header())


# 创建企业空间
def create_workspace(ws_name):
    """
    :param ws_name: 企业空间的名称
    """
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces'
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
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name
    requests.delete(url, headers=get_header())


# 创建企业空间的角色
def create_ws_role(ws_name, ws_role_name):
    """
    :param ws_name: 企业空间的名称
    :param ws_role_name: 企业空间的角色的名称
    """
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/workspaceroles'
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
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/workspaceroles/' + ws_role_name
    requests.delete(url, headers=get_header())


# 获取企业空间的角色的resourceversion
def get_ws_role_version(ws_name):
    """
    :param ws_name: 企业空间的名称
    :return: 企业空间中第一个角色的resourceversion
    """
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/workspaceroles'
    r = requests.get(url, headers=get_header())
    return r.json()['items'][0]['metadata']['resourceVersion']


# 邀请用户到企业空间
def ws_invite_user(ws_name, user_name, ws_role):
    """
    :param ws_name: 企业空间的名称
    :param user_name: 系统用户的名称
    :param ws_role: 企业空间的角色
    """
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/workspacemembers'
    data = [{"username": user_name, "roleRef": ws_role}]
    requests.post(url, headers=get_header(), data=json.dumps(data))


# 创建devops工程
def create_devops(ws_name, devops_name):
    """
    :param ws_name: 企业空间的名称
    :param devops_name: devops工程的名称
    :return:
    """
    url = config.url + '/kapis/devops.kubesphere.io/v1alpha3/workspaces/' + ws_name + '/devops'
    data = {"metadata": {"generateName": devops_name,
                         "labels": {"kubesphere.io/workspace": devops_name},
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "kind": "DevOpsProject",
            "apiVersion": "devops.kubesphere.io/v1alpha3"}
    r = requests.post(url, headers=get_header(), data=json.dumps(data))
    return r.json()['metadata']['name']


# 获取devops工程的resourceversion
def get_devops_resourceVersion(devops_name, devops_role_name):
    """
    :param devops_name: devops工程的名称
    :param devops_role_name: devops工程的角色的名称
    :return:
    """
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/devops/' + devops_name + '/roles?name=' + devops_role_name + '&sortBy=createTime&limit=10&annotation=kubesphere.io%2Fcreator'
    r = requests.get(url, headers=get_header())
    return r.json()['items'][0]['metadata']['resourceVersion']


# 创建project
def create_project(ws_name, project_name):
    """
    :param ws_name: 企业空间名称
    :param project_name: 项目名称
    """
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/namespaces'
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
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/namespaces/' + project_name
    requests.delete(url=url, headers=get_header())


# 在project项目中获取指定角色的resourceversion
def get_project_role_version(project_nmae, project_rloe_name):
    """
    :param project_nmae: 项目名称
    :param project_rloe_name: 项目角色名称
    :return:
    """
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + project_nmae + '/roles?name=' + project_rloe_name
    r = requests.get(url, headers=get_header())
    return r.json()['items'][0]['metadata']['resourceVersion']


# 获取appstore中应用的app_id
def get_app_id(key):
    url = config.url + '/kapis/openpitrix.io/v1/apps??orderBy=create_time&paging=limit%3D12%2Cpage%3D2&conditions=status%3Dactive%2Crepo_id%3Drepo-helm&reverse=true'
    url2 = config.url + '/kapis/openpitrix.io/v1/apps??orderBy=create_time&paging=limit%3D12%2Cpage%3D1&conditions=status%3Dactive%2Crepo_id%3Drepo-helm&reverse=true'
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
    url = config.url + '/kapis/openpitrix.io/v1/apps/' + app_id
    r = requests.get(url, headers=get_header())
    return r.json()['latest_app_version']['version_id']


# 获取应用模板中获取version_id
def get_app_versions(ws_name, app_id):
    versions = []
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/apps/' + app_id + '/versions?orderBy=sequence&paging=limit%3D10%2Cpage%3D1&conditions=status%3Ddraft%7Csubmitted%7Crejected%7Cin-review%7Cpassed%7Cactive%7Csuspended&reverse=true'
    r = requests.get(url=url, headers=get_header())
    # print(r.json()['items'])
    for item in r.json()['items']:
        # print(item['version_id'])
        versions.append(item['version_id'])

    return versions


# 获取没有version的应用模板的app_id
def get_app_id_noversion(ws_name, app_name):
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/apps?paging=limit%3D10%2Cpage%3D1&conditions=status%3Ddraft%7Cactive%7Csuspended%7Cpassed%2Ckeyword%3D' + app_name
    r = requests.get(url=url, headers=get_header())
    return r.json()['items'][0]['app_id']


# 获取应用商店管理/应用商店中所有的应用的app_id
def get_apps_id():
    apps = []
    for page in (1, 2):
        url = config.url + '/kapis/openpitrix.io/v1/apps?orderBy=create_time&paging=limit%3D10%2Cpage%3D' + str(
            page) + '&conditions=status%3Dactive%7Csuspended%2Crepo_id%3Drepo-helm&reverse=true'
        r = requests.get(url, get_header())
        for item in r.json()['items']:
            apps.append(item['app_id'])
    return apps


# 获取应用商店管理/应用商店页面，所有应用的分类id
def get_app_category():
    appCategorys = []
    for page in (1, 2):
        url = config.url + '/kapis/openpitrix.io/v1/apps?orderBy=create_time&paging=limit%3D10%2Cpage%3D' + str(
            page) + '&conditions=status%3Dactive%7Csuspended%2Crepo_id%3Drepo-helm&reverse=true'
        r = requests.get(url, get_header())
        # print(r.json()['items'])
        for item in r.json()['items']:
            for appCategory in item['category_set']:
                appCategorys.append(appCategory['category_id'])

    for i in appCategorys:
        print(i)


# 生成随机数字，用于拼接名称
def get_random():
    num = random.randint(1, 1000000)
    return num


# 获取x分钟之前的10位时间戳
def get_before_timestamp(minutes):
    """
    :return: 多少分钟之前的10位时间戳
    :param minutes: 需要计算多少分钟之前的时间戳
    """
    # 获取当前时间
    now = datetime.datetime.now()
    now_reduce = now - datetime.timedelta(minutes=minutes)
    # 转换成时间数组
    timeArray = time.strptime(str(now_reduce)[0:19], "%Y-%m-%d %H:%M:%S")
    # 转换成时间戳
    before_timestamp = str(time.mktime(timeArray))[0:10]
    return before_timestamp


# 获取集群的所有服务组件
def get_components_of_cluster():
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha2/components'
    response = requests.get(url=url, headers=get_header())
    namespaces = []
    try:
        for i in range(0, 100):
            namespaces.append(response.json()[i]['namespace'])
    except Exception as e:
        print(e)
    # 将list转换为set，以达到去重的目的，然后再转换为list。(ps：set是无序的，所以转换为list后的顺序和接口返回的namespaces的顺序不一致)
    return list(set(namespaces))

