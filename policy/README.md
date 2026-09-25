# Felles repo-regler

Et lokalt Java-program sender felles JSON-regler til GitHub via `gh`.
[repoer.json](repoer.json) angir hvilke repoer under `navikt` som oppdateres.

## Regler

Alle regelsett gjelder default branch.

| Regelsett | Krav | Bypass           |
|---|---|------------------|
| [dok-baseline](rulesets/dok-baseline.json) | PR påkrevd. Ingen sletting eller force-push som omskriver historikken. | Ingen            |
| [dok-required-checks](rulesets/dok-required-checks.json) | Påkrevd sjekk: `build / build-feature / Build app`. | Team, kun via PR |
| [dok-require-pr-approval](rulesets/dok-require-pr-approval.json) (valgfritt tillegg) | Minst én godkjenning og code owner-review. Gamle godkjenninger avvises når PR-diffen endres. | Ingen |

Fellesreglene krever ikke godkjenning, løste PR-samtaler eller oppdatert PR-branch.
Alle med nødvendig skrivetilgang kan merge når kravene er oppfylt.
Andre regelsett og klassisk branch protection gjelder i tillegg.

Det tas i bruk med `"tilleggsregler": ["dok-require-pr-approval"]`.
Repoets `CODEOWNERS` bestemmer hvem som må godkjenne.
Tillegget har ingen bypass, heller ikke for administratorer eller automerge.

Verktøyet endrer ikke workflows, automerge, token-rettigheter, tags eller Actions-policyer.

### ID-er i `dok-required-checks`

`actor_id: 3588236` angir teamet `navikt/teamdokumenthandtering`.
Teamet kan merge via pull request selv om den påkrevde sjekken ikke har bestått.
Finn teamets ID slik om den skulle endre seg:

```bash
gh api orgs/navikt/teams/teamdokumenthandtering --jq '.id'
```

`integration_id: 15368` angir at den påkrevde sjekken må komme fra GitHub Actions.

## Kjøring

Du trenger Java 25, Maven, `gh` og administrasjonstilgang til målrepoene.
Gjennomgå repo-listen og reglene. Kjør fra repo-roten:

```bash
./scripts/forvaltning/rull_ut_regler.sh
```

Skriptet finner repo-roten, sjekker `gh auth status`, logger inn ved behov,
bygger JAR-en og starter utrulling. Det avviser argumenter og stopper ved feil.
`GH_TOKEN`/`GITHUB_TOKEN` overstyrer lagret gh-innlogging hvis de er satt.

**Alle repoene i listen endres direkte.**
Ved feil stopper utrullingen. Utførte endringer blir stående uten automatisk tilbakeføring.

Manuell bygging og kjøring fra repo-roten med eksisterende gh-innlogging:

```bash
mvn -f scripts/forvaltning/pom.xml clean verify
java -jar scripts/forvaltning/target/forvaltning.jar
```

## Konfigurasjon og oppdatering

- `repoer.json`: `fellesregler` angir regelsett for alle repoer. `repoer` er en ikke-tom liste med `navn` og valgfrie `tilleggsregler`. Repo-navn oppgis uten `navikt/` og valideres ikke lokalt.
- `rulesets/*.json`: API-innholdet. Filnavnet må være `<name>.json`, med et unikt `dok-`-navn.

Programmet finner eksisterende regelsett etter navn og oppdaterer med `PUT`,
eller oppretter med `POST`. Det innleste og validerte JSON-innholdet sendes
via midlertidige filer med `gh api --input`; endringer i originalfilene under kjøring påvirker ikke utrullingen.
Alle regler lastes opp hver gang, også uendrede. Manuelle endringer i de forvaltede regelsettene overskrives.
Vellykkede API-responser vises i terminalen; feilrespons og stderr fra `gh` vises ikke.

## Begrensninger og opprydding

Programmet sletter ikke regelsett. Navnebytte oppretter et nytt; fjern det gamle manuelt.
Fjerning fra `fellesregler` eller `tilleggsregler` sletter ikke et allerede utrullet regelsett på GitHub.
