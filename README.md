# Dok-workflows
Fellesrepo med reusuable workflows i Github Actions som Team Dokumentløysingar sine applikasjonar kan kalle.

## Tilgjengelege workflows
- build-and-test: bygg og test Java-kode (mvn verify)
- build-and-publish: bygg og push image til Github Container Registry
- build-and-publish-artifact: bygg og push jar til Github packages (Apache Maven Registry)
- deploy-dev: deploy image til dev-fss
- deploy-prod: deploy image til prod-fss
- release-drafter: opprett draft release før prodsetjing

## Døme på bruk av reusable workflows
Alle døma under tek i bruk reusable workflows frå dette repoet.

### Build and publish
```
name: Build and publish to ghcr

on:
  push:
    branches-ignore:
      - main

jobs:
  build:
    uses: navikt/dok-workflows/.github/workflows/build-and-publish.yaml@main
    with:
      IMAGE: ghcr.io/${{ github.repository }}:${{ github.sha }}
    secrets: inherit
```

### Deploy-dev
I dømet under er det manuell deploy med val av q1 eller q2
```
name: Manual deploy to dev

on:
  workflow_dispatch:
    inputs:
      environment:
        type: choice
        description: Deploy til miljø
        options:
          - q1
          - q2
        required: true

jobs:
  deploy-dev:
    uses: navikt/dok-workflows/.github/workflows/deploy-dev.yaml@main
    with:
      IMAGE: ghcr.io/${{ github.repository }}:${{ github.sha }}
      NAIS_VARIABLES: nais/${{inputs.environment}}-config.json
    secrets: inherit
```

### Deploy-prod
I dømet under skjer release til prod ved 'Publish release' i /releases på Github
```
name: Deploy release to prod

on:
  release:
    types:
      - published

jobs:
  deploy-prod:
    uses: navikt/dok-workflows/.github/workflows/deploy-prod.yaml@main
    with:
      IMAGE: ghcr.io/${{ github.repository }}:${{ github.sha }}
    secrets: inherit
```

### Create release draft
I dømet under skjer det bygg og deploy før laging eller oppdatering av release draft.
```
name: Release Drafter

on:
  push:
    branches:
      - main

jobs:
  build-and-publish:
    uses: navikt/dok-workflows/.github/workflows/build-and-publish.yaml@main
    with:
      IMAGE: ghcr.io/${{ github.repository }}:${{ github.sha }}
    secrets: inherit

  deploy-q1:
    uses: navikt/dok-workflows/.github/workflows/deploy-dev.yaml@main
    needs: build-and-publish
    with:
      IMAGE: ghcr.io/${{ github.repository }}:${{ github.sha }}
      NAIS_VARIABLES: nais/q1-config.json
    secrets: inherit

  update_release_draft:
    uses: navikt/dok-workflows/.github/workflows/release-drafter.yml@main
    needs: deploy-q1
    secrets: inherit
```

For informasjon om workflows relatert til publisering av artifaktar kan ein sjekke ut [melding-virksomhet-dokdistfordeling sitt Github repository](https://github.com/navikt/melding-virksomhet-dokdistfordeling),
sidan den flyten er litt annleis. Reusable workflows som er i bruk der er `build-and-test`, `build-and-publish-artifact` og `release-drafter`.

## Andre spørsmål?
Spørsmål om koda eller prosjektet kan stillast på [Slack-kanalen for \#Team Dokumentløsninger](https://nav-it.slack.com/archives/C6W9E5GPJ)
