-- Digital Twin AI (TWIN.OS) - Production DDL Script (22 Tables)
-- Target RDBMS: PostgreSQL 15+
-- Extensions Required: pgcrypto / uuid-ossp

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================
-- 1. REFERENCE LOOKUP TABLES
-- ==========================================

CREATE TABLE IF NOT EXISTS expense_categories (
    category_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    type VARCHAR(20) NOT NULL DEFAULT 'expense' CHECK (type IN ('income', 'expense', 'investment', 'savings')),
    is_essential BOOLEAN NOT NULL DEFAULT TRUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subjects (
    subject_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    code VARCHAR(20) UNIQUE,
    description TEXT,
    category VARCHAR(50) DEFAULT 'General',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS habit_types (
    habit_type_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL DEFAULT 'Health',
    default_impact VARCHAR(10) DEFAULT 'medium' CHECK (default_impact IN ('low', 'medium', 'high', 'critical')),
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS goal_categories (
    category_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS simulation_templates (
    template_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(150) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT,
    default_parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- 2. CORE USERS TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    age INT CHECK (age >= 0 AND age <= 120),
    occupation VARCHAR(100),
    role VARCHAR(20) NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin', 'analyst')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- 3. CORE DOMAIN TABLES
-- ==========================================

CREATE TABLE IF NOT EXISTS financial_records (
    record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    category_id UUID REFERENCES expense_categories(category_id) ON DELETE SET NULL,
    type VARCHAR(20) NOT NULL DEFAULT 'expense' CHECK (type IN ('income', 'expense', 'transfer', 'investment')),
    amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00 CHECK (amount >= 0),
    income NUMERIC(12, 2) NOT NULL DEFAULT 0.00 CHECK (income >= 0),
    expenses NUMERIC(12, 2) NOT NULL DEFAULT 0.00 CHECK (expenses >= 0),
    savings NUMERIC(12, 2) NOT NULL DEFAULT 0.00 CHECK (savings >= 0),
    transaction_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    recurring_frequency VARCHAR(20) NOT NULL DEFAULT 'none' CHECK (recurring_frequency IN ('none', 'daily', 'weekly', 'monthly', 'annual')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS study_activities (
    activity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(subject_id) ON DELETE SET NULL,
    study_hours NUMERIC(4, 2) NOT NULL CHECK (study_hours >= 0 AND study_hours <= 24),
    performance_score NUMERIC(5, 2) DEFAULT 80.00 CHECK (performance_score >= 0 AND performance_score <= 100),
    task_completion_rate NUMERIC(5, 2) NOT NULL DEFAULT 100.00 CHECK (task_completion_rate >= 0 AND task_completion_rate <= 100),
    notes TEXT,
    activity_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS habit_tracking (
    habit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    habit_type_id UUID REFERENCES habit_types(habit_type_id) ON DELETE SET NULL,
    habit_name VARCHAR(150) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'completed' CHECK (status IN ('completed', 'missed', 'partial', 'skipped')),
    completion_rate NUMERIC(5, 2) NOT NULL DEFAULT 100.00 CHECK (completion_rate >= 0 AND completion_rate <= 100),
    streak_count INT NOT NULL DEFAULT 0 CHECK (streak_count >= 0),
    impact_level VARCHAR(10) NOT NULL DEFAULT 'medium' CHECK (impact_level IN ('low', 'medium', 'high', 'critical')),
    record_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fitness_activities (
    fitness_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    activity_type VARCHAR(100) NOT NULL,
    duration_minutes NUMERIC(6, 2) NOT NULL CHECK (duration_minutes >= 0),
    calories_burned NUMERIC(7, 2) NOT NULL DEFAULT 0.00 CHECK (calories_burned >= 0),
    intensity_level VARCHAR(20) DEFAULT 'moderate' CHECK (intensity_level IN ('low', 'moderate', 'high', 'extreme')),
    activity_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS goals (
    goal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    category_id UUID REFERENCES goal_categories(category_id) ON DELETE SET NULL,
    goal_name VARCHAR(200) NOT NULL,
    target_value NUMERIC(12, 2) NOT NULL CHECK (target_value > 0),
    current_progress NUMERIC(12, 2) NOT NULL DEFAULT 0.00 CHECK (current_progress >= 0),
    target_date TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'on_track' CHECK (status IN ('on_track', 'at_risk', 'completed', 'abandoned', 'behind')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS simulations (
    simulation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    template_id UUID REFERENCES simulation_templates(template_id) ON DELETE SET NULL,
    decision_type VARCHAR(100) NOT NULL,
    scenario_name VARCHAR(150) NOT NULL,
    input_parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    simulation_result JSONB NOT NULL DEFAULT '{}'::jsonb,
    predicted_outcome TEXT,
    confidence_score NUMERIC(4, 3) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    generated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    recommendation_text TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    priority VARCHAR(10) NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    confidence_score NUMERIC(4, 3) NOT NULL DEFAULT 0.850 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    action_plan JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_actioned BOOLEAN NOT NULL DEFAULT FALSE,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytics_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    activity_type VARCHAR(100) NOT NULL,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    response_time_ms NUMERIC(10, 2),
    status_code INT,
    metadata_json JSONB DEFAULT '{}'::jsonb,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- 4. SUPPORTING & APPLICATION TABLES
-- ==========================================

CREATE TABLE IF NOT EXISTS user_settings (
    setting_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    theme VARCHAR(20) NOT NULL DEFAULT 'light' CHECK (theme IN ('light', 'dark', 'system')),
    notifications_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    email_alerts BOOLEAN NOT NULL DEFAULT TRUE,
    ai_personality VARCHAR(50) NOT NULL DEFAULT 'analytical' CHECK (ai_personality IN ('analytical', 'encouraging', 'direct', 'socratic')),
    risk_tolerance VARCHAR(20) NOT NULL DEFAULT 'moderate' CHECK (risk_tolerance IN ('conservative', 'moderate', 'aggressive')),
    custom_preferences JSONB DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notifications (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) NOT NULL DEFAULT 'info' CHECK (type IN ('info', 'warning', 'alert', 'achievement', 'recommendation')),
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS prediction_cache (
    cache_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    cache_key VARCHAR(255) NOT NULL UNIQUE,
    model_name VARCHAR(100) NOT NULL,
    prediction_data JSONB NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_conversations (
    conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    prompt TEXT NOT NULL,
    response TEXT NOT NULL,
    context_domain VARCHAR(50) DEFAULT 'general',
    tokens_used INT DEFAULT 0 CHECK (tokens_used >= 0),
    feedback_score INT CHECK (feedback_score >= 1 AND feedback_score <= 5),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- 5. SECURITY & COMPLIANCE TABLES
-- ==========================================

CREATE TABLE IF NOT EXISTS user_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    is_valid BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    record_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feedback (
    feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    feedback_type VARCHAR(50) NOT NULL DEFAULT 'general' CHECK (feedback_type IN ('bug', 'feature_request', 'simulation_accuracy', 'recommendation_quality', 'general')),
    rating INT CHECK (rating >= 1 AND rating <= 5),
    comments TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'reviewed', 'resolved', 'dismissed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- 6. MACHINE LEARNING ROADMAP TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS model_registry (
    model_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(100) NOT NULL,
    algorithm VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    domain VARCHAR(50) NOT NULL DEFAULT 'finance',
    metrics JSONB DEFAULT '{}'::jsonb,
    feature_importances JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    trained_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
