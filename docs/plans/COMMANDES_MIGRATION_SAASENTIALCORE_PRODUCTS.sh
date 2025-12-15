#!/bin/bash
# 🚀 MIGRATION : saasentialcore/products/ → products/
# Script prêt à exécuter - Copier-coller les commandes ci-dessous

set -e  # Arrêter en cas d'erreur

echo "🚀 MIGRATION: saasentialcore/products/ → products/"
echo "================================================"
echo ""

# PRÉREQUIS : Créer la structure products/ si nécessaire
echo "📋 Phase 1: Vérification de la structure..."
test -d products || mkdir -p products
echo "   ✅ Dossier products/ prêt"
echo ""

# DÉPLACEMENT SPARKMETRIQ
echo "📦 Phase 2: Déplacement de Sparkmetriq..."
git mv saasentialcore/products/sparkmetriq products/
echo "   ✅ Sparkmetriq déplacé"
echo ""

# DÉPLACEMENT SPARKPUSHER
echo "📦 Phase 3: Déplacement de SparkPusher..."
git mv saasentialcore/products/sparkpusher products/
echo "   ✅ SparkPusher déplacé"
echo ""

# SUPPRESSION DU DOSSIER VIDE
echo "🗑️  Phase 4: Suppression du dossier vide..."
rm -f saasentialcore/products/__init__.py
rmdir saasentialcore/products 2>/dev/null || {
    echo "   ⚠️  Dossier non vide, contenu restant:"
    ls -la saasentialcore/products/ 2>/dev/null || true
    echo "   ⚠️  Suppression manuelle requise"
}
echo ""

# CORRECTION DE L'IMPORT DANS LE TEST
echo "🔧 Phase 5: Correction de l'import dans le test..."
if [ -f "products/sparkpusher/tests/test_s2_scheduler_sparkpusher.py" ]; then
    sed -i.bak 's/saasentialcore\.products\.sparkpusher/products.sparkpusher/g' products/sparkpusher/tests/test_s2_scheduler_sparkpusher.py
    rm -f products/sparkpusher/tests/test_s2_scheduler_sparkpusher.py.bak
    echo "   ✅ Import corrigé"
else
    echo "   ⚠️  Fichier test non trouvé (peut-être déjà déplacé)"
fi
echo ""

# VÉRIFICATIONS
echo "✅ Phase 6: Vérifications..."
echo ""

# Vérifier que le dossier n'existe plus
if [ -d "saasentialcore/products" ]; then
    echo "   ❌ ERREUR: Dossier saasentialcore/products/ encore présent"
    exit 1
else
    echo "   ✅ Dossier saasentialcore/products/ supprimé"
fi

# Vérifier qu'aucun import ne référence saasentialcore.products
if grep -r "saasentialcore\.products" --include="*.py" . > /dev/null 2>&1; then
    echo "   ⚠️  ATTENTION: Des imports saasentialcore.products restent"
    echo "   Fichiers concernés:"
    grep -r "saasentialcore\.products" --include="*.py" . | cut -d: -f1 | sort -u
else
    echo "   ✅ Aucun import saasentialcore.products restant dans le code Python"
fi

# Vérifier que les fichiers sont bien dans products/
if [ -f "products/sparkmetriq/api/routes/scheduler.py" ] && \
   [ -f "products/sparkpusher/api/routes/scheduler.py" ]; then
    echo "   ✅ Fichiers dans products/ OK"
else
    echo "   ❌ ERREUR: Fichiers manquants dans products/"
    exit 1
fi

echo ""
echo "🎉 MIGRATION TERMINÉE AVEC SUCCÈS"
echo ""
echo "📝 Prochaines étapes:"
echo "   1. Vérifier les changements: git status"
echo "   2. Tester les imports:"
echo "      python -c 'from products.sparkmetriq.api.routes.scheduler import router'"
echo "      python -c 'from products.sparkpusher.api.routes.scheduler import router'"
echo "   3. Relancer les tests:"
echo "      pytest saasentialcore/tests/ -v"
echo "      pytest products/sparkpusher/tests/test_s2_scheduler_sparkpusher.py -v"
echo "      pytest tests/test_s2_e2e.py -v"
echo "   4. Commit:"
echo "      git commit -m 'feat: déplacer saasentialcore/products/ vers products/ à la racine'"

