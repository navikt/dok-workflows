# Felles regler for NAIS-apper

Felles GitHub-regler for NAIS-apper.
Reglene lagres her og håndheves i hvert repo etter manuell utrulling.
Merge av disse filene endrer ikke innstillingene i GitHub.

## Innhold

| Fil | Formål |
|---|---|
| `fellesregler.yml` | Regler, bypass, Actions-policy og token-innstillinger |
| `repoer.yml` | Repoer, påkrevde checks, prod-workflows, tagmønstre og automerge-valg |
| `../scripts/forvaltning/repoer.py` | Felles innlesing, validering og repo-utvalg, uten API-kall |
| `../scripts/forvaltning/oppdater-regler.py` | Validerer og oppdaterer innstillinger via `gh api` |
| `../.github/workflows/oppdater-regler.yml` | Manuelt startet utrulling av regler |
| `../.github/workflows/automerge-repositories.yml` | Sentral automerge, foreløpig sperret |

## Hvor endres reglene?

Endre regler og bypass i `fellesregler.yml`, og repo-spesifikke valg i
`repoer.yml`. Reglenes `name` bruker navn fra GitHub, som
**Require status checks to pass before merging**. Dette er bare etiketter;
`type` og `parameters` sendes til API-et. Selve ruleset-navnet, som
`dok-quality`, sendes også.

Skriptet fyller inn disse:

| Plassholder | Kilde |
|---|---|
| `${required_checks}` | Repoets checks i `repoer.yml` |
| `${prod_workflows}` | Repoets prod-workflow-stier i `repoer.yml` |
| `${team_id}` | Miljøvariabelen `POLICY_TEAM_ID` |
| `${automerge_app_id}` | Miljøvariabelen `AUTOMERGE_APP_ID` |

Branch-reglene gjelder default branch. Tag-reglene bruker repoets `release_tags`.
Ukjente felter avvises.

## Regler som opprettes

Dette er reglene i `fellesregler.yml`. Eksisterende beskyttelse gjelder i tillegg.

| Ruleset | Krav | Bypass |
|---|---|---|
| `dok-baseline` | PR påkrevd, ingen sletting eller force-push | Ingen |
| `dok-quality` | Required checks og oppdatert PR-branch | Teamet, kun via PR |
| `dok-review` | Én teamgodkjenning, ny godkjenning ved endringer | Teamet og automerge-appen, kun via PR |
| `dok-merge` | Begrens oppdateringer av default branch | Teamet og automerge-appen, kun via PR |
| `dok-release-tag-create` | Begrens opprettelse av release-tags | Teamet |
| `dok-release-tag-immutable` | Ingen endring eller sletting av release-tags | Ingen |

Teamet kan omgå checks og godkjenning, men må bruke PR. Automerge-appen kan
omgå godkjenning, ikke kvalitetskravene.

`dok-prod-execution` tillater bare teamet og hendelsen `release` for de oppgitte
prod-workflowene. Workflow-filene må selv bruke `types: [published]`.
`GITHUB_TOKEN` får `read` som standard, og innstillingen for å opprette/godkjenne
PR-er slås av. Jobber må be eksplisitt om skrivetilgang.

Skriptet endrer bare navngitte `dok-`-regler og token-innstillingene.
Manuelle endringer i disse reglene overskrives ved neste utrulling.
Fjerning eller navnebytte i YAML sletter ikke gamle regler i GitHub.

## Engangsoppsett i GitHub

Oppsettet gjøres manuelt:

1. Opprett en privat, organisasjonseid policy-app med `Administration: write`.
   Installer den bare på valgte repoer. `Metadata: read` følger med; webhooks trengs ikke.
2. Opprett en separat automerge-app og installer den på aktuelle repoer for bypass.
   Planlagte rettigheter: `Contents: write`, `Pull requests: write`, `Checks: read`
   og `Commit statuses: read`. Vurder `Workflows: write` for workflow-endringer.
   Ikke gi administrasjonstilgang. Nøkkelen brukes ikke ennå.
3. Begrens skrivetilgang og beskytt default branch i `dok-workflows`.
   Krev gjennomgang av policy, skript, privilegerte workflows og deres avhengigheter.
4. Opprett environmentet `repository-forvaltning`. Tillat bare eksakt default
   branch, ingen tags eller andre branches, **før** privatnøkkelen legges inn.
5. Legg inn disse verdiene i environmentet:

| Navn | Type | Verdi |
|---|---|---|
| `POLICY_APP_CLIENT_ID` | Environment-variabel | Policy-appens client ID, ikke installation ID |
| `POLICY_TEAM_ID` | Environment-variabel | Numerisk ID for `navikt/teamdokumenthandtering` |
| `AUTOMERGE_APP_ID` | Environment-variabel | Automerge-appens numeriske app-ID, ikke client ID eller installation ID |
| `POLICY_APP_PRIVATE_KEY` | Environment-secret | Policy-appens PEM-privatnøkkel |

Kontroller team-/app-ID-ene manuelt; skriptet sjekker bare tallformatet.
Workflowet bruker et kortlivet token per repo. Privatnøkkelen deles ikke med målrepoene.
Bekreft at organisasjonen støtter Actions execution policies og required reviewers.
API-feil stopper kjøringen; skriptet bruker ikke svakere regler som reserve.

## Pilot - Før utrulling til bilag

- Bekreft check-navnet `build / build-feature / Build app` og produsent-ID `15368`
  mot dagens PR-bygg. Verdiene er fra kartleggingen 18. september 2026.
- Kontroller tagmønsteret. `refs/tags/*` dekker Git-taggen `v1.2.3`, men ikke
  `release/v1.2.3`: `*` matcher ikke `/`. Se [GitHubs mønsterregler](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository#using-fnmatch-syntax).
- Gjennomgå klassisk branch protection og arvede regler. Skriptet varsler om dem,
  men fjerner eller analyserer dem ikke. De kan fortsatt blokkere bypass og automerge.
- Bekreft at publisering av release draft gir riktig tag og commit uten generell
  Actions-bypass. Kontroller hvem GitHub regner som aktør ved publisering og reruns,
  og at teamgodkjenning dekker både rotfiler og underkataloger.
- Fjern `p` fra målrepoets manuelle deploy-workflow når release skal være eneste
  etablerte prodsettingsflyt. Knytt release-tag til godkjent main-bygg og image-digest,
  også ved rollback. Skriptet endrer ikke workflow-filer.

**Begrensning:** Actions-policyen begrenser kjøring, ikke publisering av release
mot en eksisterende tag. En med skrivetilgang kan lage alternative workflow-stier
utenfor policyen. Dette er en akseptert restrisiko; NAIS-håndhevingen er ikke bekreftet.

## Kjør utrulling fra GitHub Actions

Gjennomgå konfigurasjonen og eksisterende beskyttelse først.
Endringen må finnes på default branch. **Vent med utrulling til sentral automerge
er klar.** Dette er en forutsetning for innføring, ikke en sperre i skriptet.

1. Åpne **Actions → Oppdater repository-regler → Run workflow**.
2. Velg default branch og `bilag`.
3. Start workflowet og les resultatet i loggen. **Endringene utføres direkte.**

Reglene tillater ikke merge med dagens `GITHUB_TOKEN`. Bytt til sentral
automerge som del av innføringen, uten en planlagt periode med manuell merge.

`repoer` kan være ett navn, en kommaseparert liste uten mellomrom eller `alle`.
Bare repoer i `repoer.yml` godtas. Repoene behandles ett om gangen;
uendrede regler hoppes over og regel-ID-er gjenbrukes.
Ved feil stoppes utrullingen uten automatisk tilbakeføring. Rett feilen og kjør på nytt.

Før endringer lagres tidligere innstillinger og planlagte endringer.
Workflowet forsøker å laste opp kopien som artifact med sju dagers lagring,
også ved delvis feil. Ingen endringer eller feil før kopiering gir ingen kopi.
Token og privatnøkkel er ikke med. **Behandle kopier og logger som offentlige.**
Private repoer eller sensitiv konfigurasjon krever en annen lagrings-/loggløsning.

## Sentral automerge: klargjort, men sperret

Workflowet kjøres manuelt eller kl. 07:17 UTC mandag–fredag fra default branch.
Det velger repoer med `automerge.aktivert: true`; `bilag` har `false`.
Aktiverte repoer gir foreløpig feil **før tokenopprettelse og merge**.

Undersøkt versjon av `navikt/automerge-dependabot`
(`f3d979a9d48cdf487a832cc156fa4993747c1dc3`) mangler målrepo-valg og forventet
head-SHA ved merge. Før sperren fjernes må en gjennomgått action:

1. Bruke eksplisitt målrepo i alle API-kall uten å forfalske GitHub-konteksten.
2. Verifisere Dependabot-PR og innhold, og binde merge til vurdert head-SHA.
3. Håndtere checks og branchoppdateringer uten bred bypass eller automatisk approval.

Bruk deretter en SHA-pinnet action, eget environment begrenset til default branch
og egen app-nøkkel. Tokenet skal gjelde ett repo uten administrasjonstilgang.
Ikke sjekk ut eller kjør kode fra målrepoets PR.

Versjonsfiltre, alder og unntak ligger i `repoer.yml`. Overfør eventuelle
blackout-perioder, og deaktiver lokal automerge ved overgangen.
Behold vanlige PR-/main-workflows. Bekreft at app-token-merge utløser main-bygg,
dev-deploy og release draft før gamle etterfølgende bygg fjernes.

## Lokal utvikling

Bruk GitHub Actions til utrulling. Lokal validering trenger Python 3, `venv`
og pip, men ingen GitHub-autentisering. Kjør fra repo-roten:

```bash
python3 -m venv .venv
.venv/bin/python scripts/forvaltning/repoer.py --installer-avhengigheter
.venv/bin/python scripts/forvaltning/oppdater-regler.py --valider
```

`PyYAML`-versjonen ligger i `AVHENGIGHETER` øverst i `repoer.py`.
Avhengigheter installeres bare med installasjonsvalget.
`--valider` sjekker konfigurasjonen uten API-kall, ikke GitHubs støtte eller håndheving.
`repoer.py --repo bilag` viser repo-utvalget som JSON; `--automerge` filtrerer
til aktiverte repoer. Begge workflowene bruker dette skriptet til repo-utvalg.
Det leser bare `repoer.yml`; regeldefinisjonene valideres av `oppdater-regler.py`.

Lokal utrulling krever `--apply`, `gh`,
et installation token i `GH_TOKEN` og miljøvariablene `POLICY_TEAM_ID` og
`AUTOMERGE_APP_ID`. `--repo bilag` alene avvises uten API-kall.

## Forslag til fremtidige forbedringer

Dette er utsatt for å holde første versjon enkel:

- Dry-run som viser endringer uten å skrive til GitHub.
- Periodisk rapportering av avvik, uten automatisk retting.
- Automatiske tester av bypass, gjentatt utrulling, feil, sikkerhetskopiering
  og tilgangssperrer, kjørt i et eget PR-workflow uten app-nøkler.

Testene erstatter ikke piloten mot GitHub.
