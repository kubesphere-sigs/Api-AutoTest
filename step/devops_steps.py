import requests
import json
import allure
import sys

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from common.getHeader import get_header, get_header_for_patch, get_header_for_urlencoded
from common.getConfig import get_apiserver
from common.getCookie import get_token

env_url = get_apiserver()


@allure.step('创建devops工程并获取工程名称')
def step_create_devops(ws_name, devops_name):
    """
    :param ws_name: 企业空间的名称
    :param devops_name: devops工程的名称
    :return:devops工程名称
    """
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/workspaces/' + ws_name + '/devops'
    data = {"metadata": {"generateName": devops_name,
                         "labels": {"kubesphere.io/workspace": ws_name},
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "kind": "DevOpsProject",
            "apiVersion": "devops.kubesphere.io/v1alpha3"}
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.story('查询devops工程')
def step_search_devops(ws_name, condition):
    """
    :param ws_name: 企业空间
    :param condition: 查询条件
    :return: 查询结果
    """
    url = env_url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/devops?name=' + condition + '&limit=10'
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
    url = env_url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name + '/devops?name=' + devops_name + '&limit=10'
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
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/workspaces/' + ws_name + '/devops/' + devops_name
    r = requests.put(url=url, headers=get_header_for_patch(), data=json.dumps(data))

    return r.json()['metadata']['annotations']['kubesphere.io/alias-name']


@allure.step('查询凭证')
def step_search_credential(devops_name, condition):
    """
    :param devops_name: devops名称
    :param condition: 查询条件
    :return: 查询结果
    """
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + devops_name + '/credentials?' \
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
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + devops_name + '/credentials?' \
                                                                                   'name=' + condition + '&limit=10&sortBy=createTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('获取所有凭证的名称')
def step_get_credentials_name(devops_name):
    """
    :param devop_name: devops工程的名称
    :return: devops工程中所有的凭证名称
    """
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + devops_name + '/credentials?limit=10&sortBy=createTime'
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
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + devops_name + '/credentials/' + credential_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('编辑devops角色的权限信息')
def step_edit_role_authority(devops_name, role_name, annotations, resource_version):
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + devops_name + '/roles/' + role_name
    data = {"apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "Role",
            "metadata": {"name": role_name,
                         "namespace": devops_name,
                         "annotations": annotations,
                         "resourceVersion": resource_version}
            }
    response = requests.put(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('编辑devops角色的基本信息')
def step_edit_role_info(devops_name, role_name, alias, description):
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + devops_name + '/roles/' + role_name
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
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/devops/' + devope_name + '/roles?' \
                                                                                'name=' + role_name + '&sortBy=createTime&annotation=kubesphere.io%2Fcreator'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('删除devops角色')
def step_delete_role(devops_name, role_name):
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + devops_name + '/roles/' + role_name
    requests.delete(url, headers=get_header())


@allure.step('删除devops工程')
def step_delete_devops(ws_name, devops_name):
    """
    :param ws_name: 企业空间名称
    :param devops_name: devops工程名称
    :return: 删除结果
    """
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/workspaces/' + ws_name + '/devops/' + devops_name
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
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + devops_name_new + '/pipelines/' + pipline_name
    r = requests.get(url=url, headers=get_header())
    return r.json()['metadata']['resourceVersion'], r.json()['metadata']['uid'], r.json()['metadata'][
        'creationTimestamp']


@allure.step('checkScriptCompile')
def step_pipeline_check_script_compile(devops_name_new, pipeline_name, data):
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha2/devops/' + devops_name_new + '/pipelines/' \
          + pipeline_name + '/checkScriptCompile'
    print(url)
    header = {
        'Authorization': get_token(env_url),
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
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha2/devops/' + devops_name_new + '/pipelines/' + pipeline_name + '/runs'
    data = {"parameters": []}
    r = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    # 返回运行结果中的某个字段
    return r.json()['organization']


@allure.step('验证流水线运行结果')
def step_get_pipeline_status(devops_name_new, pipeline_name):
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha2/devops/' + devops_name_new + '/pipelines/' + pipeline_name + '/runs/?start=0&limit=10'
    r = requests.get(url=url, headers=get_header())
    return r.json()['items'][0]['result']


@allure.step('删除流水线')
def step_delete_pipeline(devops_name_new, pipeline_name):
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + devops_name_new + '/pipelines/' + pipeline_name
    r = requests.delete(url=url, headers=get_header())
    return r.json()['message']


@allure.step('创建账户类型凭证')
def step_create_account_credential(devops_name, name, username, password):
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + devops_name + '/credentials'
    description = '我是描述信息'

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
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + devops_name + '/credentials'
    username = 'cXdl'
    private_key = 'YXNk'

    data = {"apiVersion": "v1", "kind": "Secret",
            "metadata": {"namespace": devops_name,
                         "labels": {"app": name}, "annotations": {"kubesphere.io/creator": "admin"}, "name": name},
            "type": "credential.devops.kubesphere.io/ssh-auth",
            "data": {"username": username, "private_key": private_key}}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('创建kubeconfig类型凭证')
def step_create_kubeconfig_credential(devops_name, name, kubeconfig):
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + devops_name + '/credentials'
    data = {"apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"namespace": devops_name,
                         "labels": {"app": name},
                         "annotations": {"kubesphere.io/creator": "admin"}, "name": name},
            "type": "credential.devops.kubesphere.io/kubeconfig",
            "data": {"content": kubeconfig}}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('基于github创建多分支流水线')
def step_create_pipeline_base_github(devops, devops_name, pipeline_name, credential_name, patch, tags):
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + devops_name + '/pipelines'
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
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + devops_name + '/pipelines'
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
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + devops_name + '/pipelines'
    data = {"devopsName": devops,
            "metadata": {"name": pipeline_name, "namespace": devops_name,
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"pipeline": {"discarder": {"days_to_keep": "7", "num_to_keep": "10"}, "devopsName": devops,
                                  "cluster": "default", "devops": devops_name, "enable_timer_trigger": False,
                                  "enable_discarder": True, "name": "test"}, "type": "pipeline"}, "kind": "Pipeline",
            "apiVersion": "devops.kubesphere.io/v1alpha3"}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('编辑jenkinsfile-checkScriptCompile ')
def step_edit_jenkinsfile_check_script_compile(devops_name, pipeline_name, jenkins_file):
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha2/devops/' + devops_name + '/pipelines/' + pipeline_name + '/checkScriptCompile'

    data = 'value=' + jenkins_file
    response = requests.post(url=url, headers=get_header_for_urlencoded(), data=data)
    return response


@allure.step('编辑jenkinsfile-put')
def step_edit_jenkinsfile_put(devops_name, uid, pipeline_name, version, jenkinsfile, hash):
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + devops_name + '/pipelines/' + pipeline_name

    data = {"metadata":
                {"name": pipeline_name,
                 "namespace": devops_name,
                 "uid": uid,
                 "resourceVersion": version,
                 "generation": 1,
                 "annotations": {"kubesphere.io/creator": "admin",
                                 "pipeline.devops.kubesphere.io/jenkins-metadata":
                                     "{\"weatherScore\":100,\"estimatedDurationInMillis\":-1,\"name\":\"" + pipeline_name + "\"}",
                                 "pipeline.devops.kubesphere.io/spechash": hash,
                                 "pipeline.devops.kubesphere.io/syncstatus": "successful"},
                 "finalizers": ["pipeline.finalizers.kubesphere.io"],
                 "managedFields": [{"manager": "apiserver",
                                    "operation": "Update",
                                    "apiVersion": "devops.kubesphere.io/v1alpha3",
                                    "fieldsType": "FieldsV1",
                                    "fieldsV1": {"f:metadata": {
                                        "f:annotations": {".": {}, "f:kubesphere.io/creator": {}}},
                                        "f:spec": {".": {}, "f:pipeline": {".": {},
                                                                           "f:discarder": {".": {},
                                                                                           "f:days_to_keep": {},
                                                                                           "f:num_to_keep": {}},
                                                                           "f:name": {}},
                                                   "f:type": {}}, "f:status": {}}},
                                   {"manager": "controller-manager", "operation": "Update",
                                    "apiVersion": "devops.kubesphere.io/v1alpha3",
                                    "fieldsType": "FieldsV1", "fieldsV1": {
                                       "f:metadata": {"f:annotations": {
                                           "f:pipeline.devops.kubesphere.io/jenkins-metadata": {},
                                           "f:pipeline.devops.kubesphere.io/spechash": {},
                                           "f:pipeline.devops.kubesphere.io/syncstatus": {}},
                                           "f:finalizers": {".": {},
                                                            "v:\"pipeline.finalizers.kubesphere.io\"": {}}}}}]},
            "spec": {"type": "pipeline",
                     "pipeline": {"name": pipeline_name, "discarder": {"days_to_keep": "7", "num_to_keep": "10"},
                                  "jenkinsfile": jenkinsfile}},
            "status": {}, "kind": "Pipeline", "apiVersion": "devops.kubesphere.io/v1alpha3"
            }
    # print(json.dumps(data))
    response = requests.put(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('编辑jenkinsfile-tojson')
def step_edit_jenkinsfile_tojson(jenkins_file):
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha2/tojson'
    data = 'jenkinsfile=' + jenkins_file
    response = requests.post(url=url, headers=get_header_for_urlencoded(), data=data)
    return response


@allure.step('查询指定的流水线')
def step_get_pipeline(devops_name, pipeline_name):
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + devops_name + '/pipelines?page=1&limit=10&name=' + pipeline_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('获取流水线的详情')
def step_get_pipeline(devops_name, pipeline_name):
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + devops_name + '/pipelines?page=1&name=' + pipeline_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('删除流水线')
def step_delete_pipeline(devops_name, pipeline_name):
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + devops_name + '/pipelines/' + pipeline_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('创建凭证')
def step_create_credential(dev_name, name, description, type, data):
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/devops/' + dev_name + '/credentials'
    data = {"apiVersion": "v1", "kind": "Secret",
            "metadata": {"namespace": dev_name,
                         "labels": {"app": name},
                         "annotations": {"kubesphere.io/description": description,
                                         "kubesphere.io/creator": "admin"},
                         "name": name},
            "type": "credential.devops.kubesphere.io/" + type,
            "data": data
            }
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('项目设置/创建角色')
def step_create_role(dev_name, name):
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + dev_name + '/roles'
    data = {"apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "Role",
            "metadata": {"namespace": dev_name,
                         "name": name,
                         "annotations": {"iam.kubesphere.io/aggregation-roles": "[\"role-template-view-members\","
                                                                                "\"role-template-view-basic\"]",
                                         "kubesphere.io/creator": "admin"}
                         },
            "rules": []
            }
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('项目设置/项目角色，删除角色')
def step_delete_role(dev_name, name):
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/namespaces/' + dev_name + '/roles/' + name
    response = requests.delete(url, headers=get_header())
    return response


@allure.step('项目设置/项目成员，查询项目成员')
def step_get_member(dev_name, name):
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/devops/' + dev_name + '/members?name=' + name + '&sortBy=createTime'
    response = requests.get(url, headers=get_header())
    return response


@allure.step('项目设置/项目成员，邀请用户到devops工程')
def step_invite_member(dev_name, name, role):
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/devops/' + dev_name + '/members'
    data = [{"username": name,
             "roleRef": role}]
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('项目设置/项目成员，编辑devops工程成员的角色')
def step_edit_member(dev_name, name, role):
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/devops/' + dev_name + '/members/' + name
    data = {"username": name,
            "roleRef": role}
    response = requests.put(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('项目设置/项目成员，删除devops工程成员')
def step_remove_member(dev_name, name):
    url = env_url + '/kapis/iam.kubesphere.io/v1alpha2/devops/' + dev_name + '/members/' + name
    response = requests.delete(url, headers=get_header())
    return response


@allure.step('代码仓库，导入代码仓库')
def step_import_code_repository(dev_name, name, provider, code_url):
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/namespaces/' + dev_name + '/gitrepositories'
    data = {"kind": "GitRepository", "apiVersion": "devops.kubesphere.io/v1alpha3",
            "metadata": {"name": name, "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"provider": provider, "url": code_url,
                     "secret": {"namespace": dev_name}}}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('代码仓库，查询代码仓库')
def step_get_code_repository(dev_name, name):
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/namespaces/' + dev_name + '/gitrepositories?name=' + name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('代码仓库，删除代码仓库')
def step_delete_code_repository(dev_name, name):
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/namespaces/' + dev_name + '/gitrepositories/' + name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('代码仓库，编辑代码仓库')
def step_edit_code_repository(dev_name, name, provider, annotations, code_url):
    url = env_url + '/kapis/devops.kubesphere.io/v1alpha3/namespaces/' + dev_name + '/gitrepositories/' + name
    data = {"kind": "GitRepository", "apiVersion": "devops.kubesphere.io/v1alpha3",
            "metadata": {"name": name, "namespace": dev_name,
                         "annotations": annotations,
                         "finalizers": ["finalizer.gitrepository.devops.kubesphere.io"]},
            "spec": {"provider": provider, "url": code_url,
                     "secret": {"namespace": dev_name}}}
    response = requests.put(url=url, headers=get_header_for_patch(), data=json.dumps(data))
    return response


@allure.step('持续部署，创建持续部署')
def step_create_cd(dev_name, cd_name, annotations, ns, cd_url, path):
    url = env_url + '/kapis/gitops.kubesphere.io/v1alpha1/namespaces/' + dev_name + '/applications'
    data = {"kind": "Application", "apiVersion": "gitops.kubesphere.io/v1alpha1", "metadata": {"name": cd_name,
                                                                                               "annotations": annotations},
            "spec": {"kind": "argo-project", "argoApp": {"spec": {
                "destination": {"name": "in-cluster", "server": "https://kubernetes.default.svc", "namespace": ns},
                "source": {"repoURL": cd_url, "targetRevision": "HEAD",
                           "path": path},
                "syncPolicy": {"automated": {}, "syncOptions": ["CreateNamespace=true"]}}}}}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('持续部署，删除持续部署任务')
def step_delete_cd(dev_name, cd_name, cascade):
    """
    :param dev_name:
    :param cd_name:
    :param cascade: 是否删除部署的资源，true表示删除
    :return:
    """
    if cascade == 'true':
        url = env_url + '/kapis/gitops.kubesphere.io/v1alpha1/namespaces/' + dev_name + '/applications/' + cd_name + '?cascade=true'
    else:
        url = env_url + '/kapis/gitops.kubesphere.io/v1alpha1/namespaces/' + dev_name + '/applications/' + cd_name
    response = requests.delete(url=url, headers=get_header())
    return response