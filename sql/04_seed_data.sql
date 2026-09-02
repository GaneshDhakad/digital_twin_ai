-- Digital Twin AI (TWIN.OS) - Lookup Reference Table Seed Data

INSERT INTO expense_categories (name, type, is_essential, description) VALUES
('Housing & Rent', 'expense', TRUE, 'Monthly mortgage, rent, and property taxes'),
('Utilities', 'expense', TRUE, 'Electricity, water, gas, and internet service'),
('Groceries & Food', 'expense', TRUE, 'Supermarket food and daily essential sustenance'),
('Transport & Fuel', 'expense', TRUE, 'Public transit, gasoline, vehicle maintenance'),
('Education & Courses', 'expense', FALSE, 'Tuition fees, textbooks, online certifications'),
('Dining Out & Leisure', 'expense', FALSE, 'Restaurants, entertainment, and social activities'),
('Salary & Wages', 'income', TRUE, 'Primary professional employment income'),
('Investments & Dividends', 'income', FALSE, 'Capital gains, dividends, and asset returns')
ON CONFLICT (name) DO NOTHING;

INSERT INTO subjects (name, code, category, description) VALUES
('Data Structures & Algorithms', 'CS201', 'Computer Science', 'Core computational logic and problem solving'),
('Database Management Systems', 'CS302', 'Computer Science', 'SQL, relational algebra, and data architecture'),
('Machine Learning Engineering', 'AI401', 'Artificial Intelligence', 'Supervised learning, deep neural nets, MLOps'),
('Calculus & Linear Algebra', 'MATH101', 'Mathematics', 'Continuous mathematics and vector matrices'),
('System Design & Architecture', 'CS405', 'Software Engineering', 'Distributed systems, microservices, and databases')
ON CONFLICT (name) DO NOTHING;

INSERT INTO habit_types (name, category, default_impact, description) VALUES
('Daily Deep Work (2+ hrs)', 'Cognitive', 'high', 'Uninterrupted focused analytical sessions'),
('Morning Exercise / Cardio', 'Health', 'high', 'Physical aerobic or strength conditioning'),
('Reading / Skill Acquisition', 'Personal Growth', 'medium', 'Continuous learning and reading literature'),
('Meditation & Mindfulness', 'Mental Health', 'medium', 'Stress reduction and focus cultivation')
ON CONFLICT (name) DO NOTHING;

INSERT INTO goal_categories (name, description, icon) VALUES
('Financial Independence', 'Net worth building, savings buffers, emergency funds', 'bank-line'),
('Academic Excellence', 'GPA targets, course completion, research publication', 'book-open-line'),
('Physical Health', 'Weight targets, muscle gain, marathon running', 'heart-pulse-line'),
('Career Progression', 'Promotions, salary increments, skill certifications', 'briefcase-line')
ON CONFLICT (name) DO NOTHING;

INSERT INTO simulation_templates (name, category, description, default_parameters) VALUES
('Higher Education / Grad School ROI', 'Academic', 'Models lost income vs long-term salary growth of higher degrees.', '{"tuition_cost": 40000, "duration_years": 2, "expected_post_salary": 95000}'::jsonb),
('Emergency Fund Resilience', 'Financial', 'Stress-tests liquid savings against sudden job loss or medical events.', '{"monthly_burn": 3500, "current_savings": 20000}'::jsonb),
('Career Pivot vs Promotion', 'Career', 'Simulates risk-adjusted trajectory of switching industries vs staying.', '{"current_salary": 70000, "pivot_starting_salary": 85000}'::jsonb)
ON CONFLICT (name) DO NOTHING;
