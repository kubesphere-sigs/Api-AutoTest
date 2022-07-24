import requests
import json
import allure
import sys

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from common.getHeader import get_header
from common import commonFunction
from common.getConfig import get_apiserver

env_url = get_apiserver()


@allure.step('新建角色')
def step_create_role(role_name):
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/globalroles'
    data = {"apiVersion": "iam.kubesphere.io/v1alpha2",
            "kind": "GlobalRole",
            "rules": [],
            "metadata":
                {
                    "name": role_name,
                    "annotations": {
                        "iam.kubesphere.io/aggregation-roles":
                            "[\"role-template-manage-clusters\",\"role-template-view-clusters\","
                            "\"role-template-view-basic\"]",
                        "kubesphere.io/creator": "admin"
                    }
                }
            }
    r = requests.post(url, headers=get_header(), data=json.dumps(data))
    return r


@allure.step('编辑角色权限')
def step_edit_role_authority(role_name, version, authority):
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/globalroles/' + role_name
    data = {"apiVersion": "iam.kubesphere.io/v1alpha2",
            "kind": "GlobalRole",
            "rules": [{"verbs": ["*"], "apiGroups": ["*"], "resources": ["globalroles"]},
                      {"verbs": ["get", "list", "watch"], "apiGroups": ["iam.kubesphere.io"],
                       "resources": ["globalroles"]}, {"verbs": ["get", "list", "watch"], "apiGroups": ["*"],
                                                       "resources": ["users", "users/loginrecords"]}],
            "metadata": {"name": role_name, "labels": {"kubefed.io/managed": "false"}, "annotations": {
                "iam.kubesphere.io/aggregation-roles": authority,
                "kubesphere.io/creator": "admin"}, "resourceVersion": version}}
    r = requests.put(url, headers=get_header(), data=json.dumps(data))
    return r


@allure.step('查询角色信息')
def step_get_role_info(role_name):
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/globalroles?name=' + role_name + \
          '&annotation=kubesphere.io%2Fcreator'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('获取角色权限列表')
def step_get_role_authority(role_name):
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/globalroles/' + role_name
    response = requests.get(url=url, headers=get_header())
    return response.json()['metadata']['annotations']['iam.kubesphere.io/aggregation-roles']


@allure.step('获取角色授权用户')
def step_get_role_user(role_name):
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/users?globalrole=' + role_name + '&sortBy=createTime&limit=10'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('删除角色')
def step_delete_role(role_name):
    """
    :param role_name: 系统角色的名称
    """
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/globalroles/' + role_name
    response = requests.delete(url, headers=get_header())
    return response


@allure.step('创建用户')
def step_create_user(user_name, role):
    email = 'qq' + str(commonFunction.get_random()) + '@qq.com'
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/users'
    data = {"apiVersion": "iam.kubesphere.io/v1alpha2",
            "kind": "User",
            "metadata": {"name": user_name,
                         "annotations":
                             {"iam.kubesphere.io/globalrole": role,
                              "iam.kubesphere.io/uninitialized": "true",
                              "kubesphere.io/creator": "admin"}},
            "spec": {"email": email, "password": "P@88w0rd"}}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('查看用户详情')
def step_get_user_info(user_name):
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/users/' + user_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('删除用户')
def step_delete_user(user_name):
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/users/' + user_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('获取用户登陆ks的headers')
def step_get_headers(user_name, pwd):
    header = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/90.0.4430.212 Safari/537.36",
              "connection": "close",
              "verify": "false"}
    data = {
        'username': user_name,
        'password': pwd,
        'grant_type': 'password',
        'client_id': 'kubesphere',
        'client_secret': 'kubesphere'
    }
    url = env_url + '/oauth/token'
    response = requests.post(url=url, headers=header, data=data)
    ks_token = 'Bearer ' + response.json()['access_token']
    headers = {
        'Authorization': ks_token,
        'Content-Type': 'application/json',
        'Connection': 'close'
    }
    return headers


@allure.step('获取系统用户的resourceversion')
def step_get_user_version(user_name):
    """
    :return: 系统第一个用户的resourceversion
    """
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/users?name=' + user_name
    r = requests.get(url, headers=get_header())
    return r.json()['items'][0]['metadata']['resourceVersion']


@allure.step('编辑用户信息')
def step_edit_user(user_name, role, description, version, email):
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/users/' + user_name
    # 编辑用户的目标数据
    data = {"apiVersion": "iam.kubesphere.io/v1alpha2",
            "kind": "User",
            "metadata": {"name": user_name,
                         "annotations": {
                             "iam.kubesphere.io/globalrole": role,
                             "iam.kubesphere.io/uninitialized": "true",
                             "kubesphere.io/creator": "admin",
                             "kubesphere.io/description": description},
                         "finalizers": ["finalizers.kubesphere.io/users"],
                         "resourceVersion": version},
            "spec": {"email": email}}
    response = requests.put(url, headers=get_header(), data=json.dumps(data))  # 修改新建用户的邮箱和描述信息
    return response


@allure.step('修改用户密码')
def step_modify_user_pwd(user_name, headers, new_pwd):
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/users/' + user_name + '/password'
    data = {"currentPassword": "P@88w0rd", "password": new_pwd}
    response = requests.put(url=url, headers=headers, data=json.dumps(data))
    return response


@allure.step('从工作台获取平台信息')
def step_get_base_info(start_time, end_time, step, times):
    url = env_url + '/kapis/monitoring.kubesphere.io/v1alpha3/kubesphere?start=' + start_time + \
          '&end=' + end_time + '&step=' + step + 's&times=' + times + '&metrics_filter=kubesphere_cluser_count%7C' \
          'kubesphere_workspace_count%7Ckubesphere_user_count%7Ckubesphere_app_template_count%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询平台的企业空间信息')
def step_get_ws_info():
    url = env_url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询平台的用户信息')
def step_get_user_info(user_name):
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/users?name=' + user_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询平台的应用模版信息')
def step_get_app_info():
    url = env_url + '/kapis/openpitrix.io/v1/apps?orderBy=create_time&paging=limit%3D12%2Cpage%3D1&' \
                       'conditions=status%3Dactive%2Crepo_id%3Drepo-helm&reverse=true'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('获取集群的kubeconfig信息')
def step_get_kubeconfig():
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha2/users/admin/kubeconfig'
    response = requests.get(url=url, headers=get_header())
    return response



