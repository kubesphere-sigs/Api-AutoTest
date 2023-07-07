# 基于官方 Python 镜像构建
FROM python:3.8.2

# 将 SHELL 设置为 Bash
SHELL ["/bin/bash", "-c"]

# 切换到root用户

USER root
# 创建工作目录
WORKDIR /home/jenkins

# 更新软件包索引
RUN apt-get update

# 在构建期间更新过期的软件包
RUN apt-get upgrade -y

# 安装vim
RUN apt-get install -y vim

# 安装JDK
RUN apt-get install -y openjdk-11-jre-headless

RUN apt-get install -y openjdk-11-jdk-headless

RUN echo JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64/bin/java" > /etc/environment

RUN source /etc/environment

# 安装gettext软件包，该软件包提供了envsubst命令
RUN apt-get install -y gettext

# 设置容器启动时的默认命令
CMD [ "bash" ]
