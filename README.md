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