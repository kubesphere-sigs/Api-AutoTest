# Api-AutoTest
本工程是基于kubesphere编写的接口自动化测试用例，通过访问apiserver的方式运行，目前已基本覆盖ks的基础功能。仍在持续优化中...
## 目录结构

```
data
├── data.xlsx
├── jenkinsfile
TestCase
├── sonar-project.properties
├── testAppManage.py
├── testAppStore.py
├── testAppStoreManage.py
├── testAuditingOperating.py
├── testClusterManage.py
├── testDevops.py
├── testEventSearch.py
├── testHelp.py
├── testLogSearch.py
├── testMetering.py
├── testMultiAppStore.py
├── testMultiClusterManage.py
├── testMultiMetering.py
├── testMultiProject.py
├── testMultiWorkbench.py
├── testMultiWorkspace.py
├── testProject.py
├── testRole.py
├── testUser.py
├── testWorkbench.py
├── testWorkspace.py
common
├── commonFunction.py
├── getConfig.py
├── getCookie.py
├── getData.py
├── getHeader.py
├── getProxy.py
└── logFormat.py
requirements.txt 
config
├── config.py
├── config.yaml
├── config_new.yaml
└── note
step
├── app_steps.py
├── cluster_steps.py
├── devops_steps.py
├── multi_cluster_steps.py
├── multi_meter_steps.py
├── multi_worksapce_steps.py
├── platform_steps.py
├── project_steps.py
├── toolbox_steps.py
└── workspace_steps.py
``` 

## 使用指南
一、通过devops触发流水线

1、替换devops-jenkins的镜像为 ghcr.io/linuxsuren/ks-jenkins:allure

2、修改 deployment devops-jenkins的JAVA_TOOL_OPTIONS为
```
-Xms1200m -Xmx1600m -XX:MaxRAM=2g
-Dhudson.slaves.NodeProvisioner.initialDelay=20
-Dhudson.slaves.NodeProvisioner.MARGIN=50
-Dhudson.slaves.NodeProvisioner.MARGIN0=0.85
-Dhudson.model.LoadStatistics.clock=5000
-Dhudson.model.LoadStatistics.decay=0.2
-Dhudson.slaves.NodeProvisioner.recurrencePeriod=5000
-Dhudson.security.csrf.DefaultCrumbIssuer.EXCLUDE_SESSION_ID=true
-Dio.jenkins.plugins.casc.ConfigurationAsCode.initialDelay=10000
-Djenkins.install.runSetupWizard=false
```
3、在jenkins页面/系统管理/全局工具配置，新增Allure Commandline

![Image text](https://github.com/kubesphere-sigs/Api-Autotest/blob/master/data/photo/4.png)

4、使用如下jenkinsfile创建流水线
```
pipeline {
  agent {
    kubernetes {
      inheritFrom 'base'
      yaml '''
      spec:
        containers:
        - name: python
          image: kubespheredev/builder-python:v3.2.0
          command: [\'sleep\']
          args: [\'1d\']
      '''
      label 'default'
    }
  }
  stages {
    stage('拉取测试代码') {
      steps {
        container('python') {
          git(url: 'https://github.com/kubesphere-sigs/Api-AutoTest.git', branch: 'master', changelog: true, poll: false)
        }
      }
    }
    stage('安装第三方python依赖') {
      steps {
        container('python') {
          sh 'pip install -r requirements.txt'
        }
      }
    }
    stage('运行测试脚本') {
      environment {
        ENV_URL = "${apiserver}"
        PATH = "$PATH:/usr/local/src/allure-2.17.2/bin"
      }
      input {
        message '请输入apiserver地址(http://ip:port)'
        id 'Yes'
        parameters {
          string(name: 'apiserver')
        }
      }
      steps {
        container('python') {
          sh '''
              envsubst < ${WORKSPACE}/config/config.yaml > ${WORKSPACE}/config/config_new.yaml
              cd ${WORKSPACE}/TestCase
              pytest testClusterManage.py -s  --reruns=1 --reruns-delay=5 --alluredir ../result --clean-alluredir
              exit 0
             '''
        }
      }
    }
  }
  post{
      always {
        container('python') {
          sh 'chmod -R o+xw result'
          script {
            allure([
                    includeProperties: false,
                    jdk: '',
                    properties: [],
                    reportBuildPolicy: 'ALWAYS',
                    results: [[path: 'result']]
              ])
            }
          }
        }
      }
}
```
```
ks-apiserver地址，可直接使用内网地址
```
![Image text](https://github.com/kubesphere-sigs/Api-Autotest/blob/master/data/photo/3.png)


```
pytest test*.py -s  --reruns=1 --reruns-delay=5 --alluredir ../result --clean-alluredir

通过修改'test*.py',可指定运行的测试脚本
```


二、在本地环境运行

1、安装python3环境

2、安装allure 
- 下载allure包，选择最新或者任意版本
```
https://github.com/allure-framework/allure2/releases
```
- 如下载路径为 ’/usr/local/src/‘，解压并修改文件夹权限
```
unzip allure-commandline-2.13.6.zip
mv allure-2.13.6 allure
chmod -R 777 allure
```
- 配置allure环境变量
```
cat >> /root/.bashrc << "EOF" 
export PATH=/usr/local/src/allure/bin:$PATH 
EOF
```
- 更新环境变量配置文件并验证生效
```
source /root/.bashrc
allure --version
```
3、安装项目的依赖库
```
pip3 install -r requirements.txt
```
4、暴露apiserver端口，在ks-apiserver deployment的配置文件中的增加hostPort
```
kubectl edit deployment ks-apiserver -n kubesphere-system
``` 
5、进入TestCase目录下，运行如下命令即可执行测试用例。
(pytest [file_or_dir] --alluredir ../report --clean-alluredir。不推荐执行testAppStore.py，该脚本运行时间很长。)
```
pytest testRloe.py --alluredir ../report --clean-alluredir
```
6、生成测试报告
```
allure generate ../report ../allure_report --clean
```
7、测试报告示例
![Image text](https://github.com/kubesphere-sigs/Api-Autotest/blob/master/data/photo/1.png)
![Image text](https://github.com/kubesphere-sigs/Api-Autotest/blob/master/data/photo/2.png)

