import requests
import json
import allure
import sys

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from config import config
from common.getHeader import get_header, get_header_for_patch
from common import commonFunction
from math import ceil


@allure.step('创建应用模板')
def step_create_app_template(ws_name, app_name):
    """
    :param ws_name: 企业空间名称
    :param app_name: 应用模版名称
    :return:
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/apps'
    data = {"version_type": "helm",
            "name": app_name,
            "version_package": "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"
            }
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('查询指定的应用模版')
def step_get_app_template(ws_name, app_name):
    """
    :param ws_name: 企业空间名称
    :param app_name: 应用名称
    :return:
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/apps?conditions=keyword%3D' + app_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('部署应用')
def step_deploy_template(ws_name, project_name, app_id, name, version_id):
    """
    :param ws_name: 企业空间名称
    :param project_name: 项目名称
    :param app_id: 应用id
    :param name: 部署应用的名称
    :param version_id: 应用的版本号
    :return:
    """
    if commonFunction.check_multi_cluster() is False:
        url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + \
              '/clusters/default/namespaces/' + project_name + '/applications'
    else:
        url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + \
              '/clusters/host/namespaces/' + project_name + '/applications'

    data = {"app_id": app_id,
            "name": name,
            "version_id": version_id,
            "conf": "affinity: {}\napiserver: 'https://kubernetes.default.svc:443'\nemqxAddressType: ip\nemqxConfig:\n "
                    " EMQX_MANAGEMENT__LISTENER__HTTP: '8080'\nemqxLicneseSecretName: null\nimage: "
                    "'emqx/emqx:latest'\nimagePullPolicy: IfNotPresent\ningress:\n  annotations: {}\n  enabled: "
                    "false\n  hosts:\n    - chart-example.local\n  path: /\n  tls: []\nnamespace: "
                    "default\nnodeSelector: {}\npersistence:\n  accessMode: ReadWriteOnce\n  enabled: false\n  size: "
                    "20Mi\nreplicas: 3\nresources: {}\nservice:\n  type: ClusterIP\ntolerations: []\n"}

    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('查看应用状态')
def step_get_app_status(ws_name, project_name, app_name):
    """
    :param ws_name: 企业空间名称
    :param project_name: 项目名称
    :param app_name: 应用名称
    :return:
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/namespaces/' + project_name + '/applications?conditions=keyword%3D' + app_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看指定应用')
def step_get_app(ws_name, project_name, app_name):
    """
    :param ws_name: 企业空间名称
    :param project_name: 项目名称
    :param app_name: 应用名称
    :return:
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/namespaces/' + project_name + '/applications?conditions=keyword%3D' + app_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('删除部署的应用')
def step_delete_app(ws_name, project_name, cluster_id):
    """
    :param ws_name: 企业空间名称
    :param project_name: 项目名称
    :param cluster_id: 集群id
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/clusters/default/namespaces/' + project_name + '/applications/' + cluster_id

    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('应用模板提交审核')
def step_app_template_submit(app_id, version_id, version, update_log):
    """
    :param app_id: 应用的id
    :param version_id: 应用的版本id
    :param version: 部署时应用的版本名称
    :param update_log: 部署时应用的更新日志
    :return:
    """
    url1 = config.url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/versions/' + version_id + '/'
    url2 = config.url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/versions/' + version_id + '/action'
    data1 = {"name": version,
             "description": update_log}
    data2 = {"action": "submit"}
    requests.patch(url1, headers=get_header_for_patch(), data=json.dumps(data1))
    response = requests.post(url2, headers=get_header(), data=json.dumps(data2))
    return response


@allure.step('应用模板撤销审核')
def step_app_template_submit_cancle(app_id, version_id):
    """
    :param app_id: 应用id
    :param version_id: 应用的版本id
    """
    url = config.url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/versions/' + version_id + '/action'
    data = {"action": "cancel"}
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('应用审核--通过')
def step_app_pass(app_id, version_id):
    """
    :param app_id: 应用id
    :param version_id: 应用的版本id
    """
    url = config.url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/versions/' + version_id + '/action'
    data = {"action": "pass"}
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('应用审核--不通过')
def step_app_reject(app_id, version_id):
    """
    :param app_id: 应用id
    :param version_id: 应用的版本id
    """
    url = config.url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/versions/' + version_id + '/action'
    data = {"action": "reject", "message": "test-reject"}
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('发布应用商店')
def step_release(app_id, version_id):
    """
    :param app_id: 应用id
    :param version_id: 应用的版本id
    """
    url = config.url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/versions/' + version_id + '/action'
    data = {"action": "release"}
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('下架应用')
def step_suspend_app(app_id):
    """
    :param app_id: 应用id
    """
    url = config.url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/action'
    data = {"action": "suspend"}
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('重新上架')
def step_app_recover(app_id, version_id):
    """
    :param app_id: 应用id
    :param version_id: 应用的版本id
    """
    url = config.url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/versions/' + version_id + '/action'
    data = {"action": "recover"}
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('查看应用审核记录')
def step_audit_records(app_id, version_id):
    """
    :param app_id: 应用id
    :param version_id: 应用的版本id
    """
    url = config.url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/versions/' + version_id + '/audits?'
    response = requests.get(url, get_header())
    return response


@allure.step('添加版本')
def step_add_version(ws_name, app_id):
    """
    :param ws_name: 企业空间名称
    :param app_id: 应用id
    :return:
    """
    # 获取应用的app_id和version_id
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/apps/' + app_id + '/versions'
    data = {"type": "helm",
            "package": "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"}
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('获取应用模板中所有版本的version_id')
def step_get_app_versions(ws_name, app_id):
    """
    :param ws_name: 企业空间名称
    :param app_id: 应用id
    :return:
    """
    versions = []
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/apps/' + app_id + '/versions?orderBy=sequence&paging=limit%3D10%2Cpage%3D1&conditions=status%3Ddraft%7Csubmitted%7Crejected%7Cin-review%7Cpassed%7Cactive%7Csuspended&reverse=true'
    r = requests.get(url=url, headers=get_header())
    for item in r.json()['items']:
        versions.append(item['version_id'])
    return versions


@allure.step('删除版本')
def step_delete_version(app_id, versions):
    """
    :param app_id: 应用id
    :param versions: 应用的版本信息
    """
    for version in versions:
        url = config.url + '/kapis/openpitrix.io/v1/apps/' + app_id + '/versions/' + version + '/'
        data = {}
        r = requests.delete(url, headers=get_header(), data=json.dumps(data))  # 删除应用版本
        assert r.json()['message'] == 'success'


@allure.step('删除应用模板')
def step_delete_app_template(ws_name, app_id):
    """
    :param ws_name: 企业空间名称
    :param app_id: 应用id
    :return:
    """
    data = {}
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/apps/' + app_id + '/'
    response = requests.delete(url, headers=get_header(), data=json.dumps(data))  # 删除应用模板
    return response


@allure.step('添加仓库')
def step_add_app_repository(ws_name, rpo_name, rpo_url):
    """
    :param ws_name: 企业空间
    :param rpo_name: 应用仓库名称
    :param rpo_url: 应用仓库地址
    :return: 应用仓库的repo_id
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/repos'
    data = {"name": rpo_name,
            "repoType": "Helm",
            "type": "https",
            "visibility": "public",
            "credential": "{}",
            "providers": ["kubernetes"],
            "url": rpo_url,
            "app_default_status": "active"
            }
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('查询应用仓库列表指定仓库')
def step_get_app_repository(ws_name, rpo_name):
    """
    :param ws_name: 企业空间
    :param rpo_name: 应用仓库名称
    :return: 应用仓库的repo_id
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/repos?conditions=keyword%3D' + rpo_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('删除应用仓库')
def step_delete_app_repo(ws_name, repo_id):
    """
    :param ws_name: 企业空间名称
    :param repo_id: 仓库id
    :return:
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/repos/' + repo_id + '/'
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('在单集群环境创建企业空间')
def step_create_workspace(ws_name):
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


@allure.step('删除企业空间')
def step_delete_workspace(ws_name):
    """
    :param ws_name: 企业空间的名称
    """
    url = config.url + '/kapis/tenant.kubesphere.io/v1alpha2/workspaces/' + ws_name
    response = requests.delete(url, headers=get_header())
    return response


@allure.step('从appstore部署指定应用')
def step_deployment_app(project_name, app_id, app_version_id, name, conf):
    """
    :param project_name: 项目名称
    :param app_id: 应用id
    :param app_version_id: 应用版本号
    :param name: 部署时的应用名称
    :param conf: 应用的镜像信息
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/undefined/clusters/default/namespaces/' + project_name + '/applications'
    data = {"app_id": app_id,
            "name": name,
            "version_id": app_version_id,
            "conf": conf +
                    "Name: " + name + "\nDescription: ''\nWorkspace: " + project_name + "\n"}
    r = requests.post(url, headers=get_header(), data=json.dumps(data))
    # 验证部署应用请求成功
    assert r.json()['message'] == 'success'


@allure.step('获取appstore中应用的app_id')
def step_get_app_id():
    url = config.url + '/kapis/openpitrix.io/v1/apps?orderBy=create_time&paging=limit%3D12%2Cpage%3D2&conditions=status%3Dactive%2Crepo_id%3Drepo-helm&reverse=true'
    url2 = config.url + '/kapis/openpitrix.io/v1/apps?orderBy=create_time&paging=limit%3D12%2Cpage%3D1&conditions=status%3Dactive%2Crepo_id%3Drepo-helm&reverse=true'
    r = requests.get(url, headers=get_header())  # 获取app的id和name，将其组合成一个字典
    r2 = requests.get(url2, headers=get_header())  # 获取app的id和name，将其组合成一个字典
    item_name = []
    item_app_id = []
    items = r.json()['items']
    for item in items:
        item_name.append(item['name'])
        item_app_id.append(item['app_id'])
    items2 = r2.json()['items']
    for item in items2:
        item_name.append(item['name'])
        item_app_id.append(item['app_id'])
    dic = dict(zip(item_name, item_app_id))
    return dic


@allure.step('获取appstore中所有应用的name, app_id, version_id')
def step_get_app_version():
    url = config.url + '/kapis/openpitrix.io/v1/apps??orderBy=create_time&paging=limit%3D12%2Cpage%3D2&conditions=status%3Dactive%2Crepo_id%3Drepo-helm&reverse=true'
    url2 = config.url + '/kapis/openpitrix.io/v1/apps??orderBy=create_time&paging=limit%3D12%2Cpage%3D1&conditions=status%3Dactive%2Crepo_id%3Drepo-helm&reverse=true'
    r = requests.get(url, headers=get_header())  # 获取app的id和name，将其组合成一个字典
    r2 = requests.get(url2, headers=get_header())  # 获取app的id和name，将其组合成一个字典
    item_name = []
    item_version_id = []
    items = r.json()['items']
    for item in items:
        item_name.append(item['name'])
        item_version_id.append(item['latest_app_version']['version_id'])
    items2 = r2.json()['items']
    for item in items2:
        item_name.append(item['name'])
        item_version_id.append(item['latest_app_version']['version_id'])
    dic = dict(zip(item_name, item_version_id))
    return dic


@allure.step('从应用商店部署应用')
def step_deploy_app_from_app_store(ws_name, project_name, app_id, name, version_id, conf):
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/namespaces/' + project_name + '/applications'
    data = {
        "app_id": app_id,
        "name": name,
        "version_id": version_id,
        "conf": conf
    }
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


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
    for i in range(0, count):
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
    url = config.url + '/kapis/openpitrix.io/v1/apps?orderBy=create_time&paging=limit%3D10%2Cpage%3D' + \
          str(page) + '&conditions=status%3Dactive%7Csuspended%2Crepo_id%3Drepo-helm&reverse=true'
    # 获取应用总数量
    r = requests.get(url=url, headers=get_header())
    count = r.json()['total_count']
    # 获取页数
    pages = ceil(count / 10)
    apps = []
    for page in range(1, pages + 1):
        r = requests.get(url, get_header())
        for item in r.json()['items']:
            apps.append(item['app_id'])
    return apps


@allure.step('查看应用的详情信息')
def step_get_app_detail(app_id):
    url = config.url + '/kapis/openpitrix.io/v1/apps/' + app_id
    response = requests.get(url=url, headers=get_header())
    return response


#########多集群环境############


@allure.step('在多集群环境的host集群部署指定应用')
def step_deployment_app_multi(project_name, app_id, app_version_id, name, conf):
    """
    :param project_name: 项目名称
    :param app_id: 应用id
    :param app_version_id: 应用版本号
    :param name: 部署时的应用名称
    :param conf: 应用的镜像信息
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/undefined/clusters/host/namespaces/' + \
          project_name + '/applications'
    data = {"app_id": app_id,
            "name": name,
            "version_id": app_version_id,
            "conf": conf +
                    "Name: " + name + "\nDescription: ''\nWorkspace: " + project_name + "\n"}
    r = requests.post(url, headers=get_header(), data=json.dumps(data))
    # 验证部署应用请求成功
    assert r.json()['message'] == 'success'


@allure.step('在多集群环境的host集群查看指定应用信息')
def step_get_app_status_multi(ws_name, project_name, app_name):
    """
    :param ws_name: 企业空间
    :param project_name: 项目名称
    :param app_name: 应用名称
    :return: 应用状态
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/clusters/host/namespaces/' + \
          project_name + '/applications?conditions=keyword%3D' + app_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在多集群环境的host集群的项目的应用列表中查看应用是否存在')
def step_get_app_count_multi(ws_name, project_name, app_name):
    """
    :param ws_name: 企业空间
    :param project_name: 项目名称
    :param app_name: 应用名称
    :return:
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/clusters/host/namespaces/' + \
          project_name + '/applications?conditions=status%3Dactive%7Cstopped%7Cpending%7Csuspended%2Ckeyword%3D' + \
          app_name + '&paging=limit%3D10%2Cpage%3D1&orderBy=status_time&reverse=true'
    r = requests.get(url=url, headers=get_header())
    return r.json()['total_count']


@allure.step('在多集群环境的host集群的项目的应用列表获取指定应用的cluster_id')
def step_get_deployed_app_multi(ws_name, project_name, app_name):
    """
    :param ws_name: 企业空间
    :param project_name: 项目名称
    :param app_name: 应用名称
    :return: 应用的cluster_id
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/clusters/host/namespaces/' + \
          project_name + '/applications?conditions=keyword%3D' + app_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在多集群环境的host集群删除项目的应用列表指定的应用')
def step_delete_app_multi(ws_name, project_name, cluster_id):
    """
    :param ws_name: 企业空间
    :param project_name: 项目名称
    :param cluster_id: 部署后的应用的id
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/clusters/host/namespaces/' + \
          project_name + '/applications/' + cluster_id
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('在多集群环境的host集群从应用商店部署应用')
def step_deploy_app_from_app_store_multi(ws_name, project_name, app_id, name, version_id, conf):
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/clusters/host/namespaces/' + \
          project_name + '/applications'
    data = {
        "app_id": app_id,
        "name": name,
        "version_id": version_id,
        "conf": conf
    }
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response
