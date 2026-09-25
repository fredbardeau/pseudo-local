# Résultats d'évaluation — 25 septembre 2026

> Les empreintes de commit citées dans ce fichier (`81d5094`, `0c228a5`, `41beeb6`…) renvoient au
> dépôt privé de développement. Le dépôt public a été créé sans historique : elles n'y existent pas.
> Les empreintes SHA-256 des jeux de test et `EMPREINTES.txt`, elles, se vérifient partout.

Mesure sur le corpus fictif figé de `evaluation/corpus/` (20 documents, 195 données personnelles
annotées dans `verite_terrain.json`, empreintes dans `EMPREINTES.txt`).

- Code : commit `81d5094`
- Réglage : règles + modèle, seuil de confiance 0,4
- Commande : `uv run python evaluation/evaluer.py --faux-positifs`
- Machine : MacBook M1, 8 Go de RAM, hors ligne
- Règle de comptage : une donnée attendue est masquée si au moins 80 % de ses caractères sont couverts.

## Critères fixés à l'avance

| Critère | Cible | Obtenu | |
|---|---:|---:|---|
| Identifiants à format fixe (IBAN, NIR, email, téléphone, SIRET, SIREN, carte) | 100 % | **100 % (68/68)** | atteint |
| Noms de personnes, avant relecture | ≥ 90 % | **100 % (63/63)** | atteint |

## Détection par catégorie

« Rappel » : la donnée est masquée, quelle que soit l'étiquette. « Bonne catégorie » : masquée
avec la bonne étiquette.

| Catégorie | Attendus | Masqués | Rappel | Bonne catégorie | Faux positifs |
|---|---:|---:|---:|---:|---:|
| Téléphone | 22 | 22 | 100 % | 100 % | 0 |
| Email | 17 | 17 | 100 % | 100 % | 0 |
| IBAN | 12 | 12 | 100 % | 92 % | 0 |
| SIRET | 7 | 7 | 100 % | 100 % | 0 |
| SIREN | 4 | 4 | 100 % | 100 % | 0 |
| Numéro de sécurité sociale | 4 | 4 | 100 % | 75 % | 0 |
| Carte bancaire | 2 | 2 | 100 % | 100 % | 0 |
| Adresse IP | 2 | 2 | 100 % | 100 % | 0 |
| Plaque d'immatriculation | 4 | 4 | 100 % | 100 % | 0 |
| Date de naissance | 6 | 6 | 100 % | 100 % | 2 |
| Code postal + commune | 1 | 1 | 100 % | 100 % | 0 |
| **Nom de personne** | **63** | **63** | **100 %** | **100 %** | 0 |
| Organisation | 17 | 15 | 88 % | 88 % | 4 |
| Lieu | 9 | 8 | 89 % | 67 % | 0 |
| Adresse postale | 20 | 16 | 80 % | 80 % | 0 |
| Référence de dossier | 5 | 2 | 40 % | 40 % | 0 |
| **Ensemble** | **195** | **185** | **95 %** | | **6** |

Précision globale : **97 %** (190 détections utiles sur 196).
Durée : 35,5 s pour les 20 documents (19 868 caractères). Le 20/09 : 32 s.

## Ce qui a échappé à l'outil

Aucun nom de personne. Dix données non masquées, ou masquées en partie (« couvert » = part des
caractères tout de même masquée) :

| Couvert | Document | Catégorie | Donnée |
|---:|---|---|---|
| 57 % | 01_mail_beneficiaire.txt | Organisation | [association du corpus] |
| 57 % | 02_mail_beneficiaire.txt | Organisation | [association du corpus] |
| 33 % | 07_cr_ca.txt | Adresse | [adresse du corpus] |
| 28 % | 16_suivi_social.txt | Adresse | [adresse du corpus] |
| 0 % | 03_mail_beneficiaire.txt | Adresse | [adresse du corpus] |
| 0 % | 16_suivi_social.txt | Adresse | [adresse du corpus] |
| 0 % | 08_subvention.txt | Lieu | [lieu du corpus] |
| 0 % | 10_subvention.txt | Référence de dossier | FDVA-2026-CVL-0231 |
| 0 % | 14_suivi_social.txt | Référence de dossier | SS-2026-0148 |
| 0 % | 20_mail_relance.txt | Référence de dossier | F-2026-0177 |

Schéma récurrent : sur une adresse, le code postal et la commune partent, le numéro et la rue
restent ; une adresse sans commune reste entièrement en clair.

## Faux positifs

| Document | Étiquette posée | Texte |
|---|---|---|
| 06_cr_ca.txt | Organisation | CA (conseil d'administration), deux fois |
| 13_rh.txt | Organisation | Clio (une voiture) |
| 17_contrat.txt | Organisation | SIRENE (le répertoire) |
| 17_contrat.txt | Date de naissance | 15 mars 2026 (date de contrat) |
| 18_contrat.txt | Date de naissance | 2 juin 2026 (date de contrat) |

## Identifiants indirects : 0 détecté sur 22

Limite de conception : ces formulations désignent une personne sans la nommer. Seule la relecture
les rattrape.

| Document | Formulation |
|---|---|
| 02_mail_beneficiaire.txt | ma collègue, qui reprend le dossier à partir de la semaine prochaine |
| 03_mail_beneficiaire.txt | notre trésorier |
| 04_mail_equipe.txt | La directrice de l'antenne de [VILLE] |
| 05_cr_ca.txt | le seul éducateur homme de l'équipe |
| 06_cr_ca.txt | La responsable du chantier d'insertion |
| 06_cr_ca.txt | la personne dont le contrat aidé arrive à échéance en juin et qui habite le foyer de la rue [NOM] |
| 07_cr_ca.txt | Le commissaire aux comptes |
| 07_cr_ca.txt | Une adhérente |
| 09_subvention.txt | La maman des triplés |
| 09_subvention.txt | un maraîcher de la commune |
| 10_subvention.txt | votre instructrice |
| 11_rh.txt | Le service paie |
| 12_rh.txt | la directrice |
| 12_rh.txt | un représentant du personnel |
| 12_rh.txt | La personne qui gère la paie depuis le départ de la précédente comptable |
| 14_suivi_social.txt | Sa fille, qui vit dans [RÉGION] |
| 14_suivi_social.txt | Notre bénéficiaire en fauteuil du quartier [NOM] |
| 15_suivi_social.txt | une stagiaire |
| 15_suivi_social.txt | son médecin traitant |
| 16_suivi_social.txt | L'aînée |
| 16_suivi_social.txt | Le seul éducateur homme de l'équipe |
| 16_suivi_social.txt | la professeure principale |

## Place, mémoire, vitesse

Document de test : les fichiers `01` à `07` du corpus mis bout à bout (1 059 mots, soit environ
deux pages). Mesures dans un même processus Python, modèle chargé une fois.

| | 25/09/2026 | Rappel 20/09/2026 |
|---|---:|---:|
| Modèle téléchargé (`modeles/`) | 1,2 Go | 1 187 Mo |
| Environnement Python (`.venv/`) | 968 Mo | 898 Mo |
| Total sur le disque | 2,2 Go | 2,0 Go |
| Mémoire au repos (pipeline importé) | 19 Mo | 39 Mo |
| Mémoire, modèle chargé (pic) | 1 205 Mo | 897 Mo |
| Chargement du modèle | 18,3 s | 22 s |
| Document de 2 pages, avec modèle | 8,8 s / 6,3 s / 16,4 s (3 passages) | 4,8 s (900 mots) |
| Même document, règles seules | 0,005 s | 0,01 s |
| Commande complète (lancement + chargement + traitement), 2 essais | 24 s et 31 s, pic 1,1 à 1,2 Go | — |

D'autres applications étaient ouvertes pendant la mesure : la variation d'un passage à l'autre
(6 à 16 s sur le même texte) vient de la charge de la machine, pas de l'outil.

---

# Après la règle d'adresse — 25 septembre 2026, même jour

Tout ce qui précède décrit l'état **avant** la règle d'adresse (commit `81d5094`). Cette section
mesure l'état après (`pseudo/adresses.py`), avec les mêmes réglages.

## Méthode

1. Jeu de test séparé écrit et commité **avant** le code (`adresses_neuves/cas.json`, commit
   `0c228a5`, SHA-256 `29e37db102482b029c571c909495aca5ccaf1f9a5825b3379848f0353b504938`) :
   35 phrases (36 adresses), 6 cas limites proposés par une autre instance de Claude, 24 pièges.
2. Critères fixés dans le même commit, avant le code.
3. Règle du tout ou rien : une adresse compte comme masquée seulement si 100 % de ses caractères
   sont couverts par une seule détection (un seul code).

Limites de la méthode :
- le jeu neuf a été écrit par l'auteur de la règle, qui savait quelle règle il allait écrire ;
- l'exigence d'un ancrage pour les adresses vues par le modèle a été décidée **après** avoir vu
  ses deux faux positifs sur les pièges : le résultat sur les pièges est en partie contaminé.

## Critères

| Critère | Cible | Avant | Après | |
|---|---:|---:|---:|---|
| C1 corpus : adresses masquées entièrement, un code chacune | 21/21 | 16/21 | **21/21** | tenu |
| C2 jeu neuf : masquées entièrement | ≥ 38/42 | 31/42 | **42/42** | tenu |
| C3 pièges : faux positifs d'adresse | ≤ 2 | 2 | **2** | tenu |
| C4 autres catégories / précision | pas de baisse, ≥ 96 % | 97 % | **96 %** (191/198) | tenu |
| C5 tests existants, aucune dépendance | tous verts | 62 | **72 verts** | tenu |

## Corpus d'origine, avant / après

| Catégorie | Avant : masqués | Avant : entiers | Après : masqués | Après : entiers |
|---|---:|---:|---:|---:|
| Adresse postale | 16/20 (80 %) | 15/20 (75 %) | **20/20** | **20/20** |
| Code postal + commune | 1/1 | 1/1 | 1/1 | 1/1 |
| Toutes les autres catégories | inchangées | | inchangées | |
| **Ensemble** | **185/195 (95 %)** | | **189/195 (97 %)** | |

Précision : 97 % (190/196) avant, **96 % (191/198)** après. Nouvelle fausse alerte :
« rue [NOM] » dans « le foyer de la rue [NOM] » (06_cr_ca.txt). Elle fait partie d'un identifiant
indirect ; la masquer protège, mais l'évaluation la compte comme une erreur. Durée : 30,7 s.

Avant, les adresses non masquées entièrement étaient :

| Couvert | Document | Adresse |
|---:|---|---|
| 0 % | 03_mail_beneficiaire.txt | [adresse du corpus] |
| 94 %, en 2 codes | 06_cr_ca.txt | [adresse du corpus] |
| 33 % | 07_cr_ca.txt | [adresse du corpus] |
| 28 % | 16_suivi_social.txt | [adresse du corpus] |
| 0 % | 16_suivi_social.txt | [adresse du corpus] |

Après : aucune.

## Jeu neuf, avant / après (règles + modèle)

Avant, le modèle seul masquait entièrement 27/36 adresses et 4/6 cas limites. Échecs :
p01 (22 %), p04 (59 %), p05 (98 %), p06 (78 %), p11 (27 %), p12 (43 %), p15 (97 %), p27 (0 %),
p31 (97 %), c03 (0 %), c04 (28 %). Faux positifs du modèle : « Rue barrée », « 1er étage, salle 4 ».

Après : 36/36 et 6/6, avec ou sans le modèle. Faux positifs restants, prévus avant le code :

| Piège | Masqué à tort |
|---|---|
| n15 « Il a pris la route de Paris à 6 heures. » | route de Paris |
| n20 « La Place Beauvau a publié une circulaire… » | Place Beauvau |

---

# Références de dossier, niveaux 1 et 2 — 25 septembre 2026

Jeu gelé avant la règle : `references_neuves/cas.json`, commit `41beeb6`, SHA-256
`5cacb75a66a8b987bd53fb83375cb4c5acd69f9cb16ed61210f4c520cbe279de`. Règles : commit `c6ca13a`.

## Réserve de méthode

> Tu as écrit les 28 pièges, puis amendé L2 pour qu'ils passent. C'est honnête de l'avoir dit,
> mais la conséquence tient : R2, R3 et R4 mesurés sur ce jeu sont un PLAFOND, pas une mesure. Le
> jeu vaut comme test de non-régression, pas comme preuve de performance.

La seule mesure probante reste les documents réels annotés à la main.

R4 (2/28) est atteint en partie grâce à l'exclusion des textes publics appliquée au modèle, règle
décidée après observation des faux positifs, et non fixée d'avance.

## Critères

| Critère | Avant | Après | |
|---|---|---|---|
| R1 corpus : 5 identifiants masqués entièrement **par règle** (modèle désactivé) | 0/5 par règle (2/5 par le modèle seul) | **5/5** par règle | tenu |
| R2 annoncées, **non-régression** (≥ 18/20) | 12/20 | **20/20** | tenu |
| R3 typées, **non-régression** (≥ 7/8) | 7/8 | **8/8** | tenu |
| R4 pièges masqués à tort, **non-régression** (≤ 2/28) | 3/28 | **2/28** | tenu, au plafond |
| R5 précision ≥ 95 %, signalement sous 96 % ; aucune baisse de rappel | 96,0 % (191/198) | **96,04 %** (194/202) ; aucune catégorie en baisse | tenu |
| R6 tests verts, aucune dépendance | 72 | **87** | tenu |

Pièges masqués à tort (non-régression) :
- n08 `PLF-2026` : masqué par le modèle ;
- n27 « convention collective `1261` » : masqué par la règle du niveau 1. Aucune règle fixée d'avance
  ne l'exclut, et aucune n'a été ajoutée après coup.

Pièges écartés par l'exclusion des textes publics appliquée au modèle, décidée après observation :
n01 `article L. 1234-5`, n17 `loi n° 78-17`.

## Corpus d'origine

| Catégorie | Avant | Après |
|---|---:|---:|
| Référence de dossier (IDENTIFIANT) | 2/5 (modèle seul) | **5/5** (5/5 par règle) |
| Toutes les autres catégories | inchangées | inchangées |
| **Ensemble** | 189/195 (97 %) | **192/195 (98 %)** |

Précision : 96,04 % (194/202). Nouvelle fausse alerte : « devis n° `2026-044` » (19_contrat.txt).

Désaccord de vérité terrain non tranché : un numéro de devis entre deux structures est un
identifiant de dossier au sens de la règle. S'il devait être requalifié, la précision serait de
96,5 %. À trancher sur les documents réels, pas ici.

Durée : 33,2 s pour les 20 documents.

## Séries nues (niveau 3, non traité à ce stade)

Sans déclencheur ni structure, aucune règle ne s'applique. Le modèle en masque 2 sur 3 (b01, b03),
sans garantie ; b02 `004517` reste en clair.

Critère figé avant de coder le niveau 3 :

R7 : les 3 séries nues sont masquées OU signalées (3/3), et au plus 10 signalements au total sur
les 20 documents du corpus.

En ligne de commande, un signalement n'apparaît que sous forme de compteur, jamais d'extrait.

---

# Références de dossier : relecture, corrections, niveau 3, mesure unique — 25 septembre 2026

## Ce qui a été fait, dans l'ordre

1. **Libellés de l'interface** (commit séparé) : « clé vérifiée » réservé aux détections avec somme
   de contrôle réellement calculée (IBAN, NIR, SIREN, SIRET, carte) ; « format reconnu » pour les
   autres règles ; « modèle » pour GLiNER2 ; « à trancher » pour un signalement.
2. **Niveau 3** : une série nue de 5 à 12 chiffres est signalée, décochée, jamais masquée. En ligne
   de commande : un compteur, jamais d'extrait.
3. **Relecture du code contre les règles écrites**, ligne à ligne, sans regarder les résultats :
   sept divergences, qui ont une seule cause : la règle était écrite en prose et le code
   l'interprétait.
4. **Règle réécrite en forme testable** : `pseudo/REGLES_REFERENCES.md`, qui est désormais la
   référence. Le test `tests/test_regles_references.py` lit ses cas, il n'en contient aucun. Les
   cas de l'ancien `tests/test_references.py` y ont été versés, puis le fichier a été supprimé.
5. **Corrections** du code pour le mettre en conformité, puis **une seule mesure complète**.

## Catégories d'écarts

- **Correction de code faite après observation d'un résultat** (la série suivie d'une virgule
  n'était pas signalée). Elle remet le code en accord avec la règle annoncée d'avance (suite
  isolée de 5 à 12 chiffres) sans modifier la règle. Catégorie différente d'un changement de
  règle post-hoc.
- **Corrections code→règle, trouvées en relisant le code, sans regarder les résultats** : exclusion
  des textes publics ramenée à « immédiatement précédé de » ; symbole numéro collé au numéro ;
  date `aaaa/mm/jj` ; niveau 2 acceptant une lettre n'importe où.
- **Correction code→règle, détectée en relisant le diff, avant toute mesure** : le point facultatif
  de « réf » avait été appliqué à tous les déclencheurs.
- **Changements de règle, énoncés avant la mesure** : ordinaux (resserrement décidé pendant le
  codage, avant toute mesure, non annoncé à l'époque, régularisé le 25/09/2026) ; années non
  exclues quand un déclencheur précède (décision 6) ; variantes typographiques du symbole numéro ;
  « réf » sans point (clarification).
- **Non couvert, assumé** : le « motif alphanumérique ambigu » proposé pour le niveau 3. Le définir
  après avoir vu les résultats serait une règle post-hoc.

## Mesure unique, chiffres bruts

| Critère | Résultat | |
|---|---|---|
| R1 : 5 identifiants du corpus, par règle (modèle désactivé) | 5/5 | tenu |
| R2 : annoncées, **non-régression** | 20/20 | tenu |
| R3 : typées, **non-régression** | 8/8 | tenu |
| R4 : pièges masqués à tort, **non-régression**, limite 2/28 | **3/28** : `PLF-2026` (modèle), `1261` (règle), `2025` (règle) | **non tenu** |
| R5 : précision ≥ 95 % ; aucune baisse de rappel | **95,57 %** (194/203) ; rappel inchangé à 98 % (192/195) | **tenu** ; alerte des 96 % déclenchée |
| R6 : tests | 159 verts à la mesure (157 après le versement des cas dans le document) | tenu |
| R7 : 3 séries nues masquées ou signalées | 3/3 (2 masquées par le modèle, 1 signalée) | tenu |
| R7 : au plus 10 signalements sur les 20 documents du corpus | 0 signalement | **non mesuré** |
| Adresses (non-régression) | 36/36, 6/6, 2 pièges | inchangé |

**R5 est tenu.** 95,57 % est au-dessus du seuil de 95 %. Ce qui s'est déclenché, c'est l'alerte
des 96 %, dont l'effet est écrit dans le critère : on n'ajoute plus de règle.

**R4 est non tenu (3/28) et ne se rattrape pas.** C'est un signal, pas une mesure : un dépassement
de 1 sur 28 pièges écrits par l'outil lui-même n'a pas de valeur probante.

**R7, plafond de bruit.** Le plafond de bruit reste non testé. Le corpus contient peu de séries de
chiffres qu'aucune règle ne couvre déjà. Deux signalements sont déjà apparus sur un piège (« les
secteurs 86000 et 86100 », codes postaux isolés). Le plafond se mesure sur les documents réels ;
c'est là que se décide le maintien ou le retrait du niveau 3.

## Diagnostic des deux nouvelles fausses alertes

- Jeu gelé, n12 : « Nous avons reçu 245 demandes en `2025`. »
- Corpus, 08_subvention.txt : « DOSSIER DE DEMANDE DE SUBVENTION `2026` ».

Elles ne viennent pas de la décision 6 seule, mais de son interaction avec la fenêtre de 4 mots :
dans « 245 demandes en 2025 » et « DOSSIER DE DEMANDE DE SUBVENTION 2026 », l'année n'est pas le
numéro du déclencheur, elle est à distance derrière des mots de liaison.

**Décision : on garde la décision 6. On ne corrige rien.**

Le rappel est inchangé à 98 % : la décision 6 n'a produit aucun gain mesuré sur ce corpus, qui ne
contient aucun cas du type "matricule 2019". Son bénéfice repose sur des cas écrits pour le
document de règles ; son coût est observé sur le corpus et les pièges. Gain raisonné, coût mesuré.

**Option non retenue** : n'accepter une année que si elle suit immédiatement le déclencheur.
Formulée après avoir vu les résultats, et interdite par le critère R5, qui dit de ne plus ajouter
de règle sous 96 %. Elle sera reconsidérée sur les documents réels, pas ici.

**Trou connu, non corrigé** : un déclencheur suivi de plusieurs numéros ne masque que le premier
(« Réf. AB-12 et AB-13 » : fuite silencieuse du second). À trancher sur les documents réels.

Réserve de méthode, toujours valable : R2, R3 et R4, comme les cas du document de règles, sont de
la non-régression. La seule mesure probante reste les documents réels annotés à la main.

---

## Arrêt sur le corpus fictif

On s'arrête sur le corpus fictif. Plus aucune règle, plus aucun affinage. La prochaine étape est
la seule qui mesure quelque chose : mes dix documents réels annotés à la main.

---

# Audit avant publication — 25 septembre 2026

Le corpus de test (`evaluation/corpus/`) et sa vérité terrain (`evaluation/verite_terrain.json`)
contiennent des IBAN, numéros de sécurité sociale, SIRET et cartes à clés de contrôle valides, des
codes banque réels, des téléphones hors des tranches que l'Arcep réserve à la fiction, et des
adresses plausibles sur des domaines existants (dont un domaine ministériel). Il n'est pas possible
de garantir qu'ils ne correspondent à personne. Ils ne sortent pas du dépôt privé.
`evaluation/EMPREINTES.txt` est conservé : il prouve le gel sans exposer les données.

Enseignement :

Le corpus a été généré à partir d'une consigne demandant des documents "réalistes". Un modèle à qui
on demande du réaliste produit du vraisemblable : des clés de contrôle valides, des codes banque
réels, des adresses plausibles sur des domaines existants. "Réaliste" et "fictif" sont en tension
directe. Pour un jeu de test contenant des données personnelles, la consigne doit demander de
l'invalide par construction, pas du réaliste.

---

# Décisions de publication — 25 septembre 2026

**Dépôt public neuf, sans historique.** Pas de réécriture de l'historique du dépôt privé pour en
retirer le corpus : il y détruirait ce qu'on veut garder (le corpus gelé, sa chronologie, la mesure
rejouable). Et après une réécriture suivie d'un force-push, les anciens commits peuvent rester
accessibles par leur empreinte jusqu'au nettoyage interne de GitHub ; rendre ce dépôt public les
exposerait. Un dépôt neuf ne partage aucun objet avec l'ancien.

**Adresse du premier commit du dépôt privé : pas de réécriture**, pour ne pas invalider les douze
empreintes de commit citées dans la documentation. Le dépôt public, lui, ne porte que l'adresse
noreply.

**Exemples localisables neutralisés.** Les adresses du corpus deviennent « [adresse du corpus] »,
les lieux des formulations indirectes deviennent « [VILLE] », « [RÉGION] », « rue [NOM] ». Raison :
ces formulations sont précisément ce que le projet désigne comme le plus identifiant ; dans un dépôt
public, un exemple n'a pas besoin d'être localisable pour être parlant. Appliqué au README, à
`REGLES_REFERENCES.md`, au `LISEZMOI` de la démonstration, à ce fichier, au code et aux tests.
Le jeu gelé des adresses (`adresses_neuves/`) et son script ne sont pas publiés : ils contiennent
des voies et des communes réelles. Dans un dépôt public sans historique, leur empreinte ne prouve
rien ; la preuve du gel vit dans le dépôt privé et y reste. Le jeu des références
(`references_neuves/`) est publié : il ne contient que des numéros inventés, sans lieu ni clé
valide. Le critère est la vérifiabilité, pas l'uniformité.

**Tests : valeurs à clé valide dont le corps ne peut désigner personne.** Une clé fausse ne protège
pas : elle se recalcule à partir du corps du numéro. D'où :
- IBAN : code pays `ZZ` (ISO 3166-1, usage utilisateur, jamais attribué à un pays) ;
- NIR : lieu de naissance `99 999`. Né à l'étranger, le lieu s'écrit 99 suivi du code Insee du pays
  (service-public.fr, F33078) ; aucun code pays Insee ne finit par 999, ni en 2026 ni depuis 1943
  (COG : codes 99100 à 99699). La piste « premier chiffre 0 ou 9 » n'a pas été retenue : aucune
  source ne l'établit, la documentation officielle dit seulement que « l'usage courant retient 1 et 2 » ;
- SIREN, SIRET : Insee et DINUM, personnes morales de droit public ;
- cartes : numéros de test publiés par Stripe (4242 4242 4242 4242, 5555 5555 5555 4444).
  le numéro Visa de test proposé au départ n'apparaît pas sur la page de Stripe consultée, il n'a
  pas été utilisé ;
- téléphones : racines Arcep réservées aux œuvres audiovisuelles ; courriels : `example.org`.
  Le test d'un numéro international non français (`+32`) est remplacé par `+33 1 99 00…` : aucune
  plage fictive belge n'a été sourcée.
Chaque valeur passe par le chemin de code du validateur de clé, qui ne contrôle ni le pays, ni le
lieu de naissance, ni le préfixe.

