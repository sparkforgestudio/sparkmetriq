// scripts/calendar_setup.mjs
// Script MongoDB pour créer les collections et index du calendrier
// Usage: mongosh mongodb://localhost:27017 scripts/calendar_setup.mjs

const core = connect("mongodb://localhost:27017/musai_core");

print("Setting up Calendar collections...");

// ===== Collections =====
try {
    core.createCollection("scheduled_posts");
    print("  ✓ Collection scheduled_posts created");
} catch (e) {
    print(`  ⚠ scheduled_posts: ${e.message}`);
}

try {
    core.createCollection("publishing_jobs");
    print("  ✓ Collection publishing_jobs created");
} catch (e) {
    print(`  ⚠ publishing_jobs: ${e.message}`);
}

try {
    core.createCollection("content_assets");
    print("  ✓ Collection content_assets created");
} catch (e) {
    print(`  ⚠ content_assets: ${e.message}`);
}

try {
    core.createCollection("categories");
    print("  ✓ Collection categories created");
} catch (e) {
    print(`  ⚠ categories: ${e.message}`);
}

// ===== Indexes =====
print("\nCreating indexes...");

// scheduled_posts
try {
    core.scheduled_posts.createIndex(
        { org_id: 1, muse_id: 1, "schedule.start_at_utc": 1 },
        { name: "ix_scheduled_org_muse_start", background: true }
    );
    print("  ✓ Index ix_scheduled_org_muse_start created");
} catch (e) {
    print(`  ⚠ Index ix_scheduled_org_muse_start: ${e.message}`);
}

try {
    core.scheduled_posts.createIndex(
        { org_id: 1, platform: 1, status: 1, "schedule.start_at_utc": 1 },
        { name: "ix_scheduled_org_platform_status", background: true }
    );
    print("  ✓ Index ix_scheduled_org_platform_status created");
} catch (e) {
    print(`  ⚠ Index ix_scheduled_org_platform_status: ${e.message}`);
}

try {
    core.scheduled_posts.createIndex(
        { org_id: 1, labels: 1 },
        { name: "ix_scheduled_org_labels", background: true }
    );
    print("  ✓ Index ix_scheduled_org_labels created");
} catch (e) {
    print(`  ⚠ Index ix_scheduled_org_labels: ${e.message}`);
}

// publishing_jobs
try {
    core.publishing_jobs.createIndex(
        { org_id: 1, scheduled_post_id: 1, state: 1, next_retry_at_utc: 1 },
        { name: "ix_publishing_org_post_state", background: true }
    );
    print("  ✓ Index ix_publishing_org_post_state created");
} catch (e) {
    print(`  ⚠ Index ix_publishing_org_post_state: ${e.message}`);
}

// content_assets
try {
    core.content_assets.createIndex(
        { org_id: 1, muse_id: 1, type: 1 },
        { name: "ix_assets_org_muse_type", background: true }
    );
    print("  ✓ Index ix_assets_org_muse_type created");
} catch (e) {
    print(`  ⚠ Index ix_assets_org_muse_type: ${e.message}`);
}

// categories
try {
    core.categories.createIndex(
        { org_id: 1, name: 1 },
        { name: "ux_categories_org_name", unique: true, background: true }
    );
    print("  ✓ Index ux_categories_org_name created");
} catch (e) {
    print(`  ⚠ Index ux_categories_org_name: ${e.message}`);
}

print("\n✅ Calendar collections & indexes ready.");



