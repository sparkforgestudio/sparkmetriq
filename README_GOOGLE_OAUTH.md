# README_GOOGLE_OAUTH.md
"""
Documentation pour l'authentification Google OAuth 2.0 dans musAI Platform.
"""

## Configuration

### 1. Créer un projet Google Cloud

1. Aller sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créer un nouveau projet ou sélectionner un projet existant
3. Activer l'API "Google+ API" (ou utiliser directement OAuth 2.0)
4. Aller dans "Credentials" → "Create Credentials" → "OAuth client ID"
5. Sélectionner "Web application"
6. Configurer :
   - **Authorized JavaScript origins**: `http://localhost:3000` (dev), votre domaine (prod)
   - **Authorized redirect URIs**: `http://localhost:3000/auth/google/callback` (dev), votre callback (prod)
7. Copier le **Client ID** (pas le secret, nécessaire seulement côté frontend)

### 2. Variables d'environnement

Ajouter dans `.env` :

```bash
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=optional-for-backend
```

### 3. Installation des dépendances

```bash
pip install google-auth google-auth-oauthlib
```

## Utilisation

### Backend (API)

#### Endpoints disponibles

**POST `/api/auth/google/login`** — Connexion/Inscription avec Google

```json
{
  "token": "eyJhbGciOiJSUzI1NiIsImtpZCI6Ij...",
  "org_id": "optional_org_id"
}
```

**Réponse :**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "email": "user@example.com",
    "name": "John Doe",
    "picture": "https://lh3.googleusercontent.com/...",
    "org_id": "abc123",
    "is_admin": false
  }
}
```

**POST `/api/auth/google/register`** — Alias pour `/login` (fait la même chose)

### Frontend (React/Next.js)

#### Exemple d'intégration

```typescript
import { useGoogleLogin } from '@react-oauth/google';

function LoginWithGoogle() {
  const login = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      // tokenResponse.access_token est l'access token OAuth
      // Mais nous avons besoin de l'id_token
      const response = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
        headers: { Authorization: `Bearer ${tokenResponse.access_token}` }
      });
      const userInfo = await response.json();
      
      // Envoyer le token ID à notre backend
      const backendResponse = await fetch('http://localhost:8000/api/auth/google/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token: tokenResponse.id_token, // Si disponible
          // ou utiliser access_token pour obtenir id_token
        })
      });
      
      const { access_token, user } = await backendResponse.json();
      // Stocker access_token pour les requêtes API
      localStorage.setItem('token', access_token);
    },
    onError: (error) => {
      console.error('Login Failed:', error);
    }
  });

  return <button onClick={() => login()}>Se connecter avec Google</button>;
}
```

**Alternative avec @react-oauth/google (recommandé) :**

```typescript
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';

function App() {
  return (
    <GoogleOAuthProvider clientId="YOUR_GOOGLE_CLIENT_ID">
      <GoogleLogin
        onSuccess={async (credentialResponse) => {
          // credentialResponse.credential est l'id_token
          const response = await fetch('http://localhost:8000/api/auth/google/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              token: credentialResponse.credential
            })
          });
          
          const { access_token, user } = await response.json();
          localStorage.setItem('token', access_token);
        }}
        onError={() => {
          console.error('Login Failed');
        }}
      />
    </GoogleOAuthProvider>
  );
}
```

## Architecture

### Flow d'authentification

1. **Frontend** : Utilisateur clique sur "Se connecter avec Google"
2. **Google** : Redirige vers Google pour authentification
3. **Google** : Retourne un `id_token` (JWT signé par Google)
4. **Frontend** : Envoie le `id_token` à `/api/auth/google/login`
5. **Backend** : Vérifie le token avec Google (vérifie signature, expiration, issuer)
6. **Backend** : Récupère ou crée l'utilisateur dans MongoDB
7. **Backend** : Génère un token JWT interne et le retourne
8. **Frontend** : Stocke le token JWT et l'utilise pour les requêtes API

### Base de données

Le schéma utilisateur est étendu avec :

```javascript
{
  "email": "user@example.com",
  "google_id": "123456789",  // ID unique Google (sub)
  "name": "John Doe",        // Nom complet depuis Google
  "picture": "https://...",  // Photo de profil
  "auth_provider": "google", // "google" ou null
  "password": null,          // Pas de mot de passe pour OAuth
  "org_id": "abc123",
  "created_at": ISODate("..."),
  "updated_at": ISODate("...")
}
```

### Sécurité

- Le token Google est vérifié côté backend (signature, expiration, issuer)
- L'email dans le token doit correspondre à celui de l'utilisateur
- L'utilisateur peut se connecter avec email/password OU Google (lien par email)
- Le `org_id` est généré automatiquement si non fourni (hash de l'email)

## Notes importantes

- Le `GOOGLE_CLIENT_SECRET` n'est pas nécessaire côté backend si on utilise uniquement `id_token`
- Le frontend doit utiliser le `GOOGLE_CLIENT_ID` pour lancer le flow OAuth
- Les utilisateurs existants avec email/password peuvent être liés à Google si l'email correspond
- Un utilisateur ne peut avoir qu'un seul `google_id` (index unique sparse)



