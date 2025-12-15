# ✅ CHECKLIST : RÉORGANISATION DE LA RACINE

**Date**: 2024  
**Objectif**: Nettoyer et organiser la racine du projet

---

## 📋 CHECKLIST D'EXÉCUTION

### **Phase 1 : Préparation**

- [ ] Créer un commit de sauvegarde : `git commit -am "Checkpoint avant réorganisation racine"`
- [ ] Créer une branche : `git checkout -b cleanup/reorganize-root`

### **Phase 2 : Créer les sous-dossiers**

- [ ] `mkdir -p docs/integrations`
- [ ] `mkdir -p docs/migration`
- [ ] `mkdir -p docs/audits`
- [ ] `mkdir -p database`

### **Phase 3 : Déplacer la documentation générale**

- [ ] `git mv STRUCTURE.md docs/`
- [ ] `git mv AI_MARKETING_MODULE.md docs/`
- [ ] `git mv ARCHITECTURE_CONFORMITE.md docs/`
- [ ] `git mv ARCHITECTURE_MODULES_MAP.md docs/`
- [ ] `git mv CLASSIFICATION_MODULES.md docs/`
- [ ] `git mv DOCKER.md docs/`
- [ ] `git mv IMPLEMENTATION_FEATURE_FLAGS.md docs/`
- [ ] `git mv SCHEMA_ARCHITECTURE.md docs/`
- [ ] `git mv LISTE_RACINE.md docs/`

### **Phase 4 : Déplacer la documentation intégrations**

- [ ] `git mv MANYVIDS_INTEGRATION.md docs/integrations/`
- [ ] `git mv MYMFANS_INTEGRATION.md docs/integrations/`
- [ ] `git mv NEW_PLATFORMS_SUMMARY.md docs/integrations/`
- [ ] `git mv PLATFORMS_INTEGRATION.md docs/integrations/`
- [ ] `git mv README_GOOGLE_OAUTH.md docs/integrations/`

### **Phase 5 : Déplacer les plans et rapports de migration**

- [ ] `git mv PLAN_EXTRACTION_S2_SPARKPUSHER.md docs/migration/`
- [ ] `git mv PLAN_ERADICATION_SAASENTIALCORE_PRODUCTS.md docs/migration/`
- [ ] `git mv PLAN_REFACTOR_SCHEDULER.md docs/migration/`
- [ ] `git mv RAPPORT_MIGRATION_FINALE.md docs/migration/`
- [ ] `git mv RESUME_MIGRATION_SAASENTIALCORE_PRODUCTS.md docs/migration/`

### **Phase 6 : Déplacer les rapports d'audit**

- [ ] `git mv RAPPORT_AUDIT_FINAL.md docs/audits/`
- [ ] `git mv RAPPORT_AUDIT_SCHEDULER_FINAL.md docs/audits/`
- [ ] `git mv AUDIT_ARCHITECTURE_STRICT.md docs/audits/`
- [ ] `git mv AUDIT_ARCHITECTURE.md docs/audits/`
- [ ] `git mv AUDIT_API_SHIMS.md docs/audits/`
- [ ] `git mv AUDIT_SCHEDULER_CORE_VS_PRODUITS.md docs/audits/`

### **Phase 7 : Déplacer les scripts**

- [ ] `git mv ingestion_pipeline.py scripts/`
- [ ] `git mv setup_project.py scripts/`
- [ ] `git mv launch_all.sh scripts/`
- [ ] `git mv launch_all.bat scripts/`
- [ ] `git mv prepare_env.sh scripts/`
- [ ] `git mv prepare_env.bat scripts/`
- [ ] `git mv install_musai_scheduler.sh scripts/`

### **Phase 8 : Déplacer autres fichiers**

- [ ] `git mv mongo_schema.js database/`
- [ ] `git mv chat_tests tests/chat_tests`

### **Phase 9 : Supprimer éléments suspects**

- [ ] `rm -rf "-p"` (ou `Remove-Item -Recurse -Force "-p"` sur Windows)

### **Phase 10 : Vérification**

- [ ] Vérifier que les dossiers docs/ sont créés : `ls docs/integrations docs/migration docs/audits`
- [ ] Vérifier que les scripts sont déplacés : `ls scripts/launch_all.* scripts/prepare_env.*`
- [ ] Vérifier que mongo_schema.js est déplacé : `ls database/mongo_schema.js`
- [ ] Vérifier que chat_tests est déplacé : `ls tests/chat_tests`
- [ ] Vérifier que -p/ est supprimé : `test -d "-p" && echo "ERREUR" || echo "OK"`

### **Phase 11 : Mise à jour documentation**

- [ ] Mettre à jour `README.md` avec les nouveaux chemins des scripts
- [ ] Vérifier que tous les liens dans la documentation fonctionnent

### **Phase 12 : Commit final**

- [ ] `git add -A`
- [ ] `git commit -m "refactor: réorganiser fichiers racine - déplacer docs vers docs/, scripts vers scripts/"`
- [ ] `git push origin cleanup/reorganize-root`

---

## 📊 RÉSUMÉ

**Total actions** : 38 déplacements + 1 suppression  
**Durée estimée** : 10-15 minutes  
**Risque** : ⚠️ **FAIBLE** (déplacements git mv, pas de modification de contenu)

---

**STATUT**: ⏳ **PRÊT POUR EXÉCUTION**

