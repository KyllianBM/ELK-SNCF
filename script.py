import os
from dotenv import load_dotenv
from datetime import datetime, timezone
from requests.auth import HTTPBasicAuth
from elasticsearch import Elasticsearch, helpers
import requests, pandas as pd, re, logging, schedule, time


# On charge les variables d’environnements
load_dotenv()

# On affecte ces variables mêmes variables
ELASTIC_CLOUD_ID = os.getenv("ELASTIC_CLOUD_ID")
ELASTIC_USER = os.getenv("ELASTIC_USER")
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD")
TOKEN = os.getenv("TOKEN")

# On crée un logger
logging.basicConfig(
    filename="sncf_lille.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# Fonction qui ne laisse que les chiffres dans une chaîne de caractères
def hexa(route_id):
    numbers = re.findall(r"[A-F0-9]+", route_id)
    cleaned = "".join(numbers[1:])
    return cleaned

def connextion_to_elastic():
    es = Elasticsearch(
        cloud_id=ELASTIC_CLOUD_ID,
        basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD)
    )
    return es

# Fonction pour récuperer l'id de la gare de Lille
def id_lille():
    base_url = "https://api.sncf.com/v1/coverage/sncf/stop_areas?"
    found = False
    page = 0
    while not found:
        url = f"{base_url}&start_page={page}"
        response = requests.get(url, auth=HTTPBasicAuth(TOKEN, ""))
        data = response.json()
        if not data.get("stop_areas", []):
            logging.info(f"Aucun resultat trouvé")
            break

        for stop in data.get("stop_areas", []):
            name = stop.get("name", "")
            stop_id = stop.get("id", "")
            if "Lille" in name:
                print(f"{name} → {stop_id}")
                found = True

        page += 1


# Fontion qui recupere les trajet actuelles à Lille Flandres et retourne un dataFrame
def download_realtime_travel():
    API = "https://api.sncf.com/v1/coverage/sncf/stop_areas/stop_area:SNCF:87286005/departures"
    try :
        resp = requests.get(API, auth=HTTPBasicAuth(TOKEN, ""))
        data = resp.json()
        departures = []
        for d in data.get("departures", []):
            stop_date_time = d.get("stop_date_time", {})
            links = stop_date_time.get("links", [])
            for link in links:
                if link.get("rel") == "origins":
                    origin_id = link.get("id")
                elif link.get("rel") == "terminus":
                    terminus_id = link.get("id")

            departures.append({
                "gare": d.get("stop_point", {}).get("stop_area", {}).get("name"),
                "ligne": d.get("display_informations", {}).get("code"),
                "destination": d.get("display_informations", {}).get("direction"),
                "type": d.get("display_informations", {}).get("commercial_mode"),
                "heure_depart": d.get("stop_date_time", {}).get("departure_date_time"),
                "timestamp": datetime.now().isoformat()+"Z",
                "_id": hexa(origin_id + terminus_id + d.get("route", {}).get("id") + stop_date_time.get("departure_date_time")) # On crée un Id unique
            })
        logging.info(f"Récupéré {len(data)} départs depuis Lille.")
        df = pd.DataFrame(departures)
        return df
    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur API Sncf {e}")

# Fonction qui injecte notre dataFrame dans ElasticSearch
def load_travel_to_elastic():
    index_name = "sncf_lille_realtime"
    es = connextion_to_elastic() # Connexion a ElasticSearch
    df = download_realtime_travel()
    if df.empty:
        logging.warning(f"Aucune donnée à indexer pour {index_name}.")
        return
    try:
        actions = []
        for _, row in df.iterrows():
            doc = row.to_dict()
            doc.pop("_id", None)
            actions.append({
                "_op_type": "index",
                "_index": index_name,
                "_id": row["_id"],
                "_source": doc,
            })

        helpers.bulk(es, actions)
        logging.info(f" {len(df)} documents indexés dans {index_name}.")
    except Exception as e:
        failed = helpers.bulk(es, actions, raise_on_error=False, stats_only=False)
        logging.error(f" {failed} documents ont échoué à l’indexation.")

    return es



# Fonction qui importe les données d'un csv dans ElasticSearch
def load_historique_data():
    index_name = "historique"
    try:
        es = connextion_to_elastic()

        # Lecture du CSV
        df = pd.read_csv("frequentation-gares.csv", sep=';')

        # On supprime les colonnes inutiles
        colonnes_a_supprimer = ["Code UIC", "Code postal", "Direction Régionale Gares", "Segmentation DRG", "Segmentation Marketing", "% Non Voyageurs"]
        df = df.drop(columns=colonnes_a_supprimer, errors="ignore")

        # Ajoute un champ timestamp
        df["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Pour que les colonnes supprimées n'apparaissent pas avec un : NAN
        df = df.where(pd.notnull(df), None)
        actions = [
            {
                "_op_type": "index",
                "_index": index_name,
                "_source": row.to_dict(),
            }
            for _, row in df.iterrows()
        ]

        helpers.bulk(es, actions)
        logging.info("Frequentation historique indexée avec succès.")
        return df


    except FileNotFoundError:
        logging.error("Fichier frequentation-gares.csv introuvable.")
    except Exception as e:
        logging.error(f"Erreur chargement fréquentation : {e}")

        success, failed = helpers.bulk(
            es,
            actions,
            raise_on_error=False,
            stats_only=False
        )

        logging.info(f"{success} documents indexés avec succès.")
        if failed:
            logging.error(f"{failed} document(s) failed to index.")



if __name__ == '__main__':
    # Fait tourner la fonction toute les 15mn
    schedule.every(15).minutes.do(load_travel_to_elastic)
    logging.info("Tâche planifiée : exécution toutes les 15 minutes.")
    while True:
        # On vérifie si c'est le moment de relancer la fonction
        schedule.run_pending()
        # On attends 1mn avant chaque vérification pour des soucis de performances
        time.sleep(60)






