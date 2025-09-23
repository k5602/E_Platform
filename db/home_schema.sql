--
-- Create model Contact
--
CREATE TABLE "home_contact" (
    "id" SERIAL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL,
    "email" VARCHAR(254) NOT NULL,
    "subject" VARCHAR(200) NOT NULL,
    "message" TEXT NOT NULL,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
-- Add index for email for faster lookup if often queried
CREATE INDEX "home_contact_email_idx" ON "home_contact" ("email");


--
-- Create model FAQ
--
CREATE TABLE "home_faq" (
    "id" SERIAL PRIMARY KEY,
    "question" VARCHAR(255) NOT NULL,
    "answer" TEXT NOT NULL,
    "category" VARCHAR(100) NOT NULL,
    "order" INTEGER NOT NULL,
    "is_active" BOOLEAN NOT NULL DEFAULT TRUE, -- Add default
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
-- Add indexes for category and order, and is_active for common queries
CREATE INDEX "home_faq_category_idx" ON "home_faq" ("category");
CREATE INDEX "home_faq_order_idx" ON "home_faq" ("order");
CREATE INDEX "home_faq_is_active_idx" ON "home_faq" ("is_active");


--
-- Create model Question (Initial version, will be altered later)
--
CREATE TABLE "home_question" (
    "id" BIGSERIAL PRIMARY KEY,
    "text" TEXT NOT NULL,
    "question_type" VARCHAR(20) NOT NULL,
    "explanation" TEXT NOT NULL,
    "marks" INTEGER NOT NULL CHECK ("marks" >= 0), -- Removed "unsigned"
    "order" INTEGER NOT NULL CHECK ("order" >= 0),   -- Removed "unsigned"
    "image" VARCHAR(100) NULL,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
-- Indexes for common question queries
CREATE INDEX "home_question_question_type_idx" ON "home_question" ("question_type");
CREATE INDEX "home_question_order_idx" ON "home_question" ("order");


--
-- Create model Appointment
--
CREATE TABLE "home_appointment" (
    "id" SERIAL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL,
    "email" VARCHAR(254) NOT NULL,
    "phone" VARCHAR(20) NOT NULL,
    "appointment_date" DATE NOT NULL,
    "appointment_time" TIME NOT NULL,
    "appointment_type" VARCHAR(50) NOT NULL,
    "message" TEXT NOT NULL,
    "status" VARCHAR(20) NOT NULL DEFAULT 'pending', -- Add default
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "instructor_id" BIGINT NULL REFERENCES "authentication_customuser" ("id") ON DELETE SET NULL, -- Use ON DELETE SET NULL
    "user_id" BIGINT NULL REFERENCES "authentication_customuser" ("id") ON DELETE SET NULL -- Use ON DELETE SET NULL
);
CREATE INDEX "home_appointment_instructor_id_a96f56f9" ON "home_appointment" ("instructor_id");
CREATE INDEX "home_appointment_user_id_0cd8b1ec" ON "home_appointment" ("user_id");
CREATE INDEX "home_appointment_date_time_idx" ON "home_appointment" ("appointment_date", "appointment_time"); -- Composite for common query
CREATE INDEX "home_appointment_status_idx" ON "home_appointment" ("status");


--
-- Create model Post
--
CREATE TABLE "home_post" (
    "id" BIGSERIAL PRIMARY KEY,
    "content" TEXT NOT NULL,
    "image" VARCHAR(100) NULL,
    "video" VARCHAR(100) NULL,
    "document" VARCHAR(100) NULL,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "user_id" BIGINT NOT NULL REFERENCES "authentication_customuser" ("id") ON DELETE CASCADE -- Use ON DELETE CASCADE
);
CREATE INDEX "home_post_user_id_4e975327" ON "home_post" ("user_id");
CREATE INDEX "home_post_created_at_idx" ON "home_post" ("created_at" DESC); -- For fetching recent posts


--
-- Create model Comment (initial, will be altered)
--
CREATE TABLE "home_comment" (
    "id" BIGSERIAL PRIMARY KEY,
    "content" TEXT NOT NULL,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "user_id" BIGINT NOT NULL REFERENCES "authentication_customuser" ("id") ON DELETE CASCADE -- Use ON DELETE CASCADE
);
CREATE INDEX "home_comment_user_id_842649c8" ON "home_comment" ("user_id");


--
-- Create model Notification
--
CREATE TABLE "home_notification" (
    "id" BIGSERIAL PRIMARY KEY,
    "notification_type" VARCHAR(20) NOT NULL,
    "text" TEXT NOT NULL,
    "is_read" BOOLEAN NOT NULL DEFAULT FALSE, -- Add default
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "comment_id" BIGINT NULL REFERENCES "home_comment" ("id") ON DELETE SET NULL, -- Use ON DELETE SET NULL
    "recipient_id" BIGINT NOT NULL REFERENCES "authentication_customuser" ("id") ON DELETE CASCADE, -- Use ON DELETE CASCADE
    "sender_id" BIGINT NOT NULL REFERENCES "authentication_customuser" ("id") ON DELETE SET NULL, -- Use ON DELETE SET NULL (sender might be deleted)
    "post_id" BIGINT NULL REFERENCES "home_post" ("id") ON DELETE SET NULL -- Use ON DELETE SET NULL
);
CREATE INDEX "home_notification_comment_id_f8543752" ON "home_notification" ("comment_id");
CREATE INDEX "home_notification_recipient_id_c3a36e9c" ON "home_notification" ("recipient_id");
CREATE INDEX "home_notification_sender_id_81ccc934" ON "home_notification" ("sender_id");
CREATE INDEX "home_notification_post_id_a2b3d7f0" ON "home_notification" ("post_id");
CREATE INDEX "home_notification_recipient_read_idx" ON "home_notification" ("recipient_id", "is_read"); -- For fetching unread notifications


--
-- Add field post to comment (simulated migration)
--
-- First, rename the old table or drop it if it's empty/no data to preserve
ALTER TABLE "home_comment" RENAME TO "old_home_comment";

CREATE TABLE "home_comment" (
    "id" BIGSERIAL PRIMARY KEY,
    "content" TEXT NOT NULL,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "user_id" BIGINT NOT NULL REFERENCES "authentication_customuser" ("id") ON DELETE CASCADE,
    "post_id" BIGINT NOT NULL REFERENCES "home_post" ("id") ON DELETE CASCADE -- Add default 0 for existing rows in migration or handle in app
);

-- For an actual migration, data transfer would occur here.
-- Example for data transfer (assuming a placeholder post_id for old comments if NULL was not allowed):
-- INSERT INTO "home_comment" ("id", "content", "created_at", "user_id", "post_id")
-- SELECT "id", "content", "created_at", "user_id", <DEFAULT_POST_ID> FROM "old_home_comment";
-- If post_id cannot be NULL, you MUST ensure existing comments get a valid post_id, or handle the migration carefully.
-- For a new table creation as shown, no data transfer is implicitly performed.

DROP TABLE "old_home_comment"; -- Once data is migrated and new table is stable

CREATE INDEX "home_comment_user_id_842649c8" ON "home_comment" ("user_id");
CREATE INDEX "home_comment_post_id_11f2e780" ON "home_comment" ("post_id");
CREATE INDEX "home_comment_post_id_created_at_idx" ON "home_comment" ("post_id", "created_at" DESC); -- Optimize for comments on a post


--
-- Create model ProfileCertification
--
CREATE TABLE "home_profilecertification" (
    "id" SERIAL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL,
    "issuing_organization" VARCHAR(100) NOT NULL,
    "issue_date" DATE NULL,
    "expiration_date" DATE NULL,
    "credential_id" VARCHAR(100) NOT NULL,
    "credential_url" VARCHAR(200) NOT NULL,
    "is_visible" BOOLEAN NOT NULL DEFAULT TRUE, -- Add default
    "order" INTEGER NOT NULL,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "user_id" BIGINT NULL REFERENCES "authentication_customuser" ("id") ON DELETE CASCADE -- Use ON DELETE CASCADE for profile data
);
CREATE INDEX "home_profilecertification_user_id_412a2d0e" ON "home_profilecertification" ("user_id");
CREATE INDEX "home_profilecertification_is_visible_idx" ON "home_profilecertification" ("is_visible");


--
-- Create model ProfileEducation
--
CREATE TABLE "home_profileeducation" (
    "id" SERIAL PRIMARY KEY,
    "institution" VARCHAR(100) NOT NULL,
    "degree" VARCHAR(100) NOT NULL,
    "field_of_study" VARCHAR(100) NOT NULL,
    "start_date" DATE NULL,
    "end_date" DATE NULL,
    "description" TEXT NOT NULL,
    "is_visible" BOOLEAN NOT NULL DEFAULT TRUE, -- Add default
    "order" INTEGER NOT NULL,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "user_id" BIGINT NULL REFERENCES "authentication_customuser" ("id") ON DELETE CASCADE -- Use ON DELETE CASCADE for profile data
);
CREATE INDEX "home_profileeducation_user_id_93d1cde4" ON "home_profileeducation" ("user_id");
CREATE INDEX "home_profileeducation_is_visible_idx" ON "home_profileeducation" ("is_visible");


--
-- Create model ProfileExperience
--
CREATE TABLE "home_profileexperience" (
    "id" SERIAL PRIMARY KEY,
    "company" VARCHAR(100) NOT NULL,
    "position" VARCHAR(100) NOT NULL,
    "location" VARCHAR(100) NOT NULL,
    "start_date" DATE NULL,
    "end_date" DATE NULL,
    "description" TEXT NOT NULL,
    "is_visible" BOOLEAN NOT NULL DEFAULT TRUE, -- Add default
    "order" INTEGER NOT NULL,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "user_id" BIGINT NULL REFERENCES "authentication_customuser" ("id") ON DELETE CASCADE -- Use ON DELETE CASCADE for profile data
);
CREATE INDEX "home_profileexperience_user_id_d6b98e34" ON "home_profileexperience" ("user_id");
CREATE INDEX "home_profileexperience_is_visible_idx" ON "home_profileexperience" ("is_visible");


--
-- Create model ProfileProject
--
CREATE TABLE "home_profileproject" (
    "id" SERIAL PRIMARY KEY,
    "title" VARCHAR(100) NOT NULL,
    "description" TEXT NOT NULL,
    "url" VARCHAR(200) NOT NULL,
    "image" VARCHAR(100) NULL,
    "technologies" VARCHAR(200) NOT NULL,
    "start_date" DATE NULL,
    "end_date" DATE NULL,
    "is_visible" BOOLEAN NOT NULL DEFAULT TRUE, -- Add default
    "order" INTEGER NOT NULL,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "user_id" BIGINT NULL REFERENCES "authentication_customuser" ("id") ON DELETE CASCADE -- Use ON DELETE CASCADE for profile data
);
CREATE INDEX "home_profileproject_user_id_647e2958" ON "home_profileproject" ("user_id");
CREATE INDEX "home_profileproject_is_visible_idx" ON "home_profileproject" ("is_visible");


--
-- Create model ProfileUserProfile
--
CREATE TABLE "home_profileuserprofile" (
    "id" SERIAL PRIMARY KEY,
    "bio" TEXT NOT NULL,
    "location" VARCHAR(100) NOT NULL,
    "website" VARCHAR(200) NOT NULL,
    "social_links" JSONB NOT NULL DEFAULT '{}'::jsonb, -- Changed to JSONB with default, removed CHECK
    "privacy_settings" JSONB NOT NULL DEFAULT '{}'::jsonb, -- Changed to JSONB with default, removed CHECK
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "user_id" BIGINT NOT NULL UNIQUE REFERENCES "authentication_customuser" ("id") ON DELETE CASCADE -- Use ON DELETE CASCADE
);
-- No specific index needed here beyond the unique constraint on user_id, which implicitly creates an index.


--
-- Create model Answer
--
CREATE TABLE "home_answer" (
    "id" SERIAL PRIMARY KEY,
    "text" TEXT NOT NULL,
    "is_correct" BOOLEAN NOT NULL DEFAULT FALSE, -- Add default
    "order" INTEGER NOT NULL CHECK ("order" >= 0), -- Removed "unsigned"
    "question_id" BIGINT NOT NULL REFERENCES "home_question" ("id") ON DELETE CASCADE -- Use ON DELETE CASCADE
);
CREATE INDEX "home_answer_question_id_15b0d44a" ON "home_answer" ("question_id");
CREATE INDEX "home_answer_question_id_is_correct_idx" ON "home_answer" ("question_id", "is_correct"); -- For finding correct answers quickly


--
-- Create model Quiz (Initial version, will be altered later)
--
CREATE TABLE "home_quiz" (
    "id" BIGSERIAL PRIMARY KEY,
    "title" VARCHAR(200) NOT NULL,
    "description" TEXT NOT NULL,
    "time_limit" INTEGER NOT NULL CHECK ("time_limit" >= 0), -- Removed "unsigned"
    "passing_score" INTEGER NOT NULL CHECK ("passing_score" >= 0), -- Removed "unsigned"
    "is_active" BOOLEAN NOT NULL DEFAULT TRUE, -- Add default
    "is_randomized" BOOLEAN NOT NULL DEFAULT FALSE, -- Add default
    "total_marks" INTEGER NOT NULL CHECK ("total_marks" >= 0), -- Removed "unsigned"
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "creator_id" BIGINT NULL REFERENCES "authentication_customuser" ("id") ON DELETE SET NULL -- Use ON DELETE SET NULL
);
CREATE INDEX "home_quiz_creator_id_2abe2056" ON "home_quiz" ("creator_id");
CREATE INDEX "home_quiz_is_active_idx" ON "home_quiz" ("is_active");


--
-- Add field quiz to question (simulated migration)
--
-- First, rename the old table or drop it if it's empty/no data to preserve
ALTER TABLE "home_question" RENAME TO "old_home_question";

CREATE TABLE "home_question" (
    "id" BIGSERIAL PRIMARY KEY,
    "text" TEXT NOT NULL,
    "question_type" VARCHAR(20) NOT NULL,
    "explanation" TEXT NOT NULL,
    "marks" INTEGER NOT NULL CHECK ("marks" >= 0),
    "order" INTEGER NOT NULL CHECK ("order" >= 0),
    "image" VARCHAR(100) NULL,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "quiz_id" BIGINT NOT NULL REFERENCES "home_quiz" ("id") ON DELETE CASCADE -- Add default 0 for existing rows in migration or handle in app
);

-- For an actual migration, data transfer would occur here.
-- Example for data transfer (assuming a placeholder quiz_id for old questions if NULL was not allowed):
-- INSERT INTO "home_question" ("id", "text", "question_type", "explanation", "marks", "order", "image", "created_at", "updated_at", "quiz_id")
-- SELECT "id", "text", "question_type", "explanation", "marks", "order", "image", "created_at", "updated_at", <DEFAULT_QUIZ_ID> FROM "old_home_question";

DROP TABLE "old_home_question"; -- Once data is migrated and new table is stable

CREATE INDEX "home_question_quiz_id_8f62037c" ON "home_question" ("quiz_id");
CREATE INDEX "home_question_quiz_id_order_idx" ON "home_question" ("quiz_id", "order"); -- Optimize for questions in a quiz


--
-- Create model Subject
--
CREATE TABLE "home_subject" (
    "id" SERIAL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL,
    "code" VARCHAR(20) NOT NULL UNIQUE,
    "description" TEXT NOT NULL,
    "icon" VARCHAR(100) NOT NULL,
    "icon_color" VARCHAR(20) NOT NULL,
    "order" INTEGER NOT NULL,
    "icon_name" VARCHAR(50) NOT NULL,
    "background_icon" VARCHAR(50) NOT NULL,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "is_active" BOOLEAN NOT NULL DEFAULT TRUE, -- Add default
    "instructor_id" BIGINT NULL REFERENCES "authentication_customuser" ("id") ON DELETE SET NULL -- Use ON DELETE SET NULL
);
CREATE INDEX "home_subject_instructor_id_5f1d2581" ON "home_subject" ("instructor_id");
CREATE INDEX "home_subject_code_idx" ON "home_subject" ("code"); -- Explicitly index the unique code


--
-- Add field subject to quiz (simulated migration)
--
-- First, rename the old table or drop it if it's empty/no data to preserve
ALTER TABLE "home_quiz" RENAME TO "old_home_quiz";

CREATE TABLE "home_quiz" (
    "id" BIGSERIAL PRIMARY KEY,
    "title" VARCHAR(200) NOT NULL,
    "description" TEXT NOT NULL,
    "time_limit" INTEGER NOT NULL CHECK ("time_limit" >= 0),
    "passing_score" INTEGER NOT NULL CHECK ("passing_score" >= 0),
    "is_active" BOOLEAN NOT NULL DEFAULT TRUE,
    "is_randomized" BOOLEAN NOT NULL DEFAULT FALSE,
    "total_marks" INTEGER NOT NULL CHECK ("total_marks" >= 0),
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "creator_id" BIGINT NULL REFERENCES "authentication_customuser" ("id") ON DELETE SET NULL,
    "subject_id" BIGINT NOT NULL REFERENCES "home_subject" ("id") ON DELETE CASCADE -- Add default 0 for existing rows in migration or handle in app
);

-- For an actual migration, data transfer would occur here.
-- INSERT INTO "home_quiz" ("id", "title", ..., "creator_id", "subject_id")
-- SELECT "id", "title", ..., "creator_id", <DEFAULT_SUBJECT_ID> FROM "old_home_quiz";

DROP TABLE "old_home_quiz"; -- Once data is migrated and new table is stable

CREATE INDEX "home_quiz_creator_id_2abe2056" ON "home_quiz" ("creator_id");
CREATE INDEX "home_quiz_subject_id_67dec9ad" ON "home_quiz" ("subject_id");
-- Combined index for subject and activity status
CREATE INDEX "home_quiz_subject_id_is_active_idx" ON "home_quiz" ("subject_id", "is_active");


--
-- Create model SubjectEnrollment
--
CREATE TABLE "home_subjectenrollment" (
    "id" SERIAL PRIMARY KEY,
    "enrolled_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "is_active" BOOLEAN NOT NULL DEFAULT TRUE, -- Add default
    "student_id" BIGINT NOT NULL REFERENCES "authentication_customuser" ("id") ON DELETE CASCADE, -- Use ON DELETE CASCADE
    "subject_id" BIGINT NOT NULL REFERENCES "home_subject" ("id") ON DELETE CASCADE -- Use ON DELETE CASCADE
);
CREATE UNIQUE INDEX "home_subjectenrollment_student_id_subject_id_8a8df48a_uniq" ON "home_subjectenrollment" ("student_id", "subject_id");
CREATE INDEX "home_subjectenrollment_student_id_e1173bc9" ON "home_subjectenrollment" ("student_id");
CREATE INDEX "home_subjectenrollment_subject_id_466d7ff7" ON "home_subjectenrollment" ("subject_id");
CREATE INDEX "home_subjectenrollment_is_active_idx" ON "home_subjectenrollment" ("is_active");


--
-- Create model SubjectMaterial
--
CREATE TABLE "home_subjectmaterial" (
    "id" SERIAL PRIMARY KEY,
    "title" VARCHAR(200) NOT NULL,
    "description" TEXT NOT NULL,
    "material_type" VARCHAR(20) NOT NULL,
    "content" TEXT NOT NULL,
    "order" INTEGER NOT NULL,
    "is_active" BOOLEAN NOT NULL DEFAULT TRUE, -- Add default
    "file" VARCHAR(100) NULL,
    "external_url" VARCHAR(200) NULL,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "subject_id" BIGINT NOT NULL REFERENCES "home_subject" ("id") ON DELETE CASCADE -- Use ON DELETE CASCADE
);
CREATE INDEX "home_subjectmaterial_subject_id_a4502b1d" ON "home_subjectmaterial" ("subject_id");
CREATE INDEX "home_subjectmaterial_subject_id_order_idx" ON "home_subjectmaterial" ("subject_id", "order"); -- Optimize for materials in a subject


--
-- Create model UserAttempt
--
CREATE TABLE "home_userattempt" (
    "id" BIGSERIAL PRIMARY KEY,
    "start_time" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "end_time" TIMESTAMP WITH TIME ZONE NULL,
    "score" INTEGER NOT NULL CHECK ("score" >= 0), -- Removed "unsigned"
    "status" VARCHAR(20) NOT NULL,
    "quiz_id" BIGINT NOT NULL REFERENCES "home_quiz" ("id") ON DELETE CASCADE, -- Use ON DELETE CASCADE
    "user_id" BIGINT NOT NULL REFERENCES "authentication_customuser" ("id") ON DELETE CASCADE -- Use ON DELETE CASCADE
);
CREATE INDEX "home_userat_user_id_eeae1d_idx" ON "home_userattempt" ("user_id");
CREATE INDEX "home_userat_quiz_id_00f92d_idx" ON "home_userattempt" ("quiz_id");
CREATE INDEX "home_userat_status_ea8ce0_idx" ON "home_userattempt" ("status");
CREATE INDEX "home_userattempt_quiz_id_user_id_idx" ON "home_userattempt" ("quiz_id", "user_id"); -- For attempts of a specific user on a quiz


--
-- Create model UserAnswer
--
CREATE TABLE "home_useranswer" (
    "id" SERIAL PRIMARY KEY,
    "text_answer" TEXT NULL,
    "marks_obtained" INTEGER NOT NULL CHECK ("marks_obtained" >= 0), -- Removed "unsigned"
    "question_id" BIGINT NOT NULL REFERENCES "home_question" ("id") ON DELETE CASCADE, -- Use ON DELETE CASCADE
    "selected_answer_id" BIGINT NULL REFERENCES "home_answer" ("id") ON DELETE SET NULL, -- Use ON DELETE SET NULL
    "user_attempt_id" BIGINT NOT NULL REFERENCES "home_userattempt" ("id") ON DELETE CASCADE -- Use ON DELETE CASCADE
);
CREATE UNIQUE INDEX "home_useranswer_user_attempt_id_question_id_c5c56647_uniq" ON "home_useranswer" ("user_attempt_id", "question_id");
CREATE INDEX "home_useranswer_question_id_6e054301" ON "home_useranswer" ("question_id");
CREATE INDEX "home_useranswer_selected_answer_id_b6428a08" ON "home_useranswer" ("selected_answer_id");
CREATE INDEX "home_useranswer_user_attempt_id_7148cb4d" ON "home_useranswer" ("user_attempt_id");


--
-- Create model Like
--
CREATE TABLE "home_like" (
    "id" BIGSERIAL PRIMARY KEY,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "user_id" BIGINT NOT NULL REFERENCES "authentication_customuser" ("id") ON DELETE CASCADE, -- Use ON DELETE CASCADE
    "post_id" BIGINT NOT NULL REFERENCES "home_post" ("id") ON DELETE CASCADE -- Use ON DELETE CASCADE
);
CREATE UNIQUE INDEX "home_like_user_id_post_id_b80dede0_uniq" ON "home_like" ("user_id", "post_id");
CREATE INDEX "home_like_user_id_c0747f71" ON "home_like" ("user_id");
CREATE INDEX "home_like_post_id_aa0d0bdf" ON "home_like" ("post_id");


--
-- Create model ProfileSkill
--
CREATE TABLE "home_profileskill" (
    "id" SERIAL PRIMARY KEY,
    "name" VARCHAR(50) NOT NULL,
    "proficiency" INTEGER NOT NULL,
    "is_visible" BOOLEAN NOT NULL DEFAULT TRUE, -- Add default
    "order" INTEGER NOT NULL,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "user_id" BIGINT NULL REFERENCES "authentication_customuser" ("id") ON DELETE CASCADE -- Use ON DELETE CASCADE
);
CREATE UNIQUE INDEX "home_profileskill_user_id_name_d50c428b_uniq" ON "home_profileskill" ("user_id", "name");
CREATE INDEX "home_profileskill_user_id_43306dcf" ON "home_profileskill" ("user_id");
CREATE INDEX "home_profileskill_is_visible_idx" ON "home_profileskill" ("is_visible");