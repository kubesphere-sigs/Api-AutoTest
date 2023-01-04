import pytest
from common.commonFunction import *
from step import storage_steps, multi_cluster_storages_step


@pytest.fixture
def create_sc():
    sc_name = 'sc-' + str(get_random())
    ex = True
    # 创建存储类
    storage_steps.create_sc(sc_name, ex)
    yield sc_name
    # 删除存储类
    storage_steps.delete_sc(sc_name)


@pytest.fixture
def create_multi_cluster_sc():
    sc_name = 'sc-' + str(get_random())
    ex = True
    cluster_name = multi_cluster_steps.step_get_host_cluster_name()
    # 创建存储类
    multi_cluster_storages_step.step_create_sc(cluster_name, sc_name, ex)
    yield sc_name
    # 删除存储类
    multi_cluster_storages_step.delete_sc(self.cluster_name, sc_name)


