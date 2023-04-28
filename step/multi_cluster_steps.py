import requests
import allure
import sys
import json
from common.getConfig import get_apiserver

env_url = get_apiserver()
sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from common.getHeader import get_header, get_header_for_patch


@allure.step('获取集群信息')
def step_get_cluster():
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/clusters'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('获取多集群环境每个集群的名称')
def step_get_cluster_name():
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/clusters'
    response = requests.get(url=url, headers=get_header())
    # 获取集群的数量
    cluster_count = response.json()['totalItems']
    cluster_names = []
    for i in range(0, cluster_count):
        # 获取每个集群的名称
        cluster_name = response.json()['items'][i]['metadata']['name']
        cluster_names.append(cluster_name)
    return cluster_names


@allure.step('获取host集群的名称')
def step_get_host_cluster_name():
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/clusters?labelSelector=cluster-role.kubesphere.io%2Fhost%3D'
    response = requests.get(url=url, headers=get_header())
    host_cluster_name = response.json()['items'][0]['metadata']['name']
    return host_cluster_name


@allure.step('获取指定集群的节点列表信息')
def step_get_nodes(cluster_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/nodes'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('获取指定集群的边缘节点列表信息')
def step_get_edge_nodes(cluster_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/nodes?sortBy=createTime' \
                                                        '&limit=10&labelSelector=node-role.kubernetes.io%2Fedge%3D'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('添加边缘节点-检验内部IP地址')
def step_check_internal_ip(cluster_name, node_name, internal_ip):
    url = env_url + '/kapis/clusters/' + cluster_name + '/edgeruntime.kubesphere.io/v1alpha1/nodes/join?node_name=' \
          + node_name + '&node_ip=' + internal_ip
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('添加边缘节点-获取边缘节点配置命令')
def step_get_edge_node_config_command(cluster_name, node_name, internal_ip, add_default_taint):
    url = env_url + '/kapis/clusters/' + cluster_name + '/edgeruntime.kubesphere.io/v1alpha1/nodes/join?node_name=' \
          + node_name + '&node_ip=' + internal_ip + '&add_default_taint=' + add_default_taint
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('为节点设置污点')
def step_ste_taints(cluster_name, node_name, taints):
    url = env_url + '/api/clusters/' + cluster_name + '/v1/nodes/' + node_name
    data = {"spec": {"taints": taints}}
    response = requests.patch(url=url, headers=get_header_for_patch(), data=json.dumps(data))
    return response


@allure.step('查看节点的详细信息')
def step_get_node_detail_info(cluster_name, node_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/nodes/' + node_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('往节点中添加标签')
def step_add_labels_for_node(cluster_name, node_name, labels):
    url = env_url + '/api/clusters/' + cluster_name + '/v1/nodes/' + node_name
    data = {"metadata": {"labels": labels}}
    response = requests.patch(url=url, headers=get_header_for_patch(), data=json.dumps(data))
    return response


@allure.step('节点停止/启用调度')
def step_cordon_node(cluster_name, node_name, cordon):
    url = env_url + '/api/clusters/' + cluster_name + '/v1/nodes/' + node_name
    data = {"spec": {"unschedulable": cordon}}
    response = requests.patch(url=url, headers=get_header_for_patch(), data=json.dumps(data))
    return response


@allure.step('查看节点的pod信息')
def step_get_pod_of_node(cluster_name, node_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/pods?nodeName=' \
          + node_name + '&sortBy=startTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询指定的pod')
def step_query_pod(cluster_name, node_name, pod_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/pods?nodeName=' + \
          node_name + '&name=' + pod_name + '&sortBy=startTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看节点的event信息')
def step_get_event_of_node(cluster_name, node_name):
    url = env_url + '/api/clusters/' + cluster_name + '/v1/events?fieldSelector=involvedObject.name%3D' + \
          node_name + '%2CinvolvedObject.kind%3DNode'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看节点的监控信息')
def step_get_metrics_of_node(cluster_name, node_name, start_time, end_time, step, times):
    url = env_url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/nodes?start=' + \
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
    url = env_url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/nodes?start=' + \
          start_time + '&end=' + end_time + \
          '&step=' + step + '&times=' + times + '&resources_filter=' + node_name + \
          '%24&metrics_filter=node_cpu_utilisation%7Cnode_memory_utilisation%7Cnode_disk_size_utilisation' \
          '%7Cnode_pod_utilisation%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群指定的系统项目')
def step_query_system_project(cluster_name, project_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/namespaces?name=' \
          + project_name + '&sortBy=createTime&labelSelector=kubesphere.io%2Fworkspace%3Dsystem-workspace'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群所有的项目')
def step_get_project_of_cluster(cluster_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/namespaces/'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看项目的pod信息')
def step_get_pods_of_project(cluster_name, project_name, *condition):
    condition_actual = ''
    for i in condition:
        condition_actual += str(i) + '&'
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/namespaces/' \
          + project_name + '/pods?' + condition_actual + '&sortBy=startTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询指定项目的详细信息')
def step_get_project_detail(cluster_name, project_name):
    url = env_url + '/api/clusters/' + cluster_name + '/v1/namespaces/' + project_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询指定项目的配额信息')
def step_get_project_quota(cluster_name, project_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha2/namespaces/' + \
          project_name + '/quotas'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询指定项目的LimitRanges')
def step_get_project_limit_ranges(cluster_name, project_name):
    url = env_url + '/api/clusters/' + cluster_name + '/v1/namespaces/' + project_name + '/limitranges'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询指定项目的工作负载信息')
def step_get_project_workload(cluster_name, project_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha2/namespaces/' + \
          project_name + '/abnormalworkloads'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('创建用户项目')
def step_create_user_project(cluster_name, project_name, alias_name, description):
    url = env_url + '/api/clusters/' + cluster_name + '/v1/namespaces'
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
    url = env_url + '/api/clusters/' + cluster_name + '/v1/namespaces/' + project_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('删除用户项目')
def step_delete_user_system(cluster_name, project_name):
    url = env_url + '/api/clusters/' + cluster_name + '/v1/namespaces/' + project_name
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
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/' + \
          resource_type + '?' + condition_actual + 'sortBy=updateTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询工作负载的详情信息')
def step_get_app_workload_detail(cluster_name, project_name, resource_type, resource_name):
    url = env_url + '/apis/clusters/' + cluster_name + '/apps/v1/namespaces/' + project_name + '/' + \
          resource_type + '/' + resource_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询工作负载的Revision Records')
def step_get_app_workload_revision_records(cluster_name, project_name, label_selector):
    url = env_url + '/apis/clusters/' + cluster_name + '/apps/v1/namespaces/' + \
          project_name + '/controllerrevisions?labelSelector=' \
          + label_selector
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询的deployment的Revision Records')
def step_get_deployment_revision_records(project_name, label_selector):
    url = env_url + '/apis/apps/v1/namespaces/' + project_name + '/replicasets?labelSelector=' \
          + label_selector
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询工作负载的Monitoring')
def step_get_app_workload_monitoring(cluster_name, project_name, resource_type, resource_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/namespaces/' + \
          project_name + '/workloads/' \
          + resource_type + '/' + resource_name + '/pods?sort_metric=pod_cpu_usage&limit=5&page=1'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群资源的Event')
def step_get_resource_event(cluster_name, project_name, resource_type, resource_name, resource_uid):
    url = env_url + '/api/clusters/' + cluster_name + '/v1/namespaces/' + project_name + \
          '/events?fieldSelector=involvedObject.name%3D' \
          + resource_name + '%2CinvolvedObject.namespace%3D' + \
          project_name + '%2CinvolvedObject.kind%3D' + resource_type + '%2CinvolvedObject.uid%3D' + resource_uid
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('获取集群所有的容器组信息')
def step_get_pods_of_cluster(cluster_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/pods?sortBy=startTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('获取集群中指定项目的资源信息')
def step_get_resource_of_cluster_by_project(cluster_name, type, project_name, *name):
    name_actual = ''
    for i in name:
        name_actual += str(i) + '&'
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/namespaces/' + \
          project_name + '/' + type + '?' + name_actual + 'sortBy=createTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询CRD的详情信息')
def step_get_crd_detail(cluster_name, crd_name):
    url = env_url + '/apis/clusters/' + cluster_name + \
          '/apiextensions.k8s.io/v1/customresourcedefinitions/' + crd_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询CRD的FederatedGroupList信息')
def step_get_crd_federated_group_list(cluster_name, group, version, kind):
    if kind[-1] == 's':
        url = env_url + '/apis/clusters/' + cluster_name + '/' + group + '/' + version + '/' + kind + 'es'
    elif kind[-1] == 'x':
        url = env_url + '/apis/clusters/' + cluster_name + '/' + group + '/' + version + '/' + kind + 'es'
    elif kind[-2:] == 'ay':
        url = env_url + '/apis/clusters/' + cluster_name + '/' + group + '/' + version + '/' + kind + 's'
    elif kind[-1] == 'y' and kind[-2:] != 'ay':
        kind = kind.replace(kind[-1], 'i')
        url = env_url + '/apis/clusters/' + cluster_name + '/' + group + '/' + version + '/' + kind + 'es'
    else:
        url = env_url + '/apis/clusters/' + cluster_name + '/' + group + '/' + version + '/' + kind + 's'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询存储卷的详情信息')
def step_get_pvc_detail(cluster_name, project_name, pvc_name):
    url = env_url + '/api/clusters/' + cluster_name + '/v1/namespaces/' + project_name + \
          '/persistentvolumeclaims/' + pvc_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询存储卷的监控信息')
def step_get_metrics_of_pvc(cluster_name, project_name, pvc_name, start_time, end_time, step, times):
    url = env_url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/namespaces/' + \
          project_name + '/persistentvolumeclaims/' + pvc_name + '?cluster=default&start=' + \
          start_time + '&end=' + end_time + \
          '&step=' + step + '&times=' + times + '&metrics_filter=pvc_inodes_used%7Cpvc_inodes_total' \
                                                '%7Cpvc_inodes_utilisation%7Cpvc_bytes_available%7Cpvc_bytes_total' \
                                                '%7Cpvc_bytes_utilisation%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询存储类型的详细信息')
def step_get_storage_class_detail(cluster_name, name):
    url = env_url + '/apis/clusters/' + cluster_name + '/storage.k8s.io/v1/storageclasses/' + name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('设置存储类型为默认存储类型')
def step_set_default_storage_class(cluster_name, name, set):
    """

    :param name:
    :param set: true or false
    :return:
    """
    url = env_url + '/apis/clusters/' + cluster_name + '/storage.k8s.io/v1/storageclasses/' + name
    data = {"metadata": {"annotations": {"storageclass.kubernetes.io/is-default-class": set,
                                         "storageclass.beta.kubernetes.io/is-default-class": set}}}

    response = requests.patch(url=url, headers=get_header_for_patch(), data=json.dumps(data))
    return response


@allure.step('获取集群组件的健康情况')
def step_get_component_health(cluster_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha2/componenthealth'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群的监控的信息')
def step_get_metrics_of_cluster(cluster_name, start_time, end_time, step, times):
    url = env_url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/cluster?start=' + \
          start_time + '&end=' + end_time + \
          '&step=' + step + '&times=' + times + '&metrics_filter=cluster_cpu_usage%7Ccluster_cpu_total' \
                                                '%7Ccluster_cpu_utilisation%7Ccluster_memory_usage_wo_cache%7Ccluster_memory_total%7C' \
                                                'cluster_memory_utilisation%7Ccluster_disk_size_usage%7Ccluster_disk_size_capacity%7C' \
                                                'cluster_disk_size_utilisation%7Ccluster_pod_running_count%7Ccluster_pod_quota%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询apiserver的监控信息')
def step_get_metrics_of_apiserver(cluster_name, start_time, end_time, step, times):
    url = env_url + '/kapis/clusters/' + cluster_name + \
          '/monitoring.kubesphere.io/v1alpha3/components/apiserver?start=' + start_time + \
          '&end=' + end_time + '&step=' + step + '&times=' + times + \
          '&metrics_filter=apiserver_request_latencies%7C' \
          'apiserver_request_by_verb_latencies%7Capiserver_request_rate%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询scheduler的监控信息')
def step_get_metrics_of_scheduler(cluster_name, start_time, end_time, step, times):
    url = env_url + '/kapis/clusters/' + cluster_name + \
          '/monitoring.kubesphere.io/v1alpha3/components/scheduler?start=' + start_time + \
          '&end=' + end_time + '&step=' + step + '&times=' + times + \
          '&metrics_filter=scheduler_schedule_attempts%7Cscheduler_schedule_attempt_rate%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群的 node usage ranking信息')
def step_get_node_usage_rank(cluster_name, sort):
    url = env_url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/nodes?type=rank&' \
                                                        'metrics_filter=node_cpu_utilisation%7Cnode_cpu_usage%7Cnode_cpu_total%7Cnode_memory_utilisation%7C' \
                                                        'node_memory_usage_wo_cache%7Cnode_memory_total%7Cnode_disk_size_utilisation%7Cnode_disk_size_usage%7C' \
                                                        'node_disk_size_capacity%7Cnode_pod_utilisation%7Cnode_pod_running_count%7Cnode_pod_quota%7C' \
                                                        'node_disk_inode_utilisation%7Cnode_disk_inode_total%7Cnode_disk_inode_usage%7Cnode_load1%24&sort_type=desc&' \
                                                        'sort_metric=' + sort
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群资源使用情况')
def step_get_resource_usage_of_cluster(cluster_name, start_time, end_time, step, times):
    url = env_url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/cluster?start=' + \
          start_time + '&end=' + end_time + \
          '&step=' + step + '&times=' + times + \
          '&metrics_filter=cluster_cpu_usage%7Ccluster_memory_usage_wo_cache%7Ccluster_disk_size_usage%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群应用资源用量')
def step_get_app_usage_of_cluster(cluster_name, start_time, end_time, step, times):
    url = env_url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/cluster?start=' + \
          start_time + '&end=' + end_time + \
          '&step=' + step + '&times=' + times + \
          '&metrics_filter=cluster_deployment_count%7Ccluster_statefulset_count%7Ccluster_daemonset_count%7C' \
          'cluster_job_count%7Ccluster_cronjob_count%7Ccluster_pvc_count%7Ccluster_service_count%7C' \
          'cluster_ingresses_extensions_count%7Ccluster_pod_running_count%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群项目变化趋势')
def step_get_project_trend_of_cluster(cluster_name, start_time, end_time, step, times):
    url = env_url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/cluster' \
                                                        '?start=' + start_time + '&end=' + end_time + '&step=' + step + '&times=' + times + \
          '&metrics_filter=cluster_namespace_count%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群的版本信息')
def step_get_cluster_version(cluster_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/version'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群的clusterroles')
def step_get_cluster_roles(cluster_name, *condition):
    condition_actual = ''
    for i in condition:
        condition_actual += str(i) + '&'
    url = env_url + '/kapis/clusters/' + cluster_name + '/iam.kubesphere.io/v1alpha2/clusterroles?' + condition_actual + 'sortBy=createTime&annotation=kubesphere.io%2Fcreator'
    print(url)

    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群的namespace')
def step_get_cluster_namespace(cluster_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/namespaces?' \
                                                        'labelSelector=%21kubesphere.io%2Fkubefed-host-namespace%2C%21kubesphere.io%2Fdevopsproject'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群的组件信息')
def step_get_cluster_components(cluster_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha2/components'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查询集群的监控metrics')
def step_get_cluster_monitoring_metrics(cluster_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/cluster?' \
                                                        'metrics_filter=cluster_cpu_usage%7Ccluster_cpu_total%7Ccluster_memory_usage_wo_cache%7C' \
                                                        'cluster_memory_total%7Ccluster_disk_size_usage%7Ccluster_disk_size_capacity%7C' \
                                                        'cluster_pod_running_count%7Ccluster_pod_quota%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看集群apiserver的监控metrics信息')
def step_get_cluster_apiserver_monitoring_metrics(cluster_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/components/apiserver?' \
                                                        'metrics_filter=apiserver_request_latencies%7Capiserver_request_rate%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看集群节点的监控metrics')
def step_get_cluster_node_monitoring_metrics(cluster_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/nodes?type=rank&' \
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
    url = env_url + '/kapis/clusters/' + cluster_name + \
          '/monitoring.kubesphere.io/v1alpha3/components/scheduler?metrics_filter=scheduler_schedule_attempts%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在监控告警/查看指定集群的告警信息')
def step_get_alert_message(cluster_name, type, condition):
    url = env_url + '/kapis/clusters/' + cluster_name + '/alerting.kubesphere.io/v2alpha1/' + type + 'alerts?' + \
          condition + '&sortBy=createTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在监控告警/告警策略中创建告警策略(节点cpu利用率大于0)')
def step_create_alert_policy(cluster_name, alert_name, node_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/alerting.kubesphere.io/v2alpha1/rules'
    data = {"name": alert_name, "query": "node:node_cpu_utilisation:avg1m{node=\"" + node_name + "\"} > 0",
            "duration": "1m", "labels": {"severity": "warning"},
            "annotations": {"summary": "Node " + node_name + " CPU usage > 0%",
                            "message": "", "kind": "Node", "resources": "[\"" + node_name + "\"]",
                            "rules": "[{\"_metricType\":\"node:node_cpu_utilisation:avg1m{$1}\","
                                     "\"condition_type\":\">\",\"thresholds\":\"0\",\"unit\":\"%\"}]"}}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('在监控告警/查看用户自定义告警')
def step_get_alert_custom_policy(cluster_name, alert_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/alerting.kubesphere.io/v2alpha1/rules?name=' \
          + alert_name + '&sortBy=createTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('在监控告警/删除用户自定义告警')
def step_delete_alert_custom_policy(cluster_name, alert_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/alerting.kubesphere.io/v2alpha1/rules/' + alert_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('在监控告警/修改用户自定义告警策略的持续时间为5min')
def step_edit_alert_custom_policy(cluster_name, alert_name, id, node_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/alerting.kubesphere.io/v2alpha1/rules/' + alert_name
    data = {"cluster": "default",
            "name": alert_name, "type": "",
            "id": id,
            "query": "node:node_cpu_utilisation:avg1m{node=\"" + node_name + "\"} > 0",
            "duration": "5m", "labels": {"alerttype": "metric", "rule_id": id, "severity": "warning"},
            "state": "inactive", "health": "unknown"}
    response = requests.put(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('在监控告警/查看用户自定义告警详情')
def step_get_alert_custom_policy_detail(cluster_name, alert_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/alerting.kubesphere.io/v2alpha1/rules/' + alert_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看告警策略')
def step_get_alert_policies(cluster_name, type, condition):
    """
    :type cluster_name:
    :param type: 'builtin/' 表示内置策略，传入''表示用户自定义策略。
    :param condition: 查询条件
    :return:
    """

    url = env_url + '/kapis/clusters/' + cluster_name + '/alerting.kubesphere.io/v2alpha1/' + type + 'rules?' + condition + '&sortBy=createTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('集群设置/基本信息，查看基本信息')
def step_get_information(cluster_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/monitoring.kubesphere.io/v1alpha3/cluster?' \
                                                        'cluster=' + cluster_name + '&metrics_filter=cluster_cpu_total%7Ccluster_memory_total%7Ccluster_disk_size_capacity%7Ccluster_node_total%24'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('集群设置/基本信息，编辑信息')
def step_edit_information(cluster_name, group, description, provider):
    url = env_url + '/apis/cluster.kubesphere.io/v1alpha1/clusters/' + cluster_name
    data = {"metadata": {"name": cluster_name,
                         "labels": {"cluster-role.kubesphere.io/host": "",
                                    "kubesphere.io/managed": "true",
                                    "cluster.kubesphere.io/group": group
                                    }, "annotations": {
            "kubesphere.io/description": description},
                         "finalizers": ["finalizer.cluster.kubesphere.io"]},
            "spec": {"joinFederation": True, "enable": True, "provider": provider,
                     "connection": {"type": "direct", "kubernetesAPIEndpoint": "https://10.233.0.1:443"}}}
    response = requests.patch(url=url, headers=get_header_for_patch(), data=json.dumps(data))
    return response


@allure.step('集群设置/基本信息，查看集群的基本信息')
def step_get_base_information(cluster_name):
    url = env_url + '/kapis/resources.kubesphere.io/v1alpha3/clusters/' + cluster_name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('集群设置/集群可见性，查看集群可见性')
def step_get_cluster_visibility(cluster_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/workspaces?labelSelector=kubefed.io%2Fmanaged%3Dtrue'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('集群设置/集群可见性，取消企业空间在指定集群的授权')
def step_unauthorized_cluster_visibility(cluster_name, ws_name):
    url = env_url + '/apis/cluster.kubesphere.io/v1alpha1/clusters/' + cluster_name
    url_1 = env_url + '/kapis/tenant.kubesphere.io/v1alpha3/workspacetemplates/' + ws_name
    data = {"metadata": {"labels": {"cluster.kubesphere.io/visibility": "private"}}}
    data_1 = [{"op": "remove", "path": "/spec/placement/clusters/0", "value": {"name": cluster_name}}]
    requests.patch(url=url, headers=get_header_for_patch(), data=json.dumps(data))
    requests.patch(url=url_1, headers=get_header_for_patch(), data=json.dumps(data_1))


@allure.step('集群设置/集群可见性，添加企业空间在指定集群的授权')
def step_authorized_cluster_visibility(cluster_name, ws_name):
    url = env_url + '/apis/cluster.kubesphere.io/v1alpha1/clusters/' + cluster_name
    url_1 = env_url + '/kapis/tenant.kubesphere.io/v1alpha3/workspacetemplates/' + ws_name
    data = {"metadata": {"labels": {"cluster.kubesphere.io/visibility": "private"}}}
    data_1 = [{"op": "add", "path": "/spec/placement", "value": {"clusters": [{"name": cluster_name}]}}]
    requests.patch(url=url, headers=get_header_for_patch(), data=json.dumps(data))
    requests.patch(url=url_1, headers=get_header_for_patch(), data=json.dumps(data_1))


@allure.step('集群设置/集群成员,查看指定集群的默认成员')
def step_get_cluster_member(cluster_name, condition):
    if len(condition) > 0:
        new_condition = condition + '&'
    else:
        new_condition = condition
    url = env_url + '/kapis/clusters/' + cluster_name + '/iam.kubesphere.io/v1alpha2/clustermembers?' + new_condition + 'sortBy=createTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('邀请用户到集群成员')
def step_invite_cluster_member(cluster_name, user_name, role):
    url = env_url + '/kapis/clusters/' + cluster_name + '/iam.kubesphere.io/v1alpha2/clustermembers'
    data = [{"username": user_name, "roleRef": role}]
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('将用户从集群成员中移出')
def step_remove_cluster_member(cluster_name, user_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/iam.kubesphere.io/v1alpha2/clustermembers/' + user_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('查看指定集群的集群角色')
def step_get_cluster_role(cluster_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/iam.kubesphere.io/v1alpha2/clusterroles?sortBy=createTime&annotation=kubesphere.io%2Fcreator'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('开启指定集群网关')
def step_open_cluster_gateway(cluster_name, type):
    url = env_url + '/apis/clusters/' + cluster_name + '/gateway.kubesphere.io/v1alpha1/namespaces/kubesphere-controls-system/gateways/kubesphere-router-kubesphere-system'
    if type == 'NodePort':
        data = {"apiVersion": "gateway.kubesphere.io/v1alpha1", "kind": "Gateway",
                "metadata": {"namespace": "kubesphere-controls-system", "name": "kubesphere-router-kubesphere-system",
                             "creator": "admin",
                             "annotations": {"kubesphere.io/annotations": "", "kubesphere.io/creator": "admin"}},
                "spec": {
                    "controller": {"replicas": 1, "annotations": {}, "config": {},
                                   "scope": {"enabled": False, "namespace": ""}},
                    "deployment": {"annotations": {"servicemesh.kubesphere.io/enabled": "false"}, "replicas": 1},
                    "service": {"annotations": {},
                                "type": "NodePort"}}
                }
    elif type == 'LoadBalancer':
        data = {"apiVersion": "gateway.kubesphere.io/v1alpha1", "kind": "Gateway",
                "metadata": {"namespace": "kubesphere-controls-system", "name": "kubesphere-router-kubesphere-system",
                             "creator": "admin",
                             "annotations": {"kubesphere.io/annotations": "QingCloud Kubernetes Engine",
                                             "kubesphere.io/creator": "admin"}}, "spec": {
                "controller": {"replicas": 1, "annotations": {}, "config": {},
                               "scope": {"enabled": False, "namespace": ""}},
                "deployment": {"annotations": {"servicemesh.kubesphere.io/enabled": "false"}, "replicas": 1},
                "service": {
                    "annotations": {"service.beta.kubernetes.io/qingcloud-load-balancer-eip-ids": "",
                                    "service.beta.kubernetes.io/qingcloud-load-balancer-type": "0"},
                    "type": "LoadBalancer"}}}

    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('查询集群网关')
def step_get_cluster_gateway(cluster_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/gateway.kubesphere.io/v1alpha1/namespaces/kubesphere-system/gateways'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('关闭集群网关')
def step_delete_cluster_gateway(cluster_name):
    url = env_url + '/apis/clusters/' + cluster_name + '/gateway.kubesphere.io/v1alpha1/namespaces/kubesphere-controls-system/gateways/kubesphere-router-kubesphere-system'
    data = {}
    response = requests.delete(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('编辑集群网关')
def step_edit_cluster_gateway(cluster_name, uid, resource_version, config, status):
    """
    :param uid:
    :param resource_version:
    :param config: ex {"4": "5"}
    :param status: 链路追踪状态 true、false
    :return:
    """
    url = env_url + '/apis/clusters/' + cluster_name + '/gateway.kubesphere.io/v1alpha1/namespaces/kubesphere-controls-system/gateways/kubesphere-router-kubesphere-system'
    data = {"metadata": {"name": "kubesphere-router-kubesphere-system", "namespace": "kubesphere-controls-system",
                         "uid": uid, "resourceVersion": resource_version, "generation": 2,
                         "annotations": {"kubesphere.io/annotations": "", "kubesphere.io/creator": "admin"},
                         "finalizers": ["uninstall-helm-release"], "managedFields": [
            {"manager": "controller-manager", "operation": "Update", "apiVersion": "gateway.kubesphere.io/v1alpha1",
             "fieldsType": "FieldsV1"},
        ]},
            "spec": {"controller": {"replicas": 1, "config": config, "scope": {}}, "service": {"type": "NodePort"},
                     "deployment": {"replicas": 1, "annotations": {"servicemesh.kubesphere.io/enabled": status}}},
            "apiVersion": "gateway.kubesphere.io/v1alpha1", "kind": "Gateway"}
    response = requests.put(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('在集群设置/网关设置中查询项目网关')
def step_get_project_gateway(cluster_name, name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/gateway.kubesphere.io/v1alpha1/gateways?name=' + name + '&sortBy=createTime'
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('查看日志接收器')
def step_get_log_receiver(cluster_name, type):
    """
    :param cluster_name:
    :param type: logging、events、auditing
    :return:
    """
    url = env_url + '/apis/clusters/' + cluster_name + '/logging.kubesphere.io/v1alpha2/namespaces/kubesphere-logging' \
                                                       '-system/outputs?labelSelector=logging.kubesphere.io' \
                                                       '%2Fcomponent%3D' + type
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('添加日志收集器')
def step_add_log_receiver(cluster_name, type, log_type, name):
    """
    :param name:
    :param cluster_name:
    :param type: fluentd、kafka、es
    :param log_type: logging、events、auditing
    :return:
    """
    if type == 'fluentd':
        spec = {"match": "kube.*", "forward": {"port": 24224, "host": "192.168.0.10"}}
    elif type == 'kafka':
        spec = {"match": "kube.*", "kafka": {"topics": "test-kafka", "brokers": "192.168.0.10:9092"}}
    elif type == 'es':
        spec = {"match": "kube.*", "es": {"logstashFormat": True, "timeKey": "@timestamp",
                                          "logstashPrefix": "ks-logstash-log", "port": 9200, "host": "192.168.0.10"}}

    url = env_url + '/apis/clusters/' + cluster_name + '/logging.kubesphere.io/v1alpha2/namespaces/kubesphere-logging-system/outputs'
    data = {"apiVersion": "logging.kubesphere.io/v1alpha2", "kind": "Output",
            "metadata": {"name": name, "namespace": "kubesphere-logging-system",
                         "labels": {"logging.kubesphere.io/enabled": "true",
                                    "logging.kubesphere.io/component": log_type},
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": spec}
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('查看日志接收器')
def step_get_log_receiver(cluster_name, type):
    """
    :param cluster_name:
    :param type: logging、events、auditing
    :return:
    """

    url = env_url + '/apis/clusters/' + cluster_name + '/logging.kubesphere.io/v1alpha2/namespaces/kubesphere-logging-system/outputs?labelSelector=logging.kubesphere.io%2Fcomponent%3D' + type
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('删除日志接收器')
def step_delete_log_receiver(cluster_name, name):
    """
    :param cluster_name:
    :param name: 日志接收器名称
    :return:
    """
    url = env_url + '/apis/clusters/' + cluster_name + '/logging.kubesphere.io/v1alpha2/namespaces/kubesphere-logging-system/outputs/' + name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('查看日志接收器详情')
def step_get_log_receiver_detail(cluster_name, name):
    """
    :param cluster_name:
    :param name: 日志接收器的名称
    :return:
    """
    url = env_url + '/apis/clusters/' + cluster_name + '/logging.kubesphere.io/v1alpha2/namespaces/kubesphere-logging-system/outputs/' + name
    response = requests.get(url=url, headers=get_header())
    return response


@allure.step('更改日志接收器的状态')
def step_modify_log_receiver_status(cluster_name, name, status):
    """
    :param cluster_name: 集群名称
    :param name: 日志接收器名称
    :param status: 日志接收器状态
    :return:
    """
    url = env_url + '/apis/clusters/' + cluster_name + '/logging.kubesphere.io/v1alpha2/namespaces/kubesphere-logging-system/outputs/' + name
    data = {"metadata": {"labels": {"logging.kubesphere.io/enabled": status}}}
    response = requests.patch(url=url, headers=get_header_for_patch(), data=json.dumps(data))
    return response


@allure.step('编辑日志接收器的地址')
def step_modify_log_receiver_address(type, cluster_name, name, host, port):
    """
    :param cluster_name:
    :param host:
    :param port:
    :param name: 日志接收器名称
    :return:
    """
    url = env_url + '/apis/clusters/' + cluster_name + '/logging.kubesphere.io/v1alpha2/namespaces/kubesphere-logging-system/outputs/' + name
    if type == 'es':
        data = {"spec": {
            "es": {"host": host, "logstashFormat": True, "logstashPrefix": "ks-logstash-log", "port": port,
                   "timeKey": "@timestamp"}}}
    elif type == 'kafka':
        data = {"spec": {"kafka": {"brokers": str(host) + ':' + str(port), "topics": "test-kafka"}}}
    elif type == 'fluentd':
        data = {"spec": {"forward": {"host": host, "port": port}}}
    response = requests.patch(url=url, headers=get_header_for_patch(), data=json.dumps(data))
    return response
