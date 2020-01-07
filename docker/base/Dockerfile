###
#
# For those python dependencies that require gcc, we are currently using a multi-stage build approach
# as the base image does not have gcc (and other build tools) in it.
#
# An alternate approach would be to build wheels for each of these modules and place the wheels
# on our internal pypi
#
FROM resero/docker-python-node:p3.6.8-n8.15.1-slim-stretch

# install vim, less and locales
# set up /user-home (which will be mounted from the host os) and symlinks that
# will be used to preserve .bash_history and .python_history across shell
# invocations
RUN apt-get update && apt-get install -y --allow-unauthenticated --no-install-recommends \
        ca-certificates \
        distro-info-data \
        fonts-liberation \
        fonts-ipafont-gothic \
        fonts-wqy-zenhei \
        fonts-thai-tlwg \
        fonts-kacst \
        gconf-service \
        graphviz \
        less \
        libgcc1 \
        locales \
        netcat \
        privoxy \
        vim \
        wget \
        git \
        build-essential \
        lsb-release \
    && apt-get clean \
    && rm -rf /var/tmp/* /tmp/* /var/lib/apt/lists/* \
    && echo "en_US.UTF-8 UTF-8" > /etc/locale.gen \
    && locale-gen \
    && mkdir /user-home \
    && touch /user-home/.bash_history \
    && touch /user-home/.python_history \
    && ln -s /user-home/.bash_history /root/.bash_history \
    && ln -s /user-home/.python_history /root/.python_history

ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8

ADD pip.conf /root/.pip/pip.conf
ADD requirements.txt /requirements.txt
ADD requirements-dev.txt /requirements-dev.txt
RUN pip install -r /requirements-dev.txt && rm -rf /tmp/*

WORKDIR /workdir
RUN mkdir -p /output
