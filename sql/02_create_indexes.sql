-- Digital Twin AI (TWIN.OS) - Performance Indexing Script

-- B-Tree Indexes on Foreign Keys & High-Cardinality Queries
CREATE INDEX IF NOT EXISTS idx_fin_user_date ON financial_records(user_id, transaction_date DESC);
CREATE INDEX IF NOT EXISTS idx_fin_category ON financial_records(category_id);
CREATE INDEX IF NOT EXISTS idx_fin_type ON financial_records(type);

CREATE INDEX IF NOT EXISTS idx_study_user_date ON study_activities(user_id, activity_date DESC);
CREATE INDEX IF NOT EXISTS idx_study_subject ON study_activities(subject_id);

CREATE INDEX IF NOT EXISTS idx_habits_user_date ON habit_tracking(user_id, record_date DESC);
CREATE INDEX IF NOT EXISTS idx_habits_type ON habit_tracking(habit_type_id);

CREATE INDEX IF NOT EXISTS idx_fitness_user_date ON fitness_activities(user_id, activity_date DESC);
CREATE INDEX IF NOT EXISTS idx_fitness_type ON fitness_activities(activity_type);

CREATE INDEX IF NOT EXISTS idx_goals_user_status ON goals(user_id, status);
CREATE INDEX IF NOT EXISTS idx_goals_target_date ON goals(target_date);

CREATE INDEX IF NOT EXISTS idx_sim_user_date ON simulations(user_id, generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_sim_decision_type ON simulations(decision_type);

CREATE INDEX IF NOT EXISTS idx_rec_user_actioned ON recommendations(user_id, is_actioned);
CREATE INDEX IF NOT EXISTS idx_rec_priority ON recommendations(priority);

CREATE INDEX IF NOT EXISTS idx_analytics_user ON analytics_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON analytics_logs(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_notif_user_read ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_pred_cache_expires ON prediction_cache(user_id, expires_at);
CREATE INDEX IF NOT EXISTS idx_ai_conv_user_date ON ai_conversations(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(token_hash);

CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at DESC);

-- GIN Indexes for JSONB Deep Query Performance
CREATE INDEX IF NOT EXISTS idx_gin_sim_result ON simulations USING GIN (simulation_result);
CREATE INDEX IF NOT EXISTS idx_gin_sim_input ON simulations USING GIN (input_parameters);
CREATE INDEX IF NOT EXISTS idx_gin_rec_action_plan ON recommendations USING GIN (action_plan);
CREATE INDEX IF NOT EXISTS idx_gin_model_metrics ON model_registry USING GIN (metrics);
