# Dok-workflows
Fellesrepo med reusuable workflows i Github Actions som Team Dokumentløysingar sine applikasjonar kan kalle.

## Tilgjengelege workflows for app
- `build-dependabot-branch.yml`: unnlat å deploye branches oppretta av dependabot
- `build-deploy-feature.yml`: bygg og deploy feature-branch til alle dev-miljø (q*)
- `build-deploy-main.yml`: bygg og deploy main-branch til alle dev-miljø (q*), lag release draft
- `deploy-prod.yml`: deploy image til prod-miljø
- `codeql.yml`: statisk analyse av koden med [CodeQL](https://docs.github.com/en/code-security/code-scanning/introduction-to-code-scanning/about-code-scanning-with-codeql) (query pack: `security-and-quality`)
- `deploy-manual.yml`: manuell deploy av tag/branch til miljø

## Tilgjengelege workflows for artifakt
- `build-artifact.yml`: bygg artifakt og lag release draft viss det er main/master-branch
- `publish-artifact.yml`: bygg og push jar til Github packages (Apache Maven Registry)

### Oppsett
Kopier fylgjande (calling) workflows til workflows-mappa i repoet ein ynskjer å bruke reusable workflows.
[`/eksempel`](eksempel/.github/workflows/)
Dersom eit prosjekt skal få laga PR frå Dependabot automatisk for avhengigheiter som skal bli oppdatert må også dependabot.yml bli kopiert inn i prosjektet.

Under er ein oversikt på korleis mappestrukturen kan sjå ut i repoet (fss apper).

```
min-app/
├─ .github/
│  ├─ workflows/
│  │  ├─ build-dependabot-branch.yml
│  │  ├─ build-deploy-feature.yml
│  │  ├─ build-deploy-main.yml
│  │  ├─ codeql.yml
│  │  ├─ deploy-manual.yml
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
