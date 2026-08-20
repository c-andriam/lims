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

SERVICE       := senaite
PORT          := 8080
SITE_URL      := http://localhost:$(PORT)/senaite
IMAGE         := docker.io/senaite/senaite:v2.6.0
INSTANCE_DIR  := /home/senaite/senaitelims
ADDON         := senaite.trimeta.samplefields
ADDON_SRC     := $(INSTANCE_DIR)/src/$(ADDON)
ADDON_DIR     := addons/$(ADDON)

# ARGS permet de passer des options au testrunner :
#   make test ARGS="-t test_sample_is_findable_by_code"
ARGS ?=

.PHONY: help debug up down restart logs ps build pull shell status \
        clean fclean re install backup restore redeploy-addon \
        first-setup test test-list test-pure check-engine

check-engine:
	@if [ -z "$(ENGINE)" ]; then \
		echo "ERREUR: ni podman ni docker n'est installe."; exit 1; fi

debug: ## Affiche les outils detectes
	@echo "Outil compose  : $(COMPOSE)"
	@echo "Moteur conteneur: $(if $(ENGINE),$(ENGINE),AUCUN)"

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
	@echo "SENAITE en cours de demarrage -> $(SITE_URL)"

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

redeploy-addon: check-engine ## Recharge l'add-on apres modification dans addons/
	$(ENGINE) exec -i $(SERVICE) bash -c \
		"cd $(INSTANCE_DIR) && buildout -c custom.cfg"
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

test: check-engine ## Lance les tests de l'add-on dans le container
	@echo "Tests de $(ADDON)..."
	@$(ENGINE) exec -i $(SERVICE) bash -c '\
	  cd $(INSTANCE_DIR); \
	  if [ -x bin/test ]; then \
	    RUNNER="bin/test"; \
	  elif [ -x bin/zope-testrunner ]; then \
	    RUNNER="bin/zope-testrunner"; \
	  else \
	    echo "ERREUR: aucun testrunner dans $(INSTANCE_DIR)/bin."; \
	    echo "Ajoute zope.testrunner au buildout, puis relance"; \
	    echo "make redeploy-addon."; \
	    exit 1; \
	  fi; \
	  echo "Runner: $$RUNNER"; \
	  $$RUNNER --test-path=$(ADDON_SRC) -s $(ADDON) $(ARGS)'

test-list: check-engine ## Liste les tests sans les executer
	$(MAKE) test ARGS="--list-tests"

test-pure: ## Tests de logique pure, sans container (instantane)
	@python $(ADDON_DIR)/senaite/trimeta/samplefields/tests/run_pure.py

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
