import requests
import pytest
import json
import allure
import sys
from config import config
from common.getData import DoexcleByPandas
from common.getHeader import get_header
from common.getHeader import get_header_for_patch
from common import commonFunction
import time
import datetime
import random

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用


@allure.step('获取集群信息')
def step_get_cluster():
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/clusters'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('获取集群的节点列表信息')
def step_get_nodes(cluster_name):
    url = config.url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/nodes'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('为节点设置污点')
def step_ste_taints(cluster_name, node_name, taints):
    url = config.url + '/api/clusters/' + cluster_name + '/v1/nodes/' + node_name
    data = {"spec": {"taints": taints}}
    response = requests.patch(url=url, headers=get_header_for_patch(), data=json.dumps(data))
    return response


@allure.step('查看节点的详细信息')
def step_get_node_detail_info(cluster_name, node_name):
    url = config.url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/nodes/' + node_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('往节点中添加标签')
def step_add_labels_for_node(cluster_name, node_name, labels):
    url = config.url + '/api/clusters/' + cluster_name + '/v1/nodes/' + node_name
    data = {"metadata": {"labels": labels}}
    response = requests.patch(url=url, headers=get_header_for_patch(), data=json.dumps(data))
    return response


@allure.step('节点停止/启用调度')
def step_cordon_node(cluster_name, node_name, cordon):
    url = config.url + '/api/clusters/' + cluster_name + '/v1/nodes/' + node_name
    data = {"spec": {"unschedulable": cordon}}
    response = requests.patch(url=url, headers=get_header_for_patch(), data=json.dumps(data))
    return response


@allure.step('查看节点的pod信息')
def step_get_pod_of_node(cluster_name, node_name):
    url = config.url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/pods?nodeName=' \
          + node_name + '&sortBy=startTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询指定的pod')
def step_query_pod(cluster_name, node_name, pod_name):
    url = config.url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/pods?nodeName=' + node_name + '&name=' + pod_name + '&sortBy=startTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看节点的event信息')
def step_get_event_of_node(cluster_name, node_name):
    url = config.url + '/api/clusters/' + cluster_name + '/v1/events?fieldSelector=involvedObject.name%3D' + node_name + '%2CinvolvedObject.kind%3DNode'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看节点的监控信息')
def step_get_metrics_of_node(cluster_name, node_name, start_time, end_time, step, times):
    url = config.url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/nodes?start=' + start_time + '&end=' + end_time + \
          '&step=' + step + '&times=' + times + '&resources_filter=' + node_name + \
          '%24&metrics_filter=node_cpu_utilisation%7Cnode_load1%7Cnode_load5%7Cnode_load15%7Cnode_memory_utilisation' \
          '%7Cnode_disk_size_utilisation%7Cnode_disk_inode_utilisation%7Cnode_disk_inode_usage%7Cnode_disk_inode_total' \
          '%7Cnode_disk_read_iops%7Cnode_disk_write_iops%7Cnode_disk_read_throughput%7Cnode_disk_write_throughput' \
          '%7Cnode_net_bytes_transmitted%7Cnode_net_bytes_received%24 '
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看节点的状态信息')
def step_get_status_of_node(cluster_name, node_name, start_time, end_time, step, times):
    url = config.url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/nodes?start=' + start_time + '&end=' + end_time + \
          '&step=' + step + '&times=' + times + '&resources_filter=' + node_name + \
          '%24&metrics_filter=node_cpu_utilisation%7Cnode_memory_utilisation%7Cnode_disk_size_utilisation' \
          '%7Cnode_pod_utilisation%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群指定的系统项目')
def step_query_system_project(cluster_name, project_name):
    url = config.url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/namespaces?name=' \
          + project_name + '&sortBy=createTime&labelSelector=kubesphere.io%2Fworkspace%3Dsystem-workspace'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群所有的项目')
def step_get_project_of_cluster(cluster_name):
    url = config.url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/namespaces/'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看项目的pod信息')
def step_get_pods_of_project(cluster_name, project_name, *condition):
    condition_actual = ''
    for i in condition:
        condition_actual += str(i) + '&'
    url = config.url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/namespaces/' \
          + project_name + '/pods?' + condition_actual + '&sortBy=startTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询指定项目的详细信息')
def step_get_project_detail(project_name):
    url = config.url + '/api/v1/namespaces/' + project_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询指定项目的配额信息')
def step_get_project_quota(cluster_name, project_name):
    url = config.url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha2/namespaces/' + project_name + '/quotas'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询指定项目的LimitRanges')
def step_get_project_limit_ranges(cluster_name, project_name):
    url = config.url + '/api/clusters/' + cluster_name + '/v1/namespaces/' + project_name + '/limitranges'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询指定项目的工作负载信息')
def step_get_project_workload(cluster_name, project_name):
    url = config.url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha2/namespaces/' + \
          project_name + '/abnormalworkloads'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('创建用户项目')
def step_create_user_project(cluster_name, project_name, alias_name, description):
    url = config.url + '/api/clusters/' + cluster_name + '/v1/namespaces'
    data = {"apiVersion": "v1", "kind": "Namespace", "metadata": {"name": project_name,
                                                                  "annotations": {
                                                                      "kubesphere.io/alias-name": alias_name,
                                                                      "kubesphere.io/description": description,
                                                                      "kubesphere.io/creator": "admin"},
                                                                  "labels": {}}}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('查询指定的用户项目')
def step_get_user_system(cluster_name, project_name):
    url = config.url + '/api/clusters/' + cluster_name + '/v1/namespaces/' + project_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('删除用户项目')
def step_delete_user_system(cluster_name, project_name):
    url = config.url + '/api/clusters/' + cluster_name + '/v1/namespaces/' + project_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('查询集群的所有项目工作的资源信息')
def step_get_resource_of_cluster(cluster_name, resource_type, *condition):
    """
    :param cluster_name: 集群名称
    :param resource_type: 资源类型 deployments,statefulSets,daemonSets...
    :return:
    """
    condition_actual = ''
    for i in condition:
        condition_actual += str(i) + '&'
    url = config.url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/' + \
          resource_type + '?' + condition_actual + 'sortBy=updateTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询工作负载的详情信息')
def step_get_app_workload_detail(cluster_name, project_name, resource_type, resource_name):
    url = config.url + '/apis/clusters/' + cluster_name + '/apps/v1/namespaces/' + project_name + '/' + \
          resource_type + '/' + resource_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询工作负载的Revision Records')
def step_get_app_workload_revision_records(cluster_name, project_name, label_selector):
    url = config.url + '/apis/clusters/' + cluster_name + '/apps/v1/namespaces/' + project_name + '/controllerrevisions?labelSelector=' \
          + label_selector
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询的deployment的Revision Records')
def step_get_deployment_revision_records(project_name, label_selector):
    url = config.url + '/apis/apps/v1/namespaces/' + project_name + '/replicasets?labelSelector=' \
          + label_selector
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询工作负载的Monitoring')
def step_get_app_workload_monitoring(cluster_name, project_name, resource_type, resource_name):
    url = config.url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/namespaces/' + \
          project_name + '/workloads/' \
          + resource_type + '/' + resource_name + '/pods?sort_metric=pod_cpu_usage&limit=5&page=1'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群资源的Event')
def step_get_resource_event(cluster_name, project_name, resource_type, resource_name, resource_uid):
    url = config.url + '/api/clusters/' + cluster_name + '/v1/namespaces/' + project_name + '/events?fieldSelector=involvedObject.name%3D' \
          + resource_name + '%2CinvolvedObject.namespace%3D' + \
          project_name + '%2CinvolvedObject.kind%3D' + resource_type + '%2CinvolvedObject.uid%3D' + resource_uid
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('获取集群所有的容器组信息')
def step_get_pods_of_cluster(cluster_name):
    url = config.url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/pods?sortBy=startTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('获取集群中指定项目的资源信息')
def step_get_resource_of_cluster_by_project(cluster_name, type, project_name, *name):
    name_actual = ''
    for i in name:
        name_actual += str(i) + '&'
    url = config.url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/namespaces/' + project_name + '/' + type + '?' + name_actual + 'sortBy=createTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询CRD的详情信息')
def step_get_crd_detail(cluster_name, crd_name):
    url = config.url + '/apis/clusters/' + cluster_name + '/apiextensions.k8s.io/v1beta1/customresourcedefinitions/' + crd_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询CRD的FederatedGroupList信息')
def step_get_crd_federated_group_list(cluster_name, group, version, kind):
    if kind[-1] == 's':
        url = config.url + '/apis/clusters/' + cluster_name + '/' + group + '/' + version + '/' + kind + 'es'
    elif kind[-1] == 'y':
        kind = kind.replace(kind[-1], 'i')
        url = config.url + '/apis/clusters/' + cluster_name + '/' + group + '/' + version + '/' + kind + 'es'
    else:
        url = config.url + '/apis/clusters/' + cluster_name + '/' + group + '/' + version + '/' + kind + 's'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询存储卷的详情信息')
def step_get_pvc_detail(cluster_name, project_name, pvc_name):
    url = config.url + '/api/clusters/' + cluster_name + '/v1/namespaces/' + project_name + '/persistentvolumeclaims/' + pvc_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询存储卷的监控信息')
def step_get_metrics_of_pvc(cluster_name, project_name, pvc_name, start_time, end_time, step, times):
    url = config.url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/namespaces/' + project_name + \
          '/persistentvolumeclaims/' + pvc_name + '?cluster=default&start=' + start_time + '&end=' + end_time + \
          '&step=' + step + '&times=' + times + '&metrics_filter=pvc_inodes_used%7Cpvc_inodes_total' \
                                                '%7Cpvc_inodes_utilisation%7Cpvc_bytes_available%7Cpvc_bytes_total' \
                                                '%7Cpvc_bytes_utilisation%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询存储类型的详细信息')
def step_get_storage_class_detail(cluster_name, name):
    url = config.url + '/apis/clusters/' + cluster_name + '/storage.k8s.io/v1/storageclasses/' + name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('设置存储类型为默认存储类型')
def step_set_default_storage_class(cluster_name, name, set):
    """

    :param name:
    :param set: true or false
    :return:
    """
    url = config.url + '/apis/clusters/' + cluster_name + '/storage.k8s.io/v1/storageclasses/' + name
    data = {"metadata": {"annotations": {"storageclass.kubernetes.io/is-default-class": set,
                                         "storageclass.beta.kubernetes.io/is-default-class": set}}}

    response = requests.patch(url=url, headers=get_header_for_patch(), data=json.dumps(data))
    return response


@allure.step('获取集群组件的健康情况')
def step_get_component_health(cluster_name):
    url = config.url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha2/componenthealth'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群的监控的信息')
def step_get_metrics_of_cluster(cluster_name, start_time, end_time, step, times):
    url = config.url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/cluster?start=' + start_time + '&end=' + end_time + \
          '&step=' + step + '&times=' + times + '&metrics_filter=cluster_cpu_usage%7Ccluster_cpu_total' \
                                                '%7Ccluster_cpu_utilisation%7Ccluster_memory_usage_wo_cache%7Ccluster_memory_total%7C' \
                                                'cluster_memory_utilisation%7Ccluster_disk_size_usage%7Ccluster_disk_size_capacity%7C' \
                                                'cluster_disk_size_utilisation%7Ccluster_pod_running_count%7Ccluster_pod_quota%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询apiserver的监控信息')
def step_get_metrics_of_apiserver(cluster_name, start_time, end_time, step, times):
    url = config.url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/components/apiserver?start=' + start_time + \
          '&end=' + end_time + '&step=' + step + '&times=' + times + '&metrics_filter=apiserver_request_latencies%7C' \
                                                                     'apiserver_request_by_verb_latencies%7Capiserver_request_rate%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询scheduler的监控信息')
def step_get_metrics_of_scheduler(cluster_name, start_time, end_time, step, times):
    url = config.url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/components/scheduler?start=' + start_time + \
          '&end=' + end_time + '&step=' + step + '&times=' + times + '&metrics_filter=scheduler_schedule_attempts%7C' \
                                                                     'scheduler_schedule_attempt_rate%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群的 node usage ranking信息')
def step_get_node_usage_rank(cluster_name, sort):
    url = config.url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/nodes?type=rank&' \
                       'metrics_filter=node_cpu_utilisation%7Cnode_cpu_usage%7Cnode_cpu_total%7Cnode_memory_utilisation%7C' \
                       'node_memory_usage_wo_cache%7Cnode_memory_total%7Cnode_disk_size_utilisation%7Cnode_disk_size_usage%7C' \
                       'node_disk_size_capacity%7Cnode_pod_utilisation%7Cnode_pod_running_count%7Cnode_pod_quota%7C' \
                       'node_disk_inode_utilisation%7Cnode_disk_inode_total%7Cnode_disk_inode_usage%7Cnode_load1%24&sort_type=desc&' \
                       'sort_metric=' + sort
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群资源使用情况')
def step_get_resource_usage_of_cluster(cluster_name, start_time, end_time, step, times):
    url = config.url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/cluster?start=' + start_time + '&end=' + end_time + \
          '&step=' + step + '&times=' + times + \
          '&metrics_filter=cluster_cpu_usage%7Ccluster_memory_usage_wo_cache%7Ccluster_disk_size_usage%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群应用资源用量')
def step_get_app_usage_of_cluster(cluster_name, start_time, end_time, step, times):
    url = config.url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/cluster?start=' + start_time + '&end=' + end_time + \
          '&step=' + step + '&times=' + times + \
          '&metrics_filter=cluster_deployment_count%7Ccluster_statefulset_count%7Ccluster_daemonset_count%7C' \
          'cluster_job_count%7Ccluster_cronjob_count%7Ccluster_pvc_count%7Ccluster_service_count%7C' \
          'cluster_ingresses_extensions_count%7Ccluster_pod_running_count%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群项目变化趋势')
def step_get_project_trend_of_cluster(cluster_name, start_time, end_time, step, times):
    url = config.url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/cluster' \
                       '?start=' + start_time + '&end=' + end_time + '&step=' + step + '&times=' + times + \
          '&metrics_filter=cluster_namespace_count%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群的版本信息')
def step_get_cluster_version(cluster_name):
    url = config.url + '/kapis/clusters/' + cluster_name + '/version'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群的clusterroles')
def step_get_cluster_roles(cluster_name):
    url = config.url + '/kapis/clusters/' + cluster_name + '/iam.kubesphere.io/v1alpha2/clustermembers/admin/clusterroles'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群的namespace')
def step_get_cluster_namespace(cluster_name):
    url = config.url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/namespaces?' \
                       'labelSelector=%21kubesphere.io%2Fkubefed-host-namespace%2C%21kubesphere.io%2Fdevopsproject'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群的组件信息')
def step_get_cluster_components(cluster_name):
    url = config.url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha2/components'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群的监控metrics')
def step_get_cluster_monitoring_metrics(cluster_name):
    url = config.url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/cluster?' \
                       'metrics_filter=cluster_cpu_usage%7Ccluster_cpu_total%7Ccluster_memory_usage_wo_cache%7C' \
                       'cluster_memory_total%7Ccluster_disk_size_usage%7Ccluster_disk_size_capacity%7C' \
                       'cluster_pod_running_count%7Ccluster_pod_quota%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看集群apiserver的监控metrics信息')
def step_get_cluster_apiserver_monitoring_metrics(cluster_name):
    url = config.url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/components/apiserver?' \
                       'metrics_filter=apiserver_request_latencies%7Capiserver_request_rate%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看集群节点的监控metrics')
def step_get_cluster_node_monitoring_metrics(cluster_name):
    url = config.url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/nodes?type=rank&' \
                       'metrics_filter=node_cpu_utilisation%7Cnode_cpu_usage%7Cnode_cpu_total%7C' \
                       'node_memory_utilisation%7Cnode_memory_usage_wo_cache%7Cnode_memory_total%7C' \
                       'node_disk_size_utilisation%7Cnode_disk_size_usage%7Cnode_disk_size_capacity%7C' \
                       'node_pod_utilisation%7Cnode_pod_running_count%7Cnode_pod_quota%7Cnode_disk_inode_utilisation%7C' \
                       'node_disk_inode_total%7Cnode_disk_inode_usage%7Cnode_load1%24&sort_type=desc&' \
                       'sort_metric=node_cpu_utilisation'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看集群的调度器')
def step_get_cluster_scheduler(cluster_name):
    url = config.url + '/kapis/clusters/' + cluster_name+ '/monitoring.kubesphere.io/v1alpha3/components/scheduler?metrics_filter=scheduler_schedule_attempts%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.feature('多集群环境集群管理')
class TestCluster(object):
    @allure.story("概览")
    @allure.title('查看每个集群的版本信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_version(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询每个集群的版本信息
            r = step_get_cluster_version(cluster_name)
            # 获取版本号
            cluster_version = r.json()['gitVersion']
            # 验证获取版本号成功
            assert cluster_version == 'v3.1.0'

    @allure.story("概览")
    @allure.title('查看每个集群的clusterrole信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_roles(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询每个集群的clusterrole信息
            r = step_get_cluster_roles(cluster_name)
            # 验证查询成功
            assert r.status_code == 200

    @allure.story("概览")
    @allure.title('查看每个集群的namespaces信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_namespaces(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询每个集群的namespaces信息
            r = step_get_cluster_namespace(cluster_name)
            # 获取namespace数量
            namespaces_count = r.json()['totalItems']
            # 验证namespaces数量大于0
            assert namespaces_count > 0

    @allure.story("概览")
    @allure.title('查看每个集群的component信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_component(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询每个集群的component信息
            r = step_get_cluster_components(cluster_name)
            # 验证组件数量大于0
            assert len(r.json()) > 0

    @allure.story("概览")
    @allure.title('查看每个集群的监控metrics')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_monitoring_metrics(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询每个集群的监控metrics
            r = step_get_cluster_monitoring_metrics(cluster_name)
            # 获取监控的metrics数量
            metrics_count = len(r.json()['results'])
            # 验证监控的metrics数量为8
            assert metrics_count == 8

    @allure.story("概览")
    @allure.title('查看每个集群的apiserver监控metrics')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_apiserver_monitoring_metrics(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询每个集群的apiserver监控metrics
            r = step_get_cluster_apiserver_monitoring_metrics(cluster_name)
            # 获取apiserver监控metrics数量
            count = len(r.json()['results'])
            # 验证apiserver监控metrics的数量为2
            assert count == 2

    @allure.story("概览")
    @allure.title('查看每个集群的调度器信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_scheduler(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询每个集群的调度器信息
            r = step_get_cluster_scheduler(cluster_name)
            # 获取metric_name
            metric_name = r.json()['results'][0]['metric_name']
            # 验证metric_name为 scheduler_schedule_attempts
            assert metric_name == 'scheduler_schedule_attempts'




    @allure.story("节点")
    @allure.title('为每个集群的某个节点设置污点')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_set_taints(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 污点信息
            taints = [{"key": "tester", "value": "wx", "effect": "NoSchedule"}]
            # 获取节点列表中第一个节点的名称
            res = step_get_nodes(cluster_name)
            node_name = res.json()['items'][0]['metadata']['name']
            # 为节点设置污点
            step_ste_taints(cluster_name, node_name, taints)
            # 获取节点的污点信息
            r = step_get_node_detail_info(cluster_name, node_name)
            taints_actual = r.json()['spec']['taints']
            # 验证污点设置成功
            assert taints == taints_actual
            # 清空设置的污点
            step_ste_taints(cluster_name=cluster_name, node_name=node_name, taints=[])

    @allure.story("节点")
    @allure.title('为每个集群的某个节点添加标签')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_add_labels(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取节点列表中第一个节点的名称
            res = step_get_nodes(cluster_name)
            node_name = res.json()['items'][0]['metadata']['name']
            # 获取节点的标签信息
            re = step_get_node_detail_info(cluster_name, node_name)
            labels_old = re.json()['metadata']['labels']  # 用于删除添加的标签
            labels = re.json()['metadata']['labels']  # 用于添加标签
            # 添加标签的内容
            labels['tester/label'] = 'wxx'
            # 添加标签
            step_add_labels_for_node(cluster_name, node_name, labels)
            # # 获取编辑后节点的标签信息
            r = step_get_node_detail_info(cluster_name, node_name)
            labels_actual = r.json()['metadata']['labels']
            # # 验证标签添加成功
            assert labels == labels_actual
            # 删除添加的标签
            labels_old['tester/label'] = None
            step_add_labels_for_node(cluster_name, node_name, labels_old)

    @allure.story('节点')
    @allure.title('设置每个集群的某个节点为停止调度, 然后设置为启用调度')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_set_uncordon_node(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取节点列表中第一个节点的名称
            res = step_get_nodes(cluster_name)
            node_name = res.json()['items'][0]['metadata']['name']
            # 设置节点为停止调度
            step_cordon_node(cluster_name, node_name, True)
            # 获取节点的调度状态
            r = step_get_node_detail_info(cluster_name, node_name)
            cordon_status = r.json()['spec']['unschedulable']
            # 验证节点调度状态为停止调度
            assert cordon_status == True
            # 设置节点为启用调度
            step_cordon_node(cluster_name, node_name, False)

    @allure.story('节点')
    @allure.title('查看每个集群的某个节点的pod信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_pods(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取节点列表中第一个节点的名称
            re = step_get_nodes(cluster_name)
            node_name = re.json()['items'][0]['metadata']['name']
            # 查看节点的pod信息
            r = step_get_pod_of_node(cluster_name, node_name)
            # 验证pod信息查询成功
            assert r.status_code == 200

    @allure.story('节点')
    @allure.title('查看每个集群的某个节点的event信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_events(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取节点列表中第一个节点的名称
            re = step_get_nodes(cluster_name)
            node_name = re.json()['items'][0]['metadata']['name']
            # 查看节点的event信息
            r = step_get_event_of_node(cluster_name, node_name)
            # 获取资源类型
            kind = r.json()['kind']
            # 验证event信息查询成功
            assert kind == 'EventList'

    @allure.story('节点')
    @allure.title('查看每个集群的某个节点的监控信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_monitoring(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取节点列表中第一个节点的名称
            re = step_get_nodes(cluster_name)
            node_name = re.json()['items'][0]['metadata']['name']
            # 获取当前时间的10位时间戳
            now_timestamp = str(time.time())[0:10]
            # 获取10分钟之前的戳
            before_timestamp = commonFunction.get_before_timestamp(10)
            # 查看最近十分钟的监控信息
            r = step_get_metrics_of_node(cluster_name=cluster_name, node_name=node_name, start_time=before_timestamp,
                                         end_time=now_timestamp,
                                         step='60s', times='10')
            # 获取查询到的数据的结果类型
            resultType = r.json()['results'][0]['data']['resultType']
            # 验证查询到的数据的结果类型
            assert resultType == 'matrix'

    @allure.story('节点')
    @allure.title('查看每个集群的某个节点的状态信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_status(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取节点列表中第一个节点的名称
            re = step_get_nodes(cluster_name)
            node_name = re.json()['items'][0]['metadata']['name']
            # 获取当前时间的10位时间戳
            now_timestamp = str(time.time())[0:10]
            # 获取20分钟之前的时间戳
            before_timestamp = commonFunction.get_before_timestamp(20)
            # 查看节点的状态信息
            r = step_get_status_of_node(cluster_name=cluster_name, node_name=node_name, start_time=before_timestamp,
                                        end_time=now_timestamp, step='180s', times='20')
            # 获取查询结果中的节点信息
            node = r.json()['results'][0]['data']['result'][0]['metric']['node']
            # 验证查询结果正确
            assert node == node_name

    @allure.story('节点')
    @allure.title('在每个集群中查询节点中不存在的pod')
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_non_existent_pod(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取节点列表中第一个节点的名称
            res = step_get_nodes(cluster_name)
            node_name = res.json()['items'][0]['metadata']['name']
            # 查询不存在的pod
            pod_name = 'non-existent'
            re = step_query_pod(cluster_name, node_name, pod_name)
            # 获取查询结果
            totalItems = re.json()['totalItems']
            # 验证查询结果
            assert totalItems == 0

    @allure.story('节点')
    @allure.title('按名称在每个集群中精确查询节点中存在的pod')
    @allure.severity(allure.severity_level.NORMAL)
    def test_precise_query_existent_pod(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取节点列表中第一个节点的名称
            res = step_get_nodes(cluster_name)
            node_name = res.json()['items'][0]['metadata']['name']
            # 获取节点的任意一个pod的名称
            re = step_get_pod_of_node(cluster_name, node_name)
            pod_name = re.json()['items'][0]['metadata']['name']
            # 按名称精确查询存在的pod
            r = step_query_pod(cluster_name, node_name, pod_name)
            # 获取查询到的pod名称
            name_actual = r.json()['items'][0]['metadata']['name']
            # 验证查询结果
            assert name_actual == pod_name

    @allure.story('节点')
    @allure.title('按名称在每个集群模糊查询节点中存在的pod')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_query_existent_pod(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取节点列表中第一个节点的名称
            res = step_get_nodes(cluster_name)
            node_name = res.json()['items'][0]['metadata']['name']
            # 获取节点的任意一个pod的名称
            re = step_get_pod_of_node(cluster_name, node_name)
            pod_name = re.json()['items'][0]['metadata']['name']
            # 按名称模糊查询存在的pod
            pod_fuzzy_name = pod_name[2:]
            r = step_query_pod(cluster_name, node_name, pod_fuzzy_name)
            # 获取查询到的pod名称
            name_actual = r.json()['items'][0]['metadata']['name']
            # 验证查询结果
            assert name_actual == pod_name

    @allure.story('项目')
    @allure.title('按名称在每个集群精确查询集群中不存在的系统项目')
    @allure.severity(allure.severity_level.NORMAL)
    def test_precise_non_existent_system_project(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            project_name = 'non-existent-project'
            # 查询指定的集群的系统项目
            re = step_query_system_project(cluster_name, project_name)
            # 获取查询结果
            items = re.json()['items']
            # 验证查询结果为空
            assert items == []

    @allure.story('项目')
    @allure.title('按名称在每个集群精确查询集群中存在的系统项目')
    @allure.severity(allure.severity_level.NORMAL)
    def test_precise_query_existent_system_project(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取集群任意系统项目的名称
            re = step_query_system_project(cluster_name, '')
            project_name = re.json()['items'][0]['metadata']['name']
            # 按名称精确查询系统项目
            r = step_query_system_project(cluster_name, project_name)
            # 获取查询结果
            project_name_actual = r.json()['items'][0]['metadata']['name']
            # 验证查询结果
            assert project_name_actual == project_name

    @allure.story('项目')
    @allure.title('按名称在每个集群模糊查询集群中存在的系统项目')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_query_existent_system_project(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取集群任意系统项目的名称
            re = step_query_system_project(cluster_name, '')
            project_name = re.json()['items'][0]['metadata']['name']
            # 按名称精确查询系统项目
            fuzzy_project_name = project_name[2:]
            r = step_query_system_project(cluster_name, fuzzy_project_name)
            # 获取查询结果
            project_name_actual = r.json()['items'][0]['metadata']['name']
            # 验证查询结果
            assert project_name_actual == project_name

    @allure.story('项目')
    @allure.title('查询每个集群中所有系统项目的详情信息,并验证其状态为活跃')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_check_system_project_state(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取集群中系统项目的数量
            re = step_query_system_project(cluster_name, '')
            project_count = re.json()['totalItems']
            # 获取集群任意系统项目的名称
            for j in range(0, project_count):
                project_name = re.json()['items'][j]['metadata']['name']
                # 查询项目的详细信息
                r = step_get_project_detail(project_name)
                # 获取项目的状态
                status = r.json()['status']['phase']
                # 验证项目运行状态为活跃
                assert status == 'Active'

    @allure.story('项目')
    @allure.title('查询每个集群中所有系统项目的配额信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_one_system_project_quota(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取集群中系统项目的数量
            re = step_query_system_project(cluster_name, '')
            project_count = re.json()['totalItems']
            for j in range(0, project_count):
                # 获取集群所有系统项目的名称
                project_name = re.json()['items'][j]['metadata']['name']
                # 查询项目的配额信息
                r = step_get_project_quota(cluster_name, project_name)
                # 获取项目的配额信息
                used = r.json()['data']['used']
                # 验证项目配额信息获取成功
                assert 'count/pods' in used

    @allure.story('项目')
    @allure.title('查询每个集群中所有系统项目的LimitRanges信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_one_system_project_detail(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取集群中系统项目的数量
            re = step_query_system_project(cluster_name, '')
            project_count = re.json()['totalItems']
            for j in range(0, project_count):
                # 获取集群任意系统项目的名称
                project_name = re.json()['items'][j]['metadata']['name']
                # 查询项目的LimitRanges
                r = step_get_project_limit_ranges(cluster_name, project_name)
                # 获取请求资源的kind
                kind = r.json()['kind']
                # 验证请求资源的kind为LimitRangeList
                assert kind == 'LimitRangeList'

    @allure.story('项目')
    @allure.title('查询每个集群中所有系统项目的工作负载信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_system_project_workload(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取集群中系统项目的数量
            res = step_query_system_project(cluster_name, '')
            project_count = res.json()['totalItems']
            for j in range(0, project_count):
                # 获取集群任意系统项目的名称
                re = step_query_system_project(cluster_name, '')
                project_name = re.json()['items'][j]['metadata']['name']
                # 查询项目的工作负载信息
                r = step_get_project_workload(cluster_name, project_name)
                # 获取接口的响应数据
                data = r.json()['data']
                # 验证接口响应数据正确
                data_except = ['daemonsets', 'deployments', 'jobs', 'persistentvolumeclaims', 'statefulsets']
                assert data_except[random.randint(0, 4)] in data

    @allure.story('项目')
    @allure.title('验证每个集群中所有系统项目的pod运行正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_check_system_project_pods(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取集群中系统项目的数量
            res = step_query_system_project(cluster_name, '')
            project_count = res.json()['totalItems']
            # 获取集群中所有系统项目的名称
            for j in range(0, project_count):
                project_name = res.json()['items'][j]['metadata']['name']
                # 查询项目的pods信息
                r = step_get_pods_of_project(cluster_name=cluster_name, project_name=project_name)
                # 获取pod的数量
                pod_count = r.json()['totalItems']
                # 获取所有pod的状态
                for k in range(0, pod_count):
                    state = r.json()['items'][k]['status']['phase']
                    # 获取pod的名称
                    pod_name = r.json()['items'][k]['metadata']['name']
                    if state not in ['Running', 'Succeeded']:
                        print('集群：' + cluster_name + ' 项目：' + project_name + ' 容器组：' + pod_name + ' 状态不正常')
                    # 验证pod的运行状态
                    pytest.assume(state in ['Running', 'Succeeded'])

    @allure.story('项目')
    @allure.title('在没个集群中使用名称精确查询项目中存在的pod')
    @allure.severity(allure.severity_level.NORMAL)
    def test_precise_query_existent_pod_of_project(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 用于存放pod的名称
            pod_names = []
            # 获取集群中任一系统项目的名称
            res = step_query_system_project(cluster_name, '')
            project_name = res.json()['items'][3]['metadata']['name']
            # 查询项目的所有的pod信息
            re = step_get_pods_of_project(cluster_name=cluster_name, project_name=project_name)
            # 获取pod的数量
            pod_count = re.json()['totalItems']
            # 获取项目的pod的名称
            for j in range(0, pod_count):
                name = re.json()['items'][j]['metadata']['name']
                pod_names.append(name)
            # 使用pod的名称，精确查询存在的pod
            r = step_get_pods_of_project(cluster_name, project_name, 'name=' + pod_names[0])
            # 获取查询结果中pod名称
            pod_name_actual = r.json()['items'][0]['metadata']['name']
            # 验证查询结果正确
            assert pod_name_actual == pod_names[0]

    @allure.story('项目')
    @allure.title('在每个集群中使用名称模糊查询项目中存在的pod')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_query_existent_pod_of_project(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 用于存放pod的名称
            pod_names = []
            # 获取集群中任一系统项目的名称
            res = step_query_system_project(cluster_name, '')
            project_name = res.json()['items'][3]['metadata']['name']
            # 查询项目的所有的pod信息
            re = step_get_pods_of_project(cluster_name=cluster_name, project_name=project_name)
            # 获取pod的数量
            pod_count = re.json()['totalItems']
            # 获取项目的pod的名称
            for j in range(0, pod_count):
                name = re.json()['items'][j]['metadata']['name']
                pod_names.append(name)
            # 使用pod的名称，模糊查询存在的pod
            r = step_get_pods_of_project(cluster_name, project_name, 'name=' + pod_names[0][2:])
            # 获取查询结果中pod名称
            pod_name_actual = r.json()['items'][0]['metadata']['name']
            # 验证查询结果正确
            assert pod_name_actual == pod_names[0]

    @allure.story('项目')
    @allure.title('在每个集群中使用名称查询项目中不存在的pod')
    @allure.severity(allure.severity_level.NORMAL)
    def test_fuzzy_query_existent_pod_of_project(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取集群中任一系统项目的名称
            re = step_query_system_project(cluster_name, '')
            project_name = re.json()['items'][3]['metadata']['name']
            # 使用pod的名称，模糊查询存在的pod
            pod_name = 'test' + str(commonFunction.get_random())
            r = step_get_pods_of_project(cluster_name, project_name, 'name=' + pod_name)
            # 获取查询结果中的pod数量
            pod_count = r.json()['totalItems']
            # 验证查询结果正确
            assert pod_count == 0

    @allure.story('项目')
    @allure.title('在每个集群中创建用户项目，并验证项目创建成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_user_system(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            project_name = 'user-project' + str(commonFunction.get_random())
            alias_name = 'test'
            description = 'create user-system'
            # 创建用户项目
            step_create_user_project(cluster_name, project_name, alias_name, description)
            # 查询创建的项目，并获取其运行状态
            r = step_get_user_system(cluster_name, project_name)
            state = r.json()['status']['phase']
            # 验证项目的状态为active
            assert state == 'Active'
            # 删除创建的项目
            step_delete_user_system(cluster_name, project_name)

    @allure.story('项目')
    @allure.title('在每个集群删除用户项目，并验证删除成功')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_user_system(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            project_name = 'user-project' + str(commonFunction.get_random())
            alias_name = 'test'
            description = 'create user-system'
            # 创建用户项目
            step_create_user_project(cluster_name, project_name, alias_name, description)
            # 删除用户项目
            re = step_delete_user_system(cluster_name, project_name)
            # 获取删除项目的状态
            state = re.json()['status']['phase']
            # 验证删除项目的状态为Terminating
            assert state == 'Terminating'
            # 等待项目删除成功
            i = 0
            while i < 60:
                # 查询被删除的项目并获取查询结果
                r = step_get_user_system(cluster_name, project_name)
                status = r.json()['status']
                if status == {'phase': 'Terminating'}:
                    time.sleep(1)
                    i += 1
                else:
                    break
            # 验证项目删除成功
            assert status == 'Failure'

    @allure.story('应用负载')
    @allure.title('在每个集群查看集群所有的deployments，并验证其运行正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_check_deployments_of_cluster(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询集群所有的deployments
            re = step_get_resource_of_cluster(cluster_name, 'deployments')
            # 获取集群deployments的数量
            count = re.json()['totalItems']
            # 获取集群所有的deployments的状态
            for j in range(0, count):
                state = re.json()['items'][j]['status']['conditions'][0]['status']
                # 验证deployment的状态为True
                assert state == 'True'

    @allure.story('应用负载')
    @allure.title('查看每个集群所有的deployments的Revision Records')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_check_deployments_revision_records(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询集群所有的deployments
            re = step_get_resource_of_cluster(cluster_name, 'deployments')
            # 获取集群deployments的数量
            count = re.json()['totalItems']
            # 获取集群所有的deployments的labels
            for j in range(0, count):
                label_selector = ''
                project_name = re.json()['items'][j]['metadata']['namespace']
                labels = re.json()['items'][j]['spec']['selector']['matchLabels']
                # 将labels的key和value拼接为label_selector
                keys = list(labels.keys())
                values = list(labels.values())
                for k in range(0, len(keys)):
                    label_selector += keys[k] + '=' + values[k] + ','
                # 去掉最后的逗号
                label_selector = label_selector[:-1]
                # 查看deployments的revision records信息
                r = step_get_deployment_revision_records(project_name, label_selector)
                # 获取请求的资源类型
                kind = r.json()['kind']
                # 验证请求的资源类型为ReplicaSetList
                assert kind == 'ReplicaSetList'

    @allure.story('应用负载')
    @allure.title('查看每个集群所有的statefulSets，并验证其运行正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_check_statefulsets_of_cluster(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询集群所有的statefulSets
            re = step_get_resource_of_cluster(cluster_name, 'statefulsets')
            # 获取集群statefulSets的数量
            count = re.json()['totalItems']
            # 获取集群所有的statefulSets的副本数和ready的副本数
            for j in range(0, count):
                replica = re.json()['items'][j]['status']['replicas']
                readyReplicas = re.json()['items'][j]['status']['readyReplicas']
                # 验证每个statefulSets的ready的副本数=副本数
                assert replica == readyReplicas

    @allure.story('应用负载')
    @allure.title('查看每个集群所有的daemonSets，并验证其运行正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_check_daemonsets_of_cluster(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询集群所有的daemonSets
            re = step_get_resource_of_cluster(cluster_name, 'daemonsets')
            # 获取集群daemonSets的数量
            count = re.json()['totalItems']
            # 获取集群所有的daemonSets的currentNumberScheduled和desiredNumberScheduled
            for j in range(0, count):
                currentNumberScheduled = re.json()['items'][j]['status']['currentNumberScheduled']
                desiredNumberScheduled = re.json()['items'][j]['status']['desiredNumberScheduled']
                # 验证每个daemonSets的currentNumberScheduled=desiredNumberScheduled
                assert currentNumberScheduled == desiredNumberScheduled

    @allure.story('应用负载')
    @allure.title('查看每个集群所有的daemonSets的详情信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_check_daemonsets_detail_of_cluster(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询集群所有的daemonSets
            re = step_get_resource_of_cluster(cluster_name, 'daemonsets')
            # 获取集群daemonSets的数量
            count = re.json()['totalItems']
            # 获取集群中所有的daemonSets的名称和所在的项目名称
            for j in range(0, count):
                resource_name = re.json()['items'][j]['metadata']['name']
                project_name = re.json()['items'][j]['metadata']['namespace']
                # 查询daemonSets的详细信息
                r = step_get_app_workload_detail(cluster_name, project_name, 'daemonsets', resource_name)
                # 验证信息查询成功
                assert r.json()['kind'] == 'DaemonSet'

    @allure.story('应用负载')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('type, title',
                             [('statefulsets', '查看每个集群所有的statefulSets的Revision Records'),
                              ('daemonsets', '查看每个集群所有的daemonSets的Revision Records')])
    def test_check_app_workload_revision_records(self, type, title):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询集群所有的daemonSets
            res = step_get_resource_of_cluster(cluster_name=cluster_name, resource_type=type)
            # 获取集群daemonSets的数量
            count = res.json()['totalItems']
            # 获取所有的daemonSets的label、project_name和daemonSets的名称
            for j in range(0, count):
                labels = res.json()['items'][j]['metadata']['labels']
                # 将labels的key和value拼接为label_selector
                keys = list(labels.keys())
                values = list(labels.values())
                for k in range(0, len(keys)):
                    label_selector = ''
                    label_selector += keys[k] + '=' + values[k] + ','
                # 去掉最后的逗号
                label_selector = label_selector[:-1]
                # 获取daemonSets的名称和所在的项目名称
                project_name = res.json()['items'][i]['metadata']['namespace']
                # 查看daemonSets的revision Records 信息
                r = step_get_app_workload_revision_records(cluster_name, project_name, label_selector)
                # 获取请求的资源类型
                kind = r.json()['kind']
                # 验证请求的资源类型为ControllerRevisionList
                assert kind == 'ControllerRevisionList'

    @allure.story('应用负载')
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title('{title}')
    @pytest.mark.parametrize('type, title',
                             [('deployments', '查看每个集群所有的deployments的Monitoring'),
                              ('statefulsets', '查看每个集群所有的statefulSets的Monitoring'),
                              ('daemonsets', '查看每个集群所有的daemonSets的Monitoring'),
                              ('pods', '查看每个集群所有pod的Monitoring'),
                              ('services', '查看每个集群所有service的Monitoring')])
    def test_check_app_workload_monitoring(self, type, title):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询集群所有的daemonSets
            re = step_get_resource_of_cluster(cluster_name, type)
            # 获取集群daemonSets的数量
            count = re.json()['totalItems']
            # 获取所有的daemonSets的project_name和daemonSets的名称
            for j in range(0, count):
                project_name = re.json()['items'][j]['metadata']['namespace']
                resource_name = re.json()['items'][j]['metadata']['name']
                # 查看监控信息
                r = step_get_app_workload_monitoring(cluster_name, project_name, type, resource_name)
                # 获取请求结果中监控数据的类型
                resultType = r.json()['results'][0]['data']['resultType']
                # 验证请求结果中监控数据的类型为vector
                assert resultType == 'vector'

    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('story, type, title',
                             [('应用负载', 'deployments', '查看每个集群所有的deployments的event'),
                              ('应用负载', 'statefulsets', '查看每个集群所有的statefulSets的event'),
                              ('应用负载', 'daemonsets', '查看每个集群所有的daemonSets的event'),
                              ('应用负载', 'pods', '查看每个集群所有pod的event'),
                              ('应用负载', 'services', '查看每个集群所有service的event'),
                              ('存储', 'persistentvolumeclaims', '查看每个集群所有pvc的event')
                              ])
    def test_check_app_workload_event(self, story, type, title):
        allure.dynamic.story(story)
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询集群所有的资源
            re = step_get_resource_of_cluster(cluster_name, type)
            # 获取集群某一资源的数量
            count = re.json()['totalItems']
            # 获取某一资源所有的project_name,资源的名称和uid
            for j in range(0, count):
                project_name = re.json()['items'][j]['metadata']['namespace']
                resource_name = re.json()['items'][j]['metadata']['name']
                resource_uid = response.json()['items'][i]['metadata']['uid']
                # 查询daemonSets的event信息
                r = step_get_resource_event(cluster_name, project_name, type, resource_name, resource_uid)
                # 获取请求结果的类型
                kind = r.json()['kind']
                # 验证请求结果的类型为EventList
                assert kind == 'EventList'

    @allure.story('应用负载')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('type, title',
                             [('deployments', '在每个集群按名称精确查询存在的deployments'),
                              ('statefulsets', '在每个集群按名称精确查询存在的statefulSets'),
                              ('daemonsets', '在每个集群按名称精确查询存在的daemonSets'),
                              ('pods', '在每个集群按名称模糊查询存在的pod'),
                              ('services', '在每个按名称模糊查询存在的service')])
    def test_precise_query_app_workload_by_name(self, type, title):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取集群中存在的资源的名称
            re = step_get_resource_of_cluster(cluster_name, type)
            # 获取第一个资源的名称
            name = re.json()['items'][0]['metadata']['name']
            r = step_get_resource_of_cluster(cluster_name, type, 'name=' + name)
            # 获取查询结果的名称
            name_actual = r.json()['items'][0]['metadata']['name']
            # 验证查询结果正确
            assert name == name_actual

    @allure.story('应用负载')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('type, title',
                             [('deployments', '在每个集群按名称模糊查询存在的deployments'),
                              ('statefulsets', '在每个集群按名称模糊查询存在的statefulSets'),
                              ('daemonsets', '在每个集群按名称模糊查询存在的daemonSets'),
                              ('pods', '在每个集群按名称模糊查询存在的pod'),
                              ('services', '在每个集群按名称模糊查询存在的service')])
    def test_fuzzy_query_app_workload_by_name(self, type, title):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取集群中存在的资源的名称
            re = step_get_resource_of_cluster(cluster_name, type)
            # 获取第一个资源的名称
            name = re.json()['items'][0]['metadata']['name']
            r = step_get_resource_of_cluster(cluster_name, type, 'name=' + name[2:])
            # 获取查询结果的名称
            name_actual = r.json()['items'][0]['metadata']['name']
            # 验证查询结果正确
            assert name == name_actual

    @allure.story('应用负载')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('type, title',
                             [('deployments', '在每个集群按状态查询存在的deployments'),
                              ('statefulsets', '在每个集群按状态查询存在的statefulSets'),
                              ('daemonsets', '在每个集群按状态查询存在的daemonSets')])
    def test_query_app_workload_by_status(self, type, title):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询状态为running的资源
            r = step_get_resource_of_cluster(cluster_name, type, 'status=running')
            # 获取资源的数量
            count = r.json()['totalItems']
            # 获取资源的readyReplicas和replicas
            for j in range(0, count):
                if type == 'daemonsets':
                    readyReplicas = r.json()['items'][j]['status']['numberReady']
                    replicas = r.json()['items'][j]['status']['numberAvailable']
                else:
                    readyReplicas = r.json()['items'][j]['status']['readyReplicas']
                    replicas = r.json()['items'][j]['status']['replicas']
                # 验证readyReplicas=replicas，从而判断资源的状态为running
                assert readyReplicas == replicas

    @allure.story('应用负载')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('type, title',
                             [('deployments', '在每个集群按状态和名称查询存在的deployments'),
                              ('statefulsets', '在每个集群按状态和名称查询存在的statefulSets'),
                              ('daemonsets', '在每个集群按状态和名称查询存在的daemonSets')])
    def test_query_app_workload_by_status_and_name(self, type, title):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询集群中所有的资源
            re = step_get_resource_of_cluster(cluster_name, type)
            # 获取资源的数量
            count = re.json()['totalItems']
            running_resource = []
            for j in range(0, count):
                if type == 'daemonsets':
                    readyReplicas = re.json()['items'][j]['status']['numberReady']
                    replicas = re.json()['items'][j]['status']['numberAvailable']
                else:
                    readyReplicas = re.json()['items'][j]['status']['readyReplicas']
                    replicas = re.json()['items'][j]['status']['replicas']
                if readyReplicas == replicas:
                    running_resource.append(re.json()['items'][i]['metadata']['name'])
            # 使用名称和状态查询资源
            for name in running_resource:
                r = step_get_resource_of_cluster(cluster_name, type, 'name=' + name, 'status=running')
                # 获取查询结果中的name
                name_actual = r.json()['items'][0]['metadata']['name']
                # 验证查询的结果正确
                assert name == name_actual

    @allure.story('应用负载')
    @allure.title('获取每个集群所有的容器组，并验证其数量与从项目管理中获取的数量一致')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_pods_of_cluster(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取集群的容器组的数量
            res = step_get_pods_of_cluster(cluster_name)
            count = res.json()['totalItems']
            # 从项目管理处获取所有项目的名称
            project_name = []
            re = step_get_project_of_cluster(cluster_name)
            project_count = re.json()['totalItems']
            for j in range(0, project_count):
                name = re.json()['items'][j]['metadata']['name']
                project_name.append(name)
            # 获取每个项目的pod数量,并将其加和
            pod_counts = 0
            for project in project_name:
                r = step_get_pods_of_project(cluster_name, project)
                pod_count = r.json()['totalItems']
                pod_counts += pod_count
            # 验证集群的容器数量等于每个项目的容器数之和
            assert count == pod_counts

    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('story, type, title',
                             [('配置中心', 'secrets', '在每个集群按名称精确查询存在的密钥'),
                              ('配置中心', 'configmaps', '在每个集群按名称精确查询存在的配置'),
                              ('配置中心', 'serviceaccounts', '在每个集群按名称精确查询存在的服务账号'),
                              ('CRDs', 'customresourcedefinitions', '在每个集群按名称精确查询存在的CRD'),
                              ('存储', 'persistentvolumeclaims', '在每个集群按名称精确查询存在的存储卷'),
                              ('存储', 'storageclasses', '在每个集群按名称精确查询存在的存储类型')
                              ])
    def test_precise_query_resource_by_name(self, story, type, title):
        allure.dynamic.story(story)
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取集群中存在的任一资源的名称
            re = step_get_resource_of_cluster(cluster_name=cluster_name, resource_type=type)
            count = re.json()['totalItems']
            name = re.json()['items'][random.randint(0, count - 1)]['metadata']['name']
            # 按名称精确查询存在的资源
            r = step_get_resource_of_cluster(cluster_name, type, 'name=' + name)
            name_actual = r.json()['items'][0]['metadata']['name']
            # 验证查询结果正确
            assert name_actual == name

    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('story, type, title',
                             [('配置中心', 'secrets', '在每个集群按名称模糊查询存在的密钥'),
                              ('配置中心', 'configmaps', '在每个集群按名称模糊查询存在的配置'),
                              ('配置中心', 'serviceaccounts', '在每个集群按名称模糊查询存在的服务账号'),
                              ('CRDs', 'customresourcedefinitions', '在每个集群按名称模糊查询存在的CRD'),
                              ('存储', 'persistentvolumeclaims', '在每个集群按名称模糊查询存在的存储卷'),
                              ('存储', 'storageclasses', '在每个集群按名称模糊查询存在的存储类型')
                              ])
    def test_fuzzy_query_resource_by_name(self, story, type, title):
        allure.dynamic.story(story)
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查看集群中的某一种资源
            re = step_get_resource_of_cluster(cluster_name, resource_type=type)
            # 获取集群中某一种资源的数量
            count = re.json()['totalItems']
            # 获取集群中存在的任一资源的名称
            name = re.json()['items'][random.randint(0, count - 1)]['metadata']['name']
            fuzzy_name = name[:-1]
            # 按名称精确查询存在的资源
            r = step_get_resource_of_cluster(cluster_name, type, 'name=' + fuzzy_name)
            name_actual = r.json()['items'][0]['metadata']['name']
            # 验证查询结果正确
            assert name_actual == name

    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('story, type, title',
                             [('配置中心', 'secrets', '在每个集群按项目查询存在的密钥'),
                              ('配置中心', 'configmaps', '在每个集群按项目查询存在的配置'),
                              ('配置中心', 'serviceaccounts', '在每个集群按项目查询存在的服务账号'),
                              ('存储', 'persistentvolumeclaims', '在每个集群按项目查询存在的存储卷')
                              ])
    def test_query_configuration_by_project(self, story, type, title):
        allure.dynamic.story(story)
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询项目为kube-system的所有资源
            r = step_get_resource_of_cluster_by_project(cluster_name=cluster_name, type=type,
                                                        project_name='kubesphere-system')
            # 获取资源数量
            count = r.json()['totalItems']
            # 遍历所有资源，验证资源的项目为kubesphere-system
            for j in range(0, count):
                project = r.json()['items'][j]['metadata']['namespace']
                assert project == 'kubesphere-system'

    @allure.title('{title}')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize('story, type, title',
                             [('配置中心', 'secrets', '在每个集群按项目和名称查询存在的密钥'),
                              ('配置中心', 'configmaps', '在每个集群按项目和名称查询存在的配置'),
                              ('配置中心', 'serviceaccounts', '在每个集群按项目和名称查询存在的服务账号'),
                              ('存储', 'persistentvolumeclaims', '在每个集群按项目和名称查询存在的存储卷')
                              ])
    def test_query_configuration_by_project_and_name(self, story, type, title):
        allure.dynamic.story(story)
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询项目为kube-system的所有资源
            if type == 'persistentvolumeclaims':
                re = step_get_resource_of_cluster_by_project(cluster_name=cluster_name, type=type,
                                                         project_name='kubesphere-monitoring-system')
                # 获取资源数量
                count = re.json()['totalItems']
                # 获取任一资源的名称
                name = re.json()['items'][0]['metadata']['name']
                # 按项目和名称查询资源
                r = step_get_resource_of_cluster_by_project(cluster_name, type, 'kubesphere-monitoring-system',
                                                            'name=' + name)
                # 在查询结果中获取资源名称和数量
                name_actual = r.json()['items'][0]['metadata']['name']
                count = r.json()['totalItems']
            else:
                re = step_get_resource_of_cluster_by_project(cluster_name=cluster_name, type=type,
                                                             project_name='kubesphere-system')
                # 获取资源数量
                count = re.json()['totalItems']
                # 获取任一资源的名称
                name = re.json()['items'][random.randint(0, count - 1)]['metadata']['name']
                # 按项目和名称查询资源
                r = step_get_resource_of_cluster_by_project(cluster_name, type, 'kubesphere-system', 'name=' + name)
                # 在查询结果中获取资源名称和数量
                name_actual = r.json()['items'][0]['metadata']['name']
                count = r.json()['totalItems']
            # 验证查询结果正确
            assert name_actual == name
            assert count == 1

    @allure.story('CRDs')
    @allure.title('在每个集群查询所有CRD的详情信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_crd_detail(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询集群中的crd
            re = step_get_resource_of_cluster(cluster_name=cluster_name, resource_type='customresourcedefinitions')
            # 获取crd的数量
            count = re.json()['totalItems']
            # 获取crd的名称
            for j in range(0, count):
                name = re.json()['items'][j]['metadata']['name']
                # 查询CRD的详情信息
                r = step_get_crd_detail(cluster_name, name)
                # 获取查询结果中的kind
                kind = r.json()['kind']
                # 验证查询结果正确
                assert kind == 'CustomResourceDefinition'

    @allure.story('CRDs')
    @allure.title('在每个集群查询所有CRD的FederatedGroupList')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_crd_federated_group_list(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询集群中的crd
            res = step_get_resource_of_cluster(cluster_name=cluster_name, resource_type='customresourcedefinitions')
            # 获取crd的数量
            count = res.json()['totalItems']
            # 获取crd的group和kind
            for j in range(0, count):
                # 获取crd的名称
                name = res.json()['items'][j]['metadata']['name']
                # 获取crd的group,version和kind
                re = step_get_crd_detail(cluster_name, name)
                group = re.json()['spec']['group']
                version = re.json()['spec']['version']
                kind = res.json()['items'][j]['spec']['names']['kind']
                # 查询crd的FederatedGroupList信息
                r = step_get_crd_federated_group_list(cluster_name, group, version, kind.lower())
                # 验证查询结果正确
                assert r.status_code == 200

    @allure.story('存储')
    @allure.title('在每个集群按状态查询存储卷，并验证查询结果正确')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_pvc_by_status(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询状态为bound的存储卷
            r = step_get_resource_of_cluster(cluster_name, 'persistentvolumeclaims', 'status=bound')
            # 获取存储卷数量
            count = r.json()['totalItems']
            # 获取并验证所有存储卷的状态为Bound
            for j in range(0, count):
                status = r.json()['items'][j]['status']['phase']
                assert status == 'Bound'

    @allure.story('存储')
    @allure.title('在每个集群查询每一个存储卷的详情信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_pvc_detail(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询集群的存储卷
            re = step_get_resource_of_cluster(cluster_name, 'persistentvolumeclaims')
            # 获取存储卷的数量
            count = re.json()['totalItems']
            # 获取所有存储卷的名称和所在namespace
            for j in range(0, count):
                name = re.json()['items'][j]['metadata']['name']
                namespace = re.json()['items'][j]['metadata']['namespace']
                # 查询存储卷的详情信息
                r = step_get_pvc_detail(cluster_name, namespace, name)
                # 获取查询结果的kind
                kind = r.json()['kind']
                # 验证查询结果正确
                assert kind == 'PersistentVolumeClaim'

    @allure.story('存储')
    @allure.title('在每个集群查询每一个存储卷的监控信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_pvc_metrics(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询集群存在的存储卷信息
            re = step_get_resource_of_cluster(cluster_name, 'persistentvolumeclaims')
            # 获取存储卷的数量
            count = re.json()['totalItems']
            # 获取所有存储卷的名称和所在namespace
            for j in range(0, count):
                name = re.json()['items'][j]['metadata']['name']
                namespace = re.json()['items'][j]['metadata']['namespace']
                # 获取当前时间的10位时间戳
                now_timestamp = str(time.time())[0:10]
                # 获取60分钟之前的时间时间戳
                before_timestamp = commonFunction.get_before_timestamp(60)
                # 查询每个pvc最近1个小时的监控信息
                r = step_get_metrics_of_pvc(cluster_name, namespace, name, before_timestamp, now_timestamp, '60s', '60')
                # 获取查询到的数据的结果类型
                resultType = r.json()['results'][0]['data']['resultType']
                # 验证查询到的数据的结果类型
                assert resultType == 'matrix'

    @allure.story('存储')
    @allure.title('在每个集群查询每一个存储卷的pod信息,并验证pod运行正常')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_pvc_pods(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询集群存在的存储卷信息
            re = step_get_resource_of_cluster(cluster_name, 'persistentvolumeclaims')
            # 获取存储卷的数量
            count = re.json()['totalItems']
            # 获取所有存储卷的名称和所在namespace
            for j in range(0, count):
                name = re.json()['items'][j]['metadata']['name']
                namespace = re.json()['items'][j]['metadata']['namespace']
                # 查询存储卷的pod信息
                r = step_get_pods_of_project(cluster_name, namespace, 'pvcName=' + name)
                # 获取pod的数量
                count_pod = r.json()['totalItems']
                # 获取所有pod的运行状态
                for k in range(0, count_pod):
                    status = r.json()['items'][k]['status']['phase']
                    # 验证pod的状态为Running
                    assert status == 'Running'

    @allure.story('存储')
    @allure.title('在每个集群查看所有存储卷的快照信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_pvc_snapshot(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询集群存在的存储卷信息
            re = step_get_resource_of_cluster(cluster_name, 'persistentvolumeclaims')
            # 获取存储卷的数量
            count = re.json()['totalItems']
            # 获取所有存储卷的名称和所在namespace
            for j in range(0, count):
                name = re.json()['items'][j]['metadata']['name']
                namespace = re.json()['items'][j]['metadata']['namespace']
                # 查询每个pvc的快照信息
                r = step_get_resource_of_cluster_by_project(cluster_name, 'volumesnapshots', namespace,
                                                            'persistentVolumeClaimName=' + name)
                # 验证查询成功
                assert r.status_code == 200

    @allure.story('存储')
    @allure.title('在每个集群查询存储类型的详细信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_storage_class_detail(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询集群存在的存储类型
            re = step_get_resource_of_cluster(cluster_name, 'storageclasses')
            # 获取存储类型的数量
            count = re.json()['totalItems']
            # 获取所有的存储类型的名称
            for j in range(0, count):
                name = re.json()['items'][j]['metadata']['name']
                # 查询每个存储类型的详情信息
                r = step_get_storage_class_detail(cluster_name, name)
                # 获取详情信息中的kind
                kind = r.json()['kind']
                # 验证查询结果正确
                assert kind == 'StorageClass'

    @allure.story('存储')
    @allure.title('在每个集群将存储类型设置为默认的存储类型')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_set_default_storage_class(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询集群存在的存储类型
            re = step_get_resource_of_cluster(cluster_name, 'storageclasses')
            # 获取存储类型的数量
            count = re.json()['totalItems']
            # 获取任一存储类型的名称
            name = re.json()['items'][random.randint(0, count - 1)]['metadata']['name']
            # 将任一存储类型设置为非默认存储类型
            r = step_set_default_storage_class(cluster_name, name, 'false')
            # 获取请求结果中的storageclass.kubernetes.io/is-default-class
            result = r.json()['metadata']['annotations']['storageclass.kubernetes.io/is-default-class']
            # 验证结果为false
            assert result == 'false'

            # 将任一存储类型设置为默认存储类型
            r = step_set_default_storage_class(cluster_name, name, 'true')
            # 获取请求结果中的storageclass.kubernetes.io/is-default-class
            result = r.json()['metadata']['annotations']['storageclass.kubernetes.io/is-default-class']
            # 验证结果为true
            assert result == 'true'

    @allure.story('监控&告警')
    @allure.title('在每个集群查看组件的运行状态并验证组件均健康运行')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_component_health(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取组件的健康状况
            r = step_get_component_health(cluster_name)
            # 获取组件的数量
            component_count = len(r.json()['kubesphereStatus'])
            for j in range(0, component_count):
                # 获取每个组件的totalBackends
                totalBackends = r.json()['kubesphereStatus'][j]['totalBackends']
                # 获取每个组件的healthyBackends
                healthyBackends = r.json()['kubesphereStatus'][j]['healthyBackends']
                # 获取组件的名称
                component_name = r.json()['kubesphereStatus'][j]['name']
                # 验证 totalBackends=healthyBackends
                if totalBackends != healthyBackends:
                    print('组件：' + component_name + ' 运行不正常')
                    # 校验失败仍能继续运行
                    pytest.assume(totalBackends == healthyBackends)

    @allure.story('监控&告警')
    @allure.title('在每个集群查看组件的运行状态并验证组件均健康运行')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_node_health(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询节点的健康状况
            r = step_get_component_health(cluster_name)
            # 获取集群的totalNodes
            totalNodes = r.json()['nodeStatus']['totalNodes']
            # 获取集群的healthyNodes
            healthyNodes = r.json()['nodeStatus']['healthyNodes']
            # 验证totalNodes = healthyNodes
            assert totalNodes == healthyNodes

    @allure.story('监控&告警')
    @allure.title('查看每个集群的监控信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_metrics(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取当前时间的10位时间戳
            now_timestamp = str(time.time())[0:10]
            # 获取210分钟之前的时间戳
            before_timestamp = commonFunction.get_before_timestamp(210)
            # 查询集群的最近210分钟的监控信息
            re = step_get_metrics_of_cluster(cluster_name, before_timestamp, now_timestamp, '300s', '100')
            # 获取查询结果的数据类型
            for j in range(0, 10):
                try:
                    result_type = re.json()['results'][j]['data']['resultType']
                    # 验证数据类型为matrix
                    assert result_type == 'matrix'
                except Exception as e:
                    print(e)

    @allure.story('监控&告警')
    @allure.title('查看每个集群的apiserver的监控信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_apiserver_metrics(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取当前时间的10位时间戳
            now_timestamp = str(time.time())[0:10]
            # 获取240分钟之前的时间戳
            before_timestamp = commonFunction.get_before_timestamp(240)
            # 查询集群的最近240分钟的监控信息
            r = step_get_metrics_of_apiserver(cluster_name, before_timestamp, now_timestamp, '300s', '100')
            # 获取查询结果的数据类型
            for j in range(0, 3):
                try:
                    result_type = r.json()['results'][j]['data']['resultType']
                    # 验证数据类型为matrix
                    assert result_type == 'matrix'
                except Exception as e:
                    print(e)

    @allure.story('监控&告警')
    @allure.title('查看每个集群的schedule的监控信息')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_schedule_metrics(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取当前时间的10位时间戳
            now_timestamp = str(time.time())[0:10]
            # 获取240分钟之前的时间
            before_timestamp = commonFunction.get_before_timestamp(240)
            # 查询集群的最近240分钟的监控信息
            r = step_get_metrics_of_scheduler(cluster_name, before_timestamp, now_timestamp, '300s', '100')
            # 获取查询结果的数据类型
            for j in range(0, 2):
                try:
                    result_type = r.json()['results'][j]['data']['resultType']
                    # 验证数据类型为matrix
                    assert result_type == 'matrix'
                except Exception as e:
                    print(e)

    @allure.story('监控&告警')
    @allure.title('{title}')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize('sort, title',
                             [('node_load1', '在每个集群通过Sort by Load Average查看Node Usage Ranking'),
                              ('node_cpu_utilisation', '在每个集群通Sort by CPU查看Node Usage Ranking'),
                              ('node_memory_utilisation', '在每个集群通Sort by Memory查看Node Usage Ranking'),
                              ('node_disk_size_utilisation', '在每个集群通Sort by Local Storage查看Node Usage Ranking'),
                              ('node_disk_inode_utilisation', '在每个集群通Sort by inode Utilization查看Node Usage Ranking'),
                              ('node_pod_utilisation', '在每个集群通Sort by Pod Utilization查看Node Usage Ranking')
                              ])
    def test_get_node_usage_rank(self, sort, title):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 查询Node Usage Ranking
            r = step_get_node_usage_rank(cluster_name, sort)
            # 获取结果中的数据类型
            for j in range(0, 15):
                try:
                    result_type = r.json()['results'][j]['data']['resultType']
                    # 验证数据类型为vector
                    assert result_type == 'vector'
                except Exception as e:
                    print(e)

    @allure.story('监控&告警')
    @allure.title('查看每个集群资源使用情况')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_resource_usage(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取当前时间的10位时间戳
            now_timestamp = str(time.time())[0:10]
            # 获取1440分钟之前的时间
            before_timestamp = commonFunction.get_before_timestamp(1440)
            # 查询最近一天的集群应用资源使用情况
            r = step_get_resource_usage_of_cluster(cluster_name, before_timestamp, now_timestamp, '3600s', '24')
            # 获取结果中的数据类型
            for j in range(0, 3):
                try:
                    result_type = r.json()['results'][j]['data']['resultType']
                    # 验证数据类型为matrix
                    assert result_type == 'matrix'
                except Exception as e:
                    print(e)

    @allure.story('监控&告警')
    @allure.title('查看每个集群应用资源用量')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_app_usage(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取当前时间的10位时间戳
            now_timestamp = str(time.time())[0:10]
            # 获取1440分钟之前的时间
            before_timestamp = commonFunction.get_before_timestamp(1440)
            # 查询最近一天的集群应用资源使用情况
            r = step_get_app_usage_of_cluster(cluster_name, before_timestamp, now_timestamp, '3600s', '24')
            # 获取结果中的数据类型
            for j in range(0, 8):
                try:
                    result_type = r.json()['results'][j]['data']['resultType']
                    # 验证数据类型为matrix
                    assert result_type == 'matrix'
                except Exception as e:
                    print(e)

    @allure.story('监控&告警')
    @allure.title('查看每个集群项目变化趋势')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_cluster_app_usage(self):
        # 获取多集群环境的集群名称
        response = step_get_cluster()
        # 获取集群的数量
        cluster_count = response.json()['totalItems']
        for i in range(0, cluster_count):
            # 获取每个集群的名称
            cluster_name = response.json()['items'][i]['metadata']['name']
            # 获取当前时间的10位时间戳
            now_timestamp = str(time.time())[0:10]
            # 获取1440分钟之前的时间
            before_timestamp = commonFunction.get_before_timestamp(1440)
            # 查询最近一天的集群应用资源使用情况
            r = step_get_project_trend_of_cluster(cluster_name, before_timestamp, now_timestamp, '3600s', '24')
            # 获取结果中的数据类型
            result_type = r.json()['results'][0]['data']['resultType']
            # 验证数据类型为matrix
            assert result_type == 'matrix'
