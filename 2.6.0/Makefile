.DEFAULT_GOAL := help

# Détection automatique de l'outil compose disponible
COMPOSE := $(shell \
	if command -v podman-compose >/dev/null 2>&1; then echo "podman-compose"; \
	elif docker compose version >/dev/null 2>&1; then echo "docker compose"; \
	elif command -v docker-compose >/dev/null 2>&1; then echo "docker-compose"; \
	else echo "echo 'ERREUR: aucun outil compose trouve (podman-compose / docker compose)' && false #"; fi)

SERVICE       := senaite
PORT          := 8080
SITE_URL      := http://localhost:$(PORT)/senaite

.PHONY: help up down restart logs ps build pull shell status clean fclean re install backup restore

debug: ## Affiche l'outil compose détecté
	@echo "Outil compose utilise : $(COMPOSE)"

redeploy-addon: ## Recharge l'add-on trimeta (apres modif dans addons/) sans tout recreer
	podman exec -i $(SERVICE) bash -c "cd /home/senaite/senaitelims && buildout -c custom.cfg"
	$(MAKE) restart
	@echo "Add-on redeploye. Verifie les logs avec: make logs"

first-setup: ## Premiere installation complete sur une nouvelle machine (git clone puis make first-setup)
	@echo "=== Installation initiale SENAITE + add-on Trimeta ==="
	$(MAKE) install
	@echo "Attente du demarrage (30s)..."
	@sleep 30
	$(MAKE) redeploy-addon
	@echo "=== Termine. Verifie sur http://localhost:$(PORT)/senaite ==="

help: ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

pull: ## Télécharge l'image senaite:2.6.0
	$(COMPOSE) pull

up: ## Démarre SENAITE en arrière-plan
	$(COMPOSE) up -d
	@echo "SENAITE en cours de démarrage -> $(SITE_URL)"

install: pull up ## Pull + up en une commande

down: ## Arrête et supprime les containers (garde les volumes)
	$(COMPOSE) down

restart: down up ## Redémarre proprement

logs: ## Suit les logs en direct
	@if command -v podman >/dev/null 2>&1 && ! command -v docker >/dev/null 2>&1; then \
		podman logs -f $(SERVICE); \
	else \
		docker logs -f $(SERVICE); \
	fi

ps: ## Liste les containers du projet
	$(COMPOSE) ps

status: ## Vérifie l'état de santé du container
	@docker inspect --format='{{.State.Status}} ({{.State.Health.Status}})' $(SERVICE) 2>/dev/null || echo "Container non lancé"

shell: ## Ouvre un shell dans le container
	docker exec -it $(SERVICE) /bin/bash

backup: ## Sauvegarde le volume de données
	docker run --rm -v senaite-data:/data -v $(PWD)/backups:/backup \
		alpine tar czf /backup/senaite-data-$$(date +%Y%m%d-%H%M%S).tar.gz -C /data .
	@echo "Backup créé dans ./backups/"

restore: ## Restaure le dernier backup (usage: make restore FILE=backups/xxx.tar.gz)
	docker run --rm -v senaite-data:/data -v $(PWD)/backups:/backup \
		alpine tar xzf /backup/$(notdir $(FILE)) -C /data

clean: down ## Supprime containers ET volumes (perte de données !)
	$(COMPOSE) down -v

fclean: clean ## Nettoyage complet : containers, volumes, images locales
	docker rmi senaite/senaite:2.6.0 2>/dev/null || true

re: fclean install ## Reconstruction complète depuis zéro
