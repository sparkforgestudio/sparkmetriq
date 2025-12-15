# 🚀 COMMANDES DE MIGRATION : `saasentialcore/products/` → `products/`

**Date**: 2024  
**Usage**: Copier-coller les commandes ci-dessous dans votre terminal

---

## 📋 COMMANDES PRÊTES À EXÉCUTER

### **Option 1 : Script automatique (recommandé)**

```bash
# Exécuter le script
chmod +x COMMANDES_MIGRATION_SAASENTIALCORE_PRODUCTS.sh
./COMMANDES_MIGRATION_SAASENTIALCORE_PRODUCTS.sh
```

---

### **Option 2 : Commandes manuelles (étape par étape)**

#### **Étape 1 : Prérequis**

```bash
# Créer le dossier products/ si nécessaire
test -d products || mkdir -p products
```

#### **Étape 2 : Déplacer Sparkmetriq**

```bash
git mv saasentialcore/products/sparkmetriq products/
```

#### **Étape 3 : Déplacer SparkPusher**

```bash
git mv saasentialcore/products/sparkpusher products/
```

#### **Étape 4 : Supprimer le dossier vide**

```bash
# Supprimer __init__.py si présent
rm saasentialcore/products/__init__.py

# Supprimer le dossier vide
rmdir saasentialcore/products
```

#### **Étape 5 : Corriger l'import dans le test**

```bash
# Sur Linux/Mac
sed -i 's/saasentialcore\.products\.sparkpusher/products.sparkpusher/g' products/sparkpusher/tests/test_s2_scheduler_sparkpusher.py

# Sur Windows PowerShell
# (Get-Content products/sparkpusher/tests/test_s2_scheduler_sparkpusher.py) -replace 'saasentialcore\.products\.sparkpusher', 'products.sparkpusher' | Set-Content products/sparkpusher/tests/test_s2_scheduler_sparkpusher.py
```

---

## ✅ VÉRIFICATIONS POST-MIGRATION

### **Vérification 1 : Dossier supprimé**

```bash
test -d saasentialcore/products && echo "❌ ERREUR: dossier encore présent" || echo "✅ OK: dossier supprimé"
```

### **Vérification 2 : Aucun import saasentialcore.products**

```bash
grep -r "saasentialcore\.products" --include="*.py" . || echo "✅ OK: plus de références saasentialcore.products"
```

### **Vérification 3 : Fichiers dans products/**

```bash
test -f products/sparkmetriq/api/routes/scheduler.py && echo "✅ Sparkmetriq OK" || echo "❌ Erreur"
test -f products/sparkpusher/api/routes/scheduler.py && echo "✅ SparkPusher OK" || echo "❌ Erreur"
test -f products/sparkpusher/tests/test_s2_scheduler_sparkpusher.py && echo "✅ Tests OK" || echo "❌ Erreur"
```

### **Vérification 4 : Imports Python**

```bash
python -c "from products.sparkmetriq.api.routes.scheduler import router; print('✅ Import Sparkmetriq OK')"
python -c "from products.sparkpusher.api.routes.scheduler import router; print('✅ Import SparkPusher OK')"
```

### **Vérification 5 : Tests**

```bash
pytest saasentialcore/tests/ -v
pytest products/sparkpusher/tests/test_s2_scheduler_sparkpusher.py -v
pytest tests/test_s2_e2e.py -v
```

---

## 📊 RÉSUMÉ

- **Commandes principales** : 2 `git mv` + 2 `rm` + 1 `sed`
- **Durée estimée** : 2-5 minutes
- **Risque** : ⚠️ **FAIBLE**

**STATUT**: ✅ **PRÊT POUR EXÉCUTION**

