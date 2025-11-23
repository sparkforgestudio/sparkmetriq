# Guide Docker - SparkMetrics Platform

## Prérequis

- Docker >= 20.10
- Docker Compose >= 2.0

## Build de l'image

### Build simple

```bash
docker build -t sparkmetrics:latest .
```

### Build avec cache optimisé

```bash
docker build --cache-from sparkmetrics:latest -t sparkmetrics:latest .
```

## Utilisation avec Docker Compose (recommandé)

### Démarrer tous les services

```bash
docker-compose up -d
```

### Voir les logs

```bash
docker-compose logs -f api
```

### Arrêter les services

```bash
docker-compose down
```

### Arrêter et supprimer les volumes (⚠️ supprime les données MongoDB)

```bash
docker-compose down -v
```

## Configuration

### Variables d'environnement

Créez un fichier `.env` à la racine du projet :

```bash
# MongoDB
MONGO_URI=mongodb://mongo:27017
MONGO_URI_BI=mongodb://mongo:27017
DB_NAME_CORE=musai_core
DB_NAME_BI=musai_bi

# Feature Flags
ENABLE_BI=true
ENABLE_SCHEDULER=true
ENABLE_CLOUDPHONE=false
ENABLE_OTP=false

# Sécurité
SECRET_KEY=your-secret-key-change-in-production
SECURITY_SECRET_KEY=your-secret-key-change-in-production

# Google OAuth (optionnel)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# LLM (si utilisé)
LLM_BASE_URL=http://your-llm-server:port
DEEPSEEK_API_KEY=your-api-key
```

Puis utilisez dans `docker-compose.yml` :

```yaml
environment:
  - MONGO_URI=${MONGO_URI}
  # ... autres variables
```

Ou utilisez un fichier `.env` que Docker Compose chargera automatiquement.

## Services disponibles

### API Backend

- **URL**: http://localhost:8000
- **Health Check**: http://localhost:8000/api/healthz
- **Documentation**: http://localhost:8000/docs

### MongoDB

- **Port**: 27017
- **Utilisateur par défaut**: admin
- **Mot de passe par défaut**: changeme (⚠️ à modifier en production)

## Commandes utiles

### Accéder au shell du container API

```bash
docker-compose exec api bash
```

### Exécuter des scripts Python

```bash
docker-compose exec api python scripts/setup_musai_bi.mjs
```

### Voir les logs en temps réel

```bash
docker-compose logs -f --tail=100 api
```

### Redémarrer un service

```bash
docker-compose restart api
```

### Rebuild après modification du code

```bash
docker-compose build --no-cache api
docker-compose up -d
```

## Production

### Optimisations recommandées

1. **Utiliser un reverse proxy** (nginx/traefik) devant l'API
2. **Configurer MongoDB avec authentification** et réplication
3. **Utiliser des secrets Docker** pour les clés sensibles
4. **Activer les healthchecks** (déjà configurés)
5. **Configurer les limites de ressources** :

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '1'
      memory: 1G
```

### Exemple de configuration production

```yaml
services:
  api:
    image: sparkmetrics:latest
    restart: always
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
    environment:
      - MONGO_URI=mongodb://mongo-replica:27017
      - SECRET_KEY=${SECRET_KEY}
    secrets:
      - secret_key
      - google_oauth_secret

secrets:
  secret_key:
    external: true
  google_oauth_secret:
    external: true
```

## Dépannage

### Le container ne démarre pas

```bash
# Vérifier les logs
docker-compose logs api

# Vérifier les healthchecks
docker-compose ps
```

### MongoDB n'est pas accessible

```bash
# Vérifier que MongoDB est démarré
docker-compose ps mongo

# Tester la connexion
docker-compose exec api python -c "from motor.motor_asyncio import AsyncIOMotorClient; import asyncio; asyncio.run(AsyncIOMotorClient('mongodb://mongo:27017').admin.command('ping'))"
```

### Le frontend ne se connecte pas à l'API

Vérifiez que `NEXT_PUBLIC_API_BASE_URL` pointe vers l'URL correcte :
- En développement local : `http://localhost:8000`
- Avec Docker : `http://localhost:8000` (si le frontend est en dehors de Docker) ou `http://api:8000` (si le frontend est dans Docker)

## Structure des volumes

- `mongo-data`: Données persistantes MongoDB
- `./logs`: Logs de l'application (monté depuis le host)

## Sécurité

⚠️ **Important pour la production** :

1. Changez tous les mots de passe par défaut
2. Utilisez des secrets Docker pour les clés sensibles
3. Configurez un firewall
4. Activez HTTPS/TLS
5. Limitez les ports exposés
6. Utilisez un réseau Docker privé
7. Activez l'authentification MongoDB

## Support

Pour plus d'informations, consultez :
- [Documentation Docker](https://docs.docker.com/)
- [Documentation Docker Compose](https://docs.docker.com/compose/)
- [README principal](./README.md)

