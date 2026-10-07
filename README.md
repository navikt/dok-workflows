# Dok-workflows
Repoet blir brukt av Team Dokumentløysingar og har fylgjande funksjonalitet
- sentral styring av Github rulesets for teamet sine repo. Desse legg føringar for korleis teamet og andre kan interagere med branches og PR-ar. 
- gjenbrukbare Github Actions-workflows som teamet sine appar kan kalle.

## Utrulling av Github rulesets
[Regelstyringsverktøyet](policy/README.md) rullar ut eit sett med reglar (Github rulesets) til repoa definert i [repoer.json](policy/repoer.json).
Reglar som er felles for alle repo er definert i `fellesregler`. Dersom eit repo treng fleire reglar enn desse kan dei leggjast i `tilleggsregler`.

Etter det er gjort ei oppdatering i [policy-mappa](policy) kan ein køyre kommandoen under (på rotnivå) for å oppdatere rulesets i Github-repoa. Merk at Java 25, Maven og `gh` må vere installert:
```bash
./scripts/forvaltning/rull_ut_regler.sh
```

## Tilgjengelege workflows for app
- `build-deploy-feature.yml`: bygg og deploy feature-branch til alle dev-miljø (q*)
- `build-deploy-main.yml`: bygg og deploy main-branch til alle dev-miljø (q*), lag release draft
- `codeql.yml`: statisk analyse av koden med [CodeQL](https://docs.github.com/en/code-security/code-scanning/introduction-to-code-scanning/about-code-scanning-with-codeql) (query pack: `security-extended`)
- `deploy-prod.yml`: deploy image til prod-miljø
- `manual-deploy.yml`: manuell deploy av tag/branch til miljø
- `automerge-dependabot-pr.yml`: automatisk merge av Dependabot-PR

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
