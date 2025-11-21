from fastapi.testclient import TestClient
from api.main import app

def test_post_chat_send_reuses_existing_conversation(test_client: TestClient, mongo_client):
    client = test_client

    # 🔑 Récupère l'URL exacte, avec ou sans prefix global
    send_url = app.url_path_for("chat_send")

    # 1) Premier message (nouvelle conversation)
    resp1 = client.post(send_url, json={"message": "Bonjour MuseBot"})
    assert resp1.status_code == 200, resp1.text
    conv_id = resp1.json()["conversation_id"]

    # 2) Deuxième message (reprise)
    resp2 = client.post(send_url, json={"conversation_id": conv_id, "message": "Encore moi"})
    assert resp2.status_code == 200, resp2.text
    assert resp2.json()["conversation_id"] == conv_id

    # 3) Vérif en base
    docs = list(mongo_client["chat_messages"].find({"conversation_id": conv_id}))
    assert len(docs) == 4
    roles = [d["role"] for d in docs]
    assert roles.count("user") == 2
    assert roles.count("bot") == 2
