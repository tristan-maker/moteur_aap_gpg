# 🏔️ Moteur Automatisé d'Appels à Projets — Gravir Pour Grandir (GPG)

Ce dépôt contient le moteur hybride (**85 % Python déterministe / 15 % IA générative**) de veille, de qualification et de génération automatique de dossiers de subvention/mécénat pour l'association **Gravir Pour Grandir** (Loi 1901 d'intérêt général).

## 🎯 Philosophie : Pourquoi 85 % Python / 15 % IA ?

Un agent IA classique laissé en autonomie complète risque d'inventer des chiffres financiers, de modifier l'identité juridique de l'association ou de candidater à des appels à projets expirés.

Notre architecture sépare strictement les responsabilités :
* **15 % IA Générative (`Gemini 3.8 Flash` via Google ADK)** :
  * Ratisse le web français (requêtes Grand Angle 360° + subventions publiques IDF/AURA + rotation de 25 grandes fondations).
  * Lit les critères du financeur et choisit parmi nos 4 grilles budgétaires pré-approuvées (`ALPINISME_48K`, `ALPINISME_COMPLET_54K`, `VOILE_48K`, `PASSAGE_ECHELLE_3_ANS`).
  * Rédige uniquement **un paragraphe d'accroche sur-mesure** (strictement plafonné à 700 caractères).
* **85 % Code Pur Python (100 % Déterministe)** :
  * **Mémoire Anti-Doublons (`crm_tracker.py`)** : Lit le Google Sheets CRM avant toute recherche pour ignorer les financeurs déjà traités.
  * **Chasseur de Guichet (`portal_finder.py`)** : Traverse les sites relais (*Avise*, *Carenews*) pour extraire le lien direct de dépôt (`/deposer-un-projet/`).
  * **Auditeur HTML de Dates (`page_date_auditor.py`)** : Télécharge la vraie page web du financeur, extrait les dates en français et bloque tout dossier expiré ou à moins de `J+7`.
  * **Détecteur de Parrainage Salarié (`sponsorship_detector.py`)** : Détecte si un parrain interne est requis et génère le lien de recherche LinkedIn X-Ray + la note d'approche de 300 caractères.
  * **Moteur Budgétaire (`budget_engine.py`)** : Calcule et équilibre le budget prévisionnel au centime près (`Decimal`).
  * **Assembleur Data Room (`workspace_packager.py`)** : Crée automatiquement le dossier Google Drive contenant le Google Docs pré-rédigé, le Google Sheets budgétaire et la copie des 6 pièces administratives du Coffre-Fort GPG.

## 📂 Architecture des Fichiers

| Fichier | Rôle dans le moteur |
| :--- | :--- |
| `gpg_agent/__init__.py` | Point d'entrée exposant `root_agent` pour Google ADK / Cloud Run |
| `gpg_agent/agent.py` | Orchestration séquentielle des 3 sous-agents ADK + politique anti-429 |
| `gpg_agent/config.py` | Identité juridique certifiée GPG, preuves d'impact, textes verrouillés & requêtes 360° |
| `gpg_agent/schemas.py` | Contrat de données Pydantic (`SemanticRoutingDecision`) imposé au routeur IA |
| `gpg_agent/compliance_enforcer.py` | Garde-fou central (filtres d'exclusion + assemblage final du dossier) |
| `gpg_agent/portal_finder.py` | Scraper traversant les annuaires relais vers le guichet officiel de dépôt |
| `gpg_agent/page_date_auditor.py` | Auditeur HTML de dates limites réelles en français |
| `gpg_agent/sponsorship_detector.py` | Détecteur de parrainage salarié & générateur du Kit LinkedIn X-Ray |
| `gpg_agent/budget_engine.py` | Moteur comptable en `Decimal` (équilibre strict Charges / Produits) |
| `gpg_agent/workspace_packager.py` | Création du dossier Drive, Google Docs, Sheets et copie des 6 pièces du Coffre-Fort |
| `gpg_agent/crm_tracker.py` | Lecture anti-doublons et écriture dans le Google Sheets CRM Maître (Colonnes A à J) |
| `test_engine.py` | Suite de 6 tests unitaires déterministes (`pytest`) |
| `run_test_drive.py` | Script de test isolé de création d'une Data Room Google Drive |
| `run_test_veille.py` | Script de test de bout en bout (Veille Web -> Drive -> CRM) |
