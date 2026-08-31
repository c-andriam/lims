.DEFAULT_GOAL := help

# Detection automatique de l'outil compose disponible
COMPOSE := $(shell \
	if command -v podman-compose >/dev/null 2>&1; then echo "podman-compose"; \
	elif docker compose version >/dev/null 2>&1; then echo "docker compose"; \
	elif command -v docker-compose >/dev/null 2>&1; then echo "docker-compose"; \
	else echo "echo 'ERREUR: aucun outil compose trouve (podman-compose / docker compose)' && false #"; fi)

# Detection du moteur de conteneur, utilise pour exec / logs / rmi.
# Avant, certaines cibles utilisaient podman et d'autres docker en dur:
# sur une machine n'ayant que l'un des deux, la moitie des cibles
# echouait.
ENGINE := $(shell \
	if command -v podman >/dev/null 2>&1; then echo "podman"; \
	elif command -v docker >/dev/null 2>&1; then echo "docker"; \
	else echo ""; fi)

# Interpreteur de l'HOTE, pour les tests qui ne passent pas par le
# container. Les distributions recentes ne fournissent plus de commande
# `python` tout court: on cherche python3 d'abord.
PYTHON        := $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null)

SERVICE       := senaite
# Configuration propre a cette machine, lue depuis 2.6.0/.env
# (non versionne, voir .env.example). Ordre de priorite:
#   1. la ligne de commande   make up PORT=8081
#   2. le fichier .env        SENAITE_PORT=8081
#   3. la valeur par defaut   8080
#
# ATTENTION: SENAITE_PORT doit etre exporte APRES la lecture de .env.
# Exporte inconditionnellement a 8080, il ecraserait le .env, puisque
# l'environnement l'emporte sur le fichier pour compose.
ENV_PORT      := $(shell sed -n 's/^SENAITE_PORT=//p' .env 2>/dev/null | tail -1)
ENV_HOST      := $(shell sed -n 's/^SENAITE_HOST=//p' .env 2>/dev/null | tail -1)

PORT          ?= $(if $(ENV_PORT),$(ENV_PORT),8080)
HOST          ?= $(if $(ENV_HOST),$(ENV_HOST),localhost)

export SENAITE_PORT := $(PORT)
SITE_URL      := http://$(HOST):$(PORT)/senaite
IMAGE         := docker.io/senaite/senaite:v2.6.0
INSTANCE_DIR  := /home/senaite/senaitelims
ADDON         := senaite.trimeta.samplefields
ADDON_SRC     := $(INSTANCE_DIR)/src/$(ADDON)
ADDON_DIR     := addons/$(ADDON)

# ARGS permet de passer des options au testrunner :
#   make test ARGS="-t test_sample_is_findable_by_code"
ARGS ?=

.PHONY: help debug up down restart logs ps pull shell status \
        clean fclean re install backup restore redeploy-addon \
        first-setup test test-list test-pure check-engine fix-perms doctor require-running test-env impress-info dashboard-info sync

check-engine:
	@if [ -z "$(ENGINE)" ]; then \
		echo "ERREUR: ni podman ni docker n'est installe."; exit 1; fi

debug: ## Affiche les outils detectes
	@echo "Outil compose  : $(COMPOSE)"
	@echo "Moteur conteneur: $(if $(ENGINE),$(ENGINE),AUCUN)"
	@echo "Python hote     : $(if $(PYTHON),$(PYTHON),AUCUN)"
	@echo "Adresse publiee : $(SITE_URL)"
	@echo "Source du port  : $(if $(ENV_PORT),.env,defaut)"

help: ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------
# Cycle de vie
# ---------------------------------------------------------------------

pull: ## Telecharge l'image senaite v2.6.0
	$(COMPOSE) pull

up: ## Demarre SENAITE en arriere-plan
	$(COMPOSE) up -d
	@ENGINE=$(ENGINE) SERVICE=$(SERVICE) PORT=$(PORT) sh scripts/require-running.sh
	@echo "SENAITE demarre -> $(SITE_URL)"

install: pull up ## Pull + up en une commande

down: ## Arrete et supprime les containers (garde les volumes)
	$(COMPOSE) down

restart: down up ## Redemarre proprement

logs: check-engine ## Suit les logs en direct
	$(ENGINE) logs -f $(SERVICE)

ps: ## Liste les containers du projet
	$(COMPOSE) ps

status: check-engine ## Verifie l'etat du container
	@$(ENGINE) inspect --format='{{.State.Status}}' $(SERVICE) 2>/dev/null \
		|| echo "Container non lance"

shell: check-engine ## Ouvre un shell dans le container
	$(ENGINE) exec -it $(SERVICE) /bin/bash

# ---------------------------------------------------------------------
# Add-on
# ---------------------------------------------------------------------

redeploy-addon: require-running ## Recharge l'add-on apres modification dans addons/
	$(ENGINE) exec -i $(SERVICE) bash -c \
		"cd $(INSTANCE_DIR) && buildout -c custom.cfg"
	@ENGINE=$(ENGINE) TARGET=addons QUIET=1 sh scripts/fix-perms.sh
	$(MAKE) restart
	@echo ""
	@echo "Add-on redeploye. Verifie les logs avec: make logs"
	@echo ""
	@echo "IMPORTANT si le profil n'est pas encore installe :"
	@echo "  $(SITE_URL)/prefs_install_products_form"
	@echo "  -> installer 'SENAITE Trimeta - champs personnalises'"
	@echo "Si l'add-on etait deja installe dans une version anterieure :"
	@echo "  $(SITE_URL)/portal_setup/manage_upgrades"
	@echo "  -> jouer les etapes de mise a jour de $(ADDON)"

first-setup: ## Premiere installation complete sur une nouvelle machine
	@echo "=== Installation initiale SENAITE + add-on Trimeta ==="
	$(MAKE) install
	@echo "Attente du demarrage (30s)..."
	@sleep 30
	$(MAKE) redeploy-addon
	@echo "=== Termine. Verifie sur $(SITE_URL) ==="

# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------

test: require-running ## Lance les tests de l'add-on dans le container
	@echo "Tests de $(ADDON)..."
	@$(ENGINE) exec -i $(SERVICE) bash -c '\
	  cd $(INSTANCE_DIR); \
	  if [ -x bin/test ]; then \
	    RUNNER="bin/test"; \
	  elif [ -x bin/zope-testrunner ]; then \
	    RUNNER="bin/zope-testrunner"; \
	  else \
	    echo "ERREUR: aucun testrunner dans $(INSTANCE_DIR)/bin."; \
	    echo "Lance 'make test-env' pour inventorier ce qui"; \
	    echo "est disponible dans le container."; \
	    echo ""; \
	    echo "En attendant, 'make test-pure' tourne sans container"; \
	    echo "et couvre 66 tests de logique pure."; \
	    exit 1; \
	  fi; \
	  echo "Runner: $$RUNNER"; \
	  $$RUNNER --test-path=$(ADDON_SRC) -s $(ADDON) $(ARGS)'

impress-info: require-running ## Inventorie senaite.impress (prepare le gabarit COA)
	@ENGINE=$(ENGINE) SERVICE=$(SERVICE) INSTANCE_DIR=$(INSTANCE_DIR) sh scripts/impress-info.sh

dashboard-info: require-running ## Inventorie l'API de listing (prepare le tableau de bord)
	@ENGINE=$(ENGINE) SERVICE=$(SERVICE) INSTANCE_DIR=$(INSTANCE_DIR) sh scripts/dashboard-info.sh

test-env: require-running ## Inventorie ce qui permet de lancer les tests
	@ENGINE=$(ENGINE) SERVICE=$(SERVICE) INSTANCE_DIR=$(INSTANCE_DIR) sh scripts/test-env.sh

test-list: require-running ## Liste les tests sans les executer
	$(MAKE) test ARGS="--list-tests"

test-pure: ## Tests de logique pure, sans container (instantane)
	@if [ -z "$(PYTHON)" ]; then \
	  echo "ERREUR: aucun interpreteur python sur l'hote."; \
	  echo "Installe python3, ou lance les tests dans le"; \
	  echo "container avec 'make test'."; \
	  exit 1; \
	fi
	@$(PYTHON) $(ADDON_DIR)/senaite/trimeta/samplefields/tests/run_pure.py

require-running: check-engine
	@ENGINE=$(ENGINE) SERVICE=$(SERVICE) PORT=$(PORT) sh scripts/require-running.sh

doctor: ## Etat des lieux: containers, ports, volumes, droits, add-on
	@ENGINE=$(ENGINE) SERVICE=$(SERVICE) PORT=$(PORT) ADDON_DIR=addons sh scripts/doctor.sh

sync: ## Recupere les dernieres modifications, droits d'abord
	@# L'ordre compte: un git pull bute sur les fichiers que le
	@# container s'est appropries. On reprend la main avant.
	@ENGINE=$(ENGINE) TARGET=addons sh scripts/fix-perms.sh
	@git -C .. pull

fix-perms: ## Repare les droits sur addons/ apres un buildout en container
	@ENGINE=$(ENGINE) TARGET=addons sh scripts/fix-perms.sh

# ---------------------------------------------------------------------
# Sauvegarde / restauration
# ---------------------------------------------------------------------

backup: check-engine ## Sauvegarde le volume de donnees
	@ENGINE=$(ENGINE) SERVICE=$(SERVICE) sh scripts/backup.sh

restore: check-engine ## Restaure (FILE=backups/x.tar.gz CONFIRM=yes)
	@ENGINE=$(ENGINE) SERVICE=$(SERVICE) FILE="$(FILE)" CONFIRM="$(CONFIRM)" sh scripts/restore.sh

# ---------------------------------------------------------------------
# Nettoyage
# ---------------------------------------------------------------------

clean: down ## Supprime containers ET volumes (perte de donnees !)
	$(COMPOSE) down -v

fclean: clean check-engine ## Nettoyage complet : containers, volumes, image locale
	-$(ENGINE) rmi $(IMAGE)

re: fclean install ## Reconstruction complete depuis zero
