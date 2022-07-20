from common import commonFunction

collect_ignore = []
multi_cluster = ["TestCase/testMultiAppStore.py", "TestCase/testMultiClusterManage.py", "TestCase/testMultiProject.py",
                 "TestCase/testMultiWorkbench.py", "TestCase/testMultiWorkspace.py", "TestCase/testMultiMetering.py"]

single_cluster = ["TestCase/testAppStoreManage.py", "TestCase/testEvents.py", "TestCase/testMetering.py",
                  "TestCase/testMultiProject.py", "TestCase/testRole.py", "TestCase/testAuditing.py",
                  "TestCase/testAppManage.py", "TestCase/testClusterManage.py", "TestCase/testIppool.py",
                  "TestCase/testWorkbench.py", "TestCase/testAppStore.py", "TestCase/testDevops.py",
                  "TestCase/testLogging.py", "TestCase/testProject.py", "TestCase/testWorkspace.py"]
if commonFunction.check_multi_cluster() is False:
    collect_ignore = multi_cluster
else:
    collect_ignore = single_cluster