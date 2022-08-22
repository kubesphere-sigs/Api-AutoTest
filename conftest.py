from common import commonFunction
from common.getConfig import get_apiserver

# 获取测试地址
env_url = get_apiserver()
# 登录ks，并将token写入yaml
commonFunction.step_login(env_url)
# 将环境信息写入environment.properties
commonFunction.write_environment_info()