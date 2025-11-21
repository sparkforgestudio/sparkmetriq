# api/services/observability/metrics.py
"""
Service de métriques Prometheus pour l'observabilité.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from bson import ObjectId
from api.databases.databases import db

# Métriques Prometheus (stubs pour V1)
class PrometheusMetrics:
    """Classe pour gérer les métriques Prometheus."""
    
    def __init__(self):
        self.counters = {}
        self.gauges = {}
        self.histograms = {}
    
    def increment_counter(self, name: str, labels: Optional[Dict[str, str]] = None, value: float = 1.0):
        """Incrémenter un compteur."""
        key = f"{name}{self._format_labels(labels)}"
        self.counters[key] = self.counters.get(key, 0) + value
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Définir une jauge."""
        key = f"{name}{self._format_labels(labels)}"
        self.gauges[key] = value
    
    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Observer une valeur dans un histogramme."""
        key = f"{name}{self._format_labels(labels)}"
        if key not in self.histograms:
            self.histograms[key] = []
        self.histograms[key].append(value)
    
    def _format_labels(self, labels: Optional[Dict[str, str]]) -> str:
        """Formater les labels pour la clé."""
        if not labels:
            return ""
        return "{" + ",".join([f'{k}="{v}"' for k, v in labels.items()]) + "}"
    
    def get_metrics(self) -> Dict[str, Any]:
        """Récupérer toutes les métriques."""
        return {
            "counters": self.counters,
            "gauges": self.gauges,
            "histograms": self.histograms
        }

# Instance globale des métriques
metrics = PrometheusMetrics()

# ---------- MÉTRIQUES CLOUDPHONE ----------

def increment_cloudphone_device_created(org_id: str, area: Optional[str] = None):
    """Incrémenter le compteur de devices CloudPhone créés."""
    labels = {"org_id": org_id}
    if area:
        labels["area"] = area
    metrics.increment_counter("cloudphone_devices_created_total", labels)

def increment_cloudphone_device_started(org_id: str, area: Optional[str] = None):
    """Incrémenter le compteur de devices CloudPhone démarrés."""
    labels = {"org_id": org_id}
    if area:
        labels["area"] = area
    metrics.increment_counter("cloudphone_devices_started_total", labels)

def increment_cloudphone_device_stopped(org_id: str, area: Optional[str] = None):
    """Incrémenter le compteur de devices CloudPhone arrêtés."""
    labels = {"org_id": org_id}
    if area:
        labels["area"] = area
    metrics.increment_counter("cloudphone_devices_stopped_total", labels)

def increment_cloudphone_app_installed(org_id: str, app: str, area: Optional[str] = None):
    """Incrémenter le compteur d'apps installées."""
    labels = {"org_id": org_id, "app": app}
    if area:
        labels["area"] = area
    metrics.increment_counter("cloudphone_apps_installed_total", labels)

def increment_cloudphone_slot_created(org_id: str, app: str, isolation_strategy: str):
    """Incrémenter le compteur de slots créés."""
    labels = {
        "org_id": org_id,
        "app": app,
        "isolation_strategy": isolation_strategy
    }
    metrics.increment_counter("cloudphone_slots_created_total", labels)

def increment_cloudphone_slot_bound(org_id: str, app: str):
    """Incrémenter le compteur de slots liés."""
    labels = {"org_id": org_id, "app": app}
    metrics.increment_counter("cloudphone_slots_bound_total", labels)

def increment_cloudphone_slot_unbound(org_id: str, app: str):
    """Incrémenter le compteur de slots déliés."""
    labels = {"org_id": org_id, "app": app}
    metrics.increment_counter("cloudphone_slots_unbound_total", labels)

def increment_cloudphone_action_executed(org_id: str, action: str, app: str, success: bool):
    """Incrémenter le compteur d'actions exécutées."""
    labels = {
        "org_id": org_id,
        "action": action,
        "app": app,
        "status": "success" if success else "error"
    }
    metrics.increment_counter("cloudphone_actions_executed_total", labels)

def set_cloudphone_devices_running(org_id: str, count: int, area: Optional[str] = None):
    """Définir le nombre de devices en cours d'exécution."""
    labels = {"org_id": org_id}
    if area:
        labels["area"] = area
    metrics.set_gauge("cloudphone_devices_running", count, labels)

def set_cloudphone_slots_active(org_id: str, count: int, app: str):
    """Définir le nombre de slots actifs."""
    labels = {"org_id": org_id, "app": app}
    metrics.set_gauge("cloudphone_slots_active", count, labels)

def observe_cloudphone_action_duration(org_id: str, action: str, app: str, duration_seconds: float):
    """Observer la durée d'une action CloudPhone."""
    labels = {"org_id": org_id, "action": action, "app": app}
    metrics.observe_histogram("cloudphone_action_duration_seconds", duration_seconds, labels)

# ---------- MÉTRIQUES OTP ----------

def increment_otp_session_reserved(org_id: str, app: str, country: str, provider: str):
    """Incrémenter le compteur de sessions OTP réservées."""
    labels = {
        "org_id": org_id,
        "app": app,
        "country": country,
        "provider": provider
    }
    metrics.increment_counter("otp_sessions_reserved_total", labels)

def increment_otp_session_delivered(org_id: str, app: str, country: str, provider: str):
    """Incrémenter le compteur de sessions OTP livrées."""
    labels = {
        "org_id": org_id,
        "app": app,
        "country": country,
        "provider": provider
    }
    metrics.increment_counter("otp_sessions_delivered_total", labels)

def increment_otp_session_applied(org_id: str, app: str, country: str, provider: str, success: bool):
    """Incrémenter le compteur de sessions OTP appliquées."""
    labels = {
        "org_id": org_id,
        "app": app,
        "country": country,
        "provider": provider,
        "status": "success" if success else "failed"
    }
    metrics.increment_counter("otp_sessions_applied_total", labels)

def increment_otp_session_failed(org_id: str, app: str, country: str, provider: str, reason: str):
    """Incrémenter le compteur de sessions OTP échouées."""
    labels = {
        "org_id": org_id,
        "app": app,
        "country": country,
        "provider": provider,
        "reason": reason
    }
    metrics.increment_counter("otp_sessions_failed_total", labels)

def increment_otp_provider_failover(org_id: str, from_provider: str, to_provider: str, app: str):
    """Incrémenter le compteur de failovers OTP."""
    labels = {
        "org_id": org_id,
        "from_provider": from_provider,
        "to_provider": to_provider,
        "app": app
    }
    metrics.increment_counter("otp_provider_failover_total", labels)

def set_otp_sessions_active(org_id: str, count: int, app: str):
    """Définir le nombre de sessions OTP actives."""
    labels = {"org_id": org_id, "app": app}
    metrics.set_gauge("otp_sessions_active", count, labels)

def set_otp_provider_health_score(org_id: str, provider: str, score: float):
    """Définir le score de santé d'un provider OTP."""
    labels = {"org_id": org_id, "provider": provider}
    metrics.set_gauge("otp_provider_health_score", score, labels)

def observe_otp_response_time(org_id: str, app: str, country: str, provider: str, response_time_seconds: float):
    """Observer le temps de réponse OTP."""
    labels = {
        "org_id": org_id,
        "app": app,
        "country": country,
        "provider": provider
    }
    metrics.observe_histogram("otp_response_time_seconds", response_time_seconds, labels)

def observe_otp_session_duration(org_id: str, app: str, country: str, provider: str, duration_seconds: float):
    """Observer la durée d'une session OTP."""
    labels = {
        "org_id": org_id,
        "app": app,
        "country": country,
        "provider": provider
    }
    metrics.observe_histogram("otp_session_duration_seconds", duration_seconds, labels)

# ---------- MÉTRIQUES SYSTÈME ----------

def increment_system_error(org_id: str, error_type: str, component: str):
    """Incrémenter le compteur d'erreurs système."""
    labels = {
        "org_id": org_id,
        "error_type": error_type,
        "component": component
    }
    metrics.increment_counter("system_errors_total", labels)

def increment_system_alert(org_id: str, alert_type: str, severity: str):
    """Incrémenter le compteur d'alertes système."""
    labels = {
        "org_id": org_id,
        "alert_type": alert_type,
        "severity": severity
    }
    metrics.increment_counter("system_alerts_total", labels)

def set_system_uptime(org_id: str, uptime_seconds: float):
    """Définir le temps de fonctionnement du système."""
    labels = {"org_id": org_id}
    metrics.set_gauge("system_uptime_seconds", uptime_seconds, labels)

def set_system_memory_usage(org_id: str, memory_bytes: int):
    """Définir l'utilisation mémoire du système."""
    labels = {"org_id": org_id}
    metrics.set_gauge("system_memory_usage_bytes", memory_bytes, labels)

def set_system_cpu_usage(org_id: str, cpu_percent: float):
    """Définir l'utilisation CPU du système."""
    labels = {"org_id": org_id}
    metrics.set_gauge("system_cpu_usage_percent", cpu_percent, labels)

# ---------- FONCTIONS UTILITAIRES ----------

async def get_metrics_summary(org_id: str, days: int = 7) -> Dict[str, Any]:
    """Récupérer un résumé des métriques pour une organisation."""
    start_date = datetime.now() - timedelta(days=days)
    
    # Métriques CloudPhone
    cloudphone_stats = await db["cloudphone_devices"].aggregate([
        {"$match": {"org_id": org_id, "created_at": {"$gte": start_date}}},
        {
            "$group": {
                "_id": None,
                "total_devices": {"$sum": 1},
                "running_devices": {"$sum": {"$cond": [{"$eq": ["$state", "running"]}, 1, 0]}},
                "by_area": {"$push": "$area"}
            }
        }
    ]).to_list(1)
    
    # Métriques OTP
    otp_stats = await db["otp_sessions"].aggregate([
        {"$match": {"org_id": org_id, "created_at": {"$gte": start_date}}},
        {
            "$group": {
                "_id": None,
                "total_sessions": {"$sum": 1},
                "successful_sessions": {"$sum": {"$cond": [{"$eq": ["$state", "APPLIED_SUCCESS"]}, 1, 0]}},
                "failed_sessions": {"$sum": {"$cond": [{"$eq": ["$state", "APPLIED_FAILED"]}, 1, 0]}},
                "by_app": {"$push": "$app"},
                "by_country": {"$push": "$country"},
                "by_provider": {"$push": "$provider"}
            }
        }
    ]).to_list(1)
    
    # Métriques d'activité
    activity_stats = await db["activity_logs"].aggregate([
        {"$match": {"org_id": org_id, "timestamp": {"$gte": start_date}}},
        {
            "$group": {
                "_id": None,
                "total_activities": {"$sum": 1},
                "by_scope": {"$push": "$scope"},
                "by_action": {"$push": "$action"},
                "by_status": {"$push": "$status"}
            }
        }
    ]).to_list(1)
    
    return {
        "org_id": org_id,
        "period_days": days,
        "cloudphone": cloudphone_stats[0] if cloudphone_stats else {},
        "otp": otp_stats[0] if otp_stats else {},
        "activity": activity_stats[0] if activity_stats else {},
        "prometheus_metrics": metrics.get_metrics()
    }

def export_prometheus_metrics() -> str:
    """Exporter les métriques au format Prometheus."""
    lines = []
    
    # Compteurs
    for key, value in metrics.counters.items():
        lines.append(f"# TYPE {key.split('{')[0]} counter")
        lines.append(f"{key} {value}")
    
    # Jauges
    for key, value in metrics.gauges.items():
        lines.append(f"# TYPE {key.split('{')[0]} gauge")
        lines.append(f"{key} {value}")
    
    # Histogrammes
    for key, values in metrics.histograms.items():
        lines.append(f"# TYPE {key.split('{')[0]} histogram")
        lines.append(f"{key}_count {len(values)}")
        lines.append(f"{key}_sum {sum(values)}")
        if values:
            lines.append(f"{key}_avg {sum(values) / len(values)}")
    
    return "\n".join(lines)

# ---------- INITIALISATION ----------

async def initialize_metrics():
    """Initialiser les métriques au démarrage."""
    # Récupérer les métriques existantes depuis la base de données
    # et les charger dans les métriques Prometheus
    
    # Pour V1, on initialise avec des valeurs par défaut
    metrics.set_gauge("system_uptime_seconds", 0.0)
    metrics.set_gauge("system_memory_usage_bytes", 0)
    metrics.set_gauge("system_cpu_usage_percent", 0.0)
    
    print("✅ Métriques Prometheus initialisées")



