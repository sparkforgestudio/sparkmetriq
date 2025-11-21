# Configuration Google OAuth - Frontend Admin Panel

## Installation

Les dépendances nécessaires sont déjà ajoutées dans `package.json`. Pour installer :

```bash
cd frontend/admin_panel
npm install
```

## Configuration

### 1. Créer un projet Google Cloud Console

1. Allez sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créez un nouveau projet ou sélectionnez un projet existant
3. Activez l'API "Google+ API" (ou "Google Identity Services")

### 2. Créer les identifiants OAuth 2.0

1. Dans le menu, allez dans **APIs & Services** > **Credentials**
2. Cliquez sur **Create Credentials** > **OAuth client ID**
3. Choisissez **Web application**
4. Configurez :
   - **Name** : SparkMetrics Admin Panel
   - **Authorized JavaScript origins** :
     - `http://localhost:3000` (développement)
     - `https://votre-domaine.com` (production)
   - **Authorized redirect URIs** :
     - `http://localhost:3000` (développement)
     - `https://votre-domaine.com` (production)

### 3. Configurer les variables d'environnement

Créez un fichier `.env.local` dans `frontend/admin_panel/` :

```bash
# URL de base de l'API backend
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Google OAuth Client ID
NEXT_PUBLIC_GOOGLE_CLIENT_ID=votre-client-id.apps.googleusercontent.com
```

**Important** : Le fichier `.env.local` ne doit pas être commité dans Git (il est déjà dans `.gitignore`).

### 4. Backend Configuration

Assurez-vous que le backend est configuré avec les mêmes identifiants :

```bash
# Dans le fichier .env du backend (api/)
GOOGLE_CLIENT_ID=votre-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=votre-client-secret
```

## Utilisation

### Authentification Email/Password

L'utilisateur peut se connecter avec son email et mot de passe via le formulaire classique.

### Authentification Google OAuth

1. L'utilisateur clique sur le bouton "Se connecter avec Google"
2. Google affiche la fenêtre de consentement
3. Après autorisation, le frontend envoie le `id_token` au backend
4. Le backend vérifie le token et crée/retrouve l'utilisateur
5. Le backend renvoie un JWT d'accès
6. Le frontend stocke le token et redirige vers le dashboard

## Structure des fichiers

- `frontend/admin_panel/pages/login.tsx` : Page de connexion avec Google OAuth
- `frontend/admin_panel/lib/auth.ts` : Utilitaires d'authentification (login, register, etc.)
- `frontend/admin_panel/lib/api.ts` : Client API avec gestion automatique des tokens

## Fonctionnalités

- ✅ Connexion avec email/password
- ✅ Connexion avec Google OAuth
- ✅ Gestion automatique des tokens (localStorage)
- ✅ Gestion des erreurs
- ✅ États de chargement
- ✅ Interface responsive et moderne

## Dépannage

### Le bouton Google ne s'affiche pas

Vérifiez que `NEXT_PUBLIC_GOOGLE_CLIENT_ID` est bien configuré dans `.env.local`.

### Erreur "Invalid client ID"

Vérifiez que :
- Le Client ID est correct dans `.env.local`
- Les origines JavaScript autorisées incluent votre domaine
- Le backend a le même `GOOGLE_CLIENT_ID` configuré

### Erreur CORS

Assurez-vous que le backend autorise les requêtes depuis `http://localhost:3000` (ou votre domaine de production).


