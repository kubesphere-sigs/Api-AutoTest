import requests
import json
import allure
import sys

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from config import config
from common.getHeader import get_header, get_header_for_patch


@allure.step('创建devops工程并获取工程名称')
def step_create_devops(ws_name, devops_name):
    """
    :param ws_name: 企业空间的名称
    :param devops_name: devops工程的名称
    :return:devops工程名称
    """
    url = config.url + '/kapis/devops.kubesphere.io/v1alpha3/workspaces/' + ws_name + '/devops'
    data = {"metadata": {"generateName": devops_name,
                         "labels": {"kubesphere.io/workspace": ws_name},
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "kind": "DevOpsProject",
            "apiVersion": "devops.kubesphere.io/v1alpha3"}
    requests.post(url, headers=get_header(), data=json.dumps(data))


@allure.story('查询devops工程')
def step_search_devops(ws_name, condition):
    """
    :param ws_name: 企业空间
    :param condition: 查询条件
    :return: 查询结果
    """
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/devops?name=' + condition + '&limit=10'
    r = requests.get(url=url, headers=get_header())
    if r.json()['totalItems'] != 0:
        return r.json()['items'][0]['metadata']['name']
    else:
        return r.json()['totalItems']


@allure.step('获取devops工程的详细信息')
def step_get_devopinfo(ws_name, devops_name):
    """
    :param ws_name: 企业空间名称
    :param devop_name: devops工程的名称
    :return: devops工程的详细信息
    """
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/devops?name=' + devops_name + '&limit=10'
    print(url)
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('修改devops工程基本信息')
def step_modify_devinfo(ws_name, devops_name, data):
    """
    :return: devops工程的别名
    :param ws_name: 企业空间名称
    :param devop_name: devops工程的名称
    :param data: devops工程的详细信息
    """
    url = config.url + '/kapis/devops.kubesphere.io/v1alpha3/workspaces/' + ws_name + '/devops/' + devops_name
    r = requests.put(url=url, headers=get_header_for_patch(), data=json.dumps(data))

    return r.json()['metadata']['annotations']['kubesphere.io/alias-name']


@allure.step('查询凭证')
def step_search_credential(devops_name, condition):
    """
    :param devops_name: devops名称
    :param condition: 查询条件
    :return: 查询结果
    """
    url = config.url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + devops_name + '/credentials?' \
                                                                                      'name=' + condition + '&limit=10&sortBy=createTime'
    r = requests.get(url=url, headers=get_header())
    if r.json()['totalItems'] != 0:
        return r.json()['items'][0]['metadata']['name']
    else:
        return r.json()['totalItems']


@allure.step('查询凭证')
def step_get_credential(devops_name, condition):
    """
    :param devops_name: devops名称
    :param condition: 查询条件
    :return: 查询结果
    """
    url = config.url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + devops_name + '/credentials?' \
                                                                                      'name=' + condition + '&limit=10&sortBy=createTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('获取所有凭证的名称')
def step_get_credentials_name(devops_name):
    """
    :param devop_name: devops工程的名称
    :return: devops工程中所有的凭证名称
    """
    url = config.url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + devops_name + '/credentials?limit=10&sortBy=createTime'
    r = requests.get(url=url, headers=get_header())
    count = r.json()['totalItems']  # 得到凭证的数量
    credentials_name = []  # 存放凭证名称的数组
    for i in range(count):
        name = r.json()['items'][i]['metadata']['name']
        credentials_name.append(name)

    return credentials_name


@allure.step('删除凭证')
def step_delete_credential(devops_name, credential_name):
    """
    :param devop_name: devops工程名称
    :param credential_name: devops工程中的凭证名称
    :return: 删除结果
    """
    url = config.url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + devops_name + '/credentials/' + credential_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('创建devops工程角色')
def step_create_role(devops_name, role_name):
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + devops_name + '/roles'
    data = {"apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "Role",
            "metadata":
                {"namespace": devops_name,
                 "name": role_name,
                 "annotations":
                     {"iam.kubesphere.io/aggregation-roles": "[\"role-template-manage-pipelines\","
                                                             "\"role-template-view-pipelines\","
                                                             "\"role-template-view-credentials\","
                                                             "\"role-template-view-basic\"]",
                      "kubesphere.io/creator": "admin"}}, "rules": []}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('编辑devops角色的权限信息')
def step_edit_role_authority(devops_name, role_name, annotations, resourceVersion):
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + devops_name + '/roles/' + role_name
    data = {"apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "Role",
            "metadata": {"name": role_name,
                         "namespace": devops_name,
                         "annotations": annotations,
                        "resourceVersion": resourceVersion}
            }
    response = requests.put(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('编辑devops角色的基本信息')
def step_edit_role_info(devops_name, role_name, alias, description):
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + devops_name + '/roles/' + role_name
    data = {"metadata":
                {"name": role_name,
                 "namespace": devops_name,
                 "annotations": {"iam.kubesphere.io/aggregation-roles": "[\"role-template-view-pipelines\","
                                                                        "\"role-template-view-credentials\","
                                                                        "\"role-template-view-basic\"]",
                                 "kubesphere.io/creator": "admin",
                                 "kubesphere.io/alias-name": alias,
                                 "kubesphere.io/description": description}
                 }
            }
    response = requests.patch(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('查询指定的devops角色')
def step_get_role(devope_name, role_name):
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/devops/' + devope_name + '/roles?' \
                       'name=' + role_name + '&sortBy=createTime&limit=10&annotation=kubesphere.io%2Fcreator'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('删除devops角色')
def step_delete_role(devops_name, role_name):
    url = config.url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + devops_name + '/roles/' + role_name
    requests.delete(url, headers=get_header())


@allure.step('删除devops工程')
def step_delete_devops(ws_name, devops_name):
    """
    :param ws_name: 企业空间名称
    :param devops_name: devops工程名称
    :return: 删除结果
    """
    url = config.url + '/kapis/devops.kubesphere.io/v1alpha3/workspaces/' + ws_name + '/devops/' + devops_name
    r = requests.delete(url=url, headers=get_header())
    # 返回删除结果
    return r.json()['message']


@allure.step('获取指定流水线的uid、resourceVersion、creationTimestamp')
def step_get_pipeline_data(devops_name_new, pipline_name):
    """
    :param devops_name_new: devops工程的id
    :param pipline_name: 流水线的名称
    :return: 流水线的uid，resourceversion，creationTimestamp
    """
    url = config.url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + devops_name_new + '/pipelines/' + pipline_name
    r = requests.get(url=url, headers=get_header())
    return r.json()['metadata']['resourceVersion'], r.json()['metadata']['uid'], r.json()['metadata'][
        'creationTimestamp']


@allure.step('checkScriptCompile')
def step_pipeline_check_script_compile(devops_name_new, pipeline_name, data):
    url = config.url + '/kapis/devops.kubesphere.io/v1alpha2/devops/' + devops_name_new + '/pipelines/' \
          + pipeline_name + '/checkScriptCompile'
    print(url)
    header = {
        'Authorization': get_token(config.url),
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    r = requests.post(url=url, headers=header, data=data)
    print(r.text)


@allure.step('运行流水线')
def step_run_pipeline(devops_name_new, pipeline_name):
    """
    :param devops_name_new: devops工程的id
    :param pipeline_name: 流水线名称
    :return: 运行结果中的某个字段
    """
    url = config.url + '/kapis/devops.kubesphere.io/v1alpha2/devops/' + devops_name_new + '/pipelines/' + pipeline_name + '/runs'
    data = {"parameters": []}
    r = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    # 返回运行结果中的某个字段
    return r.json()['organization']


@allure.step('验证流水线运行结果')
def step_get_pipeline_status(devops_name_new, pipeline_name):
    url = config.url + '/kapis/devops.kubesphere.io/v1alpha2/devops/' + devops_name_new + '/pipelines/' + pipeline_name + '/runs/?start=0&limit=10'
    r = requests.get(url=url, headers=get_header())
    return r.json()['items'][0]['result']


@allure.step('删除流水线')
def step_delete_pipeline(devops_name_new, pipeline_name):
    url = config.url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + devops_name_new + '/pipelines/' + pipeline_name
    r = requests.delete(url=url, headers=get_header())
    return r.json()['message']


@allure.step('创建账户类型凭证')
def step_create_account_credential(devops_name, name):
    url = config.url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + devops_name + '/credentials'
    name = name
    description = '我是描述信息'
    username = 'YWRtaW4='
    password = 'Z2hwX0lvOWRwaTdiQWJyelRvSGxZeWlyam9rek5BQ2JVNDRlbGEwYw=='

    data = {"apiVersion": "v1", "kind": "Secret",
            "metadata": {"namespace": devops_name,
                         "labels": {"app": name},
                         "annotations": {"kubesphere.io/description": description,
                                         "kubesphere.io/creator": "admin"},
                         "name": name},
            "type": "credential.devops.kubesphere.io/basic-auth",
            "data": {"username": username, "password": password
                     }
            }
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('创建ssh凭证')
def step_create_ssh_credential(devops_name, name):
    url = config.url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + devops_name + '/credentials'
    username = 'cXdl'
    private_key = 'YXNk'

    data = {"apiVersion": "v1", "kind": "Secret",
            "metadata": {"namespace": devops_name,
                         "labels": {"app": name}, "annotations": {"kubesphere.io/creator": "admin"}, "name": name},
            "type": "credential.devops.kubesphere.io/ssh-auth",
            "data": {"username": username, "private_key": private_key}}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('基于github创建多分支流水线')
def step_create_pipeline_base_github(devops, devops_name, pipeline_name, credential_name, patch, tags):
    url = config.url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + devops_name + '/pipelines'
    data = {"devopsName": "dev",
            "metadata": {"name": pipeline_name,
                         "namespace": devops_name,
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"multi_branch_pipeline":
                         {"source_type": "github",
                          "github_source":
                              {"repo": "devops-multi",
                               "credential_id": credential_name,
                               "owner": "wenxin-01",
                               "discover_branches": 1,
                               "discover_pr_from_forks": {"strategy": 2, "trust": 2},
                               "discover_pr_from_origin": 2,
                               "discover_tags": tags,
                               "description": "test-devops",
                               "git_clone_option": {"depth": 1, "timeout": 20}},
                          "discarder": {"days_to_keep": "-1", "num_to_keep": "-1"},
                          "script_path": patch,
                          "devopsName": devops,
                          "cluster": "default",
                          "devops": devops_name,
                          "enable_timer_trigger": False,
                          "enable_discarder": True,
                          "name": pipeline_name,
                          "discover_branches": 1,
                          "discover_tags": tags,
                          "discover_pr_from_origin": 2,
                          "discover_pr_from_forks": {"strategy": 2, "trust": 2}},
                     "type": "multi-branch-pipeline"},
            "kind": "Pipeline",
            "apiVersion": "devops.kubesphere.io/v1alpha3"}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('基于gitlab创建流水线')
def step_create_pipeline_base_gitlab(devops, devops_name, pipeline_name, tags):
    url = config.url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + devops_name + '/pipelines'
    data = {"devopsName": devops_name,
            "metadata": {"name": pipeline_name,
                        "namespace": devops_name,
                        "annotations": {"kubesphere.io/creator": "admin"}
                        },
            "spec": {"multi_branch_pipeline":
                        {"source_type": "gitlab",
                         "gitlab_source": {"server_name": "https://gitlab.com",
                                          "owner": "wxsunshine",
                                          "repo": "wxsunshine/test-public",
                                          "discover_branches": 1,
                                          "discover_pr_from_forks": {"strategy": 2, "trust": 2},
                                          "discover_pr_from_origin": 2,
                                          "discover_tags": True},
                         "discarder": {"days_to_keep": "7", "num_to_keep": "5"},
                         "script_path": "jenkinsfile/test1",
                         "devopsName": devops,
                         "cluster": "default",
                         "devops": devops_name,
                         "enable_timer_trigger": False,
                         "enable_discarder": True,
                         "name": pipeline_name,
                         "discover_branches": 1,
                         "discover_tags": tags,
                         "discover_pr_from_origin": 2,
                         "discover_pr_from_forks": {"strategy": 2, "trust": 2}},
                    "type": "multi-branch-pipeline"},
            "kind": "Pipeline", "apiVersion": "devops.kubesphere.io/v1alpha3"}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('使用图形化的方式创建流水线')
def step_create_pipeline(devops, devops_name, pipeline_name):
    url = config.url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + devops_name + '/pipelines'
    data = {"devopsName": devops,
            "metadata": {"name": pipeline_name, "namespace": devops_name,
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"pipeline": {"discarder": {"days_to_keep": "7", "num_to_keep": "10"}, "devopsName": devops,
                                  "cluster": "default", "devops": devops_name, "enable_timer_trigger": False,
                                  "enable_discarder": True, "name": "test"}, "type": "pipeline"}, "kind": "Pipeline",
            "apiVersion": "devops.kubesphere.io/v1alpha3"}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('查询指定的流水线')
def step_get_pipeline(devops_name, pipeline_name):
    url = config.url + '/kapis/devops.kubesphere.io/v1alpha2/search?start=0&limit=10&q=type%3Apipeline%3Borganization' \
                       '%3Ajenkins%3Bpipeline%3A' + devops_name + '%2F%2A' + pipeline_name + \
          '%2A%3BexcludedFromFlattening%3Ajenkins.branch.MultiBranchProject' \
          '%2Chudson.matrix.MatrixProject&filter=no-folders'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('删除流水线')
def step_delete_pipeline(devops_name, pipeline_name):
    url = config.url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + devops_name + '/pipelines/' + pipeline_name
    response = requests.delete(url=url, headers=get_header())
    return response
