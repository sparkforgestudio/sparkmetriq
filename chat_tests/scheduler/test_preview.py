# chat_tests/scheduler/test_preview.py
"""
Tests d'intégration pour le preview IA.
"""

from fastapi.testclient import TestClient

def test_preview_caption(test_client: TestClient, mongo_client):
    """Test de génération de preview IA."""
    payload = {
        "platform": "twitter",
        "muse_id": "melissa",
        "prompt": "teaser evening",
        "tone": "flirty",
        "objective": "conversion",
        "language": "en"
    }
    r = test_client.post("/api/scheduler/preview", json=payload)
    assert r.status_code == 200
    b = r.json()
    assert "caption" in b
    assert "hashtags" in b
    assert "emojis" in b

def test_preview_different_platforms(test_client: TestClient, mongo_client):
    """Test de preview pour différentes plateformes."""
    platforms = ["instagram", "twitter", "reddit", "tiktok"]
    
    for platform in platforms:
        payload = {
            "platform": platform,
            "muse_id": "melissa",
            "prompt": "sexy teaser",
            "tone": "flirty",
            "objective": "teasing",
            "language": "en"
        }
        r = test_client.post("/api/scheduler/preview", json=payload)
        assert r.status_code == 200, f"Failed for platform {platform}"
        
        b = r.json()
        assert "caption" in b
        assert len(b["caption"]) > 0

def test_preview_different_tones(test_client: TestClient, mongo_client):
    """Test de preview avec différents tons."""
    tones = ["flirty", "professional", "energetic", "intimate"]
    
    for tone in tones:
        payload = {
            "platform": "instagram",
            "muse_id": "melissa",
            "prompt": "new content",
            "tone": tone,
            "objective": "engagement",
            "language": "en"
        }
        r = test_client.post("/api/scheduler/preview", json=payload)
        assert r.status_code == 200, f"Failed for tone {tone}"
        
        b = r.json()
        assert "caption" in b
        assert len(b["caption"]) > 0



