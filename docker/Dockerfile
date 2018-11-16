From ubuntu:18.04

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y \
tzdata \
&& rm -rf /var/lib/apt/lists/*

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y \
a2ps  \
build-essential \
cgroup-lite \
cppreference-doc-en-html \
curl \
file \
fp-compiler \
g++ \
gcc \
gettext \
git \
haskell-platform  \
iso-codes \
libcap-dev \
libcups2-dev \
libffi-dev \
libpq-dev \
mono-mcs \
nginx-full  \
openjdk-8-jdk-headless \
php7.2-cli  \
php7.2-fpm \
phppgadmin  \
postgresql  \
postgresql-client  \
python2.7  \
python3-pip \
python3-wheel \
python3.6  \
rustc \
shared-mime-info \
texlive-latex-base  \
vim \
wget \
zip \
&& rm -rf /var/lib/apt/lists/*

RUN wget -qO- https://github.com/cms-dev/cms/releases/download/v1.4.rc1/v1.4.rc1.tar.gz | tar xvz -C /

WORKDIR /cms/

ENV LANG en_US.UTF-8

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y \
python-pip \
python-wheel \
&& rm -rf /var/lib/apt/lists/*

RUN python prerequisites.py -y --as-root install && \
    usermod -a -G cmsuser root && \
    python -m pip install -r requirements.txt && \
    python setup.py install

COPY startup.sh /startup.sh

RUN chmod +x /startup.sh

ENTRYPOINT ["/startup.sh"]
