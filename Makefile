VENV = ./.venv
PYTHON = ${VENV}/bin/python
PIP = ${VENV}/bin/pip
OPTS = --config ./conf/mqttstatus.yaml

run:
	${PYTHON} bin/mqttstatus -v ${OPTS}

setup:
	/usr/bin/python3 -m venv .venv
	${PIP} install -r requirements.txt

install: setup
	mkdir -p /opt/mqttstatus
	cp -r . /opt/mqttstatus

clean:
	rm -rf ./.venv

