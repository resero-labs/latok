FROM rappdw/docker-ds

RUN chmod 1777 /tmp \
    && apt-get update \
    && apt-get install -y --allow-unauthenticated --no-install-recommends \
        gcc \
        linux-headers-4.9-amd64 \
        libc6-dev \
        libgtk-3-0 \
        libsm6 \
    && apt-get clean \
    && rm -rf /var/tmp/* /tmp/* /var/lib/apt/lists/*

ADD pip.conf /root/.pip/pip.conf
ADD requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt \
    && pip install pandas-ml

RUN usermod -u 2005 node; \
    groupmod -g 2005 node; \
    usermod -u 1000 jovyan

ADD docker/notebook/entrypoint docker-entrypoint.sh
