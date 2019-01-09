FROM ubuntu:18.04

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y \
tzdata \
&& rm -rf /var/lib/apt/lists/*

ENV TZ=Asia/Taipei
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install --no-install-recommends -y \
build-essential \
cgroup-lite \
cppreference-doc-en-html \
curl \
file \
g++ \
gcc \
gettext \
git \
iso-codes \
libcap-dev \
libcups2-dev \
libffi-dev \
libpq-dev \
openjdk-8-jdk-headless \
postgresql  \
postgresql-client  \
python-dev \
python-pip \
python-setuptools \
python-wheel \
python2.7  \
python3.6  \
shared-mime-info \
vim \
wget \
zip \
#fp-compiler \
#haskell-platform  \
#mono-mcs \
#php7.2-cli  \
#php7.2-fpm \
#phppgadmin  \
#python3-dev \
#python3-pip \
#python3-setuptools \
#python3-wheel \
#rustc \
&& rm -rf /var/lib/apt/lists/*

RUN locale-gen en_US.UTF-8
ENV LANG en_US.utf-8

RUN wget -qO- https://github.com/cms-dev/cms/releases/download/v1.4.rc1/v1.4.rc1.tar.gz | tar xvz -C /

WORKDIR /cms/

RUN python prerequisites.py -y --as-root install && \
    usermod -a -G cmsuser root && \
    python -m pip install --no-cache-dir -r requirements.txt && \
    python setup.py install

COPY startup.sh /startup.sh

RUN chmod +x /startup.sh

ENTRYPOINT ["/startup.sh"]
