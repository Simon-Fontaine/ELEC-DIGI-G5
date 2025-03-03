.PHONY: help venv install activate

# Variables - Windows paths
PYTHON = python
VENV = venv
BIN = $(VENV)\Scripts
PYTHON_VENV = $(BIN)\python
PIP = $(BIN)\pip
ACTIVATE = $(BIN)\activate.bat

help:
	@echo "Commandes disponibles:"
	@echo "  make venv      - Cree l'environnement virtuel"
	@echo "  make install   - Installe les dependances"
	@echo "  make activate  - Affiche la commande pour activer le venv"

venv:
	$(PYTHON) -m venv $(VENV)
	$(PYTHON_VENV) -m pip install --upgrade pip

install: venv
	$(PIP) install -r requirements.txt

activate:
	@echo "Pour activer l'environnement virtuel, executez la commande suivante:"
	@echo "$(ACTIVATE)"