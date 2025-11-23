// scripts/setup_musai_bi.mjs
// Script MongoDB pour créer les collections et index de la base BI (musai_bi)
// Usage: mongosh mongodb://localhost:27017 scripts/setup_musai_bi.mjs

const bi = connect("mongodb://localhost:27017/musai_bi");

print("Setting up musai_bi collections...");

// 1) Stats agrégées par créateur (journalier)
try {
    bi.createCollection("agg_creator_stats_daily");
    print("  ✓ Collection agg_creator_stats_daily created");
} catch (e) {
    print(`  ⚠ agg_creator_stats_daily: ${e.message}`);
}

try {
    bi.agg_creator_stats_daily.createIndex(
        { org_id: 1, muse_id: 1, date: 1 },
        { name: "ux_creator_stats_org_muse_date", unique: true, background: true }
    );
    print("  ✓ Index ux_creator_stats_org_muse_date created");
} catch (e) {
    print(`  ⚠ Index ux_creator_stats_org_muse_date: ${e.message}`);
}

try {
    bi.agg_creator_stats_daily.createIndex(
        { org_id: 1, platform: 1, date: 1 },
        { name: "ix_creator_stats_org_platform_date", background: true }
    );
    print("  ✓ Index ix_creator_stats_org_platform_date created");
} catch (e) {
    print(`  ⚠ Index ix_creator_stats_org_platform_date: ${e.message}`);
}

// 2) Performance PPV (journalier)
try {
    bi.createCollection("agg_ppv_performance_daily");
    print("  ✓ Collection agg_ppv_performance_daily created");
} catch (e) {
    print(`  ⚠ agg_ppv_performance_daily: ${e.message}`);
}

try {
    bi.agg_ppv_performance_daily.createIndex(
        { org_id: 1, muse_id: 1, date: 1 },
        { name: "ix_ppv_perf_org_muse_date", background: true }
    );
    print("  ✓ Index ix_ppv_perf_org_muse_date created");
} catch (e) {
    print(`  ⚠ Index ix_ppv_perf_org_muse_date: ${e.message}`);
}

try {
    bi.agg_ppv_performance_daily.createIndex(
        { org_id: 1, item_ref: 1, date: 1 },
        { name: "ix_ppv_perf_org_item_date", background: true }
    );
    print("  ✓ Index ix_ppv_perf_org_item_date created");
} catch (e) {
    print(`  ⚠ Index ix_ppv_perf_org_item_date: ${e.message}`);
}

// 3) Transactions (PPV, abonnements, bundles)
try {
    bi.createCollection("sales_transactions");
    print("  ✓ Collection sales_transactions created");
} catch (e) {
    print(`  ⚠ sales_transactions: ${e.message}`);
}

try {
    bi.sales_transactions.createIndex(
        { org_id: 1, muse_id: 1, created_at: -1 },
        { name: "ix_transactions_org_muse_ts", background: true }
    );
    print("  ✓ Index ix_transactions_org_muse_ts created");
} catch (e) {
    print(`  ⚠ Index ix_transactions_org_muse_ts: ${e.message}`);
}

try {
    bi.sales_transactions.createIndex(
        { org_id: 1, fan_id: 1, created_at: -1 },
        { name: "ix_transactions_org_fan_ts", background: true }
    );
    print("  ✓ Index ix_transactions_org_fan_ts created");
} catch (e) {
    print(`  ⚠ Index ix_transactions_org_fan_ts: ${e.message}`);
}

try {
    bi.sales_transactions.createIndex(
        { org_id: 1, item_type: 1, item_ref: 1, created_at: -1 },
        { name: "ix_transactions_org_item_ts", background: true }
    );
    print("  ✓ Index ix_transactions_org_item_ts created");
} catch (e) {
    print(`  ⚠ Index ix_transactions_org_item_ts: ${e.message}`);
}

// 4) Profils fans (agrégé/anonymisé)
try {
    bi.createCollection("fan_profiles");
    print("  ✓ Collection fan_profiles created");
} catch (e) {
    print(`  ⚠ fan_profiles: ${e.message}`);
}

try {
    bi.fan_profiles.createIndex(
        { org_id: 1, fan_id: 1 },
        { name: "ux_fan_profiles_org_fan", unique: true, background: true }
    );
    print("  ✓ Index ux_fan_profiles_org_fan created");
} catch (e) {
    print(`  ⚠ Index ux_fan_profiles_org_fan: ${e.message}`);
}

try {
    bi.fan_profiles.createIndex(
        { org_id: 1, segment: 1 },
        { name: "ix_fan_profiles_org_segment", background: true }
    );
    print("  ✓ Index ix_fan_profiles_org_segment created");
} catch (e) {
    print(`  ⚠ Index ix_fan_profiles_org_segment: ${e.message}`);
}

// 5) Alerts & insights IA
try {
    bi.createCollection("insights_alerts");
    print("  ✓ Collection insights_alerts created");
} catch (e) {
    print(`  ⚠ insights_alerts: ${e.message}`);
}

try {
    bi.insights_alerts.createIndex(
        { org_id: 1, muse_id: 1, created_at: -1 },
        { name: "ix_insights_org_muse_ts", background: true }
    );
    print("  ✓ Index ix_insights_org_muse_ts created");
} catch (e) {
    print(`  ⚠ Index ix_insights_org_muse_ts: ${e.message}`);
}

try {
    bi.insights_alerts.createIndex(
        { org_id: 1, type: 1, severity: 1, created_at: -1 },
        { name: "ix_insights_org_type_severity", background: true }
    );
    print("  ✓ Index ix_insights_org_type_severity created");
} catch (e) {
    print(`  ⚠ Index ix_insights_org_type_severity: ${e.message}`);
}

// 6) Recommandations de pricing
try {
    bi.createCollection("pricing_recommendations");
    print("  ✓ Collection pricing_recommendations created");
} catch (e) {
    print(`  ⚠ pricing_recommendations: ${e.message}`);
}

try {
    bi.pricing_recommendations.createIndex(
        { org_id: 1, muse_id: 1, generated_at: -1 },
        { name: "ix_pricing_org_muse_ts", background: true }
    );
    print("  ✓ Index ix_pricing_org_muse_ts created");
} catch (e) {
    print(`  ⚠ Index ix_pricing_org_muse_ts: ${e.message}`);
}

try {
    bi.pricing_recommendations.createIndex(
        { org_id: 1, item_type: 1, item_ref: 1, generated_at: -1 },
        { name: "ix_pricing_org_item_ts", background: true }
    );
    print("  ✓ Index ix_pricing_org_item_ts created");
} catch (e) {
    print(`  ⚠ Index ix_pricing_org_item_ts: ${e.message}`);
}

// 7) Registry des modèles IA (versionnés)
try {
    bi.createCollection("models_registry");
    print("  ✓ Collection models_registry created");
} catch (e) {
    print(`  ⚠ models_registry: ${e.message}`);
}

try {
    bi.models_registry.createIndex(
        { name: 1, version: 1 },
        { name: "ux_models_name_version", unique: true, background: true }
    );
    print("  ✓ Index ux_models_name_version created");
} catch (e) {
    print(`  ⚠ Index ux_models_name_version: ${e.message}`);
}

// 8) Vecteurs RAG (benchmarks, tendances marché)
try {
    bi.createCollection("knowledge_vectors");
    print("  ✓ Collection knowledge_vectors created");
} catch (e) {
    print(`  ⚠ knowledge_vectors: ${e.message}`);
}

try {
    bi.knowledge_vectors.createIndex(
        { org_id: 1, niche: 1, platform: 1, updated_at: -1 },
        { name: "ix_knowledge_vectors_org_niche", background: true }
    );
    print("  ✓ Index ix_knowledge_vectors_org_niche created");
} catch (e) {
    print(`  ⚠ Index ix_knowledge_vectors_org_niche: ${e.message}`);
}

// 9) Candidats collaboration (similarité audience/hashtags)
try {
    bi.createCollection("collab_candidates");
    print("  ✓ Collection collab_candidates created");
} catch (e) {
    print(`  ⚠ collab_candidates: ${e.message}`);
}

try {
    bi.collab_candidates.createIndex(
        { org_id: 1, muse_id: 1, similarity_score: -1 },
        { name: "ix_collab_org_muse_score", background: true }
    );
    print("  ✓ Index ix_collab_org_muse_score created");
} catch (e) {
    print(`  ⚠ Index ix_collab_org_muse_score: ${e.message}`);
}

try {
    bi.collab_candidates.createIndex(
        { org_id: 1, muse_id: 1, candidate_muse_id: 1 },
        { name: "ux_collab_org_muse_candidate", unique: true, background: true }
    );
    print("  ✓ Index ux_collab_org_muse_candidate created");
} catch (e) {
    print(`  ⚠ Index ux_collab_org_muse_candidate: ${e.message}`);
}

// 10) Jobs & logs BI
try {
    bi.createCollection("bi_jobs");
    print("  ✓ Collection bi_jobs created");
} catch (e) {
    print(`  ⚠ bi_jobs: ${e.message}`);
}

try {
    bi.bi_jobs.createIndex(
        { type: 1, state: 1, next_run_at: 1 },
        { name: "ix_bi_jobs_type_state", background: true }
    );
    print("  ✓ Index ix_bi_jobs_type_state created");
} catch (e) {
    print(`  ⚠ Index ix_bi_jobs_type_state: ${e.message}`);
}

try {
    bi.createCollection("bi_logs");
    print("  ✓ Collection bi_logs created");
} catch (e) {
    print(`  ⚠ bi_logs: ${e.message}`);
}

try {
    bi.bi_logs.createIndex(
        { org_id: 1, created_at: -1 },
        { name: "ix_bi_logs_org_ts", background: true }
    );
    print("  ✓ Index ix_bi_logs_org_ts created");
} catch (e) {
    print(`  ⚠ Index ix_bi_logs_org_ts: ${e.message}`);
}

print("\n✅ musai_bi — collections & indexes ready.");




