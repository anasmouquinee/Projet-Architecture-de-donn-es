# Documentation d'installation et d'utilisation - Data Architect

Ce document détaille la procédure pour monter et utiliser l'infrastructure locale du pipeline de données.

## 1. Prérequis

- Docker et Docker Compose
- Git
- 8 Go de RAM minimum alloués à Docker (nécessaire vu le nombre de services qui tournent en parallèle).

## 2. Configuration initiale

Après avoir récupéré le projet, il faut initialiser les variables d'environnement.

```bash
cd DataArchitectProject
cp .env.example .env
```
**Important** : Pensez à éditer le fichier `.env` pour renseigner les accès de base (mots de passe PostgreSQL, MinIO, clés secrètes Superset).

## 3. Lancement de l'infrastructure

Tous les composants (Airflow, MinIO, Kafka, Postgres, Superset) sont gérés via Docker Compose.

```bash
docker-compose up -d
```

Pour vérifier que tous les conteneurs sont bien "Up" :
```bash
docker-compose ps
```

## 4. Accès aux interfaces

Les services exposent les ports suivants sur votre machine locale :

- **Apache Airflow** : http://localhost:8080 (identifiants : `admin` / `anaskaelar`)
- **Apache Superset** : http://localhost:8088 (identifiants : `admin` / `anaskaelar`)
- **MinIO Console** : http://localhost:9001 (identifiants dans `.env`, par défaut `minio_admin` / `anaskaelar`)
- **PostgreSQL** : port local 5432 (utilisateur `warehouse_user`, mot de passe `anaskaelar` ou selon `.env`)

## 5. Utilisation du Pipeline

Tout est orchestré depuis Airflow. Pour lancer la collecte :

1. Allez sur l'interface Airflow (localhost:8080).
2. Cherchez le DAG de scraping.
3. Activez-le (toggle "Unpause") puis lancez une exécution manuelle avec le bouton "Trigger DAG".

Le comportement attendu est le suivant :
- Les scrapers (BBC, CNN, Reuters, Al Jazeera, Hespress) s'exécutent.
- Ils poussent les articles sous forme de messages dans les topics Kafka.
- Le script `kafka_consumer.py` dépile les messages et les sauvegarde dans la couche **Bronze** de MinIO.
- Les transformations passent la donnée en **Silver** (nettoyage) puis **Gold** (agrégation), en écartant les erreurs en **Quarantaine**.
- Les tables finales de la base PostgreSQL sont mises à jour.
- Superset lit directement depuis PostgreSQL pour mettre à jour les dashboards.

## 6. Problèmes connus

- **Manque de RAM / Plantages Airflow** : L'orchestrateur est très gourmand. Si les conteneurs tombent silencieusement, augmentez la mémoire allouée à Docker Desktop.
- **Connexion Superset / Postgres impossible** : Dans l'interface de connexion Superset, l'hôte (Host) doit être `postgres` et non `localhost`, car Superset tourne dans le réseau Docker interne.
- **Erreurs de parsing dans les scrapers** : Le HTML des sites de news change fréquemment. Si un scraper renvoie 0 article, vérifiez et mettez à jour ses sélecteurs BeautifulSoup dans `scrapers/`.

