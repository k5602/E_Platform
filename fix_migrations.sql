-- Delete the conflicting migrations from the Django migration history
DELETE FROM django_migrations WHERE app = 'home' AND name = '0006_question_remove_education_user_and_more';
DELETE FROM django_migrations WHERE app = 'home' AND name = '0007_remove_quiz_home_quiz_creator_c34a82_idx_and_more';
DELETE FROM django_migrations WHERE app = 'home' AND name = '0008_merge_20250430_0543';

-- Rename our fixed migrations to match the original names
UPDATE django_migrations 
SET name = '0006_question_remove_education_user_and_more' 
WHERE app = 'home' AND name = '0006_question_remove_education_user_and_more_fixed';

UPDATE django_migrations 
SET name = '0007_remove_quiz_home_quiz_creator_c34a82_idx_and_more' 
WHERE app = 'home' AND name = '0007_remove_quiz_home_quiz_creator_c34a82_idx_and_more_fixed';
