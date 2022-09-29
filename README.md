# Dok-workflows
Fellesrepo med reusuable workflows i Github Actions som Team Dokumentløysingar sine applikasjonar kan kalle.

## Tilgjengelege workflows for app
- build-deploy-feature: bygg og deploy feature-branch til alle dev-miljø (q*)
- build-deploy-main: bygg og deploy main-branch til alle dev-miljø (q*), lag release draft
- deploy-prod: deploy image til prod-fss

## Tilgjengelege workflows for artifakt
- build-artifact: bygg artifakt og lag release draft viss det er main/master-branch
- publish-artifact: bygg og push jar til Github packages (Apache Maven Registry)

## Døme på bruk av reusable workflows for app
Alle døma under tek i bruk reusable workflows frå dette repoet.

### build-deploy-feature
```
name: Build, deploy dev feature

on:
  push:
    branches-ignore:
      - main
      - master

jobs:
  build:
    uses: navikt/dok-workflows/.github/workflows/build-deploy-feature.yml@main
    secrets: inherit
```

### build-deploy-main
```
name: Build, deploy dev, draft main

on:
  push:
    branches:
      - main
      - master

jobs:
  build:
    uses: navikt/dok-workflows/.github/workflows/build-deploy-main.yml@main
    secrets: inherit
```

### deploy-prod
I dømet under skjer release til prod ved 'Publish release' i /releases på Github
```
name: Deploy release to prod

on:
  release:
    types:
      - published

jobs:
  deploy-prod:
    uses: navikt/dok-workflows/.github/workflows/deploy-prod.yml@main
    secrets: inherit
```

## Døme på bruk av reusable workflows for artifakt

### build-artifact
```
name: Build and test artifact - create draft if main branch

on:
  push:
    branches:
      - '**'

jobs:
  build-main-and-feature-branch:
    uses: navikt/dok-workflows/.github/workflows/build-artifact.yml@main
    with:
      java-version: '11'
    secrets: inherit
```

### publish-artifact
```
name: Publish artifact

on:
  release:
    types:
      - published

jobs:
  publish-artifact:
    uses: navikt/dok-workflows/.github/workflows/publish-artifact.yml@main
    with:
      java-version: '11'
    secrets: inherit
```

## Andre spørsmål?
Spørsmål om koda eller prosjektet kan stillast på [Slack-kanalen for \#Team Dokumentløsninger](https://nav-it.slack.com/archives/C6W9E5GPJ)
