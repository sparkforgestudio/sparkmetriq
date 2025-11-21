from typing import List, Tuple

class VectorStoreClient:
    """
    Client pour l'interaction avec le vector store (Pinecone, FAISS, etc.).
    Fournit une méthode `search` pour récupérer les IDs de documents similaires
    et leurs scores respectifs.
    """
    def __init__(self, index_name: str, **kwargs):
        """
        Initialise la connexion au vector store.
        :param index_name: Nom de l'index ou du namespace à utiliser.
        :param kwargs: Paramètres de configuration (API key, endpoint, etc.).
        """
        # Exemple : self.client = pinecone.Client(api_key=..., environment=...)
        #           self.index  = self.client.Index(index_name)
        raise NotImplementedError("Initialisation du VectorStoreClient non implémentée")

    async def search(self, query: str, k: int) -> List[Tuple[str, float]]:
        """
        Recherche `k` documents les plus proches du vector de `query`.
        Doit retourner une liste de tuples (document_id, score).
        """
        # Exemple :
        # vector = await self.client.embed(query)
        # results = await self.index.query(vector, top_k=k)
        # return [(match.id, match.score) for match in results.matches]
        raise NotImplementedError("VectorStoreClient.search doit être implémenté")
