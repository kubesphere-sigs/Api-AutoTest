# Api-AutoTest
本工程是基于kubesphere3.0版本编写的接口自动化测试用例，通过访问apiserver的方式运行，目前已基本覆盖ks3.0的基础功能。仍在持续优化中...
## 目录结构

```
.
├── README.md
├── TestCase
│   ├── allure-report   //测试报告
|       |── index.html  //查看html测试报告
│   ├── testAppManage.py    //测试应用管理          
│   ├── testAppStore.py     //测试appstore            
│   ├── testAppStoreManage.py   //测试应用管理
│   ├── testDevops.py   //测试devops
│   ├── testProject.py  //测试项目管理
│   ├── testRole.py     //测试系统级角色管理
│   ├── testUser.py     //测试系统级用户管理
│   └── testWorkspace.py    //测试企业空间
├── common  //公共方法
│   ├── commonFunction.py
│   ├── getCookie.py
│   ├── getData.py
│   ├── getHeader.py
│   └── logFormat.py
├── config
│   ├── config.py   //配置文件
│   └── note    //说明文档
├── data
|   ├── photo //测试图片
│   ├── data.xlsx   //测试用例
└── requirements.txt    //依赖库
``` 

## 使用指南
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
8、jenkins体验地址
http://139.198.9.112:8080   root/admin
