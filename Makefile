PROJECT=reviewqueue

PYHOME=.venv/bin
PYTHON=$(PYHOME)/python


all: test

clean:
	rm -rf MANIFEST dist/* $(PROJECT).egg-info .coverage
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete
	rm -rf .venv

test: .venv
	@echo Starting tests...
	$(PYHOME)/tox

.venv:
	# install deps for theblues (https://github.com/juju/theblues#installation)
	#sudo add-apt-repository ppa:yellow/ppa -y
	#sudo apt-get update -qy
	#sudo apt-get install -qy libmacaroons0 python-macaroons libsodium13
	# create virtualenv, install app deps
	sudo apt-get install -qy python-virtualenv libpq-dev python-dev
	virtualenv --never-download .venv

	$(PYHOME)/pip install --no-index -f deps/ -r requirements.txt
	$(PYHOME)/pip install --no-index -f deps/ -e .

serve: .venv
	$(PYHOME)/initialize_db development.ini
	$(PYHOME)/pserve --reload development.ini


.PHONY: clean
