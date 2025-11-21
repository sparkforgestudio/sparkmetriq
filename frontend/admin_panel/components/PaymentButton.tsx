// components/PaymentButton.tsx
import React, { useState } from "react";
import axios from "axios";

interface Props {
  amount: number;
  museId: string;
}

export function PaymentButton({ amount, museId }: Props) {
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    setLoading(true);
    try {
      const res = await axios.post("/api/payments/create", {
        amount,
        description: "Accès premium",
        muse_id: museId,
      });
      window.location.href = res.data.payment_url;
    } catch (err) {
      alert("Erreur de paiement");
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={loading}
      className="px-4 py-2 bg-blue-600 text-white rounded"
    >
      {loading ? "Génération du lien…" : `Payer ${amount} USDT`}
    </button>
  );
}
