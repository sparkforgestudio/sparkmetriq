// scripts/intent_engine_setup.mjs
// Script MongoDB pour créer les collections et index du Moteur d'Intentions
// Usage: mongosh mongodb://localhost:27017 scripts/intent_engine_setup.mjs

const core = connect("mongodb://localhost:27017/musai_core");

print("Setting up Intent Engine collections...");

// ===== Collections core =====
try {
    core.createCollection("chat_scenarios");
    print("  ✓ Collection chat_scenarios created");
} catch (e) {
    print(`  ⚠ chat_scenarios: ${e.message}`);
}

try {
    core.createCollection("chat_sessions");
    print("  ✓ Collection chat_sessions created");
} catch (e) {
    print(`  ⚠ chat_sessions: ${e.message}`);
}

try {
    core.createCollection("persona_profiles");
    print("  ✓ Collection persona_profiles created");
} catch (e) {
    print(`  ⚠ persona_profiles: ${e.message}`);
}

try {
    core.createCollection("knowledge_chunks");
    print("  ✓ Collection knowledge_chunks created");
} catch (e) {
    print(`  ⚠ knowledge_chunks: ${e.message}`);
}

try {
    core.createCollection("chat_policies");
    print("  ✓ Collection chat_policies created");
} catch (e) {
    print(`  ⚠ chat_policies: ${e.message}`);
}

try {
    core.createCollection("conversation_overrides");
    print("  ✓ Collection conversation_overrides created");
} catch (e) {
    print(`  ⚠ conversation_overrides: ${e.message}`);
}

// ===== Indexes =====
print("\nCreating indexes...");

// chat_scenarios
try {
    core.chat_scenarios.createIndex(
        { org_id: 1, muse_id: 1, is_active: 1, version: 1 },
        { name: "ix_scenarios_org_muse_active", background: true }
    );
    print("  ✓ Index ix_scenarios_org_muse_active created");
} catch (e) {
    print(`  ⚠ Index ix_scenarios_org_muse_active: ${e.message}`);
}

try {
    core.chat_scenarios.createIndex(
        { org_id: 1, muse_id: 1, "trigger.type": 1, platforms: 1 },
        { name: "ix_scenarios_trigger", background: true }
    );
    print("  ✓ Index ix_scenarios_trigger created");
} catch (e) {
    print(`  ⚠ Index ix_scenarios_trigger: ${e.message}`);
}

// chat_sessions
try {
    core.chat_sessions.createIndex(
        { org_id: 1, muse_id: 1, conversation_id: 1, status: 1 },
        { name: "ix_sessions_org_muse_conv", background: true }
    );
    print("  ✓ Index ix_sessions_org_muse_conv created");
} catch (e) {
    print(`  ⚠ Index ix_sessions_org_muse_conv: ${e.message}`);
}

// persona_profiles
try {
    core.persona_profiles.createIndex(
        { org_id: 1, muse_id: 1 },
        { name: "ux_persona_org_muse", unique: true, background: true }
    );
    print("  ✓ Index ux_persona_org_muse created");
} catch (e) {
    print(`  ⚠ Index ux_persona_org_muse: ${e.message}`);
}

// knowledge_chunks
try {
    core.knowledge_chunks.createIndex(
        { org_id: 1, muse_id: 1, kind: 1, ts: -1 },
        { name: "ix_knowledge_org_muse_kind", background: true }
    );
    print("  ✓ Index ix_knowledge_org_muse_kind created");
} catch (e) {
    print(`  ⚠ Index ix_knowledge_org_muse_kind: ${e.message}`);
}

// chat_policies
try {
    core.chat_policies.createIndex(
        { org_id: 1, muse_id: 1 },
        { name: "ux_policies_org_muse", unique: true, background: true }
    );
    print("  ✓ Index ux_policies_org_muse created");
} catch (e) {
    print(`  ⚠ Index ux_policies_org_muse: ${e.message}`);
}

// conversation_overrides
try {
    core.conversation_overrides.createIndex(
        { org_id: 1, muse_id: 1, conversation_id: 1 },
        { name: "ux_overrides_org_muse_conv", unique: true, background: true }
    );
    print("  ✓ Index ux_overrides_org_muse_conv created");
} catch (e) {
    print(`  ⚠ Index ux_overrides_org_muse_conv: ${e.message}`);
}

// ===== Seeds minimal (optional) =====
print("\nSeeding minimal demo policies...");

try {
    core.chat_policies.updateOne(
        { org_id: "org_demo", muse_id: "muse_demo" },
        {
            $set: {
                org_id: "org_demo",
                muse_id: "muse_demo",
                ppv_rules: { max_per_day: 3, cooldown_minutes: 120 },
                compliance: { forbidden_words: ["minor", "illegal"], nsfw_level: "soft" },
                latency_profiles: { default: { typing: true, min_ms: 800, max_ms: 2500 } }
            }
        },
        { upsert: true }
    );
    print("  ✓ Demo policy seeded");
} catch (e) {
    print(`  ⚠ Seed demo policy: ${e.message}`);
}

print("\n✅ Intent Engine collections & indexes ready.");



