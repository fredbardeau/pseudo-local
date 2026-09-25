# pseudo-local

> ### À lire avant d'utiliser cet outil
>
> **Les chiffres de détection annoncés plus bas ne sont pas des
> mesures.** Ils ont été obtenus sur des corpus de test écrits par le
> même outil qui a écrit les détecteurs. Ce sont des plafonds, utiles comme tests de non-régression,
> sans valeur probante. L'outil n'a pas encore été confronté à de vrais
> documents.
>
> **Ce qu'il ne détecte pas, et ne détectera jamais** : les identifiants
> indirects. « La directrice de l'antenne de [VILLE] », « la maman
> des triplés », « le seul éducateur homme de l'équipe » ne contiennent
> aucun nom et désignent une seule personne. Aucun outil de ce type ne
> les verra. La relecture humaine n'est pas une option de confort, c'est
> la moitié du dispositif.
>
> **Ce n'est pas de l'anonymisation.** Tant que la table de correspondance
> existe, le texte produit reste une donnée personnelle au sens du RGPD,
> avec les mêmes obligations.
>
> **Il n'existe pas de version hébergée, et il n'en existera pas.** Envoyer
> un texte sur un serveur pour savoir ce qu'il faut y cacher annule tout
> l'intérêt de la chose.

**Retirer les données personnelles d'un texte avant de le coller dans une IA, puis remettre les vraies valeurs dans la réponse.**

Tout se passe sur votre Mac. Après l'installation, l'outil ne se connecte plus à rien : aucun texte que vous traitez ne quitte votre machine, et un test automatique le vérifie à chaque exécution.

---

## Avant tout : ce que cet outil fait, et ce qu'il ne fait pas

Cet outil fait de la **pseudonymisation**, pas de l'anonymisation. La différence n'est pas un détail juridique : elle change ce que vous avez le droit de faire ensuite.

- Il remplace « Claire Durand » par `[PERSONNE_001]` et garde la correspondance dans un fichier.
- **Tant que ce fichier de correspondance existe, le texte produit reste une donnée à caractère personnel** au sens du RGPD. Il est réversible — c'est justement ce qu'on lui demande.
- Une véritable anonymisation serait irréversible. Ce n'est pas ce que fait cet outil.

Conséquence pratique : le fichier de correspondance mérite exactement la même protection que le document d'origine. Ne l'envoyez nulle part, ne le mettez pas sur un espace partagé.

**Et surtout :** la détection automatique ne voit pas les identifiants indirects. « La directrice de l'antenne de [VILLE] », « la maman des triplés », « le seul éducateur homme de l'équipe » désignent une personne aussi sûrement qu'un nom. Aucun modèle ne les repère. **La relecture avant envoi n'est pas optionnelle.**

---

## Installation

Il faut avoir [uv](https://docs.astral.sh/uv/) installé (`brew install uv`).

Ouvrez le Terminal et tapez, une ligne à la fois :

```bash
git clone https://github.com/fredbardeau/pseudo-local.git
cd pseudo-local
```

Cette procédure n'a été vérifiée que sur un Mac Apple Silicon, avec uv déjà installé. Elle n'a jamais été rejouée depuis un poste vierge.

```bash
uv sync --all-groups
```

```bash
uv run python installer_modele.py
```

La dernière commande télécharge le modèle de détection (environ 1,2 Go). **C'est le seul moment où l'outil utilise Internet.** Comptez quelques minutes. Ensuite, vous pouvez couper le réseau : tout fonctionne hors ligne.

---

## Utilisation

Pour essayer sans document à vous : le dossier `demo/` contient deux textes. **Corpus de démonstration, fictif par construction. Aucune mesure n'en est tirée, ni ne peut l'être.** Son `LISEZMOI.md` explique pourquoi chaque donnée ne peut correspondre à personne, et ce que l'outil en fait.

### Avec l'interface

```bash
./lancer.sh
```

Votre navigateur s'ouvre sur `http://127.0.0.1:7860`. Cette adresse n'est accessible que depuis votre Mac : ni votre voisin de bureau, ni le réseau de votre structure ne peuvent l'atteindre.

**Onglet 1 — Pseudonymiser**

1. Collez votre texte, ou déposez un fichier (`.txt`, `.md`, `.docx`, `.pdf`).
2. Cliquez sur **Analyser**. Les données repérées apparaissent surlignées par couleur.
3. **Relisez.** C'est l'étape qui compte.
   - Une détection est fausse ? Décochez-la dans la liste : elle restera en clair.
   - Chaque détection indique son origine : « clé vérifiée » (somme de contrôle calculée : IBAN, sécurité sociale, SIREN, SIRET, carte), « format reconnu » (autre règle, sans clé), « modèle », ou « à trancher ». Seule la première est une vérification. Relisez les autres.
   - Les lignes « à trancher » sont des suites de chiffres qui pourraient être une référence de dossier. Elles arrivent **décochées** : elles restent en clair tant que vous ne les cochez pas.
   - Une donnée a été oubliée ? Recopiez-la dans « Texte oublié à masquer », choisissez sa catégorie, cliquez sur **Ajouter**. Elle sera masquée partout où elle apparaît.
4. Cliquez sur **Produire le texte pseudonymisé**, puis sur l'icône de copie.
5. Collez ce texte dans l'IA de votre choix.

Le fichier de correspondance est enregistré dans le dossier `sorties/`. Il est lisible par vous seul.

**Onglet 2 — Réinjecter**

1. Collez la réponse de l'IA, qui contient encore les codes `[PERSONNE_001]`.
2. Si vous venez de pseudonymiser, la table de la session est utilisée automatiquement. Sinon, choisissez le fichier `.correspondances.json`.
3. Cliquez sur **Réinjecter**.

Les IA abîment souvent les codes : elles écrivent `[PERSONNE_1]` au lieu de `[PERSONNE_001]`, ou inventent un code qui n'a jamais existé. L'outil rattrape le premier cas et **refuse** le second en vous le signalant, plutôt que de remplacer au hasard.

### En ligne de commande

```bash
uv run python -m pseudo.cli --offline pseudonymiser mon-document.docx
```

Écrit `mon-document.docx.pseudonymise.txt` et `mon-document.docx.correspondances.json`, **à côté du fichier d'origine**. L'affichage ne montre que des comptages : aucun extrait de votre document n'apparaît dans le Terminal.

```bash
uv run python -m pseudo.cli --offline reinjecter reponse.txt mon-document.docx.correspondances.json
```

L'option `--offline` verrouille les connexions sortantes du programme. Sans elle, l'outil est déjà hors ligne pour le modèle ; avec elle, toute tentative de sortie échoue franchement.

---

## Comment ça marche

Quatre couches, de la plus sûre à la plus faillible.

**1. Règles et clés de contrôle.** Les identifiants français ont une structure arithmétique. Un IBAN se vérifie modulo 97, un SIRET et un numéro de carte par l'algorithme de Luhn, un numéro de sécurité sociale par sa clé. L'outil ne se contente donc pas de repérer une forme : il vérifie que le numéro est mathématiquement valide. Une suite de chiffres qui ressemble à un IBAN mais dont la clé est fausse est ignorée. Couvre : courriel, téléphone (français et international), IBAN, numéro de sécurité sociale, SIREN, SIRET, plaque d'immatriculation, numéro de carte bancaire, adresse IP, date de naissance en contexte, code postal + commune, et adresse postale. Pour les adresses, la règle du tout ou rien s'applique : dès qu'un morceau est repéré (voie, complément, code postal, commune, cedex), le bloc entier devient un seul code. Une adresse masquée à moitié rassurerait à tort. Les références de dossier (numéro d'allocataire, de demande, de facture…) sont masquées dans deux cas seulement : quand un mot les annonce (« référence », « dossier », « n° », « allocataire »…) et que le numéro qui suit en a la forme, ou quand leur forme est très typée (au moins trois groupes, comme `SS-2025-0072`). Les numéros immédiatement précédés de « loi », « décret », « arrêté », « ordonnance » ou « article » ne sont jamais masqués. Une suite isolée de 5 à 12 chiffres que rien n'a masquée est signalée « à trancher », sans être masquée. La règle exacte, avec ses cas, est dans `pseudo/REGLES_REFERENCES.md`.

**2. Modèle local.** `fastino/gliner2-privacy-filter-PII-multi`, 205 millions de paramètres, licence Apache 2.0, français pris en charge. Il repère ce qui n'a pas de forme fixe : noms de personnes, organisations, lieux, références de dossier. Pour les adresses, il ne fait que compléter un bloc déjà repéré par les règles : seul, il ne masque aucune adresse. Le seuil est réglable ; plus il est bas, plus l'outil détecte, et plus il se trompe.

**3. Codes cohérents.** La même personne garde le même code dans tout le document, y compris ses variantes d'écriture : « Mme Durand », « Claire Durand » et « C. Durand » reçoivent tous `[PERSONNE_001]`. De plus, un nom repéré une fois est masqué partout ailleurs dans le document, même là où le modèle ne l'avait pas vu.

**4. Vous.** Voir l'avertissement en haut de cette page.

---

## Résultats sur le corpus de test (non-régression)

Obtenu sur 20 documents fictifs en français (courriels d'association, comptes rendus de conseil d'administration, dossiers de subvention, échanges RH, notes de suivi social, contrats), contenant 195 données personnelles annotées à l'avance. **Le corpus et sa vérité terrain ont été écrits et figés avant l'écriture du détecteur** (leurs empreintes sont dans `evaluation/EMPREINTES.txt`), pour que le taux ne soit pas un auto-satisfecit.

| Catégorie | Attendus | Masqués | Rappel |
|---|---:|---:|---:|
| Courriel | 17 | 17 | **100 %** |
| Téléphone | 22 | 22 | **100 %** |
| IBAN | 12 | 12 | **100 %** |
| Numéro de sécurité sociale | 4 | 4 | **100 %** |
| SIRET | 7 | 7 | **100 %** |
| SIREN | 4 | 4 | **100 %** |
| Carte bancaire | 2 | 2 | **100 %** |
| Adresse IP | 2 | 2 | **100 %** |
| Plaque d'immatriculation | 4 | 4 | **100 %** |
| Date de naissance | 6 | 6 | **100 %** |
| Code postal + commune | 1 | 1 | **100 %** |
| **Nom de personne** | **63** | **63** | **100 %** |
| Organisation | 17 | 15 | 88 % |
| Lieu | 9 | 8 | 89 % |
| Adresse postale | 20 | 20 | **100 %** |
| Référence de dossier | 5 | 5 | **100 %** |
| **Ensemble** | **195** | **192** | **98 %** |

Précision : **95,6 %** — sur 203 éléments masqués, 194 étaient bien des données personnelles.
Temps : 31 à 36 secondes pour les 20 documents.

Détail daté (faux positifs, liste des oublis, identifiants indirects) : `evaluation/RESULTATS_2026-09-25.md`.

**Les deux critères fixés à l'avance sont atteints :**
- rappel de 100 % sur les identifiants à format fixe → **100 % (68/68)** ;
- rappel d'au moins 90 % sur les noms de personnes avant relecture → **100 % (63/63)**.

**Adresses : critères fixés avant d'écrire la règle, sur un jeu de test séparé**, figé avant le code (non-régression) :
- adresses du corpus masquées entièrement, en un seul code → **100 % (20/20)** ;
- jeu neuf, au moins 90 % masquées entièrement → **100 % (42/42)** ;
- phrases pièges (« une place en crèche », « le chemin de fer »…), au plus 2 fausses alertes → **2 sur 24**.

Ce jeu d'adresses n'est pas publié, ni son script de mesure : il contient des voies et des communes réelles. Il reste, avec la preuve de son gel, dans le dépôt privé de mesure. Le jeu des références, ci-dessous, est publié parce qu'il ne contient que des numéros inventés, sans lieu ni clé valide. Le critère est la vérifiabilité, pas l'uniformité.

**Références de dossier : test de non-régression** (`evaluation/references_neuves/cas.json`, gelé avant la règle). Les 5 références du corpus sont masquées par les règles seules, modèle désactivé. Sur le jeu gelé : 20/20 références annoncées, 8/8 références typées, 3 pièges sur 28 masqués à tort (limite fixée : 2). **Ces trois chiffres ne mesurent pas la performance** : les pièges ont été écrits avant que la règle soit resserrée pour les faire passer, ce sont donc des plafonds. La seule mesure probante reste des documents réels annotés à la main.

```bash
uv run python evaluation/evaluer_references.py
```

Pour refaire la mesure vous-même :

```bash
uv run python evaluation/evaluer.py
```

Cette mesure ne se rejoue qu'avec le corpus gelé, qui reste privé : il contient des identifiants à clé valide dont on ne peut garantir qu'ils ne désignent personne. Ses empreintes sont publiées dans `evaluation/EMPREINTES.txt`. Les deux jeux de non-régression ci-dessous, eux, sont publics.

---

## Limites connues

Elles sont réelles et mesurées. Les connaître, c'est savoir où regarder pendant la relecture.

**Les identifiants indirects ne sont pas détectés. Aucun. Zéro sur 22** dans le corpus de test. C'est une limite de conception, pas un défaut à corriger : reconnaître qu'une « directrice d'antenne » désigne une personne unique demande de connaître l'organisation, ce qu'aucun modèle de texte ne peut faire. C'est exactement ce que votre relecture doit rattraper.

**Les adresses reconnues sont celles qui ont une forme d'adresse.** Il faut un type de voie suivi d'un nom propre (« 5 rue de l'Exemple », « place de l'Exemple ») ou un code postal suivi d'une commune. Une adresse écrite autrement (« aux Grandes Vignes », « chez les Martin, à la sortie du bourg ») passe. À l'inverse, un type de voie suivi d'un nom propre est masqué même quand ce n'est pas une adresse : « la route de Paris », « la Place Beauvau ». Le jeu de test des adresses a été écrit par l'auteur de la règle : il prouve que les formats prévus sont couverts, pas que la règle résiste aux adresses mal formées des vrais courriers. Relisez les adresses.

**Les références de dossier ne sont masquées que sur preuve.** Niveau 1 : un mot déclencheur (« référence », « réf », « dossier », « n° », « numéro », « facture », « allocataire », « adhérent », « bénéficiaire », « cote », « matricule », « demande », « contrat », « convention », « commande », « sinistre », « identifiant », « client ») suivi, à quatre mots au plus, d'un numéro d'au moins 4 chiffres ou mêlant lettres et chiffres, qui n'est ni une date, ni un ordinal, ni un montant. Niveau 2 : sans déclencheur, une forme d'au moins trois groupes séparés par des tirets ou des barres obliques, avec au moins une lettre et un groupe d'au moins 3 chiffres (`SS-2025-0072`, `DOS/2026/112`). Niveau 3 : **une série de 5 à 12 chiffres sans mot qui l'annonce et sans cette structure n'est pas masquée**, elle est signalée « à trancher » ; en dessous de 5 chiffres, elle n'est même pas signalée. Relisez les suites de chiffres. Trois erreurs connues : un numéro public annoncé par un déclencheur est masqué à tort (« convention collective 1261 ») ; une année placée quelques mots après un déclencheur aussi (« 245 demandes en 2025 ») ; et quand un déclencheur annonce plusieurs numéros (« réf. AB-12 et AB-13 »), seul le premier est masqué. Le détail des règles et de leurs trous est dans `pseudo/REGLES_REFERENCES.md`.

**Le rapprochement des noms peut regrouper deux personnes différentes.** Deux « Durand » sans prénom dans le même document reçoivent le même code. La liste des détections affiche les regroupements : jetez-y un œil.

**Les PDF scannés sont refusés**, avec un message explicite. Il n'y a pas de reconnaissance de caractères. Ouvrez le PDF, sélectionnez le texte, collez-le.

**Les plaques d'avant 2009** (`123 ABC 45`) ne sont pas reconnues : le motif serait trop proche d'une référence de dossier quelconque.

**Le libellé « date sensible » est désactivé.** Mesure à l'appui : l'activer faisait gagner 1 donnée masquée sur 195 et ajoutait 30 fausses alertes, le modèle signalant toutes les dates de réunion et d'échéance. Le bruit rendait la relecture pénible, donc moins fiable. Pour le réactiver, une ligne dans `pseudo/modele.py` (voir `ETIQUETTES_OPTIONNELLES`).

---

## Place et vitesse, mesurées sur un MacBook M1 8 Go

| | |
|---|---|
| Modèle téléchargé | 1,2 Go |
| Environnement Python | 0,9 à 1 Go |
| **Total sur le disque** | **2,0 à 2,2 Go** |
| Mémoire au repos | 20 à 40 Mo |
| **Mémoire, modèle chargé** | **0,9 à 1,2 Go** |
| Chargement du modèle au démarrage | 18 à 22 s |
| **Document de 2 pages (900 à 1 060 mots)** | **5 à 16 s** |
| Le même, règles seules (`--sans-modele`) | moins de 0,01 s |

Fourchettes issues de deux séries de mesures, le 20 et le 25 septembre 2026, sur un MacBook M1 à 8 Go de RAM. L'écart tient surtout aux autres applications ouvertes au même moment : donnez la fourchette, pas un chiffre unique.

Sur un Mac à 8 Go de RAM, l'outil tient sans difficulté, mais évitez de le lancer en même temps qu'une autre application lourde.

---

## Vérifier que rien ne sort

```bash
uv run python -m pytest tests/ -v
```

Le fichier `tests/test_hors_ligne.py` ne se contente pas de lire des réglages. Il **remplace la fabrique de connexions réseau du programme**, puis fait tourner la chaîne complète, chargement du modèle compris. Si le moindre composant tentait de sortir, le test échouerait. Les connexions vers votre propre machine restent autorisées, sans quoi l'interface ne pourrait pas s'ouvrir.

---

## Où sont les choses

```
pseudo-local/
├── lancer.sh                  ouvre l'interface (equivalent en ligne de commande)
├── installer_modele.py        télécharge le modèle (une seule fois)
├── pseudo/                    le code
│   ├── cles.py                clés de contrôle (mod 97, Luhn, clé NIR)
│   ├── regles.py              couche 1
│   ├── adresses.py            couche 1 : adresses, assemblées en un seul bloc
│   ├── references.py          couche 1 : références de dossier (déclencheur, forme typée, signalement)
│   ├── REGLES_REFERENCES.md   la règle des références, sous forme testable (fait foi)
│   ├── modele.py              couche 2
│   ├── pseudonymisation.py    couche 3
│   ├── reinjection.py         remise des vraies valeurs
│   ├── interface.py           couche 4
│   └── hors_ligne.py          verrou réseau
├── demo/                      corpus de démonstration, fictif par construction
├── evaluation/                mesure, jeux de non-régression, empreintes du corpus privé
├── modeles/                   le modèle téléchargé
└── sorties/                   vos tables de correspondance — à protéger
```

Les journaux et l'affichage du Terminal ne contiennent jamais le texte traité, seulement des comptages.

Le corpus de test (`evaluation/corpus/`) n'est pas publié. Ses identifiants ont des clés de contrôle valides, ses codes banque sont réels et certaines adresses de courriel sont plausibles sur des domaines existants : on ne peut pas garantir qu'il ne désigne personne. Seules ses empreintes sont publiées (`evaluation/EMPREINTES.txt`). Pour essayer l'outil, utilisez `demo/`. **N'ajoutez jamais de document réel dans `evaluation/`.**

---

## Licence

Ce code est distribué sous licence **Apache 2.0** (fichier `LICENSE`), sans aucune garantie. Le modèle qu'il utilise, `fastino/gliner2-privacy-filter-PII-multi`, et la bibliothèque `gliner2` qui le charge sont également sous licence Apache 2.0.
