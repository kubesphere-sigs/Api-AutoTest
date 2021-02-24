import requests
import pytest
import json
import allure
import sys
import time
sys.path.append('../')  #将项目路径加到搜索路径中，使得自定义模块可以引用

import logging
from config import config
from common.getData import DoexcleByPandas
from common.getHeader import get_header, get_header_for_patch
from common.logFormat import log_format
from common import commonFunction


@allure.step('部署指定应用')
def step_deployment_app(project_name, app_id, app_version_id, name, conf):
    """
    :param project_name: 项目名称
    :param app_id: 应用id
    :param app_version_id: 应用的版本号
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
    #验证部署应用请求成功
    assert r.json()['message'] == 'success'

@allure.step('查看应用状态')
def step_get_app_status(ws_name, project_name, app_name):
    """
    :param ws_name: 企业空间
    :param project_name: 项目名称
    :param app_name: 应用名称
    :return: 应用状态
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/clusters/default/namespaces/' + project_name + '/applications' \
                       '?conditions=status%3Dactive%7Cstopped%7Cpending%7Csuspended%2Ckeyword%3D' + app_name + '&paging=limit%3D10%2Cpage%3D1&orderBy=status_time&reverse=true'
    r = requests.get(url=url, headers=get_header())
    return r.json()['items'][0]['cluster']['status']

@allure.step('在应用列表中查看应用是否存在')
def step_get_app_count(ws_name, project_name, app_name):
    """
    :param ws_name: 企业空间
    :param project_name: 项目名称
    :param app_name: 应用名称
    :return:
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/clusters/default/namespaces/' + project_name + '/applications' \
                       '?conditions=status%3Dactive%7Cstopped%7Cpending%7Csuspended%2Ckeyword%3D' + app_name + '&paging=limit%3D10%2Cpage%3D1&orderBy=status_time&reverse=true'
    r = requests.get(url=url, headers=get_header())
    return r.json()['total_count']

@allure.step('在应用列表获取指定应用的cluster_id')
def step_get_cluster_id(ws_name, project_name, app_name):
    """
    :param ws_name: 企业空间
    :param project_name: 项目名称
    :param app_name: 应用名称
    :return: 应用的cluster_id
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/clusters/default/namespaces/' + project_name + '/applications' \
                       '?conditions=status%3Dactive%7Cstopped%7Cpending%7Csuspended%2Ckeyword%3D' + app_name + '&paging=limit%3D10%2Cpage%3D1&orderBy=status_time&reverse=true'
    r = requests.get(url=url, headers=get_header())
    return r.json()['items'][0]['cluster']['cluster_id']

@allure.step('删除应用列表指定的应用')
def step_delete_app(ws_name, project_name, cluster_id):
    """
    :param ws_name: 企业空间
    :param project_name: 项目名称
    :param app_id: 部署后的应用的id
    """
    url = config.url + '/kapis/openpitrix.io/v1/workspaces/' + ws_name + '/clusters/default/namespaces/' + project_name + '/applications/' + cluster_id
    r = requests.delete(url=url, headers=get_header())
    #验证删除请求成功
    assert r.json()['message'] == 'success'


@allure.feature('遍历部署AppStore的所有应用')
class TestAppStore(object):
    ws_name = 'test-ws2'   #在excle中读取的用例此名称，不能修改。
    project_name = 'test-project2'  #在excle中读取的用例此名称，不能修改。
    log_format()  #配置日志格式
    #从文件中读取用例信息
    parametrize = DoexcleByPandas().get_data_for_pytest(filename='../data/data.xlsx', sheet_name='appstore')

    # 所有用例执行之前执行该方法
    def setup_class(self):
        commonFunction.create_workspace(self.ws_name)  #创建一个企业空间
        commonFunction.create_project(ws_name=self.ws_name, project_name=self.project_name)  #创建一个项目

    # 所有用例执行完之后执行该方法
    def teardown_class(self):
        commonFunction.delete_project(self.ws_name, self.ws_name)  #删除创建的项目
        commonFunction.delete_workspace(self.ws_name)  # 删除创建的企业空间


    # 以下用例由于需要获取app的id和version_id，故不能从通用的文档中获取数据
    @allure.title('从应用商店部署rabbitmq')
    @allure.severity(allure.severity_level.CRITICAL)
    def test_deployment_rabbit(self):
        #获取应用rabbitmq的app_id
        rabbitmq_id = commonFunction.get_app_id('rabbitmq')
        #获取应用rabbitmq的version_id
        rb_ver_id = commonFunction.get_app_version(rabbitmq_id)
        name = 'rabbitmq-test'
        conf = "image:\n  rabbitmq:\n    repository: rabbitmq\n    tag: 3.8.1-alpine\n    pullPolicy: IfNotPresent\nimagePullSecrets: []\nnameOverride: ''\nfullnameOverride: ''\npersistence:\n  size: 5Gi\nextraPlugins: []\nextraConfigurations: |-\n  ## Number of Erlang processes that will accept connections for the TCP\n  ## and TLS listeners.\n  ##\n  # num_acceptors.tcp = 10\n  # num_acceptors.ssl = 10\nadvancedConfigurations: |-\n  [\n    {rabbitmq_auth_backend_ldap, [\n      %% Authorisation\n    ]}\n  ].\ndefaultUsername: admin\ndefaultPassword: password\nservice:\n  type: ClusterIP\nresources: {}\nnodeSelector: {}\ntolerations: []\naffinity: {}\n"
        # 部署应用rabbitmq
        step_deployment_app(project_name=self.project_name, app_id=rabbitmq_id, app_version_id=rb_ver_id, name=name, conf=conf)
        # 查看并验证应用状态为active，最长等待时间600s
        i = 0
        while i < 900:
            status = step_get_app_status(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
            if status == 'active':
                print('应用部署耗时:' + str(i) + '秒')
                break
            elif status == 'enabled':
                print('应用部署失败')
                break
            time.sleep(60)
            i = i + 60

        # 获取部署应用的cluster_id
        cluster_id = step_get_cluster_id(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        # 根据cluster_id删除对应应用
        step_delete_app(ws_name=self.ws_name, project_name=self.project_name, cluster_id=cluster_id)
        # 验证删除成功
        time.sleep(60)
        count = step_get_app_count(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        assert count == 0
        if status != 'active':
            print('porter部署耗时15min，仍未部署成功')
            assert status == 'active'
        else:
            assert status == 'active'

    @allure.title('从应用商店部署redis')    #ok
    @allure.severity(allure.severity_level.CRITICAL)
    def test_deployment_redis(self):
        url = config.url + '/kapis/openpitrix.io/v1/workspaces/undefined/clusters/default/namespaces/' + self.project_name + '/applications'
        # 获取应用rabbitmq的app_id
        redis_id = commonFunction.get_app_id('redis')
        # 获取应用rabbitmq的version_id
        re_ver_id = commonFunction.get_app_version(redis_id)
        name = 'redis-test'
        conf = "image:\n  repository: redis\n  tag: 5.0.5-alpine\n  pullPolicy: IfNotPresent\nimagePullSecrets: []\nnameOverride: ''\nfullnameOverride: ''\npersistence:\n  size: 1Gi\nconfig: |-\n  # redis.conf\n  appendonly yes\npassword: ''\nservice:\n  type: ClusterIP\n  port: 6379\nresources: {}\nnodeSelector: {}\ntolerations: []\naffinity: {}\ntests:\n  enabled: false\n"
        # 部署应用redis
        step_deployment_app(project_name=self.project_name, app_id=redis_id, app_version_id=re_ver_id,
                            name=name,
                            conf=conf)
        # 查看并验证应用状态为active，最长等待时间600s
        i = 0
        while i < 900:
            status = step_get_app_status(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
            if status == 'active':
                print('应用部署耗时:' + str(400 + i) + '秒')
                break
            elif status == 'enabled':
                print('应用部署失败')
                break
            time.sleep(60)
            i = i + 60
        assert status == 'active'
        # 获取部署应用的cluster_id
        cluster_id = step_get_cluster_id(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        # 根据cluster_id删除对应应用
        step_delete_app(ws_name=self.ws_name, project_name=self.project_name, cluster_id=cluster_id)
        # 验证删除成功
        time.sleep(60)
        count = step_get_app_count(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        assert count == 0
        if status != 'active':
            print('porter部署耗时15min，仍未部署成功')
            assert status == 'active'
        else:
            assert status == 'active'

    @allure.title('从应用商店部署tomcat')  #ok
    @allure.severity(allure.severity_level.CRITICAL)
    def test_deployment_tomcat(self):
        url = config.url + '/kapis/openpitrix.io/v1/workspaces/undefined/clusters/default/namespaces/' + self.project_name + '/applications'
        # 获取应用rabbitmq的app_id
        tomcat_id = commonFunction.get_app_id('tomcat')
        # 获取应用rabbitmq的version_id
        tom_ver_id = commonFunction.get_app_version(tomcat_id)
        name ='tomcat-test'
        conf = "replicaCount: 1\nimage:\n  webarchive:\n    repository: ananwaresystems/webarchive\n    tag: '1.0'\n  tomcat:\n    repository: tomcat\n    tag: 8.5.41-alpine\n  pullPolicy: IfNotPresent\n  pullSecrets: []\ndeploy:\n  directory: /usr/local/tomcat/webapps\nservice:\n  name: http\n  type: ClusterIP\n  externalPort: 80\n  internalPort: 8080\ningress:\n  enabled: false\n  annotations: {}\n  path: /\n  hosts:\n    - chart-example.local\n  tls: []\nenv: []\nextraVolumes: []\nextraVolumeMounts: []\nextraInitContainers: []\nreadinessProbe:\n  path: /sample\n  initialDelaySeconds: 60\n  periodSeconds: 30\n  failureThreshold: 6\n  timeoutSeconds: 5\nlivenessProbe:\n  path: /sample\n  initialDelaySeconds: 60\n  periodSeconds: 30\n  failureThreshold: 6\n  timeoutSeconds: 5\nresources: {}\nnodeSelector: {}\ntolerations: []\naffinity: {}\n"
        # 部署应用tomcat
        step_deployment_app(project_name=self.project_name, app_id=tomcat_id, app_version_id=tom_ver_id, name=name, conf=conf)
        # 查看并验证应用状态为active，最长等待时间600s
        i = 0
        while i < 900:
            status = step_get_app_status(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
            if status == 'active':
                print('应用部署耗时:' + str(i) + '秒')
                break
            elif status == 'enabled':
                print('应用部署失败')
                break
            time.sleep(60)
            i = i + 60

        # 获取部署应用的cluster_id
        cluster_id = step_get_cluster_id(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        # 根据cluster_id删除对应应用
        step_delete_app(ws_name=self.ws_name, project_name=self.project_name, cluster_id=cluster_id)
        # 验证删除成功
        time.sleep(5)
        count = step_get_app_count(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        assert count == 0
        if status != 'active':
            print('porter部署耗时15min，仍未部署成功')
            assert status == 'active'
        else:
            assert status == 'active'

    @allure.title('从应用商店部署redis-exporter')  #ok
    @allure.severity(allure.severity_level.CRITICAL)
    def test_deployment_redis_ex(self):
        url = config.url + '/kapis/openpitrix.io/v1/workspaces/undefined/clusters/default/namespaces/' + self.project_name + '/applications'
        # 获取应用rabbitmq的app_id
        redis_ex_id = commonFunction.get_app_id('redis-exporter')
        # 获取应用rabbitmq的version_id
        redis_ex_ver_id = commonFunction.get_app_version(redis_ex_id)
        name = 'redis-e-test'
        conf = "rbac:\n  create: true\n  pspEnabled: true\nserviceAccount:\n  create: true\n  name: null\nreplicaCount: 1\nimage:\n  repository: oliver006/redis_exporter\n  tag: v1.3.4\n  pullPolicy: IfNotPresent\nextraArgs: {}\nenv: {}\nservice:\n  type: ClusterIP\n  port: 9121\n  annotations: {}\n  labels: {}\nresources: {}\nnodeSelector: {}\ntolerations: []\naffinity: {}\nredisAddress: 'redis://myredis:6379'\nannotations: {}\nserviceMonitor:\n  enabled: true\nprometheusRule:\n  enabled: false\n  additionalLabels: {}\n  namespace: ''\n  rules: []\nauth:\n  enabled: false\n  secret:\n    name: ''\n    key: ''\n  redisPassword: ''\n"
        # 部署应用redis-exporter
        step_deployment_app(project_name=self.project_name, app_id=redis_ex_id, app_version_id=redis_ex_ver_id,
                            name=name,
                            conf=conf)
        # 查看并验证应用状态为active，最长等待时间900s
        i = 0
        while i < 900:
            status = step_get_app_status(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
            if status == 'active':
                print('应用部署耗时:' + str(400 + i) + '秒')
                break
            elif status == 'enabled':
                print('应用部署失败')
                break
            time.sleep(60)
            i = i + 60

        # 获取部署应用的cluster_id
        cluster_id = step_get_cluster_id(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        # 根据cluster_id删除对应应用
        step_delete_app(ws_name=self.ws_name, project_name=self.project_name, cluster_id=cluster_id)
        # 验证删除成功
        time.sleep(5)
        count = step_get_app_count(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        assert count == 0
        if status != 'active':
            print('porter部署耗时15min，仍未部署成功')
            assert status == 'active'
        else:
            assert status == 'active'

    @allure.title('从应用商店部署porter')  #xxx
    @allure.severity(allure.severity_level.CRITICAL)
    def test_deployment_porter(self):
        url = config.url + '/kapis/openpitrix.io/v1/workspaces/undefined/clusters/default/namespaces/' + self.project_name + '/applications'
        # 获取应用的app_id
        porter_id = commonFunction.get_app_id('porter')
        # 获取应用的version_id
        por_ver_id = commonFunction.get_app_version(porter_id)
        name = 'porter-test'
        conf = "manager:\n  image:\n    repository: kubespheredev/porter\n    tag: v0.3-dev\n    pullPolicy: IfNotPresent\n  resources:\n    limits:\n      cpu: 100m\n      memory: 30Mi\n    requests:\n      cpu: 100m\n      memory: 20Mi\n  terminationGracePeriodSeconds: 10\n  tolerations:\n    - key: CriticalAddonsOnly\n      operator: Exists\n    - effect: NoSchedule\n      key: node-role.kubernetes.io/master\nagent:\n  image:\n    repository: kubespheredev/porter-agent\n    tag: v0.3-dev\n    pullPolicy: IfNotPresent\n  resources:\n    limits:\n      cpu: 100m\n      memory: 30Mi\n    requests:\n      cpu: 100m\n      memory: 20Mi\nserviceAccount:\n  create: true\n"
        # 部署应用porter
        step_deployment_app(project_name=self.project_name, app_id=porter_id, app_version_id=por_ver_id,
                            name=name,
                            conf=conf)
        # 查看并验证应用状态为active，最长等待时间900s
        i = 0
        while i < 900:
            status = step_get_app_status(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
            if status == 'active':
                print('应用部署耗时:' + str(i) + '秒')
                break
            elif status == 'enabled':
                print('应用部署失败')
                break
            time.sleep(60)
            print(i)
            i = i + 60
        # 获取部署应用的cluster_id
        cluster_id = step_get_cluster_id(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        # 根据cluster_id删除对应应用
        step_delete_app(ws_name=self.ws_name, project_name=self.project_name, cluster_id=cluster_id)
        # 验证删除成功
        time.sleep(60)
        count = step_get_app_count(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        assert count == 0
        if status != 'active':
            print('porter部署耗时15min，仍未部署成功')
            assert status == 'active'
        else:
            assert status == 'active'

    @allure.title('从应用商店部署mysql')  #xxxxx
    @allure.severity(allure.severity_level.CRITICAL)
    def test_deployment_mysql(self):
        url = config.url + '/kapis/openpitrix.io/v1/workspaces/undefined/clusters/default/namespaces/' + self.project_name + '/applications'
        # 获取应用的app_id
        mysql_id = commonFunction.get_app_id('mysql')
        # 获取应用的version_id
        ms_ver_id = commonFunction.get_app_version(mysql_id)
        name = 'mysql-test'
        conf = "image: mysql\nimageTag: 5.7.30\nstrategy:\n  type: Recreate\nbusybox:\n  image: busybox\n  tag: '1.32'\ntestFramework:\n  enabled: true\n  image: bats/bats\n  tag: 1.2.1\n  imagePullPolicy: IfNotPresent\n  securityContext: {}\nimagePullPolicy: IfNotPresent\nargs: []\nextraVolumes: |\n  # - name: extras\n  #   emptyDir: {}\nextraVolumeMounts: |\n  # - name: extras\n  #   mountPath: /usr/share/extras\n  #   readOnly: true\nextraInitContainers: |\n  # - name: do-something\n  #   image: busybox\n  #   command: ['do', 'something']\nnodeSelector: {}\naffinity: {}\ntolerations: []\nlivenessProbe:\n  initialDelaySeconds: 30\n  periodSeconds: 10\n  timeoutSeconds: 5\n  successThreshold: 1\n  failureThreshold: 3\nreadinessProbe:\n  initialDelaySeconds: 5\n  periodSeconds: 10\n  timeoutSeconds: 1\n  successThreshold: 1\n  failureThreshold: 3\npersistence:\n  enabled: true\n  accessMode: ReadWriteOnce\n  size: 8Gi\n  annotations: {}\nsecurityContext:\n  enabled: false\n  runAsUser: 999\n  fsGroup: 999\nresources:\n  requests:\n    memory: 256Mi\n    cpu: 100m\nconfigurationFilesPath: /etc/mysql/conf.d/\nconfigurationFiles: {}\ninitializationFiles: {}\nmetrics:\n  enabled: false\n  image: prom/mysqld-exporter\n  imageTag: v0.10.0\n  imagePullPolicy: IfNotPresent\n  resources: {}\n  annotations: {}\n  livenessProbe:\n    initialDelaySeconds: 15\n    timeoutSeconds: 5\n  readinessProbe:\n    initialDelaySeconds: 5\n    timeoutSeconds: 1\n  flags: []\n  serviceMonitor:\n    enabled: false\n    additionalLabels: {}\nservice:\n  annotations: {}\n  type: ClusterIP\n  port: 3306\nserviceAccount:\n  create: false\nssl:\n  enabled: false\n  secret: mysql-ssl-certs\n  certificates: null\ndeploymentAnnotations: {}\npodAnnotations: {}\npodLabels: {}\ninitContainer:\n  resources:\n    requests:\n      memory: 10Mi\n      cpu: 10m\n"
        # 部署应用mysql
        step_deployment_app(project_name=self.project_name, app_id=mysql_id, app_version_id=ms_ver_id,
                            name=name,
                            conf=conf)
        # 查看并验证应用状态为active，最长等待时间900s
        i = 0
        while i < 900:
            status = step_get_app_status(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
            if status == 'active':
                print('应用部署耗时:' + str(i) + '秒')
                break
            elif status == 'enabled':
                print('应用部署失败')
                break
            time.sleep(60)
            i = i + 60

        # 获取部署应用的cluster_id
        cluster_id = step_get_cluster_id(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        # 根据cluster_id删除对应应用
        step_delete_app(ws_name=self.ws_name, project_name=self.project_name, cluster_id=cluster_id)
        # 验证删除成功
        time.sleep(60)
        count = step_get_app_count(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        assert count == 0
        if status != 'active':
            print('porter部署耗时15min，仍未部署成功')
            assert status == 'active'
        else:
            assert status == 'active'

    @allure.title('从应用商店部署mysql-exporter')  #xxxxxxx
    @allure.severity(allure.severity_level.CRITICAL)
    def test_deployment_mysql_ex(self):
        url = config.url + '/kapis/openpitrix.io/v1/workspaces/undefined/clusters/default/namespaces/' + self.project_name + '/applications'
        # 获取应用的app_id
        mysql_ex_id = commonFunction.get_app_id('mysql-exporter')
        # 获取应用的version_id
        mysql_ex_ver_id = commonFunction.get_app_version(mysql_ex_id)
        name = 'mysql-ex-test'
        conf = "replicaCount: 1\nimage:\n  repository: prom/mysqld-exporter\n  tag: v0.11.0\n  pullPolicy: IfNotPresent\nservice:\n  name: mysql-exporter\n  type: ClusterIP\n  externalPort: 9104\n  internalPort: 9104\nserviceMonitor:\n  enabled: true\n  additionalLabels: {}\n  jobLabel: ''\n  targetLabels: []\n  podTargetLabels: []\nresources: {}\nnodeSelector: {}\ntolerations: []\naffinity: {}\npodLabels: {}\nannotations:\n  prometheus.io/scrape: 'true'\n  prometheus.io/path: /metrics\n  prometheus.io/port: '9104'\ncollectors: {}\nmysql:\n  db: ''\n  host: localhost\n  param: ''\n  pass: password\n  port: 3306\n  protocol: ''\n  user: exporter\n  existingSecret: false\ncloudsqlproxy:\n  enabled: false\n  image:\n    repo: gcr.io/cloudsql-docker/gce-proxy\n    tag: '1.14'\n    pullPolicy: IfNotPresent\n  instanceConnectionName: 'project:us-central1:dbname'\n  port: '3306'\n  credentials: >-\n    { \"type\": \"service_account\", \"project_id\": \"project\", \"private_key_id\":\n    \"KEYID1\", \"private_key\": \"-----BEGIN PRIVATE KEY-----\\sdajsdnasd\\n-----END\n    PRIVATE KEY-----\\n\", \"client_email\": \"user@project.iam.gserviceaccount.com\",\n    \"client_id\": \"111111111\", \"auth_uri\":\n    \"https://accounts.google.com/o/oauth2/auth\", \"token_uri\":\n    \"https://accounts.google.com/o/oauth2/token\", \"auth_provider_x509_cert_url\":\n    \"https://www.googleapis.com/oauth2/v1/certs\", \"client_x509_cert_url\":\n    \"https://www.googleapis.com/robot/v1/metadata/x509/user%40project.iam.gserviceaccount.com\"\n    }\n"
        # 部署应用mysql-exporter
        step_deployment_app(project_name=self.project_name, app_id=mysql_ex_id, app_version_id=mysql_ex_ver_id, name=name,
                            conf=conf)
        # 查看并验证应用状态为active，最长等待时间600s
        i = 0
        while i < 900:
            status = step_get_app_status(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
            if status == 'active':
                print('应用部署耗时:' + str(i) + '秒')
                break
            elif status == 'enabled':
                print('应用部署失败')
                break
            time.sleep(60)
            i = i + 60

        # 获取部署应用的cluster_id
        cluster_id = step_get_cluster_id(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        # 根据cluster_id删除对应应用
        step_delete_app(ws_name=self.ws_name, project_name=self.project_name, cluster_id=cluster_id)
        # 验证删除成功
        time.sleep(60)
        count = step_get_app_count(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        assert count == 0
        if status != 'active':
            print('porter部署耗时15min，仍未部署成功')
            assert status == 'active'
        else:
            assert status == 'active'

    @allure.title('从应用商店部署nginx,验证部署成功后，删除部署的应用')   #xxxxx
    @allure.severity(allure.severity_level.CRITICAL)
    def test_deployment_nginx(self):
        url = config.url + '/kapis/openpitrix.io/v1/workspaces/undefined/clusters/default/namespaces/' + self.project_name + '/applications'
        # 获取应用nginx的app_id
        nginx_id = commonFunction.get_app_id('nginx')
        # 获取应用nginx的version_id
        ng_ver_id = commonFunction.get_app_version(nginx_id)
        #应用名称
        name = 'nginx-test'
        #应用镜像信息
        conf = "replicaCount: 1\nimage:\n  nginx:\n    repository: nginx\n    pullPolicy: IfNotPresent\nnameOverride: ''\nfullnameOverride: ''\nservice:\n  name: http\n  type: ClusterIP\n  port: 80\ningress:\n  enabled: false\n  annotations: {}\n  paths:\n    - /\n  hosts:\n    - nginx.local\n  tls: []\nextraVolumes: []\nextraVolumeMounts: []\nextraInitContainers: []\nreadinessProbe:\n  path: /\n  initialDelaySeconds: 5\n  periodSeconds: 3\n  failureThreshold: 6\nlivenessProbe:\n  path: /\n  initialDelaySeconds: 5\n  periodSeconds: 3\nresources: {}\nconfigurationFile: {}\nextraConfigurationFiles: {}\nnodeSelector: {}\ntolerations: []\naffinity: {}\ntests:\n  enabled: false\n"
        #部署应用nginx
        step_deployment_app(project_name=self.project_name, app_id=nginx_id, app_version_id=ng_ver_id, name=name, conf=conf)

        #查看并验证应用状态为active，最长等待时间900s
        i = 0
        while i < 900:
            status = step_get_app_status(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
            if status == 'active':
                print('应用部署耗时:' + str(i) + '秒')
                break
            elif status == 'enabled':
                print('应用部署失败')
                break
            time.sleep(60)
            i = i + 60
        #获取部署应用的cluster_id
        cluster_id = step_get_cluster_id(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        #根据cluster_id删除对应应用
        step_delete_app(ws_name=self.ws_name, project_name=self.project_name, cluster_id=cluster_id)
        #验证删除成功
        time.sleep(60)
        count = step_get_app_count(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        assert count == 0
        if status != 'active':
            print('porter部署耗时15min，仍未部署成功')
            assert status == 'active'
        else:
            assert status == 'active'

    @allure.title('从应用商店部署postgresql,验证其部署成功后，删除部署的应用')  ##ok
    @allure.severity(allure.severity_level.CRITICAL)
    def test_deployment_postgresql(self):
        # 获取应用的app_id
        post_id = commonFunction.get_app_id('postgresql')
        # 获取应用的version_id
        post_ver_id = commonFunction.get_app_version(post_id)
        name = 'postgre-test'
        conf = "image:\n  postgres:\n    repository: postgres\n    tag: 12.0-alpine\n    pullPolicy: IfNotPresent\nimagePullSecrets: []\nnameOverride: ''\nfullnameOverride: ''\nserviceAccount:\n  create: true\n  name: null\npodSecurityContext: {}\nsecurityContext: {}\npersistence:\n  enabled: true\n  size: 5Gi\n  subPath: null\nrootUsername: postgres\nrootPassword: password\nservice:\n  type: ClusterIP\n  port: 5432\nresources: {}\nnodeSelector: {}\ntolerations: []\naffinity: {}\ntests:\n  enabled: false\n"
        # 部署应用postgresql
        step_deployment_app(project_name=self.project_name, app_id=post_id, app_version_id=post_ver_id, name=name, conf=conf)
        # 查看并验证应用状态为active，最长等待时间900s
        i = 0
        while i < 900:
            status = step_get_app_status(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
            if status == 'active':
                print('应用部署耗时:' + str(i) + '秒')
                break
            elif status == 'enabled':
                print('应用部署失败')
                break
            time.sleep(60)
            i = i + 60
        # 获取部署应用的cluster_id
        cluster_id = step_get_cluster_id(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        # 根据cluster_id删除对应应用
        step_delete_app(ws_name=self.ws_name, project_name=self.project_name, cluster_id=cluster_id)
        # 验证删除成功
        time.sleep(60)
        count = step_get_app_count(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        assert count == 0
        if status != 'active':
            print('porter部署耗时15min，仍未部署成功')
            assert status == 'active'
        else:
            assert status == 'active'

    @allure.title('从应用商店部署minio,验证其部署成功后，删除部署的应用')  ##ok
    @allure.severity(allure.severity_level.CRITICAL)
    def test_deployment_minio(self):
        # 获取应用的app_id
        minio_id = commonFunction.get_app_id('minio')
        # 获取应用的version_id
        minio_ver_id = commonFunction.get_app_version(minio_id)
        name = 'minio-test1'
        conf = "nameOverride: ''\nfullnameOverride: ''\nclusterDomain: cluster.local\nimage:\n  repository: minio/minio\n  tag: RELEASE.2020-04-28T23-56-56Z\n  pullPolicy: IfNotPresent\nmcImage:\n  repository: minio/mc\n  tag: RELEASE.2020-04-25T00-43-23Z\n  pullPolicy: IfNotPresent\nhelmKubectlJqImage:\n  repository: bskim45/helm-kubectl-jq\n  tag: 3.1.0\n  pullPolicy: IfNotPresent\nmode: standalone\nextraArgs: []\nDeploymentUpdate:\n  type: RollingUpdate\n  maxUnavailable: 0\n  maxSurge: 100%\nStatefulSetUpdate:\n  updateStrategy: RollingUpdate\npriorityClassName: ''\nexistingSecret: ''\naccessKey: AKIAIOSFODNN7EXAMPLE\nsecretKey: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\ncertsPath: /etc/minio/certs/\nconfigPathmc: /etc/minio/mc/\nmountPath: /export\nbucketRoot: ''\ndrivesPerNode: 1\nreplicas: 4\nzones: 1\ntls:\n  enabled: false\n  certSecret: ''\n  publicCrt: public.crt\n  privateKey: private.key\npersistence:\n  enabled: true\n  existingClaim: ''\n  storageClass: ''\n  VolumeName: ''\n  accessMode: ReadWriteOnce\n  size: 10Gi\n  subPath: ''\nservice:\n  type: ClusterIP\n  clusterIP: null\n  port: 9000\n  nodePort: 31311\n  externalIPs: []\n  annotations: {}\ningress:\n  enabled: false\n  labels: {}\n  annotations: {}\n  path: /\n  hosts:\n    - chart-example.local\n  tls: []\nnodeSelector: {}\ntolerations: []\naffinity: {}\nsecurityContext:\n  enabled: true\n  runAsUser: 1000\n  runAsGroup: 1000\n  fsGroup: 1000\npodAnnotations: {}\npodLabels: {}\nlivenessProbe:\n  initialDelaySeconds: 5\n  periodSeconds: 30\n  timeoutSeconds: 1\n  successThreshold: 1\n  failureThreshold: 3\nreadinessProbe:\n  initialDelaySeconds: 60\n  periodSeconds: 15\n  timeoutSeconds: 1\n  successThreshold: 1\n  failureThreshold: 3\nresources:\n  requests:\n    memory: 256Mi\n    cpu: 250m\ndefaultBucket:\n  enabled: false\n  name: bucket\n  policy: none\n  purge: false\nbuckets: []\nmakeBucketJob:\n  annotations: null\nupdatePrometheusJob:\n  annotations: null\ns3gateway:\n  enabled: false\n  replicas: 4\n  serviceEndpoint: ''\n  accessKey: ''\n  secretKey: ''\nazuregateway:\n  enabled: false\n  replicas: 4\ngcsgateway:\n  enabled: false\n  replicas: 4\n  gcsKeyJson: ''\n  projectId: ''\nossgateway:\n  enabled: false\n  replicas: 4\n  endpointURL: ''\nnasgateway:\n  enabled: false\n  replicas: 4\n  pv: null\nb2gateway:\n  enabled: false\n  replicas: 4\nenvironment: null\nnetworkPolicy:\n  enabled: false\n  allowExternal: true\npodDisruptionBudget:\n  enabled: false\n  maxUnavailable: 1\nserviceAccount:\n  create: true\n  name: null\nmetrics:\n  serviceMonitor:\n    enabled: false\n    additionalLabels: {}\netcd:\n  endpoints: []\n  pathPrefix: ''\n  corednsPathPrefix: ''\n  clientCert: ''\n  clientCertKey: ''\n"
        # 部署应用minio
        step_deployment_app(project_name=self.project_name, app_id=minio_id, app_version_id=minio_ver_id, name=name, conf=conf)
        # 查看并验证应用状态为active，最长等待时间900s
        i = 0
        while i < 900:
            status = step_get_app_status(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
            if status == 'active':
                print('应用部署耗时:' + str(i) + '秒')
                break
            elif status == 'enabled':
                print('应用部署失败')
                break
            time.sleep(60)
            i = i + 60
        # 获取部署应用的cluster_id
        cluster_id = step_get_cluster_id(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        # 根据cluster_id删除对应应用
        step_delete_app(ws_name=self.ws_name, project_name=self.project_name, cluster_id=cluster_id)
        # 验证删除成功
        time.sleep(60)
        count = step_get_app_count(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        assert count == 0
        if status != 'active':
            print('porter部署耗时15min，仍未部署成功')
            assert status == 'active'
        else:
            assert status == 'active'

    @allure.title('从应用商店部署mongodb,验证其部署成功后，删除部署的应用')  ##ok
    @allure.severity(allure.severity_level.CRITICAL)
    def test_deployment_mongodb(self):
        # 获取应用的app_id
        mon_id = commonFunction.get_app_id('mongodb')
        # 获取应用的version_id
        mon_ver_id = commonFunction.get_app_version(mon_id)
        name = 'mongodb-test'
        conf = "image:\n  init:\n    repository: mikefarah/yq\n    tag: 2.4.1\n    pullPolicy: IfNotPresent\n  mongo:\n    repository: mongo\n    tag: 4.2.1\n    pullPolicy: IfNotPresent\nimagePullSecrets: []\nnameOverride: ''\nfullnameOverride: ''\npersistence:\n  size: 5Gi\nextraConfigurations: {}\nrootUsername: admin\nrootPassword: password\nservice:\n  type: ClusterIP\n  port: 27017\nresources: {}\nnodeSelector: {}\ntolerations: []\naffinity: {}\n"

        # 部署应用mongodb
        step_deployment_app(project_name=self.project_name, app_id=mon_id, app_version_id=mon_ver_id, name=name,
                            conf=conf)
        # 查看并验证应用状态为active，最长等待时间900s
        i = 0
        while i < 900:
            status = step_get_app_status(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
            if status == 'active':
                print('应用部署耗时:' + str(i) + '秒')
                break
            elif status == 'enabled':
                print('应用部署失败')
                break
            time.sleep(60)
            i = i + 60
        # 获取部署应用的cluster_id
        cluster_id = step_get_cluster_id(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        # 根据cluster_id删除对应应用
        step_delete_app(ws_name=self.ws_name, project_name=self.project_name, cluster_id=cluster_id)
        # 验证删除成功
        time.sleep(60)
        count = step_get_app_count(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        assert count == 0
        if status != 'active':
            print('porter部署耗时15min，仍未部署成功')
            assert status == 'active'
        else:
            assert status == 'active'

    @allure.title('从应用商店部署harbor')
    @allure.severity(allure.severity_level.CRITICAL)  #xxxx
    def test_deployment_harbor(self):
        # 获取应用的app_id
        harbor_id = commonFunction.get_app_id('harbor')
        # 获取应用的version_id
        harbor_ver_id = commonFunction.get_app_version(harbor_id)
        name = 'harbor-test'
        conf = "expose:\n  type: ingress\n  tls:\n    enabled: true\n    secretName: ''\n    notarySecretName: ''\n    commonName: ''\n  ingress:\n    hosts:\n      core: core.harbor.domain\n      notary: notary.harbor.domain\n    controller: default\n    annotations:\n      ingress.kubernetes.io/ssl-redirect: 'true'\n      ingress.kubernetes.io/proxy-body-size: '0'\n      nginx.ingress.kubernetes.io/ssl-redirect: 'true'\n      nginx.ingress.kubernetes.io/proxy-body-size: '0'\n  clusterIP:\n    name: harbor\n    ports:\n      httpPort: 80\n      httpsPort: 443\n      notaryPort: 4443\n  nodePort:\n    name: harbor\n    ports:\n      http:\n        port: 80\n        nodePort: 30002\n      https:\n        port: 443\n        nodePort: 30003\n      notary:\n        port: 4443\n        nodePort: 30004\n  loadBalancer:\n    name: harbor\n    IP: ''\n    ports:\n      httpPort: 80\n      httpsPort: 443\n      notaryPort: 4443\n    annotations: {}\n    sourceRanges: []\nexternalURL: 'https://core.harbor.domain'\ninternalTLS:\n  enabled: false\n  certSource: auto\n  trustCa: ''\n  core:\n    secretName: ''\n    crt: ''\n    key: ''\n  jobservice:\n    secretName: ''\n    crt: ''\n    key: ''\n  registry:\n    secretName: ''\n    crt: ''\n    key: ''\n  portal:\n    secretName: ''\n    crt: ''\n    key: ''\n  chartmuseum:\n    secretName: ''\n    crt: ''\n    key: ''\n  clair:\n    secretName: ''\n    crt: ''\n    key: ''\n  trivy:\n    secretName: ''\n    crt: ''\n    key: ''\npersistence:\n  enabled: true\n  resourcePolicy: keep\n  persistentVolumeClaim:\n    registry:\n      existingClaim: ''\n      storageClass: ''\n      subPath: ''\n      accessMode: ReadWriteOnce\n      size: 5Gi\n    chartmuseum:\n      existingClaim: ''\n      storageClass: ''\n      subPath: ''\n      accessMode: ReadWriteOnce\n      size: 5Gi\n    jobservice:\n      existingClaim: ''\n      storageClass: ''\n      subPath: ''\n      accessMode: ReadWriteOnce\n      size: 1Gi\n    database:\n      existingClaim: ''\n      storageClass: ''\n      subPath: ''\n      accessMode: ReadWriteOnce\n      size: 1Gi\n    redis:\n      existingClaim: ''\n      storageClass: ''\n      subPath: ''\n      accessMode: ReadWriteOnce\n      size: 1Gi\n    trivy:\n      existingClaim: ''\n      storageClass: ''\n      subPath: ''\n      accessMode: ReadWriteOnce\n      size: 5Gi\n  imageChartStorage:\n    disableredirect: false\n    type: filesystem\n    filesystem:\n      rootdirectory: /storage\n    azure:\n      accountname: accountname\n      accountkey: base64encodedaccountkey\n      container: containername\n    gcs:\n      bucket: bucketname\n      encodedkey: base64-encoded-json-key-file\n    s3:\n      region: us-west-1\n      bucket: bucketname\n    swift:\n      authurl: 'https://storage.myprovider.com/v3/auth'\n      username: username\n      password: password\n      container: containername\n    oss:\n      accesskeyid: accesskeyid\n      accesskeysecret: accesskeysecret\n      region: regionname\n      bucket: bucketname\nimagePullPolicy: IfNotPresent\nimagePullSecrets: null\nupdateStrategy:\n  type: RollingUpdate\nlogLevel: info\nharborAdminPassword: Harbor12345\nsecretKey: not-a-secure-key\nproxy:\n  httpProxy: null\n  httpsProxy: null\n  noProxy: '127.0.0.1,localhost,.local,.internal'\n  components:\n    - core\n    - jobservice\n    - clair\nnginx:\n  image:\n    repository: goharbor/nginx-photon\n    tag: v2.0.0\n  replicas: 1\n  nodeSelector: {}\n  tolerations: []\n  affinity: {}\n  podAnnotations: {}\nportal:\n  image:\n    repository: goharbor/harbor-portal\n    tag: v2.0.0\n  replicas: 1\n  nodeSelector: {}\n  tolerations: []\n  affinity: {}\n  podAnnotations: {}\ncore:\n  image:\n    repository: goharbor/harbor-core\n    tag: v2.0.0\n  replicas: 1\n  livenessProbe:\n    initialDelaySeconds: 300\n  nodeSelector: {}\n  tolerations: []\n  affinity: {}\n  podAnnotations: {}\n  secret: ''\n  secretName: ''\n  xsrfKey: ''\njobservice:\n  image:\n    repository: goharbor/harbor-jobservice\n    tag: v2.0.0\n  replicas: 1\n  maxJobWorkers: 10\n  jobLogger: file\n  nodeSelector: {}\n  tolerations: []\n  affinity: {}\n  podAnnotations: {}\n  secret: ''\nregistry:\n  registry:\n    image:\n      repository: goharbor/registry-photon\n      tag: v2.0.0\n  controller:\n    image:\n      repository: goharbor/harbor-registryctl\n      tag: v2.0.0\n  replicas: 1\n  nodeSelector: {}\n  tolerations: []\n  affinity: {}\n  podAnnotations: {}\n  secret: ''\n  relativeurls: false\n  credentials:\n    username: harbor_registry_user\n    password: harbor_registry_password\n    htpasswd: >-\n      harbor_registry_user:$2y$10$9L4Tc0DJbFFMB6RdSCunrOpTHdwhid4ktBJmLD00bYgqkkGOvll3m\n  middleware:\n    enabled: false\n    type: cloudFront\n    cloudFront:\n      baseurl: example.cloudfront.net\n      keypairid: KEYPAIRID\n      duration: 3000s\n      ipfilteredby: none\n      privateKeySecret: my-secret\nchartmuseum:\n  enabled: true\n  absoluteUrl: false\n  image:\n    repository: goharbor/chartmuseum-photon\n    tag: v2.0.0\n  replicas: 1\n  nodeSelector: {}\n  tolerations: []\n  affinity: {}\n  podAnnotations: {}\nclair:\n  enabled: true\n  clair:\n    image:\n      repository: goharbor/clair-photon\n      tag: v2.0.0\n  adapter:\n    image:\n      repository: goharbor/clair-adapter-photon\n      tag: v2.0.0\n  replicas: 1\n  updatersInterval: 12\n  nodeSelector: {}\n  tolerations: []\n  affinity: {}\n  podAnnotations: {}\ntrivy:\n  enabled: true\n  image:\n    repository: goharbor/trivy-adapter-photon\n    tag: v2.0.0\n  replicas: 1\n  debugMode: false\n  vulnType: 'os,library'\n  severity: 'UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL'\n  ignoreUnfixed: false\n  insecure: false\n  gitHubToken: ''\n  skipUpdate: false\n  resources:\n    requests:\n      cpu: 200m\n      memory: 512Mi\n    limits:\n      cpu: 1\n      memory: 1Gi\n  podAnnotations: {}\nnotary:\n  enabled: true\n  server:\n    image:\n      repository: goharbor/notary-server-photon\n      tag: v2.0.0\n    replicas: 1\n  signer:\n    image:\n      repository: goharbor/notary-signer-photon\n      tag: v2.0.0\n    replicas: 1\n  nodeSelector: {}\n  tolerations: []\n  affinity: {}\n  podAnnotations: {}\n  secretName: ''\ndatabase:\n  type: internal\n  internal:\n    image:\n      repository: goharbor/harbor-db\n      tag: v2.0.0\n    initContainerImage:\n      repository: busybox\n      tag: latest\n    password: changeit\n    nodeSelector: {}\n    tolerations: []\n    affinity: {}\n  external:\n    host: 192.168.0.1\n    port: '5432'\n    username: user\n    password: password\n    coreDatabase: registry\n    clairDatabase: clair\n    notaryServerDatabase: notary_server\n    notarySignerDatabase: notary_signer\n    sslmode: disable\n  maxIdleConns: 50\n  maxOpenConns: 100\n  podAnnotations: {}\nredis:\n  type: internal\n  internal:\n    image:\n      repository: goharbor/redis-photon\n      tag: v2.0.0\n    nodeSelector: {}\n    tolerations: []\n    affinity: {}\n  external:\n    host: 192.168.0.2\n    port: '6379'\n    coreDatabaseIndex: '0'\n    jobserviceDatabaseIndex: '1'\n    registryDatabaseIndex: '2'\n    chartmuseumDatabaseIndex: '3'\n    clairAdapterIndex: '4'\n    trivyAdapterIndex: '5'\n    password: ''\n  podAnnotations: {}\n"
        # 部署应用harbor
        step_deployment_app(project_name=self.project_name, app_id=harbor_id, app_version_id=harbor_ver_id, name=name,
                            conf=conf)
        # 查看并验证应用状态为active，最长等待时间900s
        i = 0
        while i < 900:
            status = step_get_app_status(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
            if status == 'active':
                print('应用部署耗时:' + str(i) + '秒')
                break
            elif status == 'enabled':
                print('应用部署失败')
                break
            time.sleep(60)
            i = i + 60
        # 获取部署应用的cluster_id
        cluster_id = step_get_cluster_id(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        # 根据cluster_id删除对应应用
        step_delete_app(ws_name=self.ws_name, project_name=self.project_name, cluster_id=cluster_id)
        # 验证删除成功
        time.sleep(60)
        count = step_get_app_count(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        assert count == 0
        if status != 'active':
            print('porter部署耗时15min，仍未部署成功')
            assert status == 'active'
        else:
            assert status == 'active'

    @allure.title('从应用商店部署memcached,验证其部署成功后，删除部署的应用')
    @allure.severity(allure.severity_level.CRITICAL)  #xxx
    def test_deployment_memcached(self):
        url = config.url + '/kapis/openpitrix.io/v1/workspaces/undefined/clusters/default/namespaces/' + self.project_name + '/applications'
        # 获取应用的app_id
        memcached_id = commonFunction.get_app_id('harbor')
        # 获取应用的version_id
        memcached_ver_id = commonFunction.get_app_version(memcached_id)
        name = 'memcached-test'
        conf = "image: 'memcached:1.5.20'\nreplicaCount: 3\npdbMinAvailable: 2\nAntiAffinity: hard\nmemcached:\n  maxItemMemory: 64\n  verbosity: v\n  extendedOptions: modern\n  extraArgs: []\nserviceAnnotations: {}\nkind: StatefulSet\nupdateStrategy:\n  type: RollingUpdate\nresources:\n  requests:\n    memory: 64Mi\n    cpu: 50m\nnodeSelector: {}\ntolerations: {}\naffinity: {}\nsecurityContext:\n  enabled: true\n  fsGroup: 1001\n  runAsUser: 1001\nmetrics:\n  enabled: false\n  serviceMonitor:\n    enabled: false\n    interval: 15s\n  image: 'quay.io/prometheus/memcached-exporter:v0.6.0'\n  resources: {}\nextraContainers: ''\nextraVolumes: ''\npodAnnotations: {}\n"

        # 部署应用memcached
        step_deployment_app(project_name=self.project_name, app_id=memcached_id, app_version_id=memcached_ver_id, name=name,
                            conf=conf)
        # 查看并验证应用状态为active，最长等待时间900s
        i = 0
        while i < 900:
            status = step_get_app_status(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
            if status == 'active':
                print('应用部署耗时:' + str(i) + '秒')
                break
            elif status == 'enabled':
                print('应用部署失败')
                break
            time.sleep(60)
            i = i + 60
        # 获取部署应用的cluster_id
        cluster_id = step_get_cluster_id(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        # 根据cluster_id删除对应应用
        step_delete_app(ws_name=self.ws_name, project_name=self.project_name, cluster_id=cluster_id)
        # 验证删除成功
        time.sleep(60)
        count = step_get_app_count(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        assert count == 0
        if status != 'active':
            print('porter部署耗时15min，仍未部署成功')
            assert status == 'active'
        else:
            assert status == 'active'



    @allure.title('从应用商店部署elasticsearch-exporter,验证其部署成功后，删除部署的应用')
    @allure.severity(allure.severity_level.CRITICAL)  #ok
    def test_deployment_elasticsearch_ex(self):
        # 获取应用的app_id
        es_id = commonFunction.get_app_id('elasticsearch-exporter')
        # 获取应用的version_id
        es_ver_id = commonFunction.get_app_version(es_id)
        name ='ela-ex-test'
        conf = "replicaCount: 1\nrestartPolicy: Always\nimage:\n  repository: justwatch/elasticsearch_exporter\n  tag: 1.1.0\n  pullPolicy: IfNotPresent\n  pullSecret: ''\nsecurityContext:\n  enabled: true\n  runAsUser: 1000\nresources: {}\npriorityClassName: ''\nnodeSelector: {}\ntolerations: {}\npodAnnotations: {}\naffinity: {}\nservice:\n  type: ClusterIP\n  httpPort: 9108\n  metricsPort:\n    name: http\n  annotations: {}\n  labels: {}\nenv: {}\nenvFromSecret: ''\nextraEnvSecrets: {}\nsecretMounts: []\nes:\n  uri: 'http://localhost:9200'\n  all: true\n  indices: true\n  indices_settings: true\n  shards: true\n  snapshots: true\n  cluster_settings: false\n  timeout: 30s\n  sslSkipVerify: false\n  ssl:\n    enabled: false\n    useExistingSecrets: false\n    ca:\n      path: /ssl/ca.pem\n    client:\n      enabled: true\n      pemPath: /ssl/client.pem\n      keyPath: /ssl/client.key\nweb:\n  path: /metrics\nserviceMonitor:\n  enabled: true\n  labels: {}\n  interval: 10s\n  scrapeTimeout: 10s\n  scheme: http\n  relabelings: []\nprometheusRule:\n  enabled: false\n  labels: {}\n  rules: []\nserviceAccount:\n  create: false\n  name: default\npodSecurityPolicies:\n  enabled: false\n"
        # 部署应用elasticsearch-exporter
        step_deployment_app(project_name=self.project_name, app_id=es_id, app_version_id=es_ver_id,
                            name=name,
                            conf=conf)
        # 查看并验证应用状态为active，最长等待时间900s
        i = 0
        while i < 900:
            status = step_get_app_status(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
            if status == 'active':
                print('应用部署耗时:' + str(i) + '秒')
                break
            elif status == 'enabled':
                print('应用部署失败')
                break
            time.sleep(60)
            i = i + 60
        # 获取部署应用的cluster_id
        cluster_id = step_get_cluster_id(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        # 根据cluster_id删除对应应用
        step_delete_app(ws_name=self.ws_name, project_name=self.project_name, cluster_id=cluster_id)
        # 验证删除成功
        time.sleep(60)
        count = step_get_app_count(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        assert count == 0
        if status != 'active':
            print('porter部署耗时15min，仍未部署成功')
            assert status == 'active'
        else:
            assert status == 'active'

    @allure.title('从应用商店部署etcd,验证其部署成功后，删除部署的应用')
    @allure.severity(allure.severity_level.CRITICAL)  #ok
    def test_deployment_etcd(self):
        url = config.url + '/kapis/openpitrix.io/v1/workspaces/undefined/clusters/default/namespaces/' + self.project_name + '/applications'
        # 获取应用的app_id
        etcd_id = commonFunction.get_app_id('etcd')
        # 获取应用的version_id
        etcd_ver_id = commonFunction.get_app_version(etcd_id)
        name = 'etcd-test'
        conf = "image:\n  repository: kubesphere/etcd\n  pullPolicy: IfNotPresent\nimagePullSecrets: []\nnameOverride: ''\nfullnameOverride: ''\npersistence:\n  size: 5Gi\nextraArgs: []\nservice:\n  port: 2379\nresources: {}\nnodeSelector: {}\ntolerations: []\naffinity: {}\ntests:\n  enabled: false\n"
        # 部署应用elasticsearch-exporter
        step_deployment_app(project_name=self.project_name, app_id=etcd_id, app_version_id=etcd_ver_id,
                            name=name,
                            conf=conf)
        # 查看并验证应用状态为active，最长等待时间900s
        i = 0
        while i < 900:
            status = step_get_app_status(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
            if status == 'active':
                print('应用部署耗时:' + str(i) + '秒')
                break
            elif status == 'enabled':
                print('应用部署失败')
                break
            time.sleep(60)
            i = i + 60
        # 获取部署应用的cluster_id
        cluster_id = step_get_cluster_id(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        # 根据cluster_id删除对应应用
        step_delete_app(ws_name=self.ws_name, project_name=self.project_name, cluster_id=cluster_id)
        # 验证删除成功
        time.sleep(60)
        count = step_get_app_count(ws_name=self.ws_name, project_name=self.project_name, app_name=name)
        assert count == 0
        if status != 'active':
            print('porter部署耗时15min，仍未部署成功')
            assert status == 'active'
        else:
            assert status == 'active'


    @allure.title('{title}')  # 设置用例标题
    @allure.severity(allure.severity_level.CRITICAL)  # 设置用例优先级
    # 将用例信息以参数化的方式传入测试方法
    @pytest.mark.parametrize('id,url,data,story,title,method,severity,condition,except_result', parametrize)
    def test_ws_role_user(self, id, url, data, story, title, method, severity, condition, except_result):

        '''
        :param id: 用例编号
        :param url: 用例请求的URL地址
        :param data: 用例使用的请求数据
        :param title: 用例标题
        :param method: 用例的请求方式
        :param severity: 用例优先级
        :param condition: 用例的校验条件
        :param except_result: 用例的预期结果
        '''

        allure.dynamic.story(story)  # 动态生成模块
        allure.dynamic.severity(severity)  # 动态生成用例等级

        # test开头的测试函数
        url = config.url + url
        if method == 'get':
            # 测试get方法
            r = requests.get(url, headers=get_header())

        elif method == 'post':
            # 测试post方法
            data = eval(data)
            r = requests.post(url, headers=get_header(), data=json.dumps(data))

        elif method == 'patch':
            # 测试patch方法
            data = eval(data)
            r = requests.patch(url, headers=get_header_for_patch(), data=json.dumps(data))

        elif method == 'delete':
            # 测试delete方法
            r = requests.delete(url, headers=get_header())

        # 将校验条件和预期结果参数化
        if condition != 'nan':
            condition_new = eval(condition)  # 将字符串转化为表达式
            if isinstance(condition_new, str):
                # 判断表达式的结果是否为字符串，如果为字符串格式，则去掉其首尾的空格
                assert condition_new.strip() == except_result
            else:
                assert condition_new == except_result

        # 将用例中的内容打印在报告中
        print(
            '用例编号: ' + str(id) + '\n'
                                 '用例请求的URL地址: ' + str(url) + '\n'
                                                             '用例使用的请求数据: ' + str(data) + '\n'
                                                                                         '用例模块: ' + story + '\n'
                                                                                                            '用例标题: ' + title + '\n'
                                                                                                                               '用例的请求方式: ' + method + '\n'
                                                                                                                                                      '用例优先级: ' + severity + '\n'
                                                                                                                                                                             '用例的校验条件: ' + str(
                condition) + '\n'
                             '用例的实际结果: ' + str(condition_new) + '\n'
                                                                '用例的预期结果: ' + str(except_result)
        )




if __name__ == "__main__":
    pytest.main(['-vs', 'testAppStore.py'])  # -s参数是为了显示用例的打印信息。 -q参数只显示结果，不显示过程






