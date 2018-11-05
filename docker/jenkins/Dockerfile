FROM python:3.6.5
ARG DEBIAN_FRONTEND=noninteractive

RUN chmod 1777 /tmp \
    && apt-get update && apt-get install -y --allow-unauthenticated \
        git curl \
    && apt-get clean \
    && rm -rf /var/tmp /tmp /var/lib/apt/lists/* \
    && mkdir -p /var/tmp /tmp \
    && mkdir /workdir

# Install the docker client
RUN curl -sSL -o /tmp/docker.tgz https://get.docker.com/builds/Linux/x86_64/docker-latest.tgz \
    && tar -xvf /tmp/docker.tgz \
    && mv docker/* /usr/local/bin \
    && rm -rf docker \
    && rm /tmp/docker.tgz

# Install kubectl (v1.11.0)
RUN curl -sSL -o /tmp/kubectl https://storage.googleapis.com/kubernetes-release/release/v1.11.0/bin/linux/amd64/kubectl \
    && chmod +x /tmp/kubectl \
    && mv /tmp/kubectl /usr/local/bin

# Install heptio-authenticator-aws
RUN curl -o /tmp/heptio-authenticator-aws https://amazon-eks.s3-us-west-2.amazonaws.com/1.10.3/2018-06-05/bin/linux/amd64/heptio-authenticator-aws \
    && chmod +x /tmp/heptio-authenticator-aws \
    && mv /tmp/heptio-authenticator-aws /usr/local/bin

# Install docker utils
RUN pip install dockerutils==1.1.5 versioneer==0.18 awscli==1.15.3 poetry==0.11.5 poetry-setup==0.3.4

WORKDIR /workdir
ENV USE_HTTPS YES
