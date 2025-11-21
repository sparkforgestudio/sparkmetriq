// pages/muses/[id].tsx
import { useRouter } from "next/router";
import { PaymentButton } from "@/components/PaymentButton";

export default function MusePage() {
  const { query } = useRouter();
  const museId = query.id as string;
  return (
    <div className="p-6">
      <h1 className="text-2xl">Page de la Muse {museId}</h1>
      <PaymentButton amount={10} museId={museId} />
    </div>
  );
}
