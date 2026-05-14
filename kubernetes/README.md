# Déploiement Kubernetes & Helm

Cette section contient les configurations pour déployer la plateforme Data Architect sur un cluster Kubernetes (K8s) via **Helm Charts**. 

## 🏗 Architecture de déploiement

Conformément à la documentation (section 11.2), le déploiement Kubernetes garantit :
- **Haute disponibilité (HA)** : ReplicaSets pour Kafka, Zookeeper et les workers Airflow.
- **Scalabilité Automatique (HPA)** : Ajustement des pods en fonction de l'usage CPU/RAM.
- **Sécurité** : Gestion des mots de passe (Postgres, MinIO, Superset) via des Kubernetes Secrets.
- **Persistance** : StorageClasses et PVC pour MinIO et PostgreSQL.

## 🚀 Lancement avec Helm

L'installation complète repose sur un chart unifié (`data-architect-platform`) ou l'orchestration de sub-charts officiels.

```bash
# 1. Création des namespaces isolés
kubectl create namespace data-ingestion
kubectl create namespace data-storage
kubectl create namespace data-analytics

# 2. Installation de la stack (Exemple via Helm)
helm install data-platform ./helm-chart \
  --namespace data-storage \
  -f values-production.yaml
```

## 📊 Monitoring K8s
La pile **Prometheus / Grafana** (détaillée en section 11.3) est automatiquement provisionnée via `kube-prometheus-stack` pour monitorer les pods, les nodes et la santé des pipelines.
