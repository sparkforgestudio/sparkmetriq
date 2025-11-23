# api/services/intent/scenario_engine.py
"""
Moteur de scénarios pour le Mode B (LLM + Scénario).
Gère la sélection et l'exécution des scénarios.
"""

import logging
from typing import Dict, Any, Optional
from api.databases.databases import get_core_db
from api.schemas.intent import ChatScenario, ChatSession, ScenarioStep

logger = logging.getLogger(__name__)


class ScenarioEngine:
    """Moteur de gestion des scénarios."""
    
    async def pick_applicable(
        self,
        org_id: str,
        muse_id: str,
        event: Dict[str, Any]
    ) -> Optional[ChatScenario]:
        """
        Sélectionne un scénario applicable pour l'événement.
        
        Args:
            org_id: ID de l'organisation
            muse_id: ID de la muse
            event: Événement entrant (InboundEvent.dict())
            
        Returns:
            Scénario applicable ou None
        """
        platform = event.get("platform")
        trig_type = event.get("type")
        
        if not platform or not trig_type:
            logger.warning(f"Event missing platform or type: {event}")
            return None
        
        db = get_core_db()
        
        try:
            # Rechercher un scénario actif correspondant
            row = await db["chat_scenarios"].find_one({
                "org_id": org_id,
                "muse_id": muse_id,
                "is_active": True,
                "platforms": {"$in": [platform]},
                "trigger.type": trig_type
            })
            
            if not row:
                logger.debug(
                    f"No applicable scenario found for org_id={org_id}, "
                    f"muse_id={muse_id}, platform={platform}, type={trig_type}"
                )
                return None
            
            # Convertir en ChatScenario
            scenario = ChatScenario(**row)
            logger.info(
                f"Selected scenario '{scenario.title}' for org_id={org_id}, "
                f"muse_id={muse_id}, event_type={trig_type}"
            )
            return scenario
            
        except Exception as e:
            logger.error(f"Erreur lors de la sélection du scénario: {e}")
            return None
    
    async def next_step(
        self,
        scenario: ChatScenario,
        session: Optional[ChatSession]
    ) -> Optional[ScenarioStep]:
        """
        Retourne la prochaine étape du scénario.
        
        Args:
            scenario: Scénario en cours
            session: Session actuelle (None pour démarrer)
            
        Returns:
            Prochaine étape ou None si terminé
        """
        if not scenario.steps:
            logger.warning(f"Scenario '{scenario.title}' has no steps")
            return None
        
        # Si aucune session, retourner la première étape
        if session is None:
            return scenario.steps[0]
        
        # Trouver l'index de l'étape actuelle
        step_ids = [s.id for s in scenario.steps]
        
        try:
            current_idx = step_ids.index(session.current_step)
        except ValueError:
            logger.warning(
                f"Current step '{session.current_step}' not found in scenario "
                f"'{scenario.title}'"
            )
            return None
        
        # Avancer à la prochaine étape
        next_idx = current_idx + 1
        
        if next_idx >= len(scenario.steps):
            logger.debug(f"Scenario '{scenario.title}' completed")
            return None
        
        return scenario.steps[next_idx]
    
    async def get_current_step(
        self,
        scenario: ChatScenario,
        session: ChatSession
    ) -> Optional[ScenarioStep]:
        """
        Retourne l'étape actuelle de la session.
        
        Args:
            scenario: Scénario en cours
            session: Session actuelle
            
        Returns:
            Étape actuelle ou None si introuvable
        """
        if not scenario.steps:
            return None
        
        step_ids = [s.id for s in scenario.steps]
        
        try:
            idx = step_ids.index(session.current_step)
            return scenario.steps[idx]
        except ValueError:
            logger.warning(
                f"Step '{session.current_step}' not found in scenario "
                f"'{scenario.title}'"
            )
            return None




