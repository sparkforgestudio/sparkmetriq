// scripts/index_bi_muses.mjs
// Script MongoDB pour créer les index BI nécessaires pour les analytics muses
// Usage: mongosh mongodb://localhost:27017/musai_bi scripts/index_bi_muses.mjs

const db = db.getSiblingDB('musai_bi');

print("Creating BI indexes for muse analytics...");

// Index pour payments
try {
  db.payments.createIndex(
    {org_id: 1, muse_id: 1, ts: -1},
    {name: "ix_payments_org_muse_ts", background: true}
  );
  print("  ✓ Index ix_payments_org_muse_ts created");
} catch (e) {
  print(`  ⚠ Index ix_payments_org_muse_ts: ${e.message}`);
}

// Index pour ppv_sales
try {
  db.ppv_sales.createIndex(
    {org_id: 1, muse_id: 1, ts: -1},
    {name: "ix_ppv_org_muse_ts", background: true}
  );
  print("  ✓ Index ix_ppv_org_muse_ts created");
} catch (e) {
  print(`  ⚠ Index ix_ppv_org_muse_ts: ${e.message}`);
}

// Index pour messages
try {
  db.messages.createIndex(
    {org_id: 1, muse_id: 1, ts: -1},
    {name: "ix_messages_org_muse_ts", background: true}
  );
  print("  ✓ Index ix_messages_org_muse_ts created");
} catch (e) {
  print(`  ⚠ Index ix_messages_org_muse_ts: ${e.message}`);
}

// Index pour funnel_events
try {
  db.funnel_events.createIndex(
    {org_id: 1, muse_id: 1, event: 1, ts: -1},
    {name: "ix_funnel_org_muse_event_ts", background: true}
  );
  print("  ✓ Index ix_funnel_org_muse_event_ts created");
} catch (e) {
  print(`  ⚠ Index ix_funnel_org_muse_event_ts: ${e.message}`);
}

print("\n✅ BI indexes created for muse analytics.");



