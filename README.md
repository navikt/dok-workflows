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

### Oppsett

Kopier filene frå  [`/eksempel`](/eksempel) til rotområdet på repoet ein ynskjer at tar i bruk reusable workflows.

Under er ein oversikt på korleis mappestrukturen skal sjå ut.

```

min-app/
├─ .github/
│  ├─ workflows/
│  │  ├─ build-deploy-feature.yml
│  │  ├─ build-deploy-main.yml
│  │  ├─ deploy-prod.yaml
│  ├─ CODEOWNERS
│  ├─ release-drafter.yml
├─ nais/
├─ app/
├─ .gitignore
├─ pom.xml
├─ Dockerfile
├─ README.md
```

## Andre spørsmål?
Spørsmål om koda eller prosjektet kan stillast på [Slack-kanalen for \#Team Dokumentløsninger](https://nav-it.slack.com/archives/C6W9E5GPJ)
