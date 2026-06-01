-- ============================================================================
-- SCRIPT D'INITIALISATION - TABLE CLIENTS NEOVOLT
-- Plateforme de Données d'Énergie pour Distributeur
-- ============================================================================

-- Garantit la réversibilité et re-exécutabilité
DROP TABLE IF EXISTS clients CASCADE;

-- ============================================================================
-- CRÉATION DE LA TABLE CLIENTS
-- ============================================================================
CREATE TABLE clients (
  id_client VARCHAR(10) PRIMARY KEY,
  segment VARCHAR(20) NOT NULL,
  commune VARCHAR(50) NOT NULL,
  code_postal VARCHAR(10) NOT NULL,
  date_entree DATE,
  nb_personnes_foyer INT,
  surface_m2 INT,
  
  -- Contraintes nommées pour faciliter le débuggage
  CONSTRAINT chk_segment CHECK (segment IN ('particulier', 'petit_pro', 'entreprise', 'collectivite')),
  CONSTRAINT chk_nb_personnes_foyer CHECK (nb_personnes_foyer IS NULL OR (nb_personnes_foyer >= 1 AND nb_personnes_foyer <= 5))
);

-- ============================================================================
-- COMMENTAIRES DE DOCUMENTATION - TABLE
-- ============================================================================
COMMENT ON TABLE clients IS 'Table centralisée des clients Neovolt. Stocke les métadonnées commerciales et géographiques de tous les clients du distributeur d''énergie.';

-- ============================================================================
-- COMMENTAIRES DE DOCUMENTATION - COLONNES
-- ============================================================================
COMMENT ON COLUMN clients.id_client IS 'Identifiant unique du client au format CLI-XXXXX. Plage : CLI-00001 à CLI-00700. Clé primaire.';
COMMENT ON COLUMN clients.segment IS 'Segment commercial du client. Valeurs autorisées : ''particulier'', ''petit_pro'', ''entreprise'', ''collectivite''. Utilisé pour la segmentation des analyses énergétiques.';
COMMENT ON COLUMN clients.commune IS 'Nom de la commune ou zone géographique associée au client. Obligatoire pour la géolocalisation et rapports territoriaux.';
COMMENT ON COLUMN clients.code_postal IS 'Code postal de la localité du client. Format FR standard (5 chiffres). Obligatoire.';
COMMENT ON COLUMN clients.date_entree IS 'Date d''entrée en relation commerciale avec Neovolt. Utilisée pour l''analyse de rétention client et cohortes temporelles.';
COMMENT ON COLUMN clients.nb_personnes_foyer IS 'Nombre de personnes au foyer (résidentiel uniquement). Plage autorisée : 1 à 5 si renseigné. NULL pour les segments non-résidentiels. Utilisé pour normaliser les consommations énergétiques.';
COMMENT ON COLUMN clients.surface_m2 IS 'Surface utile du local en mètres carrés. Utilisée pour la normalisation des consommations énergétiques et analyses comparatives d''efficacité énergétique.';

-- ============================================================================
-- CRÉATION DE LA TABLE COMPTEURS
-- ============================================================================

-- Garantit la réversibilité et re-exécutabilité
DROP TABLE IF EXISTS compteurs CASCADE;

CREATE TABLE compteurs (
  id_pdl VARCHAR(12) PRIMARY KEY,
  id_client VARCHAR(10) NOT NULL,
  zone VARCHAR(30) NOT NULL,
  type_client VARCHAR(20) NOT NULL,
  puissance_souscrite_kva INT NOT NULL,
  type_chauffage VARCHAR(20),
  type_compteur VARCHAR(20) NOT NULL,
  date_pose DATE,
  statut VARCHAR(20) NOT NULL,
  
  -- Clé étrangère vers clients avec suppression en cascade
  CONSTRAINT fk_compteur_client FOREIGN KEY (id_client) REFERENCES clients(id_client) ON DELETE CASCADE,
  
  -- Contraintes nommées pour faciliter le débuggage
  CONSTRAINT chk_compteur_zone CHECK (zone IN ('Val-Nord', 'Centre-Ville', 'Plateau-Est', 'Rives-Sud', 'Zone-Industrielle', 'Coteaux-Ouest', 'Bourg-Ancien', 'Parc-Tertiaire')),
  CONSTRAINT chk_type_client CHECK (type_client IN ('residentiel', 'professionnel', 'industriel')),
  CONSTRAINT chk_puissance_kva CHECK (puissance_souscrite_kva IN (6, 9, 12, 36, 120, 250)),
  CONSTRAINT chk_type_chauffage CHECK (type_chauffage IS NULL OR type_chauffage IN ('electrique', 'gaz', 'reseau_chaleur', 'autre')),
  CONSTRAINT chk_type_compteur CHECK (type_compteur IN ('communicant', 'ancien')),
  CONSTRAINT chk_statut_contrat CHECK (statut IN ('actif', 'resilie'))
);

-- ============================================================================
-- COMMENTAIRES DE DOCUMENTATION - TABLE COMPTEURS
-- ============================================================================
COMMENT ON TABLE compteurs IS 'Table centralisée des compteurs Neovolt. Stocke les métadonnées techniques des points de livraison (PDL) associés aux clients.';

-- ============================================================================
-- COMMENTAIRES DE DOCUMENTATION - COLONNES COMPTEURS
-- ============================================================================
COMMENT ON COLUMN compteurs.id_pdl IS 'Identifiant unique du point de livraison (compteur) au format PDL-XXXXXX. Plage : PDL-000001 à PDL-000700. Clé primaire.';
COMMENT ON COLUMN compteurs.id_client IS 'Identifiant du client rattaché. Clé étrangère vers la table clients. Suppression en cascade si client supprimé.';
COMMENT ON COLUMN compteurs.zone IS 'Zone géographique de desserte. Valeurs autorisées : ''Val-Nord'', ''Centre-Ville'', ''Plateau-Est'', ''Rives-Sud'', ''Zone-Industrielle'', ''Coteaux-Ouest'', ''Bourg-Ancien'', ''Parc-Tertiaire''.';
COMMENT ON COLUMN compteurs.type_client IS 'Catégorie d''usage du PDL. Valeurs autorisées : ''residentiel'', ''professionnel'', ''industriel''. Utilisé pour segmentation tarifaire et analyses.';
COMMENT ON COLUMN compteurs.puissance_souscrite_kva IS 'Puissance souscrite en kVA. Valeurs autorisées : 6, 9, 12, 36, 120, 250. Détermine la capacité maximale du PDL.';
COMMENT ON COLUMN compteurs.type_chauffage IS 'Mode de chauffage déclaré du logement/local. Valeurs autorisées : ''electrique'', ''gaz'', ''reseau_chaleur'', ''autre''. NULL pour PDL non-résidentiels. Utilisé pour analyses énergétiques.';
COMMENT ON COLUMN compteurs.type_compteur IS 'Génération du compteur installé. Valeurs autorisées : ''communicant'' (télérelevé), ''ancien'' (relevé manuel).';
COMMENT ON COLUMN compteurs.date_pose IS 'Date d''installation du compteur. Utilisée pour suivi du cycle de vie des équipements.';
COMMENT ON COLUMN compteurs.statut IS 'État du contrat associé au PDL. Valeurs autorisées : ''actif'' (en service), ''resilie'' (contrat terminé).';

-- ============================================================================
-- CRÉATION DE LA TABLE METEO
-- ============================================================================

-- Garantit la réversibilité et re-exécutabilité
DROP TABLE IF EXISTS meteo CASCADE;

CREATE TABLE meteo (
  date DATE NOT NULL,
  zone VARCHAR(50) NOT NULL,
  temp_moyenne_c DECIMAL(4,1),
  temp_min_c DECIMAL(4,1),
  temp_max_c DECIMAL(4,1),
  dju_chauffage DECIMAL(4,1) DEFAULT 0.0,
  
  -- Clé primaire composite sur (date, zone)
  PRIMARY KEY (date, zone),
  
  -- Contraintes nommées pour faciliter le débuggage
  CONSTRAINT chk_meteo_zone CHECK (zone IN ('Val-Nord', 'Centre-Ville', 'Plateau-Est', 'Rives-Sud', 'Zone-Industrielle', 'Coteaux-Ouest', 'Bourg-Ancien', 'Parc-Tertiaire')),
  CONSTRAINT chk_temp_coherence CHECK (temp_min_c <= temp_max_c)
);

-- ============================================================================
-- COMMENTAIRES DE DOCUMENTATION - TABLE METEO
-- ============================================================================
COMMENT ON TABLE meteo IS 'Table centralisée des données météorologiques Neovolt. Stocke les observations météo quotidiennes par zone géographique, indispensables pour corréler consommations énergétiques et conditions climatiques.';

-- ============================================================================
-- COMMENTAIRES DE DOCUMENTATION - COLONNES METEO
-- ============================================================================
COMMENT ON COLUMN meteo.date IS 'Date de l''observation météo. Format DATE. Composante de la clé primaire (date, zone).';
COMMENT ON COLUMN meteo.zone IS 'Zone géographique de l''observation. Valeurs autorisées : ''Val-Nord'', ''Centre-Ville'', ''Plateau-Est'', ''Rives-Sud'', ''Zone-Industrielle'', ''Coteaux-Ouest'', ''Bourg-Ancien'', ''Parc-Tertiaire''. Composante de la clé primaire (date, zone). Permet jointure avec compteurs.zone.';
COMMENT ON COLUMN meteo.temp_moyenne_c IS 'Température moyenne quotidienne en degrés Celsius. Valeur décimale à 1 décimale (ex: 15.2°C).';
COMMENT ON COLUMN meteo.temp_min_c IS 'Température minimale quotidienne en degrés Celsius. Valeur décimale à 1 décimale. Doit être inférieure ou égale à temp_max_c.';
COMMENT ON COLUMN meteo.temp_max_c IS 'Température maximale quotidienne en degrés Celsius. Valeur décimale à 1 décimale. Doit être supérieure ou égale à temp_min_c.';
COMMENT ON COLUMN meteo.dju_chauffage IS 'Degré-Jour Unifié (DJU) de chauffage. Indice thermique indispensable pour corréler consommation énergétique et rigueur climatique. Calculé si Temp < 17°C alors DJU = 17 - Temp, sinon DJU = 0. Défaut 0.0.';

-- ============================================================================
-- CRÉATION DE LA TABLE DE FAITS RELEVES_CONSOMMATION
-- ============================================================================

-- Garantit la réversibilité et re-exécutabilité
DROP TABLE IF EXISTS releves_consommation CASCADE;

CREATE TABLE releves_consommation (
  id_pdl VARCHAR(12) NOT NULL,
  date DATE NOT NULL,
  consommation_kwh DECIMAL(8,2),
  zone VARCHAR(50),
  
  -- Clé primaire composite sur (id_pdl, date)
  PRIMARY KEY (id_pdl, date),
  
  -- Clé étrangère vers compteurs avec suppression en cascade
  CONSTRAINT fk_releves_compteur FOREIGN KEY (id_pdl) REFERENCES compteurs(id_pdl) ON DELETE CASCADE,
  
  -- Contraintes nommées pour faciliter le débuggage et la qualité des données
  CONSTRAINT chk_releves_zone CHECK (zone IN ('Val-Nord', 'Centre-Ville', 'Plateau-Est', 'Rives-Sud', 'Zone-Industrielle', 'Coteaux-Ouest', 'Bourg-Ancien', 'Parc-Tertiaire')),
  CONSTRAINT chk_consommation_positive CHECK (consommation_kwh >= 0)
);

-- ============================================================================
-- COMMENTAIRES DE DOCUMENTATION - TABLE RELEVES_CONSOMMATION
-- ============================================================================
COMMENT ON TABLE releves_consommation IS 'Table de faits centralisée des relevés de consommation énergétique Neovolt. Stocke les données quotidiennes de consommation pour tous les compteurs. Volumétrie estimée : +500 000 lignes. Structure optimisée pour séries temporelles et requêtes analytiques du Data Scientist.';

-- ============================================================================
-- COMMENTAIRES DE DOCUMENTATION - COLONNES RELEVES_CONSOMMATION
-- ============================================================================
COMMENT ON COLUMN releves_consommation.id_pdl IS 'Identifiant du point de livraison (compteur). Clé étrangère vers compteurs.id_pdl. Composante de la clé primaire (id_pdl, date).';
COMMENT ON COLUMN releves_consommation.date IS 'Date du relevé quotidien. Format DATE. Composante de la clé primaire (id_pdl, date). Essentielle pour analyses temporelles et jointures météo.';
COMMENT ON COLUMN releves_consommation.consommation_kwh IS 'Énergie consommée quotidienne exprimée en kilowatt-heure (kWh). Précision : 2 décimales. Doit être >= 0 (rejette les valeurs négatives aberrantes).';
COMMENT ON COLUMN releves_consommation.zone IS 'Zone géographique du PDL. Copie dénormalisée de compteurs.zone pour accélérer les requêtes analytiques sans jointures lourdes. Valeurs autorisées : ''Val-Nord'', ''Centre-Ville'', ''Plateau-Est'', ''Rives-Sud'', ''Zone-Industrielle'', ''Coteaux-Ouest'', ''Bourg-Ancien'', ''Parc-Tertiaire''.';

-- ============================================================================
-- INDEXES DE PERFORMANCE (Optimisation Analytique)
-- ============================================================================
CREATE INDEX idx_releves_date ON releves_consommation (date);
COMMENT ON INDEX idx_releves_date IS 'Index B-Tree sur date pour accélérer les requêtes analytiques par plage temporelle.';

CREATE INDEX idx_releves_zone_date ON releves_consommation (zone, date);
COMMENT ON INDEX idx_releves_zone_date IS 'Index composite (zone, date) pour optimiser les requêtes analytiques segmentées par zone. Support rapide pour API FastAPI et analyses Data Scientist.';


