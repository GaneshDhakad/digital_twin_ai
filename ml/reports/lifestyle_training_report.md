# Lifestyle Model Training Report

## Model
- Best model: `GradientBoostingClassifier`
- Target: `sleep_disorder`
- Classes: `Normal`, `Insomnia`, `Sleep Apnea`
- Dataset: `lifestyle_clean.csv`
- Rows: `374`
- Version: `2.0`

## Validation
- Split: stratified 80/20 hold-out
- Cross-validation: 5-fold StratifiedKFold
- Primary model-selection metric: Macro F1

## Cross-validation
- Accuracy: 0.9766
- Precision Macro: 0.9734
- Recall Macro: 0.9618
- F1 Macro: 0.9646

## Held-out Test
- Accuracy: 0.9733
- Precision Macro: 0.9852
- Recall Macro: 0.9710
- F1 Macro: 0.9773

## Classes
sleep_disorder
Normal         213
Sleep Apnea    117
Insomnia        44

## Features
- age
- sleep_hours
- sleep_quality
- physical_activity_level
- stress_level
- heart_rate
- daily_steps
- activity_sleep_balance
- lifestyle_risk_score
- gender
- occupation
- bmi_category
- blood_pressure

## Deployment
- Model: `C:\Users\gkdha\OneDrive\Desktop\INFO_PROJECT\digital_twin_ai\backend\app\ml_models\lifestyle\model.joblib`
- Metadata: `C:\Users\gkdha\OneDrive\Desktop\INFO_PROJECT\digital_twin_ai\backend\app\ml_models\lifestyle\metadata.json`
- Feature info: `C:\Users\gkdha\OneDrive\Desktop\INFO_PROJECT\digital_twin_ai\backend\app\ml_models\lifestyle\feature_info.json`
- Registry: `C:\Users\gkdha\OneDrive\Desktop\INFO_PROJECT\digital_twin_ai\backend\app\ml_models\model_registry.json`

## Important
The target labels were generated from the project's supplied reference
ranges for Normal, Insomnia and Sleep Apnea. They are not clinical diagnoses.
