# 🚆 Projet ELK – Mobilité Voyageurs (SNCF Lille)

## 📖 Description
Ce projet automatise la **collecte et l’indexation en temps réel** des départs de trains depuis la gare **Lille Flandres** à l’aide de :
- l’API publique **SNCF**,  
- **Elastic Cloud** (Elasticsearch + Kibana),  
- un script Python programmé pour s’exécuter **toutes les 15 minutes**.

Deux types de données sont indexées :
- **Historique** : fréquentation annuelle des gares (`frequentation-gares.csv`)
- **Temps réel** : départs actuels de Lille Flandres (API SNCF)

Un dashboard Kibana permet ensuite de visualiser :
- le trafic réel des trains
- ls fréquentations annuelles
- les lignes les plus actives de France
- et des KPI de mobilité voyageurs

---

## 🧩 Fonctionnalités principales

| Fonction | Description |
|-----------|-------------|
| `load_historique_data()` | Charge les données historiques depuis le CSV et les indexe dans Elasticsearch |
| `download_realtime_travel()` | Récupère les départs actuels via l’API SNCF |
| `load_travel_to_elastic()` | Envoie les données temps réel dans Elasticsearch |
| `id_lille()` | Recherche l’ID de la gare “Lille” via l’API |
| `schedule.every(15).minutes.do()` | Planifie l’exécution automatique toutes les 15 min |

---

## ⚙️ Prérequis

### 🔸 Python 3.10+
### 🔸 Dépendances
Installer les bibliothèques nécessaires :
```bash
pip install pandas requests elasticsearch python-dotenv schedule
```

### 🔸 Fichiers requis
- `script.py` → script principal  
- `frequentation-gares.csv` → données de fréquentation  
- `.env` → variables d’environnement (voir ci-dessous)

---

## 🔐 Configuration (fichier `.env`)

Créer un fichier nommé `.env` à la racine du projet contenant vos identifiants Elastic et votre clé API SNCF :

```bash
ELASTIC_CLOUD_ID="votre_cloud_id_elastic"
ELASTIC_USER="elastic"
ELASTIC_PASSWORD="votre_mot_de_passe"
TOKEN="votre_token_api_sncf"
```

⚠️ **Ne jamais versionner ce fichier** →  `.gitignore` :
```
.env
```

---

## 🚀 Lancer le script

Exécutez simplement :
```bash
python script.py
```

Le script :
- se connecte à Elastic Cloud,
- récupère les départs SNCF de Lille Flandres,
- les envoie dans l’index `sncf_lille_realtime`,
- et relance automatiquement le traitement toutes les 15 minutes.

Les logs sont enregistrés dans :
```
sncf_lille.log
```

---

## 🕒 Automatisation

Le module [`schedule`](https://pypi.org/project/schedule/) gère la planification :
```python
schedule.every(15).minutes.do(load_travel_to_elastic)
```

Pour changer la fréquence :
```python
schedule.every(30).minutes.do(load_travel_to_elastic)  # toutes les 30 minutes
```

## 🧱 Structure du projet

```
📁 Projet_ELK_SNCF/
 ├─ script.py                 # Script principal
 ├─ frequentation-gares.csv   # Données historiques
 ├─ .env                      # Identifiants Elastic + API SNCF
 ├─ sncf_lille.log            # Logs d’exécution
 ├─ README.md                 # Documentation
```

---

## 🧠 Exemple de logs

```
2025-11-12 14:00:00 [INFO] 🚆 Indexation temps réel démarrée...
2025-11-12 14:00:02 [INFO] 48 départs récupérés depuis Lille.
2025-11-12 14:00:03 [INFO] 48 documents indexés dans sncf_lille_realtime.
2025-11-12 14:15:00 [INFO] 🚆 Indexation temps réel démarrée...
```

---

## 🧰 Améliorations possibles
- Déploiement du script en tâche cron ou service système.
- Ajout d’une API interne Flask pour requêter les données Elastic.
- Création automatique des index avec mapping personnalisé.
- Enrichissement des données (retards, perturbations, météo...).

---

## 👨‍💻 Auteur
**Kyllian Jean-Gilles**  
Projet individuel – Enigma-School  
Thème : *Mobilité Voyageurs SNCF – Analyse et Indexation temps réel avec ELK Stack*  
Année : 2025  - 2026
