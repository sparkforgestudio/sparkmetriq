# SparkMetrIQ AI Management Platform
## Feature Flags (modules activables)

| Flag               | Description                              | Par défaut |
|--------------------|------------------------------------------|------------|
| ENABLE_BI          | Routes /api/bi (insights, pricing)       | true       |
| ENABLE_SCHEDULER   | Scheduler & connecteurs publication      | true       |
| ENABLE_CLOUDPHONE  | Cloud Phone & OTP                        | false      |
| ENABLE_OTP         | OTP Manager (réservation, parsing)       | false      |

**.env exemple**
ENABLE_BI=true
ENABLE_SCHEDULER=true
ENABLE_CLOUDPHONE=false
ENABLE_OTP=false

## Tests

### Tests unitaires (saasentialcore)
```bash
pytest saasentialcore/tests -q
```

### Tests E2E (opt-in)
Les tests end-to-end sont désactivés par défaut pour ne pas bloquer les refactorings.
Pour les exécuter, définir la variable d'environnement `RUN_E2E=1` :

```bash
RUN_E2E=1 pytest tests/test_s2_e2e.py -q
```