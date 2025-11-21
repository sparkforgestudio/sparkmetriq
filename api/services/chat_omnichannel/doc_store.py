from typing import Any

class Document:
    """
    Modèle représentant un document récupéré depuis le doc store.
    """
    def __init__(self, content: str, source: str = None):
        self.content = content
        self.source = source

class DocumentStoreClient:
    """
    Client pour l'interaction avec le document store (S3, base de données, etc.).
    Fournit une méthode `get` pour récupérer le contenu et la source d'un document.
    """
    def __init__(self, **kwargs):
        """
        Initialise la connexion au document store.
        :param kwargs: Paramètres de configuration (credentials, endpoint, bucket, etc.).
        """
        # Exemple : self.bucket = boto3.resource('s3').Bucket(bucket_name)
        raise NotImplementedError("Initialisation du DocumentStoreClient non implémentée")

    async def get(self, doc_id: str) -> Document:
        """
        Récupère le document identifié par `doc_id`.
        :return: Instance de Document avec `content` et `source`.
        """
        # Exemple :
        # obj = await self.bucket.Object(doc_id).get()
        # data = obj['Body'].read().decode()
        # return Document(content=data, source=doc_id)
        raise NotImplementedError("DocumentStoreClient.get doit être implémenté")
