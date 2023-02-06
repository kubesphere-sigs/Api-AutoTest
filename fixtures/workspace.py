import pytest
from common import commonFunction
from step import multi_cluster_steps, cluster_steps, multi_project_steps, multi_workspace_steps


@pytest.fixture
def create_multi_workspace():
    # 创建一个多集群企业空间（包含所有的集群）
    ws_name = 'ws-multi-' + str(commonFunction.get_random())
    alias_name = '跨集群'
    description = '包含所有的集群的企业空间'
    clusters = cluster_steps.step_get_cluster_name()
    multi_workspace_steps.step_create_multi_ws(ws_name, alias_name, description, clusters)
    yield ws_name
    multi_workspace_steps.step_delete_workspace(ws_name)


@pytest.fixture
def create_multi_project(create_multi_workspace):
    # 创建一个多集群项目(包含所有集群)
    pro_name = 'pro-multi-' + str(commonFunction.get_random())
    clusters = cluster_steps.step_get_cluster_name()
    multi_project_steps.step_create_multi_project(create_multi_workspace, pro_name, clusters)
    yield pro_name
    multi_project_steps.step_delete_multi_project(project_name=pro_name)