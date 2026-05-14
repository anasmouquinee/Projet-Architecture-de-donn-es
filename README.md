# Plateforme Big Data : Architecture de Données Médiatiques

Ce projet est une plateforme complète et distribuée d'ingestion, de traitement et de visualisation de données issues d'articles de presse (Scraping, Data Lake, Data Warehouse, Architecture Médaillon, ETL/ELT).

## 🚀 Prérequis

- **Docker** et **Docker Compose** installés sur votre machine.
- Au moins 8 Go de RAM alloués à Docker (recommandé).

## 🛠️ Comment lancer le projet ?

1. **Cloner le dépôt** :
   ```bash
   git clone https://github.com/anasmouquinee/Projet-Architecture-de-donn-es.git
   cd Projet-Architecture-de-donn-es
   ```

2. **Démarrer l'infrastructure** :
   Lancez l'ensemble des conteneurs en arrière-plan (Kafka, Airflow, MinIO, PostgreSQL, Superset, Prometheus, Grafana) :
   ```bash
   docker-compose up -d
   ```

3. **Accéder aux différents services** :
   Une fois les conteneurs démarrés (cela peut prendre 1 à 2 minutes), vous pouvez accéder aux interfaces via votre navigateur avec les identifiants par défaut :
   - **Apache Airflow** (Orchestration) : `http://localhost:8080` *(admin / admin)*
   - **MinIO Console** (Data Lake) : `http://localhost:9001` *(minio_admin / anaskaelar)*
   - **Apache Superset** (Visualisation) : `http://localhost:8088` *(admin / anaskaelar)*
   - **Grafana** (Monitoring) : `http://localhost:3000` *(admin / anaskaelar)*
   - **Prometheus** (Métriques) : `http://localhost:9090`
   - **Kafka UI** (Gestion des messages) : `http://localhost:8090`

## 🛑 Arrêter le projet

Pour stopper tous les services sans supprimer vos données :
```bash
docker-compose stop
```

Pour détruire l'infrastructure complète (attention, cela efface vos buckets MinIO et votre base de données) :
```bash
docker-compose down -v
```

---
💡 *Note : Pour une documentation plus détaillée, l'architecture complète, et le déploiement sur Kubernetes, veuillez consulter le fichier `docs/Guide_Installation_Utilisation.md`.*
