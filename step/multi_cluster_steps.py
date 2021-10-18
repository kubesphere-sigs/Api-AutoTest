import requests
import allure
import sys
import json

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from config import config
from common.getHeader import get_header, get_header_for_patch


@allure.step('获取集群信息')
def step_get_cluster():
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/clusters'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('获取多集群环境每个集群的名称')
def step_get_cluster_name():
    url = config.url + '/kapis/resources.kubesphere.io/v1alpha3/clusters'
    response = requests.get(url=url, headers=get_header())
    # 获取集群的数量
    cluster_count = response.json()['totalItems']
    cluster_names = []
    for i in range(0, cluster_count):
        # 获取每个集群的名称
        cluster_name = response.json()['items'][i]['metadata']['name']
        cluster_names.append(cluster_name)
    return cluster_names


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
    url = config.url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/pods?nodeName=' + \
          node_name + '&name=' + pod_name + '&sortBy=startTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看节点的event信息')
def step_get_event_of_node(cluster_name, node_name):
    url = config.url + '/api/clusters/' + cluster_name + '/v1/events?fieldSelector=involvedObject.name%3D' + \
          node_name + '%2CinvolvedObject.kind%3DNode'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看节点的监控信息')
def step_get_metrics_of_node(cluster_name, node_name, start_time, end_time, step, times):
    url = config.url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/nodes?start=' + \
          start_time + '&end=' + end_time + \
          '&step=' + step + '&times=' + times + '&resources_filter=' + node_name + \
          '%24&metrics_filter=node_cpu_utilisation%7Cnode_load1%7Cnode_load5%7Cnode_load15%7Cnode_memory_utilisation' \
          '%7Cnode_disk_size_utilisation%7Cnode_disk_inode_utilisation%7Cnode_disk_inode_usage%7Cnode_disk_inode_total' \
          '%7Cnode_disk_read_iops%7Cnode_disk_write_iops%7Cnode_disk_read_throughput%7Cnode_disk_write_throughput' \
          '%7Cnode_net_bytes_transmitted%7Cnode_net_bytes_received%24 '
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看节点的状态信息')
def step_get_status_of_node(cluster_name, node_name, start_time, end_time, step, times):
    url = config.url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/nodes?start=' + \
          start_time + '&end=' + end_time + \
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
    url = config.url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha2/namespaces/' + \
          project_name + '/quotas'
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
    url = config.url + '/apis/clusters/' + cluster_name + '/apps/v1/namespaces/' + \
          project_name + '/controllerrevisions?labelSelector=' \
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
    url = config.url + '/api/clusters/' + cluster_name + '/v1/namespaces/' + project_name + \
          '/events?fieldSelector=involvedObject.name%3D' \
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
    url = config.url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/namespaces/' + \
          project_name + '/' + type + '?' + name_actual + 'sortBy=createTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询CRD的详情信息')
def step_get_crd_detail(cluster_name, crd_name):
    url = config.url + '/apis/clusters/' + cluster_name + \
          '/apiextensions.k8s.io/v1beta1/customresourcedefinitions/' + crd_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询CRD的FederatedGroupList信息')
def step_get_crd_federated_group_list(cluster_name, group, version, kind):
    if kind[-1] == 's':
        url = config.url + '/apis/clusters/' + cluster_name + '/' + group + '/' + version + '/' + kind + 'es'
    elif kind[-1] == 'x':
        url = config.url + '/apis/clusters/' + cluster_name + '/' + group + '/' + version + '/' + kind + 'es'
    elif kind[-2:] == 'ay':
        url = config.url + '/apis/clusters/' + cluster_name + '/' + group + '/' + version + '/' + kind + 's'
    elif kind[-1] == 'y' and kind[-2:] != 'ay':
        kind = kind.replace(kind[-1], 'i')
        url = config.url + '/apis/clusters/' + cluster_name + '/' + group + '/' + version + '/' + kind + 'es'
    else:
        url = config.url + '/apis/clusters/' + cluster_name + '/' + group + '/' + version + '/' + kind + 's'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询存储卷的详情信息')
def step_get_pvc_detail(cluster_name, project_name, pvc_name):
    url = config.url + '/api/clusters/' + cluster_name + '/v1/namespaces/' + project_name + \
          '/persistentvolumeclaims/' + pvc_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询存储卷的监控信息')
def step_get_metrics_of_pvc(cluster_name, project_name, pvc_name, start_time, end_time, step, times):
    url = config.url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/namespaces/' + \
          project_name + '/persistentvolumeclaims/' + pvc_name + '?cluster=default&start=' + \
          start_time + '&end=' + end_time + \
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
    url = config.url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/cluster?start=' + \
          start_time + '&end=' + end_time + \
          '&step=' + step + '&times=' + times + '&metrics_filter=cluster_cpu_usage%7Ccluster_cpu_total' \
        '%7Ccluster_cpu_utilisation%7Ccluster_memory_usage_wo_cache%7Ccluster_memory_total%7C' \
        'cluster_memory_utilisation%7Ccluster_disk_size_usage%7Ccluster_disk_size_capacity%7C' \
        'cluster_disk_size_utilisation%7Ccluster_pod_running_count%7Ccluster_pod_quota%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询apiserver的监控信息')
def step_get_metrics_of_apiserver(cluster_name, start_time, end_time, step, times):
    url = config.url + '/kapis/clusters/' + cluster_name + \
          '/monitoring.kubesphere.io/v1alpha3/components/apiserver?start=' + start_time + \
          '&end=' + end_time + '&step=' + step + '&times=' + times + \
          '&metrics_filter=apiserver_request_latencies%7C' \
          'apiserver_request_by_verb_latencies%7Capiserver_request_rate%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询scheduler的监控信息')
def step_get_metrics_of_scheduler(cluster_name, start_time, end_time, step, times):
    url = config.url + '/kapis/clusters/' + cluster_name + \
          '/monitoring.kubesphere.io/v1alpha3/components/scheduler?start=' + start_time + \
          '&end=' + end_time + '&step=' + step + '&times=' + times + \
          '&metrics_filter=scheduler_schedule_attempts%7Cscheduler_schedule_attempt_rate%24'
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
    url = config.url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/cluster?start=' + \
          start_time + '&end=' + end_time + \
          '&step=' + step + '&times=' + times + \
          '&metrics_filter=cluster_cpu_usage%7Ccluster_memory_usage_wo_cache%7Ccluster_disk_size_usage%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群应用资源用量')
def step_get_app_usage_of_cluster(cluster_name, start_time, end_time, step, times):
    url = config.url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/cluster?start=' + \
          start_time + '&end=' + end_time + \
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
    url = config.url + '/kapis/clusters/' + cluster_name + \
          '/iam.kubesphere.io/v1alpha2/clustermembers/admin/clusterroles'
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
    url = config.url + '/kapis/clusters/' + cluster_name + \
          '/monitoring.kubesphere.io/v1alpha3/components/scheduler?metrics_filter=scheduler_schedule_attempts%24'
    response = requests.get(url=url, headers=get_header())
    return response
