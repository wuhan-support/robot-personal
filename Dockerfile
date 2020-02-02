FROM python:3.6

MAINTAINER maicius
WORKDIR /ncov_robot
RUN mv /etc/apt/sources.list /etc/apt/sources.list.bak

RUN echo "deb http://mirrors.ustc.edu.cn/ubuntu/ trusty main restricted universe multiverse\n\
deb http://mirrors.ustc.edu.cn/ubuntu/ trusty-security main restricted universe multiverse\n\
deb http://mirrors.ustc.edu.cn/ubuntu/ trusty-updates main restricted universe multiverse\n\
deb http://mirrors.ustc.edu.cn/ubuntu/ trusty-proposed main restricted universe multiverse\n\
deb http://mirrors.ustc.edu.cn/ubuntu/ trusty-backports main restricted universe multiverse\n\
deb-src http://mirrors.ustc.edu.cn/ubuntu/ trusty main restricted universe multiverse\n\
deb-src http://mirrors.ustc.edu.cn/ubuntu/ trusty-security main restricted universe multiverse\n\
deb-src http://mirrors.ustc.edu.cn/ubuntu/ trusty-updates main restricted universe multiverse\n\
deb-src http://mirrors.ustc.edu.cn/ubuntu/ trusty-proposed main restricted universe multiverse\n\
deb-src http://mirrors.ustc.edu.cn/ubuntu/ trusty-backports main restricted universe multiverse\n\
" > /etc/apt/sources.list
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 40976EAF437D05B5
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 3B4FE6ACC0B21F32
RUN apt-get update --allow-unauthenticated
# RUN apt-get -q -y --force-yes install libleptonica-dev
# RUN apt-get -q -y --force-yes install gcc


COPY requirements.txt /ncov_robot
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
COPY cnocr-models-v1.0.0.zip /root/.cnocr/
COPY . /ncov_robot
CMD python src/robot/NcovWeRobotServer.py
