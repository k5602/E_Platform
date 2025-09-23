CREATE TABLE IF NOT EXISTS "Ai_prototype_mockaifeedback" (
    "id" SERIAL PRIMARY KEY,
    "feedback_type" VARCHAR(50) NOT NULL,
    "submission_id" VARCHAR(50) NOT NULL,
    "feedback_text" TEXT NOT NULL,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "user_id" BIGINT NULL REFERENCES "authentication_customuser" ("id") ON DELETE SET NULL
);

CREATE INDEX "Ai_prototype_mockaifeedback_user_id_4de995a5" ON "Ai_prototype_mockaifeedback" ("user_id");

CREATE INDEX "Ai_prototype_mockaifeedback_submission_id" ON "Ai_prototype_mockaifeedback" ("submission_id");

CREATE INDEX "Ai_prototype_mockaifeedback_created_at" ON "Ai_prototype_mockaifeedback" ("created_at");

CREATE INDEX "Ai_prototype_mockaifeedback_feedback_type_submission_id" ON "Ai_prototype_mockaifeedback" ("feedback_type", "submission_id");