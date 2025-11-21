# api/services/payment_gateway/cryptobot.py

import os
# Correction de l'import pour pointer vers le schéma correct
from api.schemas.payments import PaymentRequest

# ... autres imports nécessaires ...

def generate_payment_link(payment_request: PaymentRequest, user):
    """
    Simule la génération d'un lien de paiement pour la demande fournie.
    :param payment_request: données de la demande de paiement
    :param user: utilisateur courant (UserResponse)
    :return: URL de paiement
    """
    # Exemple fictif : construire une URL en encodant les données
    base_url = os.getenv("PAYMENT_BASE_URL", "https://payments.example.com/pay")
    # On pourrait ici interagir avec une API tierce
    return f"{base_url}?amount={payment_request.amount}&currency={payment_request.currency}&user={user.email}"
