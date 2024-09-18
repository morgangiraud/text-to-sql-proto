# Default
all: test
.PHONY: all

OS := $(shell uname | tr '[:upper:]' '[:lower:]')
CURRENT_DIR=$(shell pwd)
PROJECT_NAME="text-to-sql-proto"

ifeq (,$(shell which conda))
HAS_CONDA=False
else
HAS_CONDA=True
endif

###
# Package
###
install:
ifeq (True,$(HAS_CONDA))
	@echo ">>> Detected conda, creating conda environment."
	conda env create -f environment_$(OS).yml
	@echo ">>> Conda env created."
else
	@echo ">>> Please install conda first"
endif

## Export conda environment
export_env:
ifeq (True,$(HAS_CONDA))
	@echo ">>> Detected conda, exporting conda environment."
	conda env export -n $(PROJECT_NAME) | grep -v "^prefix: " > environment_$(OS).yml

	@echo ">>> Conda env exported."
else
	@echo ">>> Please install conda first"
endif

.PHONY: install update_env export_env

##
# CI
###
lint:
	ruff check .

lint-fix:
	ruff check . --fix

lint-fix-unsafe:
	ruff check . --fix --unsafe-fixes

format:
	ruff format .


.PHONY: lint lint-fix lint-fix-unsafe format
