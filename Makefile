.PHONY: all install list test version


PACKAGE := $(shell grep '^PACKAGE =' setup.py | cut -d "'" -f2)
VERSION := $(shell head -n 1 $(PACKAGE)/VERSION)

all: list

install:
	pip install --upgrade -e .[develop]
		
list:
	@grep '^\.PHONY' Makefile | cut -d' ' -f2- | tr ' ' '\n'

test:
	bash ./tools/generate_key_pair.sh
	pylama $(PACKAGE)
	PRIVATE_KEY=`cat private.pem` tox

version:
	@echo $(VERSION)
