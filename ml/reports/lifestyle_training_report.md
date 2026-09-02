# Lifestyle Model Training Report

- **Dataset**: lifestyle_clean.csv
- **Target**: sleep_disorder
- **Problem Type**: classification
- **Split Strategy**: 80/20 train/test split. Stratified if classification.
- **Leakage Checks**: Removed identified leaky/id columns.
- **Candidate Models**: LogisticRegression, DecisionTreeClassifier, RandomForestClassifier, ExtraTreesClassifier, GradientBoostingClassifier, SVC
- **Best Model**: LogisticRegression
- **Final Test Score (F1)**: 0.9111
- **Saved Model Path**: backend/app/ml_models\lifestyle\model.joblib
