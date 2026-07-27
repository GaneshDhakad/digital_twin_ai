# Digital Twin AI - System Architecture

## High-Level Architecture

```text
                    +----------------------+
                    |      Streamlit       |
                    |      Frontend        |
                    +----------+-----------+
                               |
                               | REST API
                               |
                    +----------v-----------+
                    |       FastAPI        |
                    |       Backend        |
                    +----------+-----------+
                               |
        +----------------------+----------------------+
        |                      |                      |
        |                      |                      |
+-------v-------+      +-------v-------+      +-------v-------+
| Authentication|      | Logic|               | Recommendation|
+---------------+      +---------------+      +---------------+
                               |
                    +----------v-----------+
                    |    SQLAlchemy ORM    |
                    +----------+-----------+
                               |
                    +----------v-----------+
                    |     PostgreSQL       |
                    +----------------------+

                               |
                    +----------v-----------+
                    | Machine Learning     |
                    |  - Prophet           |
                    |  - XGBoost           |
                    |  - Scikit-learn      |
                    |  - Digital Twin      |
                    +----------------------+

                               |
                    +----------v-----------+
                    |       Redis          |
                    |   Cache / Queue      |
                    +----------------------+
```

## Components

- **Frontend:** Streamlit dashboard for user interaction.
- **Backend:** FastAPI REST API handling authentication, business logic, and ML requests.
- **Database:** PostgreSQL for persistent storage.
- **ORM:** SQLAlchemy.
- **Cache & Tasks:** Redis (and Celery in later stages).
- **Machine Learning:** Forecasting, recommendations, and digital twin simulations.