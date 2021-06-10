##### BASE IMAGE #####
FROM elixircloud/foca:latest


##### METADATA ##### 

LABEL software="Broker"
LABEL software.description="Broker is a decoupled, publish-subscribe-based continuous integration (CI) and continuous delivery (CD) microservice that allows developers to notify deploments of available updates."
LABEL software.website="https://github.com/akash2237778/Broker"
LABEL software.license="https://spdx.org/licenses/Apache-2.0"
LABEL maintainer="akash2237778@gmail.com"
LABEL maintainer.organisation="ELIXIR Cloud & AAI"


## Copy remaining app files
COPY ./ /app

## Install app
RUN cd /app \
  && python setup.py develop \
  && cd / \
  && chmod g+w /app/broker/api/ \
  && pip install yq \
  && pip install docker \
  && apt-get update \
  && pip install GitPython \
  && apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
  && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
  && echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
  && apt-get update \
  && apt-get install -y docker-ce docker-ce-cli containerd.io

CMD ["bash", "-c", "cd /app/broker; python app.py"]
