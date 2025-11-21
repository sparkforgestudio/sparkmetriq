// scripts/seed_muse_categories.mjs
// Script MongoDB pour créer les catégories de muses et les index
// Usage: mongosh mongodb://localhost:27017/musai_core scripts/seed_muse_categories.mjs

const db = db.getSiblingDB('musai_core');

print("Seeding muse categories...");

// Catégories (idempotent)
const categories = [
  {_id: "cosplay",  label: "Cosplay",  description: "Costumes & univers fictionnels", is_active: true, order: 10},
  {_id: "fitness",  label: "Fitness",  description: "Sport & bien-être", is_active: true, order: 20},
  {_id: "dominant", label: "Dominant", description: "Femdom / D/s",      is_active: true, order: 30},
  {_id: "submissive", label: "Submissive", description: "Soumission", is_active: true, order: 40},
  {_id: "milf",     label: "MILF",     description: "Mature", is_active: true, order: 50},
  {_id: "teen",     label: "Teen",     description: "18-24 ans", is_active: true, order: 60},
  {_id: "bbw",      label: "BBW",      description: "Curvy", is_active: true, order: 70},
  {_id: "athletic", label: "Athletic", description: "Sportive", is_active: true, order: 80},
];

categories.forEach(c => {
  db.muse_categories.updateOne(
    {_id: c._id},
    {$set: c},
    {upsert: true}
  );
  print(`  ✓ Category '${c._id}' seeded`);
});

// Indexes (idempotents)
print("\nCreating indexes...");

try {
  db.muses.createIndex({org_id: 1, status: 1}, {name: "ix_muses_org_status", background: true});
  print("  ✓ Index ix_muses_org_status created");
} catch (e) {
  print(`  ⚠ Index ix_muses_org_status: ${e.message}`);
}

try {
  db.muses.createIndex({org_id: 1, categories: 1}, {name: "ix_muses_org_categories", background: true});
  print("  ✓ Index ix_muses_org_categories created");
} catch (e) {
  print(`  ⚠ Index ix_muses_org_categories: ${e.message}`);
}

try {
  db.muse_categories.createIndex({is_active: 1, order: 1}, {name: "ix_categories_active_order", background: true});
  print("  ✓ Index ix_categories_active_order created");
} catch (e) {
  print(`  ⚠ Index ix_categories_active_order: ${e.message}`);
}

print("\n✅ Muse categories seeded & indexes created.");



