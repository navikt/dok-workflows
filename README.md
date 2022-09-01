# Dok-workflows
Fellesrepo med reusuable workflows i Github Actions som Team Dokumentløysingar sine applikasjonar kan kalle.

## Tilgjengelege workflows
- build: bygg og push image til Github Container Registry
- deploy-dev: deploy image til dev-fss
- deploy-prod: deploy image til prod-fss
- release-drafter: opprett draft release før prodsetjing

## Døme på bruk av reusable workflows
Alle døma under tek i bruk reusable workflows frå dette repoet.

### Build
```
name: Build and push

on:
  push:
    branches-ignore:
      - main

jobs:
  build:
    uses: navikt/dok-workflows/.github/workflows/build.yaml@main
    with:
      IMAGE: ghcr.io/${{ github.repository }}:${{ github.sha }}
    secrets: inherit
```

### Deploy-dev
I dømet under er det manuell deploy med val av q1 eller q2
```
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
      NAIS_VARIABLES: nais/p-config.json
    secrets: inherit
```

### Create release draft
I dømet under skjer det også bygg og deploy
```
name: Release Drafter

on:
  push:
    # branches to consider in the event; optional, defaults to all
    branches:
      - main

jobs:
  build:
    uses: navikt/dok-workflows/.github/workflows/build.yaml@main
    with:
      IMAGE: ghcr.io/${{ github.repository }}:${{ github.sha }}
    secrets: inherit

  deploy-q1:
    uses: navikt/dok-workflows/.github/workflows/deploy-dev.yaml@main
    needs: build
    with:
      IMAGE: ghcr.io/${{ github.repository }}:${{ github.sha }}
      NAIS_VARIABLES: nais/q1-config.json
    secrets: inherit

  update-release-draft:
    uses: navikt/dok-workflows/.github/workflows/release-drafter.yml@main
    needs: deploy-q1
    secrets: inherit
```