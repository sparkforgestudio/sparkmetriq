# api/services/ai_marketing/rag_system.py
"""
Système RAG (Retrieval-Augmented Generation) pour les recommandations IA.
Utilise un vector store pour l'indexation et la recherche de données pertinentes.
Utilise la base BI pour stocker les documents et embeddings.
"""

import asyncio
import json
import os
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import pickle
import hashlib

from sentence_transformers import SentenceTransformer
import faiss
from api.services.ai_marketing.logger import logger
from api.databases.databases import get_bi_db

@dataclass
class Document:
    """Document pour l'indexation vectorielle."""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None

@dataclass
class SearchResult:
    """Résultat de recherche vectorielle."""
    document: Document
    score: float
    relevance_explanation: str

class RAGSystem:
    """Système RAG pour les recommandations marketing."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.embedding_model = None
        self.vector_index = None
        self.documents = {}
        self.db = get_bi_db()  # Utilise la base BI
        
        # Initialiser le modèle d'embedding
        self._load_embedding_model()
        
    def _load_embedding_model(self):
        """Charge le modèle d'embedding."""
        try:
            self.embedding_model = SentenceTransformer(self.model_name)
            logger.info(f"Modèle d'embedding chargé: {self.model_name}")
        except Exception as e:
            logger.error(f"Erreur chargement modèle embedding: {e}")
            raise

    async def add_documents(self, documents: List[Document]):
        """Ajoute des documents à l'index vectoriel."""
        try:
            # Générer les embeddings
            texts = [doc.content for doc in documents]
            embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
            
            # Mettre à jour les documents avec leurs embeddings
            for i, doc in enumerate(documents):
                doc.embedding = embeddings[i]
                self.documents[doc.id] = doc
            
            # Mettre à jour l'index FAISS
            await self._update_faiss_index()
            
            # Sauvegarder
            await self._save_index()
            
            logger.info(f"Ajouté {len(documents)} documents à l'index RAG")
            
        except Exception as e:
            logger.error(f"Erreur ajout documents: {e}")
            raise

    async def search(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Recherche dans l'index vectoriel."""
        try:
            if not self.vector_index or len(self.documents) == 0:
                logger.warning("Index vectoriel vide")
                return []
            
            # Générer l'embedding de la requête
            query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
            
            # Recherche dans l'index FAISS
            scores, indices = self.vector_index.search(query_embedding, top_k)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.documents):
                    doc_id = list(self.documents.keys())[idx]
                    document = self.documents[doc_id]
                    
                    # Appliquer les filtres si spécifiés
                    if filters and not self._matches_filters(document, filters):
                        continue
                    
                    # Calculer la pertinence
                    relevance_explanation = self._explain_relevance(query, document)
                    
                    results.append(SearchResult(
                        document=document,
                        score=float(score),
                        relevance_explanation=relevance_explanation
                    ))
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur recherche RAG: {e}")
            return []

    async def _update_faiss_index(self):
        """Met à jour l'index FAISS."""
        if not self.documents:
            return
        
        # Extraire tous les embeddings
        embeddings = []
        doc_ids = []
        
        for doc_id, doc in self.documents.items():
            if doc.embedding is not None:
                embeddings.append(doc.embedding)
                doc_ids.append(doc_id)
        
        if not embeddings:
            return
        
        embeddings_array = np.array(embeddings).astype('float32')
        dimension = embeddings_array.shape[1]
        
        # Créer ou mettre à jour l'index FAISS
        if self.vector_index is None:
            self.vector_index = faiss.IndexFlatIP(dimension)  # Inner Product pour similarité cosinus
        
        # Normaliser les embeddings pour la similarité cosinus
        faiss.normalize_L2(embeddings_array)
        
        # Ajouter à l'index
        self.vector_index.add(embeddings_array)
        
        logger.info(f"Index FAISS mis à jour avec {len(embeddings)} embeddings")

    def _matches_filters(self, document: Document, filters: Dict[str, Any]) -> bool:
        """Vérifie si un document correspond aux filtres."""
        for key, value in filters.items():
            if key not in document.metadata:
                return False
            
            doc_value = document.metadata[key]
            
            # Support pour différents types de filtres
            if isinstance(value, list):
                if doc_value not in value:
                    return False
            elif isinstance(value, dict):
                # Filtre de plage (ex: {"min": 10, "max": 100})
                if "min" in value and doc_value < value["min"]:
                    return False
                if "max" in value and doc_value > value["max"]:
                    return False
            else:
                if doc_value != value:
                    return False
        
        return True

    def _explain_relevance(self, query: str, document: Document) -> str:
        """Explique pourquoi un document est pertinent pour la requête."""
        # Analyse simple basée sur les mots-clés
        query_words = set(query.lower().split())
        content_words = set(document.content.lower().split())
        
        common_words = query_words.intersection(content_words)
        
        if common_words:
            return f"Pertinent car contient les mots-clés: {', '.join(common_words)}"
        else:
            return "Pertinent par similarité sémantique"

    async def _save_index(self):
        """Sauvegarde l'index et les documents."""
        try:
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            
            # Sauvegarder l'index FAISS
            if self.vector_index:
                faiss.write_index(self.vector_index, f"{self.index_path}.faiss")
            
            # Sauvegarder les documents
            with open(self.documents_path, 'wb') as f:
                pickle.dump(self.documents, f)
            
            logger.info("Index RAG sauvegardé")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde index: {e}")

    async def _load_index(self):
        """Charge l'index et les documents sauvegardés."""
        try:
            # Charger l'index FAISS
            if os.path.exists(f"{self.index_path}.faiss"):
                self.vector_index = faiss.read_index(f"{self.index_path}.faiss")
                logger.info("Index FAISS chargé")
            
            # Charger les documents
            if os.path.exists(self.documents_path):
                with open(self.documents_path, 'rb') as f:
                    self.documents = pickle.load(f)
                logger.info(f"Documents chargés: {len(self.documents)}")
            
        except Exception as e:
            logger.error(f"Erreur chargement index: {e}")

    async def initialize(self):
        """Initialise le système RAG."""
        await self._load_index()
        
        # Si pas d'index, créer des documents de base
        if not self.documents:
            await self._create_base_knowledge()
    
    async def _create_base_knowledge(self):
        """Crée la base de connaissances initiale."""
        base_documents = [
            Document(
                id="benchmark_cosplay",
                content="""
                Benchmarks Cosplay:
                - Prix moyen abonnement: $19.99/mois
                - Conversion PPV: 8-12%
                - Plateformes principales: Reddit, Twitter, TikTok
                - Contenu performant: Transformations, BTS, Tutorials
                - Engagement optimal: 2-3 posts/jour sur Instagram, 1 TikTok/jour
                """,
                metadata={"category": "benchmark", "niche": "cosplay"}
            ),
            Document(
                id="benchmark_fitness",
                content="""
                Benchmarks Fitness:
                - Prix moyen abonnement: $24.99/mois
                - Conversion PPV: 10-15%
                - Plateformes principales: Instagram, TikTok
                - Contenu performant: Workouts, Progress pics, Nutrition tips
                - Engagement optimal: 1-2 posts/jour sur Instagram, 3-4 TikToks/semaine
                """,
                metadata={"category": "benchmark", "niche": "fitness"}
            ),
            Document(
                id="benchmark_dominatrix",
                content="""
                Benchmarks Dominatrix:
                - Prix moyen abonnement: $29.99/mois
                - Conversion PPV: 12-18%
                - Plateformes principales: Reddit, Twitter, Fansly
                - Contenu performant: Teasing, Commands, Custom content
                - Engagement optimal: 1-2 posts/jour, focus sur Reddit
                """,
                metadata={"category": "benchmark", "niche": "dominatrix"}
            ),
            Document(
                id="pricing_strategies",
                content="""
                Stratégies de Pricing:
                - Test A/B: Augmenter prix de 20% sur 50% des nouveaux abonnés
                - Bundles: 3 PPV à prix réduit (25% discount)
                - Promotions: 50% off premier mois pour nouveaux fans
                - Upsell: Contenu premium à prix plus élevé
                - Retention: 20% off renouvellement pour fans actifs
                """,
                metadata={"category": "pricing", "niche": "general"}
            ),
            Document(
                id="content_strategies",
                content="""
                Stratégies de Contenu:
                - Cross-platform: Adapter le même contenu pour chaque plateforme
                - Teasing: Poster teasers sur réseaux sociaux, contenu complet sur OF
                - User-generated: Concours et challenges pour engagement
                - Seasonal: Adapter le contenu aux tendances saisonnières
                - Educational: Contenu informatif pour fidéliser l'audience
                """,
                metadata={"category": "content", "niche": "general"}
            ),
            Document(
                id="acquisition_strategies",
                content="""
                Stratégies d'Acquisition:
                - Reddit: Participer aux discussions, poster du contenu de qualité
                - TikTok: Utiliser les tendances audio, hashtags populaires
                - Instagram: Stories interactives, Reels engageants
                - Twitter: Threads informatifs, interactions avec l'audience
                - Collaborations: Partenariats avec autres créateurs
                """,
                metadata={"category": "acquisition", "niche": "general"}
            )
        ]
        
        await self.add_documents(base_documents)
        logger.info("Base de connaissances initiale créée")

    async def get_relevant_benchmarks(self, niche: str, category: str = None) -> List[SearchResult]:
        """Récupère les benchmarks pertinents pour une niche."""
        query = f"benchmark {niche}"
        filters = {"category": "benchmark", "niche": niche} if niche != "general" else {"category": "benchmark"}
        
        return await self.search(query, top_k=3, filters=filters)

    async def get_pricing_recommendations(self, niche: str) -> List[SearchResult]:
        """Récupère les recommandations de pricing."""
        query = f"pricing strategies {niche}"
        filters = {"category": "pricing"}
        
        return await self.search(query, top_k=5, filters=filters)

    async def get_content_recommendations(self, niche: str) -> List[SearchResult]:
        """Récupère les recommandations de contenu."""
        query = f"content strategies {niche}"
        filters = {"category": "content"}
        
        return await self.search(query, top_k=5, filters=filters)

    async def get_acquisition_recommendations(self, niche: str) -> List[SearchResult]:
        """Récupère les recommandations d'acquisition."""
        query = f"acquisition strategies {niche}"
        filters = {"category": "acquisition"}
        
        return await self.search(query, top_k=5, filters=filters)

    async def update_knowledge_with_data(self, creator_data: Dict[str, Any]):
        """Met à jour la base de connaissances avec de nouvelles données."""
        try:
            # Extraire les insights des données du créateur
            insights = await self._extract_insights(creator_data)
            
            # Créer des documents à partir des insights
            documents = []
            for insight in insights:
                doc = Document(
                    id=f"insight_{hashlib.md5(insight['content'].encode()).hexdigest()}",
                    content=insight['content'],
                    metadata=insight['metadata']
                )
                documents.append(doc)
            
            # Ajouter à l'index
            if documents:
                await self.add_documents(documents)
                logger.info(f"Ajouté {len(documents)} nouveaux insights à la base de connaissances")
            
        except Exception as e:
            logger.error(f"Erreur mise à jour connaissances: {e}")

    async def _extract_insights(self, creator_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrait des insights des données du créateur."""
        insights = []
        
        # Analyser les performances par plateforme
        platforms = creator_data.get("platforms", {})
        
        for platform, data in platforms.items():
            if "posts" in data:
                posts = data["posts"]
                if posts:
                    # Insight sur le contenu performant
                    top_post = max(posts, key=lambda x: x.get("likes", 0) + x.get("comments", 0))
                    
                    insight_content = f"""
                    Contenu performant sur {platform}:
                    - Titre: {top_post.get('title', 'N/A')}
                    - Engagement: {top_post.get('likes', 0)} likes, {top_post.get('comments', 0)} commentaires
                    - Type: {top_post.get('media_type', 'N/A')}
                    - Prix: ${top_post.get('price', 0)}
                    """
                    
                    insights.append({
                        "content": insight_content,
                        "metadata": {
                            "category": "performance",
                            "platform": platform,
                            "creator_id": creator_data.get("creator_username", "unknown")
                        }
                    })
        
        return insights

    async def generate_contextual_recommendations(self, query: str, creator_profile: Dict[str, Any]) -> str:
        """Génère des recommandations contextuelles basées sur le profil du créateur."""
        try:
            # Rechercher des documents pertinents
            search_results = await self.search(query, top_k=5)
            
            if not search_results:
                return "Aucune recommandation trouvée dans la base de connaissances."
            
            # Construire le contexte
            context = "Contexte du créateur:\n"
            context += f"- Niche: {creator_profile.get('niche', 'N/A')}\n"
            context += f"- Plateformes: {', '.join(creator_profile.get('platforms', []))}\n"
            context += f"- Abonnés: {creator_profile.get('followers', {})}\n"
            context += f"- Prix abonnement: ${creator_profile.get('subscription_price', 0)}\n\n"
            
            context += "Recommandations pertinentes:\n"
            for i, result in enumerate(search_results, 1):
                context += f"{i}. {result.document.content}\n"
                context += f"   Pertinence: {result.relevance_explanation}\n\n"
            
            return context
            
        except Exception as e:
            logger.error(f"Erreur génération recommandations contextuelles: {e}")
            return "Erreur lors de la génération des recommandations."
