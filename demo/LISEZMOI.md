# Corpus de démonstration

**Corpus de démonstration, fictif par construction. Aucune mesure n'en est tirée, ni ne peut l'être.**

Ces deux documents servent à essayer l'outil, rien d'autre. Ils ne remplacent pas le corpus de test
gelé et ne servent jamais à mesurer quoi que ce soit.

## Pourquoi chaque donnée ne peut correspondre à personne

Une clé de contrôle fausse ne suffirait pas : elle se recalcule à partir du reste du numéro. Ce qui
rend ces données fictives, c'est leur corps, impossible ou non personnel.

| Donnée | Valeur | Pourquoi elle ne peut désigner personne |
|---|---|---|
| Téléphones | `01 99 00 12 34`, `05 36 49 00 11`, `06 39 98 56 78` | Racines réservées aux œuvres audiovisuelles par l'Arcep (plan national de numérotation, § 2.5 : 01 99 00, 02 61 91, 03 53 01, 04 65 71, 05 36 49, 06 39 98), qui « ne peuvent pas faire l'objet d'une attribution ». |
| Courriels | `@example.org`, `@example.com`, `@example.net` | Domaines réservés à la documentation par la RFC 2606. |
| IBAN | `ZZ43 0000 0000 0000 0000 0000 123` | Clé valide, mais `ZZ` est un code « à usage utilisateur » de l'ISO 3166-1, jamais attribué à un pays. |
| N° de sécurité sociale | `2 85 12 99 999 456 76` | Clé valide, lieu de naissance `99 999` impossible : né à l'étranger, le lieu s'écrit 99 suivi du code Insee du pays (service-public.fr, fiche F33078), et aucun code pays Insee ne finit par 999, ni en 2026 ni depuis 1943 (Code officiel géographique). |
| SIRET | `120 027 016 00563` | Siège de l'Insee, personne morale de droit public, publié au répertoire Sirene : pas une donnée personnelle. |
| Carte | `4242 4242 4242 4242` | Numéro de test publié par Stripe (docs.stripe.com/testing). |
| Adresse | `12 rue de l'Exemple, 00100 Nullepart` | Aucun code postal ne commence par `00` : il n'existe pas de département 00. |
| Noms | Alice Exemple, Bruno Fictif | Aucun nom ne peut être garanti fictif ; ceux-ci sont choisis pour être manifestement inventés et ne sont associés à aucune autre donnée réelle. |

## Ce que l'outil en fera (constaté le 25/09/2026)

- Téléphones, courriels, IBAN, n° de sécurité sociale, SIRET, carte, adresse et référence
  `DEM-2026-00042` : masqués par les règles, clés de contrôle vérifiées quand elles existent.
- Noms : masqués par le modèle seulement (règles seules : laissés en clair).
- « Le trésorier de l'association partenaire » : jamais vu. C'est à la relecture de le repérer.
