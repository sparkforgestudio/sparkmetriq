"""
Service RAG (Retrieval-Augmented Generation) pour le chat.
Utilise la base Core pour les conversations et documents de chat.
"""
from typing import Any, Dict, List
from api.databases.databases import get_core_db

# Importer vos propres clients de store situés dans api/services/chat_omnichannel
from api.services.chat_omnichannel.vector_store import VectorStoreClient
from api.services.chat_omnichannel.doc_store import DocumentStoreClient

class RAGService:
    """
    Service de Retrieval-Augmented Generation (RAG).
    Permet de récupérer des extraits pertinents et de bâtir
    un prompt enrichi pour l'IA.
    """
    def __init__(
        self,
        vector_store: VectorStoreClient,
        doc_store: DocumentStoreClient,
        top_k: int = 5
    ):
        self.vector_store = vector_store
        self.doc_store = doc_store
        self.top_k = top_k

    async def retrieve(
        self,
        conversation_id: str,
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Interroge le vector store pour obtenir les fragments les plus
        pertinents par rapport à la query.
        Retourne une liste de dicts {"content": ..., "source": ..., "score": ...}.
        """
        # Recherche dans le store de vecteurs
        results = await self.vector_store.search(query=query, k=self.top_k)
        snippets: List[Dict[str, Any]] = []
        for doc_id, score in results:
            # Récupérer le document source
            doc = await self.doc_store.get(doc_id)
            snippets.append({
                "content": doc.content,
                "source": getattr(doc, 'source', None),
                "score": score
            })
        return snippets

    def build_augmented_prompt(
        self,
        user_query: str,
        snippets: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Construit la liste de messages pour le LLM :
        - Messages system contenant les snippets
        - Un message user avec la question originale
        """
        messages: List[Dict[str, Any]] = []
        if snippets:
            messages.append({
                "role": "system",
                "content": "Contexte pertinent :"
            })
            for sn in snippets:
                prefix = f"[Source: {sn['source']}]\n" if sn.get('source') else ""
                messages.append({
                    "role": "system",
                    "content": prefix + sn["content"]
                })
        # Question utilisateur
        messages.append({
            "role": "user",
            "content": user_query
        })
        return messages
