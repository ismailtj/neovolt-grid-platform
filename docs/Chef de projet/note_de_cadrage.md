# Note de cadrage stratégique & business case — Programme Néovolt Grid+

**Commanditaire :** Direction des Systèmes d'Information de Néovolt
**Volet :** Chef de Projet IT & Data
**Documents liés :** `pilotage_neovolt_cdp.xlsx` (business case, budget, planning, RACI, risques, gouvernance, pilotage) · `docs/architecture.svg`

> Cette note couvre les 5 livrables du volet : cadrage & business case (§1-6), plan de projet (§7), gouvernance des données (§8), conduite du changement (§9), et renvoie au tableau de bord de pilotage du classeur. Elle s'appuie sur un **prototype déjà construit et validé**, ce qui sécurise les décisions d'investissement.

---

## 1. Reformulation du besoin

Néovolt, distributeur régional d'énergie (600 000 points de livraison, infrastructure critique), produit une masse de données de compteurs communicants qu'il exploite mal : données dispersées et de qualité inégale, pics de consommation mal anticipés (achats d'énergie d'urgence coûteux), fraudes détectées avec des mois de retard, décideurs sans tableaux de bord fiables, sécurité jamais auditée, et aucun pilotage d'ensemble.

Le besoin : **transformer la donnée en décisions**, tout en **maîtrisant le risque** (vie privée, sécurité) et en **pilotant** l'investissement.

## 2. Périmètre

**Réalisé dans le prototype :** plateforme de données centralisée (base PostgreSQL alimentée par un pipeline ETL), analyses et tableaux de bord décisionnels, modèle de détection de fraude, modèle de prévision de consommation, API d'exposition des résultats.

**Hors périmètre du prototype :** mise en production sur les systèmes réels, connexion à l'environnement SCADA (volontairement isolé), déploiement à l'échelle des 600 000 PDL (l'architecture est pensée pour, le prototype travaille sur l'échantillon fourni).

## 3. Objectifs mesurables

| Objectif | Indicateur cible | État (prototype) |
|---|---|---|
| Fiabiliser la donnée | Données disponibles à J+1, qualité tracée | ✅ Pipeline ETL idempotent, base validée par contraintes |
| Détecter les anomalies plus tôt | Détection sous 7 jours (vs plusieurs mois) | ✅ Modèle ROC-AUC 0,92 ; ~79 % des fraudes dans ~37 contrôles |
| Anticiper la demande | Prévision exploitable pour les achats | ✅ Prévision J+1 à ~4,5 % d'erreur |
| Outiller les décideurs | Tableaux de bord par profil | ✅ 3 vues (exploitation, finance, relation client) |
| Sécuriser & se conformer | Notification incident < 24 h ; RGPD/NIS 2 | Cadré (volet sécurité) |
| Disponibilité plateforme | 99,5 % | Cible de production |

## 4. Hypothèses explicites

Regroupées dans l'onglet *Hypotheses* du classeur (modifiables, recalcul automatique). Principales : parc de **600 000 PDL**, énergie distribuée **~16,2 TWh/an** (extrapolée des relevés), pertes non techniques estimées à **1,2 %** de l'énergie distribuée, valorisées à **0,10 €/kWh**, part récupérable **15 %** en régime établi. Coûts unitaires : ceux du dossier de cas. Ces hypothèses sont des **valeurs de cadrage à valider** avec la Direction Financière.

## 5. Contraintes

- **Techniques :** coexistence avec l'existant, **isolement strict du SCADA**, architecture pensée pour la montée en charge, **hébergement des données dans l'UE**, réversibilité (formats ouverts, conteneurs — pas de verrou fournisseur).
- **Réglementaires :** RGPD (base légale, minimisation, conservation, droits, **AIPD** pour la fraude), **NIS 2** (continuité, notification), bonnes pratiques ISO 27001, et **décision automatisée défavorable jamais sans intervention humaine**.
- **Budgétaires :** enveloppe indicative de **450 000 €** pour la phase 1.

## 6. Business case (synthèse)

| Indicateur | Valeur |
|---|---|
| Budget phase 1 | **≈ 398 000 €** (marge sous l'enveloppe de 450 k€) |
| Bénéfice annuel — année 1 | **≈ 1,3 M€** |
| Bénéfice annuel — régime établi | **≈ 3,2 M€** |
| Retour sur investissement | **≈ 4 mois** |
| Bénéfice net cumulé sur 3 ans | **≈ 6,9 M€** |

Le détail (gisements A/B/C, budget ligne à ligne, test de sensibilité) est dans le classeur. **Argument clé :** le prototype étant déjà fonctionnel (modèles validés, plateforme opérationnelle), le risque d'échec technique du programme est fortement réduit — l'investissement porte sur l'industrialisation, pas sur une faisabilité incertaine.

## 7. Plan de projet (lots, jalons, priorisation)

Le programme est découpé en **8 lots** (L0 à L7), séquencés par dépendances et priorisés par valeur/risque (onglet *Planning*). **Choix structurant :** la détection de fraude est priorisée **avant** la prévision — gain plus rapide et mesurable (gisement de pertes non techniques), modèle plus simple, et signal de terrain disponible (24 fraudes confirmées). La prévision exige le croisement météo et produit surtout de la valeur en régime établi. Ce choix s'est confirmé à l'exécution : la fraude a donné un résultat actionnable (liste de suspects) dès le prototype.

## 8. Gouvernance des données

Chaque domaine a un **propriétaire** (Data Owner) et un **intendant** (Steward), une **classification** (public / interne / personnel / confidentiel) et une **règle d'accès** (onglet *Gouvernance*). Principes appliqués : minimisation, pseudonymisation pour la data science, accès aux journaux de sécurité restreint au RSSI/SOC, cas de fraude jamais exposés côté client. La qualité est garantie « par conception » : les contraintes de la base (clés, `CHECK`) rejettent toute donnée non conforme, et le pipeline ETL trace ses corrections.

## 9. Conduite du changement

**Acteurs impactés :** exploitants réseau, service client, décideurs financiers, représentants du personnel.

**Freins anticipés :** crainte d'une surveillance des salariés et des clients, défiance envers l'automatisation (peur d'accuser un client à tort), attachement aux fichiers Excel personnels.

**Leviers :** implication précoce des métiers dans la conception des tableaux de bord (co-conception), **transparence** sur l'usage des données, **« humain dans la boucle »** systématique pour toute décision de fraude, formation ciblée, et démonstration de **quick wins** (premiers suspects détectés, premier dashboard utile). Démarche en quatre temps : sensibiliser → former → accompagner → ancrer. *Note : l'analyse des réclamations a révélé une satisfaction client basse (2,45/5) — un argument supplémentaire pour embarquer le service client autour d'outils qui l'aident concrètement.*

## 10. Risques principaux

Les 8 risques majeurs sont consignés dans le registre (onglet *Risques*, score = probabilité × impact). Le seul risque **critique** (score ≥ 15) est le **faux positif de la détection de fraude** : un client accusé à tort. Parade : seuil prudent, **revue humaine obligatoire**, AIPD. Viennent ensuite la fuite de données personnelles et la fragilisation du SCADA, traités par cloisonnement et isolement.

---

## Synthèse des 5 livrables du volet

| Livrable attendu | Où le trouver |
|---|---|
| Note de cadrage + business case | Ce document (§1-6) + onglet *BusinessCase* |
| Plan de projet (lots, jalons, priorisation, risques) | §7 + onglets *Planning* et *Risques* |
| Plan de gouvernance des données (RACI) | §8 + onglets *Gouvernance* et *RACI* |
| Plan de conduite du changement | §9 |
| Tableau de bord de pilotage | Onglet *Synthese* |
