from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from api.databases.databases import get_core_db
from api.schemas.chat import ChatMessageIn, ChatMessageOut
from bson import ObjectId
import os
from api.services.chat_omnichannel.llm_service import Message, LLMService, OpenAIService
from api.services.chat_omnichannel.deepseek_service import DeepSeekService

# Collection Motor pour les messages de chat (base Core)
db_core = get_core_db()
CHAT_COLLECTION = db_core['chat_messages']

class ChatManager:
    @staticmethod
    async def save_message(
        msg: ChatMessageIn,
        role: str = 'user'
    ) -> ChatMessageOut:
        """
        Enregistre un message (user ou bot) dans la base et retourne un ChatMessageOut.
        
        Args:
            msg: Message à enregistrer
            role: Rôle du message (user ou bot)
            
        Returns:
            ChatMessageOut: Message enregistré avec timestamp
        """
        doc: Dict[str, Any] = {
            'conversation_id': msg.conversation_id,
            'platform': msg.platform,
            'user_id': msg.user_id,
            'text': msg.message,
            'attachments': msg.attachments,
            'metadata': msg.metadata,
            'role': role,
            'timestamp': datetime.now(timezone.utc),
        }
        result = await CHAT_COLLECTION.insert_one(doc)
        return ChatMessageOut(
            conversation_id=doc['conversation_id'],
            message=doc['text'],
            attachments=doc.get('attachments'),
            timestamp=doc['timestamp'],
        )

    @staticmethod
    async def get_history(
        conversation_id: str,
        skip: int = 0,
        limit: int = 50,
        role: Optional[str] = None
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Récupère l'historique des messages d'une conversation.
        
        Args:
            conversation_id: ID de la conversation
            skip: Nombre de messages à sauter (pagination)
            limit: Nombre maximum de messages à retourner
            role: Filtrer par rôle (user ou bot)
            
        Returns:
            Tuple contenant le total et la liste des messages
        """
        query: Dict[str, Any] = {'conversation_id': conversation_id}
        if role:
            query['role'] = role

        total = await CHAT_COLLECTION.count_documents(query)
        cursor = (
            CHAT_COLLECTION
            .find(query)
            .sort('timestamp', 1)
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return total, docs

# Instance unique à réutiliser
chat_manager = ChatManager()


def _get_llm_service() -> LLMService:
    """
    Initialise et retourne le service LLM approprié selon la configuration.
    
    Returns:
        Instance de LLMService (OpenAI ou DeepSeek)
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY", "")
    model = os.getenv("LLM_MODEL", "gpt-4")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    
    if provider == "deepseek":
        endpoint_url = os.getenv("DEEPSEEK_ENDPOINT_URL", "https://api.deepseek.com")
        return DeepSeekService(endpoint_url=endpoint_url, api_key=api_key)
    else:
        return OpenAIService(api_key=api_key, model=model, temperature=temperature)


async def handle_message(
    user_email: str,
    conversation_id: Optional[str],
    message: str,
    platform: Optional[str] = None,
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> ChatMessageOut:
    """
    Orchestration d'un message utilisateur vers l'IA :
      1. Sauvegarde du message user
      2. Appel au LLM pour générer la réponse
      3. Sauvegarde de la réponse bot
      4. Retour de la réponse
    
    Args:
        user_email: Email de l'utilisateur
        conversation_id: ID de la conversation (créé si None)
        message: Contenu du message utilisateur
        platform: Plateforme d'origine (Instagram, Telegram, etc.)
        user_id: ID de l'utilisateur
        metadata: Métadonnées supplémentaires
        
    Returns:
        ChatMessageOut: Réponse du bot
    """
    # 0. Créer un conversation_id si absent
    from uuid import uuid4
    if not conversation_id:
        conversation_id = str(uuid4())
    
    # 1. Création de l'objet ChatMessageIn
    msg_in = ChatMessageIn(
        conversation_id=conversation_id,
        message=message,
        platform=platform,
        user_id=user_id,
        metadata=metadata,
    )

    # 2. Sauvegarde du message user
    await chat_manager.save_message(msg_in, role='user')

    # 3. Récupérer l'historique pour le contexte
    total, history_docs = await chat_manager.get_history(conversation_id, limit=10)
    
    # Convertir l'historique en format Message pour le LLM
    messages = []
    for doc in history_docs:
        messages.append(Message(
            role=doc.get('role', 'user'),
            content=doc.get('text', '')
        ))
    
    # 4. Appeler le LLM pour générer la réponse
    try:
        llm_service = _get_llm_service()
        response = await llm_service.generate(
            messages=messages,
            tenant_id=user_email
        )
        bot_response_text = response.text
    except Exception as e:
        # Fallback en cas d'erreur LLM
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur LLM: {e}")
        bot_response_text = f"Désolé, je ne peux pas traiter votre demande pour le moment. ({str(e)})"

    # 5. Sauvegarde de la réponse bot
    bot_msg_in = ChatMessageIn(
        conversation_id=msg_in.conversation_id,
        message=bot_response_text,
        platform=platform,
        user_id=user_id,
        attachments=None,
        metadata=None,
    )
    bot_msg_out = await chat_manager.save_message(bot_msg_in, role='bot')
    return bot_msg_out

async def get_history(
    conversation_id: str,
    skip: int = 0,
    limit: int = 50,
    role: Optional[str] = None
) -> Tuple[int, List[Dict[str, Any]]]:
    """
    Fonction wrapper pour la route GET /chat/history.
    
    Args:
        conversation_id: ID de la conversation
        skip: Nombre de messages à sauter
        limit: Nombre maximum de messages
        role: Filtrer par rôle
        
    Returns:
        Tuple contenant le total et la liste des messages
    """
    return await chat_manager.get_history(
        conversation_id=conversation_id,
        skip=skip,
        limit=limit,
        role=role,
    )

async def dispatch_message(
    platform: str,
    muse_id: str,
    user_id: str,
    message: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Any:
    """
    Point d'entrée pour les webhooks des plateformes :
      1. Enregistre le message entrant
      2. Génère la réponse via LLM
      3. Sauvegarde et retourne la réponse
    
    Args:
        platform: Nom de la plateforme (Instagram, Telegram, etc.)
        muse_id: ID de la muse
        user_id: ID de l'utilisateur
        message: Contenu du message
        metadata: Métadonnées supplémentaires
        
    Returns:
        Réponse du bot
    """
    # Traiter le message avec LLM
    bot_msg = await handle_message(
        user_email=muse_id,
        conversation_id=None,
        message=message,
        platform=platform,
        user_id=user_id,
        metadata=metadata,
    )
    # Retourner la réponse (à envoyer via la plateforme)
    return bot_msg.message
