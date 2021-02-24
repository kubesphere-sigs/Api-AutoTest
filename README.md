# Api-Autotest
本工程是基于kubesphere3.0版本编写的接口自动化测试用例，已基本覆盖ks3.0的基础功能。仍在持续优化中...
## 目录结构

’‘’
.
├── README.md
├── TestCase
│   ├── allure-report     //测试报告
│   ├── testAppManage.py  //测试应用管理
│   ├── testAppStore.py   //测试应用商店
│   ├── testAppStoreManage.py   //测试应用商店管理
│   ├── testDevops.py     //测试devops
│   ├── testProject.py    //测试项目管理
│   ├── testRole.py       //测试系统角色管理
│   ├── testUser.py       //测试系统用户管理
│   └── testWorkspace.py  //测试企业空间
├── common    //公共方法
│   ├── commonFunction.py
│   ├── getCookie.py
│   ├── getData.py
│   ├── getHeader.py
│   └── logFormat.py
├── config    
│   ├── config.py   //配置文件
│   └── note        //说明文档
├── data
│   ├── data.xlsx   //测试用例
└── requirements.txt    //依赖库
‘’‘

## 使用指南
