import requests
import json
import allure
import sys

sys.path.append('../')  # 将项目路径加到搜索路径中，使得自定义模块可以引用

from common.getHeader import *
from common.getConfig import get_apiserver

env_url = get_apiserver()


@allure.step('通过名称查询存储卷')
def search_volume_by_name(cluster_name, volume_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/persistentvolumeclaims?name='+volume_name+'&sortBy=createTime&limit=10'
    response = requests.get(url=url, headers=get_header())
    return response


def delete_volume(cluster_name, project_name, volume_name):
    url = env_url + '/api/clusters/'+cluster_name+'/v1/namespaces/'+project_name+'/persistentvolumeclaims/' + volume_name
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('创建存储类')
def step_create_sc(cluster_name, sc_name, expansion):
    url = env_url + '/apis/clusters/' + cluster_name + '/storage.k8s.io/v1/storageclasses'
    data = {"apiVersion": "storage.k8s.io/v1",
            "kind": "StorageClass",
            "metadata": {
                "name": sc_name,
                "annotations": {
                    "kubesphere.io/provisioner": "disk.csi.qingcloud.com",
                    "storageclass.kubesphere.io/supported-access-modes": "[\"ReadWriteOnce\"]",
                    "kubesphere.io/creator": "admin"}
            },
            "parameters": {
                "fstype": "ext4"},
            "reclaimPolicy": "Delete",
            "allowVolumeExpansion": expansion,
            "volumeBindingMode": "WaitForFirstConsumer",
            "provisioner": "disk.csi.qingcloud.com"}
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('创建授权规则')
def create_sc_accessor(cluster_name, sc_name):
    url = env_url + '/apis/clusters/'+cluster_name+'/storage.kubesphere.io/v1alpha1/accessors'
    data = {"apiVersion": "storage.kubesphere.io/v1alpha1",
            "kind": "Accessor",
            "metadata": {"name": sc_name + "-accessor",
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"storageClassName": sc_name + "-disabled",
                     "namespaceSelector": {"fieldSelector": [{"fieldExpressions": [{"field": "Name",
                                                                                    "operator": "In", "values": []}
                                                                                   ]}]},
                     "workspaceSelector": {"fieldSelector": [{"fieldExpressions": [{"field": "Name",
                                                                                    "operator": "In", "values": []}
                                                                                   ]}]}}
            }
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('开启/关闭授权规则')
def open_sc_accessor(cluster_name, sc_name, enable):
    url = env_url + '/apis/clusters/' + cluster_name + '/storage.kubesphere.io/v1alpha1/accessors/' + sc_name + '-accessor'
    data = {"spec": {"storageClassName": sc_name + enable}}
    response = requests.patch(url=url, headers=get_header_for_patch(), data=json.dumps(data))
    return response


@allure.step('删除授权规则')
def delete_sc_accessor(cluster_name, sc_name):
    url = env_url + '/apis/clusters/' + cluster_name + '/storage.kubesphere.io/v1alpha1/accessors/' + sc_name + '-accessor'
    response = requests.delete(url=url, headers=get_header())
    return response


@allure.step('删除存储类')
def delete_sc(cluster_name, sc_name):
    url = env_url + '/apis/clusters/' + cluster_name + '/storage.k8s.io/v1/storageclasses/' + sc_name
    response = requests.delete(url, headers=get_header())
    return response


@allure.step('按名称查询存储类')
def search_sc_by_name(cluster_name, sc_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/storageclasses?name=' + sc_name + '&sortBy=createTime&limit=10'
    response = requests.get(url, headers=get_header())
    return response

@allure.step('查询存储类信息')
def get_sc_info(cluster_name, sc_name):
    url = env_url + '/apis/clusters/' + cluster_name + '/storage.k8s.io/v1/storageclasses/' + sc_name
    response = requests.get(url, headers=get_header())
    return response


@allure.step('查询存储类已有存储卷')
def search_volume_by_sc(cluster_name, sc_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/persistentvolumeclaims?storageClassName=' + sc_name + '&sortBy=createTime&limit=10'
    response = requests.get(url, headers=get_header())
    return response


@allure.step('在存储类详情查询存储卷')
def search_volume(cluster_name, sc_name, volume_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/persistentvolumeclaims?storageClassName=' + sc_name + \
          '&name=' + volume_name + '&sortBy=createTime&limit=10'
    response = requests.get(url, headers=get_header())
    return response


@allure.step('查询存储类授权规则')
def get_sc_accessor(cluster_name, sc_name):
    url = env_url + '/apis/clusters/' + cluster_name + '/storage.kubesphere.io/v1alpha1/accessors/' + sc_name + '-accessor'
    response = requests.get(url, headers=get_header())
    return response


@allure.step('设置存储类授权规则')
def set_sc_accessor(cluster_name, sc_name, ns_accessor, ws_accessor, scn):
    re = get_sc_accessor(sc_name)
    uid = re.json()['metadata']['uid']
    resource_version = re.json()['metadata']['resourceVersion']
    gen = re.json()['metadata']['generation']
    createtime = re.json()['metadata']['creationTimestamp']
    time = re.json()['metadata']['managedFields'][0]['time']
    url = env_url + '/apis/clusters/' + cluster_name + '/storage.kubesphere.io/v1alpha1/accessors/' + sc_name + '-accessor'
    data = {"apiVersion": "storage.kubesphere.io/v1alpha1",
            "kind": "Accessor",
            "metadata": {
                "annotations": {"kubesphere.io/creator": "admin"},
                "creationTimestamp": createtime,
                "generation": gen,
                "managedFields": [
                    {"apiVersion": "storage.kubesphere.io/v1alpha1",
                     "fieldsType": "FieldsV1",
                     "fieldsV1": {"f:metadata": {"f:annotations": {".": {}, "f:kubesphere.io/creator": {}}},
                                  "f:spec": {".": {}, "f:storageClassName": {}}},
                     "manager": "python-requests",
                     "operation": "Update",
                     "time": time}],
                "name": sc_name + "-accessor",
                "resourceVersion": resource_version,
                "uid": uid
            },
            "spec": {"storageClassName": scn,
                     "namespaceSelector": {"fieldSelector": [{"fieldExpressions": ns_accessor}]},
                     "workspaceSelector": {"fieldSelector": [{"fieldExpressions": ws_accessor}]}
                     }
            }
    response = requests.put(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('设置项目存储类授权规则')
def set_sc_ns_accessor(cluster_name, sc_name, ns_accessor, scn):
    r = get_sc_accessor(sc_name)
    uid = r.json()['metadata']['uid']
    version = r.json()['metadata']['resourceVersion']
    gen = r.json()['metadata']['generation']
    createtime = r.json()['metadata']['creationTimestamp']
    time = r.json()['metadata']['managedFields'][0]['time']
    url = env_url + '/apis/clusters/' + cluster_name + '/storage.kubesphere.io/v1alpha1/accessors/' + sc_name + '-accessor'
    data = {"cluster": cluster_name,
            "name": sc_name + "-accessor",
            "apiVersion": "storage.kubesphere.io/v1alpha1",
            "kind": "Accessor",
            "metadata": {
                "annotations": {"kubesphere.io/creator": "admin"},
                "creationTimestamp": createtime,
                "generation": gen,
                "managedFields": [
                    {"apiVersion": "storage.kubesphere.io/v1alpha1",
                     "fieldsType": "FieldsV1",
                     "fieldsV1": {"f:metadata": {"f:annotations": {".": {}, "f:kubesphere.io/creator": {}}},
                                  "f:spec": {".": {}, "f:storageClassName": {}}},
                     "manager": "python-requests",
                     "operation": "Update",
                     "time": time}],
                "name": sc_name + "-accessor",
                "resourceVersion": version,
                "uid": uid
            },
            "spec": {"storageClassName": scn,
                     "namespaceSelector": {"fieldSelector": [{"fieldExpressions": ns_accessor}]},
                     }
            }
    response = requests.put(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('设置存储类授权规则')
def set_sc_ws_accessor(cluster_name, sc_name, ws_accessor, scn):
    res = get_sc_accessor(sc_name)
    uid = res.json()['metadata']['uid']
    resource = res.json()['metadata']['resourceVersion']
    gen = res.json()['metadata']['generation']
    createtime = res.json()['metadata']['creationTimestamp']
    time = res.json()['metadata']['managedFields'][0]['time']
    url = env_url + '/apis/clusters/' + cluster_name + '/storage.kubesphere.io/v1alpha1/accessors/' + sc_name + '-accessor'
    data = {"apiVersion": "storage.kubesphere.io/v1alpha1",
            "kind": "Accessor",
            "metadata": {
                "annotations": {"kubesphere.io/creator": "admin"},
                "creationTimestamp": createtime,
                "generation": gen,
                "managedFields": [
                    {"apiVersion": "storage.kubesphere.io/v1alpha1",
                     "fieldsType": "FieldsV1",
                     "fieldsV1": {"f:metadata": {"f:annotations": {".": {}, "f:kubesphere.io/creator": {}}},
                                  "f:spec": {".": {}, "f:storageClassName": {}}},
                     "manager": "python-requests",
                     "operation": "Update",
                     "time": time}],
                "name": sc_name + "-accessor",
                "resourceVersion": resource,
                "uid": uid
            },
            "spec": {"storageClassName": scn,
                     "workspaceSelector": {"fieldSelector": [{"fieldExpressions": ws_accessor}]}
                     }
            }
    response = requests.put(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('设置卷操作')
def set_volume_operations(cluster_name, sc_name, expansion, allow_clone, allow_snapshot):
    url = env_url + '/apis/clusters/' + cluster_name + '/storage.k8s.io/v1/storageclasses/' + sc_name
    data = {"metadata": {"annotations": {"storageclass.kubesphere.io/allow-clone": allow_clone,
                                         "storageclass.kubesphere.io/allow-snapshot": allow_snapshot}},
            "allowVolumeExpansion": expansion}
    response = requests.patch(url, headers=get_header_for_patch(), data=json.dumps(data))
    return response


@allure.step('设置默认存储类')
def set_default_sc(cluster_name, sc_name, expansion):
    url = env_url + '/apis/clusters/' + cluster_name + '/storage.k8s.io/v1/storageclasses/' + sc_name
    data = {"metadata": {"annotations": {"storageclass.kubernetes.io/is-default-class": expansion,
                                         "storageclass.beta.kubernetes.io/is-default-class": expansion}
                         }
            }
    response = requests.patch(url, headers=get_header_for_patch(), data=json.dumps(data))
    return response


@allure.step('创建存储卷')
def step_create_volume(cluster_name, project_name, sc_name, volume_name):
    url = env_url + '/api/clusters/' + cluster_name + '/v1/namespaces/' + project_name + '/persistentvolumeclaims'
    data = {"apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {"namespace": project_name,
                         "name": volume_name,
                         "labels": {},
                         "annotations": {"kubesphere.io/creator": "admin"}
                         },
            "spec": {"resources": {"requests": {"storage": "10Gi"}},
                     "storageClassName": sc_name,
                     "accessModes": ["ReadWriteOnce"]
                     }
            }
    response = requests.post(url=url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('创建卷快照类')
def create_vsc(cluster_name, vsc_name, driver, policy):
    url = env_url + '/apis/clusters/' + cluster_name + '/snapshot.storage.k8s.io/v1beta1/volumesnapshotclasses'
    data = {"apiVersion": "snapshot.storage.k8s.io/v1beta1",
            "kind": "VolumeSnapshotClass",
            "deletionPolicy": policy,
            "driver": driver,
            "metadata": {"name": vsc_name,
                         "annotations": {"kubesphere.io/creator": "admin"}
                         }
            }
    response = requests.post(url, data=json.dumps(data), headers=get_header())
    return response


@allure.step('编辑卷快照类')
def set_vsc(cluster_name, vsc_name, driver, policy, creationtime, time, generation, version, uid, alias_name, des):
    url = env_url + '/apis/clusters/' + cluster_name + '/snapshot.storage.k8s.io/v1beta1/volumesnapshotclasses/' + vsc_name
    data = {"apiVersion": "snapshot.storage.k8s.io/v1beta1",
            "deletionPolicy": policy,
            "driver": driver,
            "kind": "VolumeSnapshotClass",
            "metadata": {"annotations": {"kubesphere.io/alias-name": alias_name,
                                         "kubesphere.io/creator": "admin",
                                         "kubesphere.io/description": des},
                         "creationTimestamp": creationtime,
                         "generation": generation,
                         "managedFields": [{"apiVersion": "snapshot.storage.k8s.io/v1beta1",
                                            "fieldsType": "FieldsV1",
                                            "fieldsV1": {"f:deletionPolicy": {}, "f:driver": {},
                                                         "f:metadata": {"f:annotations": {".": {},
                                                                                          "f:kubesphere.io/alias-name": {},
                                                                                          "f:kubesphere.io/creator": {}}}},
                                            "manager": "Mozilla",
                                            "operation": "Update",
                                            "time": time}],
                         "name": vsc_name,
                         "resourceVersion": version,
                         "uid": uid}}
    response = requests.patch(url=url, headers=get_header_for_patch(), data=json.dumps(data))
    return response


@allure.step('删除卷快照类')
def delete_vsc(cluster_name, vsc_name):
    url = env_url + '/apis/clusters/' + cluster_name + '/snapshot.storage.k8s.io/v1beta1/volumesnapshotclasses/' + vsc_name
    response = requests.delete(url, headers=get_header())
    return response


@allure.step('按名称查询卷快照类')
def search_vsc_by_name(cluster_name, vsc_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/volumesnapshotclasses?name=' + vsc_name + '&sortBy=createTime&limit=10'
    response = requests.get(url, headers=get_header())
    return response


@allure.step('获取卷快照类已有快照')
def get_vs_for_vsc(cluster_name, vsc_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/volumesnapshots?volumeSnapshotClassName=' + vsc_name + '&sortBy=createTime&limit=10'
    response = requests.get(url, headers=get_header())
    return response


@allure.step('查询卷快照类已有快照')
def search_vs_for_vsc(cluster_name, vsc_name, vs_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/volumesnapshots?volumeSnapshotClassName=' + vsc_name + '&name='+vs_name+'&sortBy=createTime&limit=10'
    response = requests.get(url, headers=get_header())
    return response


@allure.step('创建快照')
def create_volume_snapshots(cluster_name, project, vs_name, vsc_name, volume_name):
    url = env_url + '/apis/clusters/' + cluster_name + '/snapshot.storage.k8s.io/v1beta1/namespaces/' + project + '/volumesnapshots'
    data = {"apiVersion": "snapshot.storage.k8s.io/v1beta1",
            "kind": "VolumeSnapshot",
            "metadata": {"name": vs_name,
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"volumeSnapshotClassName": vsc_name,
                     "source": {"kind": "VolumeSnapshot",
                                "persistentVolumeClaimName": volume_name}
                     }
            }
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


@allure.step('按名称查询卷快照')
def search_vs_by_name(cluster_name, vs_name):
    url = env_url + '/kapis/clusters/' + cluster_name + '/resources.kubesphere.io/v1alpha3/volumesnapshots?name=' + vs_name + '&sortBy=createTime&limit=10'
    response = requests.get(url, headers=get_header())
    return response


@allure.step('删除卷快照')
def delete_vs(cluster_name, project_name, vs_name):
    url = env_url + '/apis/clusters/' + cluster_name + '/snapshot.storage.k8s.io/v1beta1/namespaces/'+project_name+'/volumesnapshots/' + vs_name
    response = requests.delete(url, headers=get_header())
    return response


@allure.step('通过卷快照创建卷')
def create_volumne_by_vs(cluster_name, project_name, volume_name, sc_name):
    url = env_url + '/api/clusters/' + cluster_name + '/v1/namespaces/'+project_name+'/persistentvolumeclaims'
    data = {"apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {"namespace": project_name,
                         "name": volume_name,
                         "labels": {},
                         "annotations": {"kubesphere.io/creator": "admin"}},
            "spec": {"resources": {"requests": {"storage": "10Gi"}},
                     "storageClassName": sc_name,
                     "dataSource": {"name": volume_name,
                                    "kind": "VolumeSnapshot",
                                    "apiGroup": "snapshot.storage.k8s.io"},
                     "accessModes": ["ReadWriteOnce"]}
            }
    response = requests.post(url, headers=get_header(), data=json.dumps(data))
    return response


# 存储卷 [{name: "volume-pkb0hm", persistentVolumeClaim: {claimName: "vv"}}]
#  volume mounts [{name: "volume-pkb0hm", readOnly: false, mountPath: "/data"}]
@allure.step('挂载存储卷')
def mount_volume(cluster_name, ns_name, deploy_name, container_name, volume, volumeMounts):
    url1 = env_url + '/apis/' + cluster_name + '/apps/v1/namespaces/pro/deployments/' + deploy_name
    re = requests.get(url1, headers=get_header())
    version = re.json()['metadata']['resourceVersion']
    url2 = env_url + '/apis/apps/v1/namespaces/pro/deployments/' + deploy_name
    data = {"kind": "Deployment",
            "apiVersion": "apps/v1",
            "metadata": {"name": deploy_name,
                         "namespace": ns_name,
                         "labels": {"app": deploy_name},
                         "annotations": {"deployment.kubernetes.io/revision": "2",
                                         "kubesphere.io/creator": "admin"},
                         "resourceVersion": version},
            "spec": {"replicas": 1,
                     "selector": {"matchLabels": {"app": deploy_name}},
                     "template": {"metadata": {"creationTimestamp": None,
                                               "labels": {"app": deploy_name},
                                               "annotations": {"logging.kubesphere.io/logsidecar-config": "{}"}},
                                  "spec": {"volumes": volume,
                                           "containers": [{"name": container_name,
                                                           "image": "nginx",
                                                           "ports": [{"name": "tcp-80",
                                                                      "containerPort": 80,
                                                                      "protocol": "TCP"}],
                                                           "resources": {},
                                                           "volumeMounts": volumeMounts,
                                                           "terminationMessagePath": "/dev/termination-log",
                                                           "terminationMessagePolicy": "File",
                                                           "imagePullPolicy": "IfNotPresent"}],
                                           "restartPolicy": "Always",
                                           "terminationGracePeriodSeconds": 30,
                                           "dnsPolicy": "ClusterFirst",
                                           "serviceAccountName": "default",
                                           "serviceAccount": "default",
                                           "securityContext": {},
                                           "schedulerName": "default-scheduler",
                                           "initContainers": []}},
                     "strategy": {"type": "RollingUpdate",
                                  "rollingUpdate": {"maxUnavailable": "25%",
                                                    "maxSurge": "25%"}},
                     "revisionHistoryLimit": 10,
                     "progressDeadlineSeconds": 600}}
    response = requests.put(url2, data=json.dumps(data), headers=get_header())
    return response
