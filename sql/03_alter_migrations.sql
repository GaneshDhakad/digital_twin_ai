-- Digital Twin AI (TWIN.OS) - Backward Compatible Migration Script
-- Extends existing Integer-PK schema to 3NF UUID architecture safely

-- Step 1: Ensure pgcrypto extension for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Step 2: Add category_id FKs to domain tables if missing
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='financial_records' AND column_name='category_id') THEN
        ALTER TABLE financial_records ADD COLUMN category_id UUID REFERENCES expense_categories(category_id) ON DELETE SET NULL;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='study_activities' AND column_name='subject_id') THEN
        ALTER TABLE study_activities ADD COLUMN subject_id UUID REFERENCES subjects(subject_id) ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='habit_tracking' AND column_name='habit_type_id') THEN
        ALTER TABLE habit_tracking ADD COLUMN habit_type_id UUID REFERENCES habit_types(habit_type_id) ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='goals' AND column_name='category_id') THEN
        ALTER TABLE goals ADD COLUMN category_id UUID REFERENCES goal_categories(category_id) ON DELETE SET NULL;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='simulations' AND column_name='template_id') THEN
        ALTER TABLE simulations ADD COLUMN template_id UUID REFERENCES simulation_templates(template_id) ON DELETE SET NULL;
    END IF;
END $$;
