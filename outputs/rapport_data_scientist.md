# Rapport Data Scientist — Programme Néovolt Grid+

**Cas d'usage traités :** (1) détection de fraude sur les compteurs ; (2) prévision de la consommation réseau.
**Livrables associés :** scripts `06`→`10`, `suspects_fraude.csv`, `prevision_test.csv`, `models/model_card.json`.

---

## 1. Démarche expérimentale

La même rigueur a guidé les deux cas d'usage : **comprendre les données avant de modéliser**, **commencer par une baseline simple**, puis n'ajouter de la complexité que si elle apporte une valeur mesurable.

**Détection de fraude.** Les 3 types de fraude (sous-comptage, branchement illicite, compteur trafiqué) ont une signature commune : le compteur enregistre *moins* que la réalité. On a construit des features de comportement par compteur, dont la plus discriminante est le **ratio de chute** (consommation des 90 derniers jours / 90 premiers jours) : médiane 0,49 chez les fraudeurs contre 0,94 chez les clients sains. Trois approches ont été comparées : détection non supervisée (Isolation Forest), règle simple (tri par ratio de chute), et modèle supervisé (Random Forest).

**Prévision de consommation.** Série journalière de la demande totale, enrichie de variables calendaires, de **retards** (consommation de la veille et de la semaine précédente) et de la **météo** (température, degrés-jour). Validation strictement **chronologique** (entraînement sur le passé, test sur les 6 derniers mois).

## 2. Résultats et métriques

**Le piège de l'exactitude.** Avec 96,6 % de compteurs sains, un modèle qui prédit « tout le monde est honnête » atteint 96,6 % d'exactitude tout en détectant **zéro fraude**. C'est pourquoi l'évaluation repose sur des métriques adaptées au déséquilibre : précision, rappel, PR-AUC, et **recall@N** (part des fraudes connues retrouvées dans le top N des suspects).

| Cas d'usage | Métrique clé | Résultat |
|---|---|---|
| Détection de fraude | ROC-AUC | **0,92** |
| Détection de fraude | Recall@50 (top 50 suspects) | **88 %** des fraudes connues |
| Détection de fraude | Seuil recommandé 0,20 | rappel 79 %, ~37 compteurs signalés |
| Prévision conso | MAPE à J+1 | **4,5 %** (vs baseline saisonnière 6,1 %) |

**Deux enseignements méthodologiques forts.** (1) En non supervisé, la **règle simple bat l'Isolation Forest** : le signal étant concentré dans une variable, le modèle complexe le dilue. (2) En supervisé, le **Random Forest dépasse la règle simple** (88 % vs 67 % au top 50) en combinant le ratio de chute *et* la consommation relative aux pairs — il rattrape ainsi les fraudes « sans chute » (frauduleuses dès le départ). La complexité n'est utile que lorsqu'elle est *guidée* par le signal.

## 3. Évaluation critique : limites et biais

**Limites des données.** Seulement **24 fraudes confirmées** : c'est très peu pour un apprentissage robuste, et les métriques ont une forte incertitude. Surtout, le groupe « normal » contient **presque certainement des fraudes non encore détectées** (l'énoncé le dit) : nos étiquettes sont donc *bruitées*, ce qui sous-estime la vraie performance (des « faux positifs » du modèle pourraient être de vraies fraudes ignorées). La représentativité de l'échantillon de 700 compteurs vis-à-vis des 600 000 réels est une hypothèse.

**Limites des modèles.** Le ratio de chute ne détecte pas une fraude présente *dès l'origine* (rien ne « baisse »). La prévision à 4,5 % se dégrade lors d'événements rares non vus à l'entraînement (vague de froid exceptionnelle, jour férié atypique).

**Biais et risques éthiques.** Le risque majeur est le **faux positif** : accuser à tort un client honnête. Conséquences possibles — atteinte à la réputation, discrimination involontaire si le modèle signale plus certaines zones ou certains profils. Parades : (1) le modèle ne **décide jamais seul** — il produit une liste de suspects soumise à **revue humaine obligatoire** (exigence RGPD sur les décisions automatisées) ; (2) un **contrôle d'équité** par type de client et par zone doit précéder tout déploiement ; (3) une **AIPD** (analyse d'impact RGPD) est requise pour ce traitement.

## 4. MLOps : industrialisation

**Versioning.** Modèles sauvegardés avec version + horodatage ; code sous Git ; données de référence figées. **Suivi d'expériences.** Métriques journalisées dans une *model card* (`model_card.json`) — en production, un outil comme MLflow. **Reproductibilité.** Graine aléatoire fixée, dépendances épinglées, pipeline de features sauvegardé avec le modèle.

**Déploiement.** Fraude : **scoring batch quotidien** (J+1), liste de suspects transmise à l'équipe anti-fraude via l'API (volet Ingénierie). Prévision : **exécution quotidienne** alimentant la décision d'achat d'énergie. **Surveillance.** Détection de **dérive des données** (la distribution des consommations change-t-elle ?) et de **dérive du modèle** (le rappel baisse-t-il ?) ; ré-entraînement déclenché si la performance franchit un seuil d'alerte ; supervision des volumes de suspects signalés.

## 5. Ouverture (perspective)

Une brique d'**IA générative** pourrait traduire le score d'un compteur suspect en **explication lisible** pour l'agent (« consommation divisée par deux en septembre, 40 % sous les clients similaires »), accélérant la revue humaine sans jamais se substituer à elle. C'est une piste d'amélioration, à encadrer pour éviter toute sur-confiance dans l'explication générée.
