# Utrulling av Github rulesets

Oppdatering av Github rulesets for teamet sine repoer blir gjort av et Java-program som sender felles JSON-regler til
GitHub via `gh`. Filen [repoer.json](repoer.json) angir hvilke `navikt`-repoer som oppdateres.

## Tilgjengelige regelsett

Alle regelsett gjelder default branch (master/main).

| Regelsett                                                                            | Krav                                                                                    | De som kan bypasse kravet |
|--------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|---------------------------|
| [dok-baseline](rulesets/dok-baseline.json)                                           | PR påkrevd. Ingen sletting eller force-push som omskriver historikken.                  | Ingen                     |
| [dok-required-checks](rulesets/dok-required-checks.json)                             | Påkrevd sjekk: `build / build-feature / Build app`.                                     | Teamet                    |
| [dok-require-pr-approval](rulesets/dok-require-pr-approval.json) (valgfritt tillegg) | Minst én godkjenning fra et team-medlem. Dersom PR-en endres må den godkjennes på nytt. | Ingen                     |

Regelsettene i [rulesets](rulesets) vil bli opprettet eller oppdatert i et repo, basert på om et regelsett med samme navn eksisterer fra før. Eksisterende regelsett (med andre navn) vil ikke bli påvirket.
De to regelsettene [dok-baseline](rulesets/dok-baseline.json) og [dok-required-checks](rulesets/dok-required-checks.json) er felles for alle repo.

Majoriteten av teamets repoer har kun `read`-tilgang for andre i Nav. Noen få utvalgte har `write`-tilgang for `NAV IT GitHub users`, som gjør det mulig for andre i Nav å opprette og merge en PR.
For å ha kontroll på kode som kommer utenfra teamet har disse repoene tilleggsreglene [dok-require-pr-approval](rulesets/dok-require-pr-approval.json), 
som krever godkjenning fra et team-medlem (repoets `CODEOWNERS`) for å kunne merge PR-en. For å ta i bruk tilleggsregler, legger en til `"tilleggsregler": ["dok-require-pr-approval"]` i [repoer.json](repoer.json).

### ID-er i `dok-required-checks`

`actor_id: 3588236` angir teamet `navikt/teamdokumenthandtering`.
Dersom teamets ID endres finner en den nye slik:

```bash
gh api orgs/navikt/teams/teamdokumenthandtering --jq '.id'
```

`integration_id: 15368` angir at den påkrevde sjekken må komme fra GitHub Actions.

## Kjøring

Java 25, Maven og `gh` må være installert, og du trenger rollen `admin` for alle repoer i [repoer.json](repoer.json). Kjør følgende kommando på rotnivå:

```bash
./scripts/forvaltning/rull_ut_regler.sh
```

Skriptet finner repo-roten, sjekker `gh auth status` og logger inn ved behov. JAR-en blir bygd, og utrullingen startet. Det avviser argumenter og stopper ved feil.
`GH_TOKEN`/`GITHUB_TOKEN` overstyrer lagret gh-innlogging hvis de er satt.

Ved feil stopper utrullingen, men endringer som allerede er gjort vil ikke bli rullet tilbake.

### Manuell bygging og kjøring ved eksisterende gh-innlogging (kjøres på rotnivå):

```bash
mvn -f scripts/forvaltning/pom.xml clean verify
java -jar scripts/forvaltning/target/forvaltning.jar
```

## Konfigurasjon og oppdatering

- `repoer.json`: `fellesregler` angir regelsett som skal gjelde for alle repoer. `repoer` er en ikke-tom liste med `navn` og valgfrie
  `tilleggsregler`. Repo-navn oppgis uten `navikt/` og valideres ikke lokalt.
- `rulesets/*.json`: API-innholdet. Filnavnet må være `<name>.json`, med et unikt `dok-`-navn.

Programmet finner eksisterende regelsett etter navn og oppdaterer med `PUT`, eller oppretter med `POST`. 
Det innleste og validerte JSON-innholdet sendes via midlertidige filer med `gh api --input`; endringer i originalfilene under kjøring påvirker ikke utrullingen.
Alle regler lastes opp hver gang, også uendrede. Manuelle endringer i de forvaltede regelsettene overskrives.
Vellykkede API-responser vises i terminalen; feilrespons og stderr fra `gh` vises ikke.

## Begrensninger og opprydding

Utrullingen vil aldri slette et regelsett, og kan kun legge til nye eller oppdatere eksisterende. Altså må tidligere utrullede regelsett slettes manuelt bl.a. dersom
- et regelsett bytter navn
- et repo blir fjernet fra [repoer.json](repoer.json)
- et repo får fjernet sine `tilleggsregler`
