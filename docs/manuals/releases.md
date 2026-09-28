# Releases: taggen, publiceren en pinnen

!!! note "Voor wie / wanneer"
    **Voor:** beheerders van VSA-tooling en van consumer-repo’s (bibliotheek,
    VSA-demo, …).
    **Wanneer:** je wilt een vaste tooling-versie uitgeven, of een consumer
    vastzetten op die versie i.p.v. `main`.
    **Niet:** productpipelines of Hugo-site-CI van de bibliotheek — die horen
    in de consumer-repo; zie
    [Ownership](../guides/reuse-vsa-tooling.md#ownership-tooling-vs-consumer).

**Antwoord in het kort:** in VSA-tooling zet je een **git-tag** (en bij
voorkeur een GitHub Release) op `main`. In de bibliotheek (en andere
consumers) **pin** je die tag in de `pip install`-URL en in
`uses: …@TAG` voor herbruikbare workflows. Zo schuift CI niet mee met elke
push op `main`.

## Begrippen

| Term               | Betekenis                                                                                                    |
| ------------------ | ------------------------------------------------------------------------------------------------------------ |
| **Tag**            | Vaste snapshot van de VSA-tooling-repo (`0.2.0`). Pip en Actions kunnen die ref gebruiken.                   |
| **GitHub Release** | Pagina bij de tag (titel, release notes, optioneel artifacts). Handig voor mensen; pip heeft hem niet nodig. |
| **Pinnen**         | Consumer gebruikt `@0.2.0` i.p.v. `@main`, zodat builds reproduceerbaar blijven.                             |
| **`@main`**        | Altijd de tip van de default branch. Handig tijdens ontwikkeling; riskant voor productie-CI.                 |

## Versienummers (conventie)

Gebruik **semver zonder `v`-prefix**: `0.1.0`, `0.2.0`, `1.0.0`.

- De git-tag heet precies zo (`0.2.0`), niet `v0.2.0`.
- Zelfde string in `pyproject.toml` onder `[project] version`.
- Pip-URL: `…VSA-tooling.git@0.2.0`.
- Workflow-pin: `uses: orthodox-ronl/VSA-tooling/.github/workflows/….yml@0.2.0`.

Bestaande tag: `0.1.0` (juni 2026, pre-release). Nieuwe features ná die tag
(zoals `mvsa pdf`, `--layout`, `--bibliotheek-id`) zitten **niet** in `0.1.0`;
gebruik daarvoor `main` tot er een nieuwere tag is, of maak die tag (stappen
hieronder).

---

## Deel A — Release maken in VSA-tooling

Doe dit alleen op een schone, groene `main`.

### A1. Checklist vóór de tag

1. Alle gewenste PR’s zijn gemerged op `main`.
2. CI op `main` is groen (pytest / VSA CI / docs).
3. Je hebt afgesproken welk versienummer het wordt (bijv. `0.2.0`).
4. Release notes: kort wat consumers merken (CLI-commando’s, breaking changes).

### A2. Versie in de repo zetten

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
git checkout main
git pull
```

Zet in `pyproject.toml` het veld `version` op het nieuwe nummer (zelfde als de
tag). Commit die wijziging op `main` (apart PR of directe commit volgens jullie
gewoonte), push, wacht tot CI groen is.

### A3. Lokaal smoke (aanbevolen)

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
test
vsa --version
```

Optioneel: handmatige workflow **Release artifacts** op GitHub
(`.github/workflows/release-artifacts.yml`) met input `version` = het
versienummer. Die bouwt wheel/sdist en een consumer-minimal smoke-artifact;
die workflow **maakt zelf geen git-tag**.

### A4. Tag zetten en pushen

Vervang `0.2.0` overal door het echte nummer.

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
git checkout main
git pull
git tag 0.2.0
git push origin 0.2.0
```

Controle:

```cmd
git tag -l 0.2.0
gh release list --limit 5
```

### A5. GitHub Release aanmaken

```cmd
cd /d C:\Git\orthodox-ronl\VSA-tooling
gh release create 0.2.0 --title "0.2.0" --notes-file -
```

Typ de release notes in het editorvenster dat `gh` opent, of gebruik
`--notes "…"` voor een korte tekst. Voorbeeld-inhoud:

- `mvsa pdf` / layoutprofielen `partituur` en `plain`
- `--bibliotheek-id` voor colofon
- breaking changes of verwijderde vlaggen (als die er zijn)

### A6. Na de release

- Vermeld in de bibliotheek-chat / issue dat tag `0.2.0` klaar is om te pinnen.
- Optioneel: update voorbeelden in
  [Hergebruik](../guides/reuse-vsa-tooling.md) als die nog een oud nummer tonen.

**Tag per ongeluk verkeerd?** Alleen herschrijven als de tag **nog niet** door
consumers wordt gebruikt, en alleen met expliciete afspraak (`git push --force`
op tags is destructief). Liever een nieuwe patch-tag (`0.2.1`) dan een
bestaande tag verplaatsen.

---

## Deel B — Pinnen in een consumer (voorbeeld: bibliotheek)

De bibliotheek (en VSA-demo) **kiezen** welke tooling-versie ze gebruiken.
VSA-tooling dwingt die pin niet af.

### B1. Wanneer `@main` en wanneer een tag?

| Situatie                                         | Pin                                 |
| ------------------------------------------------ | ----------------------------------- |
| Snel uitproberen / eerste CI-opzet               | `@main` mag                         |
| Stabiele product-CI / reproduceerbare builds     | vaste tag, bijv. `@0.2.0`           |
| Je hebt features nodig die nog niet getagd zijn  | tijdelijk `@main`, daarna tag + pin |

### B2. Pip-install pinnen

In een workflow-stap, bootstrap-script of developer-README van de bibliotheek:

```cmd
cd /d C:\Git\orthodox-ronl\bibliotheek
python -m pip install "vsa-tool[rendering] @ git+https://github.com/orthodox-ronl/VSA-tooling.git@0.2.0"
vsa --version
```

Zelfde URL in `requirements.txt` / `requirements-ci.txt` als jullie die gebruiken:

```text
vsa-tool[rendering] @ git+https://github.com/orthodox-ronl/VSA-tooling.git@0.2.0
```

Na install: controleer dat `vsa --version` het verwachte pakket toont en dat
nieuwe CLI-vlaggen (bijv. `mvsa mscz --help`) bestaan op die tag.

### B3. Herbruikbare GitHub Actions pinnen

Pip-pin en workflow-pin zijn **twee aparte refs**. Zet beide op dezelfde tag
tenzij je bewust afwijkt.

Voorbeeld — render-helper:

```yaml
jobs:
  vsa:
    uses: orthodox-ronl/VSA-tooling/.github/workflows/vsa-render-reusable.yml@0.2.0
    with:
      input_dir: content
      output_dir: generated/vsa/content
      assets_dir: generated/vsa/static/vsa
      assets_url_prefix: /vsa
      output_mode: img
```

Voorbeeld — Pages-deploy-helper:

```yaml
jobs:
  deploy:
    uses: orthodox-ronl/VSA-tooling/.github/workflows/pages-deploy-reusable.yml@0.2.0
    with:
      artifact_name: pages-site
      publish_dir: site
      destination_dir: preview
      url_prefix: /bibliotheek/preview/
```

Zoek in de consumer-repo naar `@main` onder `.github/workflows/` en vervang
waar de call naar `orthodox-ronl/VSA-tooling` gaat.

### B4. Upgrade naar een nieuwere tag

1. Lees de GitHub Release notes van de nieuwe tag in VSA-tooling.
2. Vervang in de bibliotheek alle pins (`pip` + `uses:`) van oud → nieuw nummer.
3. Draai lokaal of in CI: validate / jullie site-`check`.
4. Merge die pin-bump als aparte, kleine PR in de bibliotheek (makkelijk te
   reverten).

```cmd
cd /d C:\Git\orthodox-ronl\bibliotheek
python -m pip install --force-reinstall "vsa-tool[rendering] @ git+https://github.com/orthodox-ronl/VSA-tooling.git@0.2.0"
vsa --version
```

### B5. Wat je níet in de bibliotheek hoeft te doen

- Geen fork van VSA-tooling-scripts; dunne wrappers die `vsa` / `mvsa`
  aanroepen volstaan.
- Geen eigen git-tag op VSA-tooling vanuit de bibliotheek-repo.
- Productgates (`sync_*` / `check_*`, freshness) blijven bibliotheek-beleid;
  die pinnen niet mee met de tooling-tag behalve via de CLI die ze aanroepen.

---

## Snelle checklist (beide kanten)

**VSA-tooling**

1. `pyproject.toml` version = gewenste semver  
2. `main` groen  
3. `git tag X.Y.Z` + `git push origin X.Y.Z`  
4. `gh release create X.Y.Z …`  
5. Consumers informeren  

**Bibliotheek / andere consumer**

1. Pip-URL → `@X.Y.Z`  
2. `uses: …/VSA-tooling/…@X.Y.Z`  
3. `vsa --version` + validate/CI groen  
4. Pin-bump als aparte PR  

---

## Zie ook

- Installatie en ownership:
  [Hergebruik in andere repo’s](../guides/reuse-vsa-tooling.md)
- Wat hoort in welke repo:
  [Consumer-site — waar hoort wat](consumer-site.md)
- Handmatige smoke-artifacts:
  `.github/workflows/release-artifacts.yml`
- Releases op GitHub:
  https://github.com/orthodox-ronl/VSA-tooling/releases
