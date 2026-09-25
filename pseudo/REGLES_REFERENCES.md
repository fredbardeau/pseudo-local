# Règles des références de dossier — forme testable

Ce document est la référence. « Le code est conforme » se vérifie contre lui, pas contre une
phrase en prose. Chaque règle a une formulation précise, puis des cas qui doivent matcher (`+`)
et des cas qui ne doivent pas matcher (`-`). Les cas sont nouveaux : aucun ne vient du jeu gelé
`evaluation/references_neuves/` ni du corpus `evaluation/corpus/`. Tout est fictif.

Format des cas : `+ texte => extrait attendu` (plusieurs extraits séparés par ` ; `),
`- texte` pour un cas où rien ne doit sortir. `\n` dans un cas désigne un saut de ligne.
**Statut des cas : non-régression.** Les cas sont écrits par celui qui écrit le code. Le test
exécutable qui les lit (`tests/test_regles_references.py`) empêche le code de dériver de ce
document ; il ne produit pas une mesure. Ce document est la source : le test lit les blocs de
cas ci-dessous, il n'en contient aucune copie.

Les cas se vérifient règles seules, modèle désactivé. Pour les niveaux 1, 2 et l'exclusion,
on regarde les références **masquées** ; pour le niveau 3, les **signalements**.

## Définitions communes

- **Mot** : suite de caractères sans blanc, délimitée par des blancs. Un deux-points isolé
  (` : `) n'est pas un mot. Un signe ouvrant en tête de mot (`(`, `«`, `"`, `'`) est ignoré
  pour lire le jeton qui suit.
- **Ponctuation forte** : `.` `;` `!` `?` en fin de mot, ou saut de ligne. Le point qui fait
  partie d'un déclencheur (`réf.`) n'en est pas une.
- **Jeton** : lettres ASCII (A-Z, a-z) et chiffres, en un ou plusieurs groupes séparés par `-`
  ou `/`. Ou bien : des chiffres groupés par milliers avec des espaces (`4 402 117`), la
  comparaison se faisant alors sur les chiffres sans les espaces.
- **Date**, formats exhaustifs : `j/m/aa`, `j/m/aaaa`, `j-m-aaaa`, `j.m.aaaa` (jour et mois sur
  1 ou 2 chiffres) ; `aaaa-mm-jj` ; `aaaa/mm/jj`.
- **Année** : exactement 4 chiffres, de 1900 à 2099.
- **Ordinal** : un nombre suivi de `e`, `er`, `re`, `ère`, `ème` ou `eme`, casse ignorée
  (`3e`, `1er`, `2ème`).
- **Montant** : un jeton suivi, après d'éventuels espaces, de `€`, `k€`, `euro`, `euros`, `EUR`
  ou `%`, casse ignorée.

## Niveau 1 — numéro annoncé par un déclencheur (masqué)

**Déclencheurs**, liste fermée, casse ignorée, singulier ou pluriel :
référence, reference, réf, ref, dossier, numéro, numero, facture, allocataire, adhérent,
bénéficiaire, cote, matricule, demande, contrat, convention, commande, sinistre, identifiant,
client ; et le **symbole numéro** : `n` ou `N` suivi de `°` (U+00B0) ou de `º` (U+00BA), collé au
numéro ou séparé de lui par des espaces.

Le déclencheur « réf » est le mot, pas le mot suivi d'un point : `réf.`, `réf :` et `réf`
seul sont la même chose.

**Fenêtre** : le numéro est l'un des 4 premiers mots qui suivent le déclencheur, sur la même
ligne, sans ponctuation forte avant lui. On retient le premier mot de la fenêtre qui a la forme
d'une référence.

**Forme d'une référence** : un jeton qui contient au moins un chiffre, ET qui a au moins
4 chiffres ou au moins une lettre, ET qui n'est ni une date, ni un ordinal, ni un montant.
Une année n'est PAS exclue : le déclencheur lève l'ambiguïté (« matricule 2019 »).

```cas
+ Mon numéro d'allocataire est le 3381904. => 3381904
+ Dossier N°58213 transmis au service. => 58213
+ Dossier Nº 58214 transmis au service. => 58214
+ Facture nº58215 réglée hier. => 58215
+ Le matricule 2019 est inactif. => 2019
+ Dossier 1987 archivé en cave. => 1987
+ Client : BX4410 en attente. => BX4410
+ Numéro de contrat : 4 402 117. => 4 402 117
+ Adhérent (réf. HB-3302) relancé. => HB-3302
+ Réf : QV-8812 à rappeler. => QV-8812
+ Votre ref WT5510 est enregistrée. => WT5510
+ La commande porte le numéro 88AZ12 cette fois. => 88AZ12
+ Sinistre déclaré sous la cote 90-5518. => 90-5518
+ Votre référence : QX-7781. => QX-7781
+ Dossier suivi sous le numéro 5519-B. => 5519-B
+ L'adhérent 90213 a réglé sa cotisation. => 90213
+ Merci d'indiquer votre numéro client, le 3 318 204, en objet. => 3 318 204
- Votre dossier du 3e trimestre est prêt.
- La facture du 2026/07/14 est réglée.
- Dossier du 14/07/2026 clos.
- Facture de 3 200 € à payer.
- Demande de 4500 € refusée.
- Le client a 3 enfants et 2 chiens.
- Dossier traité par l'équipe en mars, sans suite 88317.
- Référence : voir annexe.
- Le dossier du 4 juin est complet.
- Facture de 2 400 euros à régler.
- Demande de 3 500 € déposée.
- Le numéro 7 de la liste.
- Réunion au 2e étage, dossier en main.
- Numéro 12 du bulletin.
- Commande passée ; 55120 colis livrés.
- Le dossier\n45512 est rangé ailleurs.
- Voici le dossier. 70418 visiteurs cette année.
```

## Exclusion des textes publics (s'applique à toutes les couches)

Un identifiant est écarté s'il est **immédiatement précédé** de : un des mots loi, décret,
arrêté, ordonnance, article (casse ignorée), puis éventuellement le symbole numéro (variantes
ci-dessus), puis éventuellement un préfixe de code d'une lettre majuscule suivie d'un point
(`L.`, `R.`, `D.`), séparés uniquement par des espaces. Une détection du modèle qui commence
par l'un de ces mots est aussi écartée. Un de ces mots placé ailleurs dans la phrase n'écarte
rien.

```cas
+ L'article que vous citez concerne le dossier 55813. => 55813
+ Le versement est arrêté, dossier 6621-B. => 6621-B
+ La loi impose que votre dossier n° 60218 soit complet. => 60218
+ Décret en attente pour le dossier 7710-C. => 7710-C
- L'arrêté n° 2024-0087 fixe les tarifs.
- Le décret n°2023-1004 s'applique.
- La loi nº 2021-1109 est citée.
- L'ordonnance n° 2020-306 est abrogée.
- Selon le décret n° 2024-1180, le délai est de deux mois.
- L'arrêté n° 2025-0071 fixe les horaires.
```

Détections du modèle : format `- texte => extrait repéré par le modèle`, qui doit être écarté.

```cas-modele
- Voir la loi n° 2016-1321 pour le détail. => loi n° 2016-1321
- Selon l'article L. 3142-1 du code. => article L. 3142-1
```

## Niveau 2 — forme typée sans déclencheur (masquée)

Un mot qui n'est collé ni à une lettre, ni à un chiffre, ni à `-`, ni à `/`, formé d'au moins
**trois groupes** séparés par `-` ou `/`, chaque groupe composé uniquement de **majuscules**
A-Z et de chiffres ; avec **au moins une lettre** quelque part, ET **au moins un groupe
entièrement en chiffres d'au moins 3 chiffres**.

```cas
+ Transmis sous AB12-2026-0033 hier. => AB12-2026-0033
+ Voir PRJ/2025/0419 pour l'historique. => PRJ/2025/0419
+ Pièce QX-77-8841-B jointe au courrier. => QX-77-8841-B
+ Transmis sous PRJ-2024-00318 hier. => PRJ-2024-00318
- Le programme ERA-2030 démarre.
- Norme EN-12464 respectée.
- Séance du 2026-07-14 annulée.
- Le code AB-CD-EF est invalide.
- Version V2-R4-B1 déployée.
- Le lot ab-2025-0419 est en minuscules.
- Code postal F-75011 écrit ainsi.
```

## Niveau 3 — série nue (signalée, jamais masquée)

Une série signalée n'est jamais masquée : le test le vérifie sur chaque cas `+` de ce niveau.

Une suite de **5 à 12 chiffres**, non collée à une lettre, à un chiffre, à `-` ou à `/` ; qui
n'est ni la partie décimale ni la partie entière d'un nombre décimal (pas de `,` ou `.` suivi
d'un chiffre, ni précédé d'un chiffre) ; qu'aucune détection retenue ne chevauche ; qui n'est
pas un montant. Elle est signalée « à trancher », décochée, jamais masquée d'office.

L'exclusion des années ne s'applique pas ici par construction : une année a 4 chiffres, une
série nue en a au moins 5.

```cas
+ Famille Roux : 4418820 à vérifier. => 4418820
+ Voir 99812. => 99812
+ Voir 99813, merci. => 99813
+ Le code 123456789012 figure au dos. => 123456789012
+ Dossier papier de la famille : 7730021, à classer. => 7730021
- Le code 1234567890123 figure au dos.
- Montant : 12345,67 réglé.
- Montant retenu : 12345,50 € au total.
- Versement de 25000 € reçu.
- Versement de 25000 euros reçu.
- Le code 1234 à l'entrée.
- Le dossier n° 55812 est masqué, pas signalé.
```

## Trous connus

- **Un déclencheur, plusieurs numéros.** « Dossiers 55813 et 55814 » : seul le premier numéro
  de la fenêtre est retenu. Pour une série de 5 chiffres ou plus, le niveau 3 rattrape le
  suivant en signalement. Pour « Réf. AB-12 et AB-13 », rien ne rattrape : **fuite
  silencieuse**. Non corrigé à dessein : retenir tous les jetons de la fenêtre change le volume
  masqué et ferait bouger R4 et R5, alors qu'une seule mesure est prévue. À trancher après la
  mesure.
- **« No 12345 » n'est pas un déclencheur**, assumé. Deux raisons : ce n'est pas une variante
  typographique du symbole numéro mais une autre graphie, et l'accepter ouvrirait la porte à
  Num, Dos, Id ; surtout, une série de 5 chiffres ou plus est rattrapée en signalement par le
  niveau 3, donc l'omettre ne crée pas de fuite silencieuse.
- **Motif alphanumérique ambigu sans déclencheur ni structure** (proposé pour le niveau 3) :
  non couvert. Le définir après avoir vu les résultats serait une règle post-hoc.

## Options non retenues

- **N'accepter une année que si elle suit immédiatement le déclencheur** (« matricule 2019 »
  oui, « 245 demandes en 2025 » non). Formulée après avoir vu les résultats de la mesure du
  25/09/2026, et interdite par le critère R5, qui dit de ne plus ajouter de règle sous 96 % de
  précision. À reconsidérer sur les documents réels, pas sur le corpus fictif.

## Historique des décisions

- **Ordinaux exclus du niveau 1** : resserrement décidé pendant le codage, avant toute mesure,
  non annoncé à l'époque, régularisé le 25/09/2026.
- **Années avec déclencheur** : l'exclusion des années est retirée quand un déclencheur précède.
  Changement de règle énoncé le 25/09/2026, avant la mesure.
- **Symbole numéro** : `º` (U+00BA), `N°`, `Nº` et les formes collées ajoutés le 25/09/2026. Ce
  sont des variantes typographiques du déclencheur déjà accepté, pas un nouveau mot.
- **« Réf » sans point** : le déclencheur est le mot « réf » ; le point, les deux-points ou
  rien sont de la ponctuation. Clarification, pas extension, décidée le 25/09/2026 : même
  correction que pour `n°`, qui avait été traité comme un caractère précis.
- **Point facultatif appliqué à tous les déclencheurs** : correction code→règle, détectée en
  relisant le diff, avant toute mesure. En rendant « réf » valable sans point, le code avait
  rendu le point facultatif pour tous les déclencheurs, et avalait un point de fin de phrase
  (« Voici le dossier. 70418 visiteurs »). Remis en accord avec la définition de la ponctuation
  forte ; le cas correspondant a été ajouté.
- **Cas de tests/test_references.py versés ici** le 25/09/2026, puis fichier supprimé : une seule
  source. Le cas « 310 dossiers depuis 2023 » n'a pas été repris : il encodait l'exclusion des
  années, levée quand un déclencheur précède.
- **Exclusion des textes publics** : ramenée à « immédiatement précédé de » le 25/09/2026. La
  version précédente du code l'appliquait à toute la proposition, au-delà de la règle.
