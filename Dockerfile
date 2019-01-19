FROM selenium/standalone-chrome-debug

USER root

RUN apt-get update && apt-get upgrade -y && apt-get install -y \
	build-essential python-dev python-setuptools python-pip python-smbus \
	libncursesw5-dev libgdbm-dev libc6-dev \
	zlib1g-dev libsqlite3-dev tk-dev \
	libssl-dev \
	libffi-dev

RUN cd /opt/ && wget https://www.python.org/ftp/python/3.7.1/Python-3.7.1.tgz
RUN cd /opt/ && tar -xzf Python-3.7.1.tgz
RUN cd /opt/Python-3.7.1 && ./configure
RUN cd /opt/Python-3.7.1 && make
RUN cd /opt/Python-3.7.1 && make install

RUN pip3 install -U selenium setuptools mitmproxy paho-mqtt asyncio

ADD ./docker/entry_point.sh /opt/bin/entry_point.sh
RUN chmod +x /opt/bin/entry_point.sh
ADD ./docker/run.sh /opt/run.sh
RUN chmod +x /opt/run.sh
ADD ./python/smartrent-bridge.py /opt/smartrent-bridge.py
ADD ./python/smartrent-login.py /opt/smartrent-login.py
