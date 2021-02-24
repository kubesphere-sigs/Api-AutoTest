import datetime
import logging
import os

#配置日志格式
def log_format():
    dt = datetime.datetime.now().strftime('%Y-%m-%d')
    logging.basicConfig(level=logging.DEBUG,  # 控制台打印的日志级别
                        filename=os.path.join('../log', str(dt) + '.log'),  # 定义保存日志的路径，使用os.path.join()方法拼接文件路径，其展现为层级关系
                        filemode='a',  # 模式，有w和a，w就是写模式，每次都会重新写日志，覆盖之前的日志
                        # a是追加模式，默认如果不写的话，就是追加模式
                        format=
                        '%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'
                        # 日志格式
                        )