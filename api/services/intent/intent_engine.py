# api/services/intent/intent_engine.py
"""
Moteur d'Intentions principal.
Orchestre la décision entre Mode A (LLM Pilote) et Mode B (LLM + Scénario).
"""

import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone

from api.databases.databases import get_core_db
from api.schemas.intent import (
    InboundEvent, OutboundMessage, ConversationModePatch,
    ChatScenario, ChatSession, PersonaProfile, ChatPolicies
)
from api.services.intent.rag_unified import UnifiedRetriever
from api.services.intent.llm_handler import LLMHandler
from api.services.intent.scenario_engine import ScenarioEngine
from api.services.intent.validator import MessageValidator
from api.services.intent.dispatcher import ChannelDispatcher

logger = logging.getLogger(__name__)


class IntentEngine:
    """Moteur d'intentions principal."""
    
    def __init__(self):
        """Initialise le moteur d'intentions."""
        self.retriever = UnifiedRetriever()
        self.llm = LLMHandler()
        self.scenario = ScenarioEngine()
        self.validator = MessageValidator()
        self.dispatch = ChannelDispatcher()
    
    async def _get_mode_for_conversation(
        self,
        org_id: str,
        muse_id: str,
        conversation_id: str
    ) -> str:
        """
        Détermine le mode d'exécution pour une conversation.
        
        Args:
            org_id: ID de l'organisation
            muse_id: ID de la muse
            conversation_id: ID de la conversation
            
        Returns:
            Mode ("llm_pilot" ou "scenario_guided")
        """
        db = get_core_db()
        
        # Vérifier s'il y a une session active (implique scenario_guided)
        sess = await db["chat_sessions"].find_one({
            "org_id": org_id,
            "muse_id": muse_id,
            "conversation_id": conversation_id,
            "status": {"$ne": "completed"}
        })
        
        if sess:
            return "scenario_guided"
        
        # Vérifier les overrides explicites
        override = await db["conversation_overrides"].find_one({
            "org_id": org_id,
            "muse_id": muse_id,
            "conversation_id": conversation_id
        })
        
        if override:
            return override.get("mode", "llm_pilot")
        
        # Par défaut : llm_pilot
        return "llm_pilot"
    
    async def _load_persona_and_policies(
        self,
        org_id: str,
        muse_id: str
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Charge la persona et les politiques pour une muse.
        
        Args:
            org_id: ID de l'organisation
            muse_id: ID de la muse
            
        Returns:
            Tuple (persona_dict, policies_dict)
        """
        db = get_core_db()
        
        persona_row = await db["persona_profiles"].find_one({
            "org_id": org_id,
            "muse_id": muse_id
        })
        
        policies_row = await db["chat_policies"].find_one({
            "org_id": org_id,
            "muse_id": muse_id
        })
        
        persona = persona_row or {}
        policies = policies_row or {}
        
        return persona, policies
    
    async def handle_inbound(self, ev: InboundEvent) -> Dict[str, Any]:
        """
        Traite un événement entrant.
        
        Args:
            ev: Événement entrant
            
        Returns:
            Résultat du traitement
        """
        org_id = ev.org_id
        muse_id = ev.muse_id
        
        logger.info(
            f"Handling inbound event: org_id={org_id}, muse_id={muse_id}, "
            f"platform={ev.platform}, type={ev.type}, conversation_id={ev.conversation_id}"
        )
        
        # Charger persona et policies
        persona, policies = await self._load_persona_and_policies(org_id, muse_id)
        
        # Construire les règles de branding
        brand_rules = []
        if persona:
            tone_profile = persona.get("tone_profile", {})
            if isinstance(tone_profile, dict):
                brand_rules.extend(tone_profile.get("do", []))
                brand_rules.extend(tone_profile.get("dont", []))
            brand_rules.extend(persona.get("brand_boosters", []))
        
        # Récupérer le contexte RAG
        retrieved = await self.retriever.retrieve(
            org_id, muse_id, query=ev.text or ""
        )
        
        # Déterminer le mode
        mode = await self._get_mode_for_conversation(
            org_id, muse_id, ev.conversation_id
        )
        
        logger.debug(f"Mode determined: {mode} for conversation_id={ev.conversation_id}")
        
        # Mode A: LLM Pilote
        if mode == "llm_pilot":
            return await self._handle_llm_pilot(
                ev, persona, brand_rules, retrieved, policies
            )
        
        # Mode B: Scenario Guided
        return await self._handle_scenario_guided(
            ev, persona, brand_rules, retrieved, policies
        )
    
    async def _handle_llm_pilot(
        self,
        ev: InboundEvent,
        persona: Dict[str, Any],
        brand_rules: list,
        retrieved: list,
        policies: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gère le Mode A (LLM Pilote)."""
        # Mettre à jour le validateur avec les politiques
        validator = MessageValidator(
            forbidden_words=set(policies.get("compliance", {}).get("forbidden_words", [])),
            platform=ev.platform
        )
        
        # Générer la réponse libre
        tone_profile = persona.get("tone_profile", {}) if persona else {}
        
        reply = await self.llm.freeform_reply({
            "system": "You respond as the muse with brand-compliant tone.",
            "user": ev.text or "",
            "retrieved": retrieved,
            "brand_rules": brand_rules,
            "platform": ev.platform,
            "persona": tone_profile
        })
        
        # Valider
        is_valid, error = validator.validate(reply)
        if not is_valid:
            logger.warning(f"Message validation failed: {error}, using fallback")
            reply = "Thanks for your message! 😊"  # Fallback sécurisé
        
        # Construire le message sortant
        out = OutboundMessage(
            conversation_id=ev.conversation_id,
            text=reply,
            platform=ev.platform,
            metadata={"mode": "llm_pilot"}
        )
        
        # Envoyer
        dispatch_result = await self.dispatch.send(ev.platform, out.model_dump())
        
        logger.info(
            f"LLM Pilot response sent for conversation_id={ev.conversation_id}, "
            f"text_length={len(reply)}"
        )
        
        return {
            "mode": "llm_pilot",
            "sent": out.model_dump(),
            "dispatch_result": dispatch_result
        }
    
    async def _handle_scenario_guided(
        self,
        ev: InboundEvent,
        persona: Dict[str, Any],
        brand_rules: list,
        retrieved: list,
        policies: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gère le Mode B (Scenario Guided)."""
        db = get_core_db()
        org_id = ev.org_id
        muse_id = ev.muse_id
        conversation_id = ev.conversation_id
        
        # Charger ou créer la session
        sess_row = await db["chat_sessions"].find_one({
            "org_id": org_id,
            "muse_id": muse_id,
            "conversation_id": conversation_id
        })
        
        scenario = None
        
        # Si pas de session, chercher un scénario applicable
        if not sess_row:
            scenario = await self.scenario.pick_applicable(
                org_id, muse_id, ev.model_dump()
            )
            
            if scenario:
                # Créer une nouvelle session
                from api.schemas.intent import ChatSession
                session_data = {
                    "org_id": org_id,
                    "muse_id": muse_id,
                    "conversation_id": conversation_id,
                    "scenario_id": scenario.title,  # Utiliser title comme ID pour MVP
                    "current_step": scenario.steps[0].id if scenario.steps else "",
                    "status": "in_progress",
                    "platform": ev.platform,
                    "context": {"first_text": ev.text or ""}
                }
                await db["chat_sessions"].insert_one(session_data)
                sess_row = session_data
                logger.info(
                    f"New scenario session created: scenario='{scenario.title}', "
                    f"conversation_id={conversation_id}"
                )
        
        # Si on a une session mais pas de scénario, charger le scénario
        if sess_row and not scenario:
            scenario_row = await db["chat_scenarios"].find_one({
                "org_id": org_id,
                "muse_id": muse_id,
                "title": sess_row["scenario_id"]
            })
            if scenario_row:
                scenario = ChatScenario(**scenario_row)
        
        # Si aucun scénario, fallback vers LLM Pilote
        if not scenario:
            logger.warning(
                f"No scenario available, falling back to LLM pilot for "
                f"conversation_id={conversation_id}"
            )
            return await self._handle_llm_pilot(
                ev, persona, brand_rules, retrieved, policies
            )
        
        # Exécuter l'étape actuelle
        session = ChatSession(**sess_row) if sess_row else None
        step = await self.scenario.get_current_step(scenario, session)
        
        if not step:
            # Scénario terminé
            await db["chat_sessions"].update_one(
                {"_id": sess_row["_id"]},
                {"$set": {"status": "completed"}}
            )
            return {
                "mode": "scenario_guided",
                "status": "completed",
                "scenario": scenario.title
            }
        
        # Exécuter l'étape
        if step.type in ["message", "ppv_offer", "media"]:
            text = step.template or ""
            
            # Styliser avec LLM si demandé
            if step.use_llm_tone and text:
                tone_profile = persona.get("tone_profile", {}) if persona else {}
                text = await self.llm.style_rewrite(text, {
                    "retrieved": retrieved,
                    "brand_rules": brand_rules,
                    "platform": ev.platform,
                    "persona": tone_profile
                })
            
            # Valider
            validator = MessageValidator(
                forbidden_words=set(policies.get("compliance", {}).get("forbidden_words", [])),
                platform=ev.platform
            )
            is_valid, error = validator.validate(text)
            
            if not is_valid:
                logger.warning(f"Step text validation failed: {error}")
                text = "Thanks for your message! 😊"  # Fallback
            
            # Construire et envoyer
            out = OutboundMessage(
                conversation_id=conversation_id,
                text=text,
                platform=ev.platform,
                metadata={
                    "mode": "scenario_guided",
                    "scenario": scenario.title,
                    "step_id": step.id,
                    "step_type": step.type
                }
            )
            
            dispatch_result = await self.dispatch.send(ev.platform, out.model_dump())
            
            # Actions post-envoi
            if step.actions_on_send:
                await self._execute_step_actions(
                    step, org_id, muse_id, conversation_id, ev
                )
            
            # Avancer à l'étape suivante
            next_step_id = await self._advance_step(db, sess_row, scenario)
            
            logger.info(
                f"Scenario step executed: step_id={step.id}, "
                f"scenario={scenario.title}, next_step={next_step_id}"
            )
            
            return {
                "mode": "scenario_guided",
                "scenario": scenario.title,
                "step": step.id,
                "step_type": step.type,
                "advanced_to": next_step_id,
                "sent": out.model_dump(),
                "dispatch_result": dispatch_result
            }
        
        # Pour les autres types d'étapes (wait, tag_fan, etc.)
        logger.debug(f"Step type '{step.type}' not implemented yet, skipping")
        return {
            "mode": "scenario_guided",
            "step": step.id,
            "step_type": step.type,
            "status": "skipped"
        }
    
    async def _execute_step_actions(
        self,
        step,
        org_id: str,
        muse_id: str,
        conversation_id: str,
        ev: InboundEvent
    ):
        """Exécute les actions post-envoi d'une étape."""
        # TODO: Implémenter tag_fan, track_event, etc.
        logger.debug(
            f"Executing step actions: {step.actions_on_send} for "
            f"conversation_id={conversation_id}"
        )
    
    async def _advance_step(
        self,
        db,
        sess_row: Dict[str, Any],
        scenario: ChatScenario
    ) -> Optional[str]:
        """Avance à l'étape suivante du scénario."""
        step_ids = [s.id for s in scenario.steps]
        
        try:
            current_idx = step_ids.index(sess_row["current_step"])
        except ValueError:
            logger.warning(
                f"Current step '{sess_row['current_step']}' not found in scenario"
            )
            await db["chat_sessions"].update_one(
                {"_id": sess_row["_id"]},
                {"$set": {"status": "aborted"}}
            )
            return None
        
        next_idx = current_idx + 1
        
        if next_idx >= len(scenario.steps):
            await db["chat_sessions"].update_one(
                {"_id": sess_row["_id"]},
                {"$set": {"status": "completed"}}
            )
            return None
        
        next_step_id = scenario.steps[next_idx].id
        await db["chat_sessions"].update_one(
            {"_id": sess_row["_id"]},
            {"$set": {"current_step": next_step_id}}
        )
        
        return next_step_id
    
    async def set_conversation_mode(
        self,
        org_id: str,
        muse_id: str,
        conversation_id: str,
        mode: str
    ) -> Dict[str, Any]:
        """
        Force le mode d'exécution pour une conversation.
        
        Args:
            org_id: ID de l'organisation
            muse_id: ID de la muse
            conversation_id: ID de la conversation
            mode: Mode souhaité ("llm_pilot" ou "scenario_guided")
            
        Returns:
            Confirmation
        """
        db = get_core_db()
        
        await db["conversation_overrides"].update_one(
            {
                "org_id": org_id,
                "muse_id": muse_id,
                "conversation_id": conversation_id
            },
            {
                "$set": {
                    "mode": mode,
                    "updated_at": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
        
        logger.info(
            f"Conversation mode set: conversation_id={conversation_id}, mode={mode}"
        )
        
        return {"ok": True, "mode": mode}
