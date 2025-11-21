// mongo_schema_full.js
// Création des collections + validateurs + index pour la base musai_bi

db = db.getSiblingDB("musai_bi");

// --- COLLECTION : creators ---
db.createCollection("creators", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["source", "username", "inserted_at", "updated_at"],
      properties: {
        source: {
          bsonType: "object",
          required: ["provider", "provider_id"],
          properties: {
            provider: { bsonType: "string", description: "Nom du fournisseur de données" },
            provider_id: { bsonType: "string", description: "ID du profil fournisseur" }
          }
        },
        username: { bsonType: "string", description: "Handle / nom utilisateur" },
        full_name: { bsonType: ["string","null"], description: "Nom complet si disponible" },
        gender: { bsonType: ["string","null"], description: "Genre estimé ou déclaré" },
        age_est: { bsonType: ["int","null"], description: "Âge estimé" },
        country: { bsonType: ["string","null"], description: "Pays principal" },
        language: { bsonType: ["string","null"], description: "Langue principale" },
        avatar_url: { bsonType: ["string","null"], description: "URL avatar" },
        banner_url: { bsonType: ["string","null"], description: "URL bannière ou header" },
        bio: { bsonType: ["string","null"], description: "Bio brute" },
        about_cleaned: { bsonType: ["string","null"], description: "Bio nettoyée / NLP" },
        persona_archetype: { bsonType: ["string","null"], description: "Archetype (ex. Glamour, Curvy…)" },
        niche_tags: {
          bsonType: ["array","null"],
          items: { bsonType: "string" },
          description: "Liste de tags / niches"
        },
        join_date: { bsonType: ["date","null"], description: "Date d’entrée sur la plateforme" },
        verified: { bsonType: ["bool","null"], description: "Profil vérifié ?" },
        links: {
          bsonType: ["object","null"],
          description: "URLs externes",
          properties: {
            website: { bsonType: ["string","null"] },
            instagram: { bsonType: ["string","null"] },
            twitter: { bsonType: ["string","null"] },
            youtube: { bsonType: ["string","null"] },
            onlyfans: { bsonType: ["string","null"] }
          },
          additionalProperties: true
        },
        monetization: {
          bsonType: ["object","null"],
          description: "Données monétisation",
          properties: {
            subscribe_price_usd: { bsonType: ["double","null"], description: "Prix abonnement USD" },
            tips_enabled: { bsonType: ["bool","null"], description: "Pourboires activés ?" },
            tips_min_usd: { bsonType: ["double","null"] },
            tips_max_usd: { bsonType: ["double","null"] },
            bundles: {
              bsonType: ["array","null"],
              items: {
                bsonType: "object",
                required: ["duration_months","price_usd","discount_pct"],
                properties: {
                  duration_months: { bsonType: "int" },
                  price_usd: { bsonType: "double" },
                  discount_pct: { bsonType: "double" }
                }
              }
            }
          },
          additionalProperties: true
        },
        category_restricted: { bsonType: ["bool","null"], description: "Restriction catégorie adulte ?" },
        is_performer: { bsonType: ["bool","null"], description: "Acteur(trice) / performeur ?" },
        first_published_post_date: { bsonType: ["date","null"], description: "Date 1ʳᵉ post publié" },
        last_seen: { bsonType: ["date","null"], description: "Dernière activité vue" },
        inserted_at: { bsonType: "date", description: "Date d’insertion" },
        updated_at: { bsonType: "date", description: "Date de mise à jour" }
      },
      additionalProperties: true
    }
  },
  validationLevel: "moderate",
  validationAction: "error"
});
db.creators.createIndex({ "source.provider": 1, "source.provider_id": 1 }, { unique: true });
db.creators.createIndex({ "username": 1 });

// --- COLLECTION : platform_metrics ---
db.createCollection("platform_metrics", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["creator_id","platform","followers","inserted_at","updated_at"],
      properties: {
        creator_id: { bsonType: "objectId", description: "Référence vers creators._id" },
        platform: { bsonType: "string", description: "Nom plateforme (instagram/tiktok/onlyfans…)" },
        handle: { bsonType: ["string","null"], description: "Handle plateforme" },
        followers: { bsonType: "int", description: "Nombre de followers" },
        following: { bsonType: ["int","null"] },
        posts_count: { bsonType: ["int","null"] },
        avg_likes: { bsonType: ["double","null"] },
        avg_comments: { bsonType: ["double","null"] },
        engagement_rate: { bsonType: ["double","null"] },
        last_post_date: { bsonType: ["date","null"] },
        posting_frequency_per_week: { bsonType: ["double","null"] },
        audience_country_dist: {
          bsonType: ["array","null"],
          items: {
            bsonType: "object",
            required: ["country","pct"],
            properties: {
              country: { bsonType: "string" },
              pct: { bsonType: "double" }
            }
          }
        },
        audience_age_gender_split: { bsonType: ["object","null"], description: "Distribution âge/genre (%)" },
        inserted_at: { bsonType: "date" },
        updated_at: { bsonType: "date" }
      },
      additionalProperties: true
    }
  },
  validationLevel: "moderate",
  validationAction: "error"
});
db.platform_metrics.createIndex({ "creator_id": 1, "platform": 1 });

// --- COLLECTION : content_samples ---
db.createCollection("content_samples", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["creator_id","platform","post_id","post_date","inserted_at"],
      properties: {
        creator_id: { bsonType: "objectId" },
        platform: { bsonType: "string" },
        post_id: { bsonType: "string" },
        caption: { bsonType: ["string","null"] },
        hashtags: {
          bsonType: ["array","null"],
          items: { bsonType: "string" }
        },
        media_urls: {
          bsonType: ["array","null"],
          items: { bsonType: "string" }
        },
        geo_tag: { bsonType: ["string","null"] },
        media_type: { bsonType: ["string","null"], description: "photo/video/carousel/reel" },
        likes: { bsonType: ["int","null"] },
        comments: { bsonType: ["int","null"] },
        views: { bsonType: ["int","null"] },
        sentiment_score: { bsonType: ["double","null"] },
        tone_category: { bsonType: ["string","null"] },
        ai_category: { bsonType: ["string","null"] },
        post_date: { bsonType: "date" },
        inserted_at: { bsonType: "date" }
      },
      additionalProperties: true
    }
  },
  validationLevel: "moderate",
  validationAction: "error"
});
db.content_samples.createIndex({ "creator_id": 1, "post_date": -1 });

// --- COLLECTION : audience_insights ---
db.createCollection("audience_insights", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["creator_id","inserted_at","updated_at"],
      properties: {
        creator_id: { bsonType: "objectId" },
        brand_affinity_index: { bsonType: ["double","null"] },
        loyalty_segment: { bsonType: ["string","null"] },
        top_countries: {
          bsonType: ["array","null"],
          items: { bsonType: "string" }
        },
        top_cities: {
          bsonType: ["array","null"],
          items: { bsonType: "string" }
        },
        age_split: { bsonType: ["object","null"] },
        gender_split: { bsonType: ["object","null"] },
        inserted_at: { bsonType: "date" },
        updated_at: { bsonType: "date" }
      },
      additionalProperties: true
    }
  },
  validationLevel: "moderate",
  validationAction: "error"
});
db.audience_insights.createIndex({ "creator_id": 1, "updated_at": -1 });

print("🎉 All collections created & schema validated for musai_bi.");
