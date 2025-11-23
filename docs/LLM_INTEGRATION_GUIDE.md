# docs/LLM_INTEGRATION_GUIDE.md
"""
# Guide d'intégration LLM - musAI Platform

## Configuration des APIs LLM

Le système de chat de musAI nécessite une clé API pour fonctionner. Vous pouvez utiliser OpenAI ou DeepSeek.

### Variables d'environnement requises

Créez un fichier `.env` à la racine du projet avec les variables suivantes :

```bash
# Provider LLM (openai ou deepseek)
LLM_PROVIDER=openai

# Clé API OpenAI (si vous utilisez OpenAI)
OPENAI_API_KEY=sk-your-api-key-here

# OU Clé API DeepSeek (si vous utilisez DeepSeek)
DEEPSEEK_API_KEY=sk-your-api-key-here

# Modèle à utiliser
LLM_MODEL=gpt-4

# Temperature (0.0 à 1.0) - contrôle la créativité
LLM_TEMPERATURE=0.7

# URL de base (si provider personnalisé)
DEEPSEEK_ENDPOINT_URL=https://api.deepseek.com
```

## Instructions d'installation

### 1. Installer les dépendances

```bash
pip install openai httpx
```

### 2. Configurer les variables d'environnement

Copiez le fichier `.env.example` vers `.env` :

```bash
cp .env.example .env
```

Éditez `.env` et ajoutez votre clé API :

```bash
OPENAI_API_KEY=sk-votre-clé-api-ici
```

### 3. Tester la connexion

Exécutez le script de test :

```bash
python scripts/test_llm_connection.py
```

Si la connexion est réussie, vous verrez :
```
✅ Connexion LLM réussie!
🔗 Provider: openai
🤖 Model: gpt-4
```

### 4. Utiliser dans le code

Le système est maintenant automatiquement connecté. Quand un utilisateur envoie un message via l'API :

```python
POST /api/chat/send
{
    "message": "Bonjour, comment ça va?",
    "conversation_id": "optional-conversation-id"
}
```

Le système :
1. ✅ Sauvegarde le message utilisateur
2. ✅ Récupère l'historique de la conversation (10 derniers messages)
3. ✅ Appelle le LLM avec le contexte
4. ✅ Sauvegarde la réponse du bot
5. ✅ Retourne la réponse

## Configuration avancée

### Changer de provider

Pour utiliser DeepSeek au lieu d'OpenAI :

```bash
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-deepseek-key
DEEPSEEK_ENDPOINT_URL=https://api.deepseek.com
```

### Ajuster la créativité

La température contrôle la créativité des réponses :
- `0.0` : Réponses très factuelles et déterministes
- `0.7` : Équilibre entre créativité et cohérence (défaut)
- `1.0` : Réponses très créatives mais moins prévisibles

```bash
LLM_TEMPERATURE=0.5  # Plus factuel
```

### Changer le modèle

```bash
# GPT-4 (plus puissant, plus cher)
LLM_MODEL=gpt-4

# GPT-3.5-turbo (plus rapide, moins cher)
LLM_MODEL=gpt-3.5-turbo

# DeepSeek
LLM_MODEL=deepseek-chat
```

## Obtenir une clé API

### OpenAI

1. Allez sur [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Créez un compte ou connectez-vous
3. Cliquez sur "Create new secret key"
4. Copiez la clé (commence par `sk-`)
5. Ajoutez-la à votre fichier `.env`

⚠️ **Important** : Ne partagez jamais votre clé API publiquement !

### DeepSeek

1. Allez sur [https://www.deepseek.com](https://www.deepseek.com)
2. Créez un compte
3. Générez une clé API dans les paramètres
4. Ajoutez-la à votre fichier `.env`

## Dépannage

### Erreur : "OpenAI API key not found"

**Solution** : Vérifiez que la variable `OPENAI_API_KEY` est bien définie dans `.env`

### Erreur : "API rate limit exceeded"

**Solution** : Vous avez atteint la limite de votre plan. 
- Attendez quelques minutes
- Ou upgradez votre plan OpenAI

### Erreur : "Model not found"

**Solution** : Vérifiez que le modèle existe et est accessible avec votre clé API

### Les réponses sont trop longues/courtes

**Solution** : Ajustez le système de prompt dans `handle_message()` pour donner plus de contexte au LLM

## Code modifié dans manager.py

### Avant (Placeholder)
```python
# Placeholder: echo
bot_response_text = f"Bot répond: {message}"
```

### Après (Intégration LLM)
```python
# Récupérer l'historique pour le contexte
total, history_docs = await chat_manager.get_history(conversation_id, limit=10)

# Convertir l'historique en format Message pour le LLM
messages = []
for doc in history_docs:
    messages.append(Message(
        role=doc.get('role', 'user'),
        content=doc.get('text', '')
    ))

# Appeler le LLM pour générer la réponse
try:
    llm_service = _get_llm_service()
    response = await llm_service.generate(
        messages=messages,
        tenant_id=user_email
    )
    bot_response_text = response.text
except Exception as e:
    logger.error(f"Erreur LLM: {e}")
    bot_response_text = f"Désolé, je ne peux pas traiter votre demande pour le moment."
```

## Fallback en cas d'erreur

Si le LLM ne peut pas être appelé (API down, erreur réseau, etc.), le système affiche un message d'erreur amical :

```
"Désolé, je ne peux pas traiter votre demande pour le moment. (détails de l'erreur)"
```

## Sécurité

✅ Les clés API ne sont jamais exposées dans les logs  
✅ Utilisation de variables d'environnement  
✅ Gestion d'erreurs avec fallback  
✅ Pas de fuite de données sensibles

## Prochaines étapes

1. ✅ Configurez votre clé API dans `.env`
2. ✅ Testez avec `scripts/test_llm_connection.py`
3. ✅ Essayez d'envoyer un message via l'API
4. 🚀 Le système fonctionne automatiquement !

---

**Note** : Si vous utilisez un provider LLM personnalisé, implémentez votre propre classe en suivant l'interface `LLMService` dans `api/services/chat_omnichannel/llm_service.py`




