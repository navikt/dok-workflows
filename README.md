# Dok-workflows
Fellesrepo med gjenbrukbare workflows i GitHub Actions som Team Dokumentløysingar sine applikasjonar kan kalle.

## Felles repository-regler

[Oppsett og bruk](policy/README.md) for sentral forvaltning av branch/tag rulesets
og Actions-policy for NAIS-appar. `bilag` er pilot. Utrulling blir starta manuelt
og utfører endringane direkte; eksisterande workflows blir ikkje erstatta automatisk.
Sentral Dependabot-automerge er klargjord, men sperra til automerge-actionen
støttar trygg køyring mot eit eksplisitt målrepository.
Vent med utrulling til sentral automerge er klar, og byt automerge-flyt ved innføringa.
Dette er ein føresetnad for innføring, ikkje ei sperre i utrullingsskriptet.

## Tilgjengelege workflows for app

Dei gjenbrukbare workflowene ligg i [`.github/workflows/`](.github/workflows/).
Appane brukar eigne caller-workflows, som vist i [`eksempel/`](eksempel/.github/workflows/).

| Gjenbrukbart workflow | Eksempel på caller | Oppgåve |
|---|---|---|
| [`build-deploy-feature-gar.yml`](.github/workflows/build-deploy-feature-gar.yml) | [`build-deploy-feature.yml`](eksempel/.github/workflows/build-deploy-feature.yml) | Bygg feature-branch og deploy til konfigurerte dev-miljø; Dependabot-bygg blir ikkje deploya |
| [`build-deploy-main-gar.yml`](.github/workflows/build-deploy-main-gar.yml) | [`build-deploy-main.yml`](eksempel/.github/workflows/build-deploy-main.yml) | Bygg, deploy til konfigurerte dev-miljø og lag release draft |
| [`codeql.yml`](.github/workflows/codeql.yml) | [`codeql.yml`](eksempel/.github/workflows/codeql.yml) | Statisk analyse av Java/Kotlin med CodeQL og `security-extended` |
| [`deploy-prod-gar.yml`](.github/workflows/deploy-prod-gar.yml) | [`deploy-prod.yml`](eksempel/.github/workflows/deploy-prod.yml) | Deploy image-taggen frå ein publisert release til prod-miljøet `p` |
| [`automerge-dependabot-pr.yml`](.github/workflows/automerge-dependabot-pr.yml) | [`automerge-dependabot-pr.yml`](eksempel/.github/workflows/automerge-dependabot-pr.yml) | Eksisterande repo-lokal Dependabot-automerge med `GITHUB_TOKEN` og etterfølgjande bygg |

Dev-miljø blir funne frå `nais/q*-config.json`. Standard cluster er `dev-fss`
for dev og `prod-fss` for prod; caller-eksempla vel `dev-gcp` og `prod-gcp`.

[`manual-deploy.yml`](eksempel/.github/workflows/manual-deploy.yml) er eit
caller-eksempel, ikkje eit eige gjenbrukbart workflow med same namn. Det brukar
[`deploy-nais-app-with-custom-checkout-gar.yml`](.github/workflows/deploy-nais-app-with-custom-checkout-gar.yml)
til å hente NAIS-konfigurasjon frå valt ref og deploye eit eksisterande image med
den valde build-taggen. Det byggjer ikkje eit nytt image.
Eksemplet tilbyr framleis `p` og `q2`; `p` må fjernast når appen tek i bruk
release som einaste etablerte prodsettingsflyt, slik den nye policyen føreset.

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
│  │  ├─ automerge-dependabot-pr.yml
│  │  ├─ build-deploy-feature.yml
│  │  ├─ build-deploy-main.yml
│  │  ├─ codeql.yml
│  │  ├─ deploy-prod.yaml
│  │  ├─ manual-deploy.yml
│  ├─ CODEOWNERS
│  ├─ dependabot.yml
│  ├─ release-drafter.yml
├─ nais/
├─ app/
├─ .gitignore
├─ pom.xml
├─ Dockerfile
├─ README.md
├─ LICENSE.md
```

## Andre spørsmål?
Spørsmål om koda eller prosjektet kan stillast på [Slack-kanalen for \#Team Dokumentløsninger](https://nav-it.slack.com/archives/C6W9E5GPJ)
