###
#
# For those python dependencies that require gcc, we are currently using a multi-stage build approach
# as the base image does not have gcc (and other build tools) in it.
#
# An alternate approach would be to build wheels for each of these modules and place the wheels
# on our internal pypi
#
###
# FROM python:3.6.5 asbuilder

# ADD pip.conf /root/.pip/pip.conf
# ADD requirements.txt /requirements.txt
# ADD requirements-dev.txt /requirements-dev.txt
# RUN pip install -r /requirements-dev.txt

FROM resero/docker-python-node:p3.6.8-n8.15.1-slim-stretch

RUN yarn add puppeteer \
    && yarn cache clean

ENV NODE_PATH="/node_modules"

#RUN groupadd -r pptruser && useradd -r -g pptruser -G audio,video pptruser \
#    && mkdir -p /home/pptruser/Downloads \
#    && chown -R pptruser:pptruser /home/pptruser


# install vim, less and locals, + puppeteer/chrome dependencies
# set up /user-home (which will be mounted from the host os) and symlinks that
# will be used to preserve .bash_history and .python_history across lanista shell
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
        libappindicator1 \
        libasound2 \
        libatk1.0-0 \
        libc6 \
        libcairo2 \
        libcups2 \
        libdbus-1-3 \
        libexpat1 \
        libfontconfig1 \
        libgcc1 \
        libgconf-2-4 \
        libgdk-pixbuf2.0-0 \
        libglib2.0-0 \
        libgomp1 \
        libgtk-3-0 \
        libnspr4 \
        libnss3 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libstdc++6 \
        liburi-encode-perl \
        libx11-6 \
        libx11-xcb1 \
        libxcb1 \
        libxcomposite1 \
        libxcursor1 \
        libxdamage1 \
        libxext6 \
        libxfixes3 \
        libxi6 \
        libxrandr2 \
        libxrender1 \
        libxss1 \
        libxtst6 \
        locales \
        netcat \
        privoxy \
        tor \
        torsocks \
        ttf-freefont \
        vim \
        wget \
        xdg-utils \
        build-essential \
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

# COPY --from=builder /usr/local /usr/local

# instead of apt-get install lsb-release, which has a dependency on python3 which isn't satisfied by the
# python.org version of python we have installed, we are just going to drop lsb_release into the image
COPY ./lsb_release /usr/bin/

ADD pip.conf /root/.pip/pip.conf
ADD requirements.txt /requirements.txt
ADD requirements-dev.txt /requirements-dev.txt
RUN pip install -r /requirements-dev.txt && rm -rf /tmp/*

WORKDIR /workdir
RUN mkdir -p /output
