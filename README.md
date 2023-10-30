# Dok-workflows
Fellesrepo med reusuable workflows i Github Actions som Team Dokumentløysingar sine applikasjonar kan kalle.

## Tilgjengelege workflows for app
- build-deploy-feature: bygg og deploy feature-branch til alle dev-miljø (q*)
- build-deploy-main: bygg og deploy main-branch til alle dev-miljø (q*), lag release draft
- deploy-prod: deploy image til prod-miljø

## Tilgjengelege workflows for artifakt
- build-artifact: bygg artifakt og lag release draft viss det er main/master-branch
- publish-artifact: bygg og push jar til Github packages (Apache Maven Registry)

### Oppsett
Kopier fylgjande (calling) workflows til rotområdet på repoet ein ynskjer å bruke reusable workflows.
- fss: [`/eksempel/fss`](eksempel/.github/workflows/fss)
- gcp: [`/eksempel/gcp`](eksempel/.github/workflows/gcp)
Dersom eit prosjekt skal få laga PR frå Dependabot automatisk for avhengigheiter som skal bli oppdatert må også dependabot.yml bli kopiert inn i prosjektet.

Under er ein oversikt på korleis mappestrukturen skal sjå ut i repoet (i fss).

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
