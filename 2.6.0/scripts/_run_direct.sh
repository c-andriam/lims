#!/bin/sh
podman exec -i senaite bash -c '\
  cd /home/senaite/senaitelims; \
  if [ -x bin/test ]; then \
    RUNNER="bin/test"; \
  elif [ -x bin/zope-testrunner ]; then \
    RUNNER="bin/zope-testrunner"; \
  else \
    echo "ERREUR: aucun testrunner dans /home/senaite/senaitelims/bin."; \
    echo "Lance '"'"'make test-env'"'"' pour inventorier ce qui"; \
    echo "est disponible dans le container."; \
    echo ""; \
    echo "En attendant, '"'"'make test-pure'"'"' tourne sans container"; \
    echo "et couvre 134 tests de logique pure."; \
    exit 1; \
  fi; \
  echo "Runner: $RUNNER"; \
  $RUNNER --test-path=/home/senaite/senaitelims/src/senaite.trimeta.samplefields -s senaite.trimeta.samplefields'
