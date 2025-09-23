CREATE TABLE "chatting_conversation" (
    "id" BIGSERIAL PRIMARY KEY,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX "chatting_conversation_created_at_e890a2c0" ON "chatting_conversation" ("created_at");

CREATE INDEX "chatting_conversation_updated_at_aecdacdc" ON "chatting_conversation" ("updated_at");


CREATE TABLE "chatting_conversation_participants" (
    "id" SERIAL PRIMARY KEY,
    "conversation_id" BIGINT NOT NULL REFERENCES "chatting_conversation" ("id") ON DELETE CASCADE, 
    "customuser_id" BIGINT NOT NULL REFERENCES "authentication_customuser" ("id") ON DELETE CASCADE, 
    UNIQUE ("conversation_id", "customuser_id")

CREATE INDEX "chatting_conversation_participants_conversation_id_5a95cfeb" ON "chatting_conversation_participants" ("conversation_id");
CREATE INDEX "chatting_conversation_participants_customuser_id_24cd1ff8" ON "chatting_conversation_participants" ("customuser_id");


CREATE TABLE "chatting_message" (
    "id" BIGSERIAL PRIMARY KEY, 
    "content" TEXT NOT NULL,
    "timestamp" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "is_read" BOOLEAN NOT NULL DEFAULT FALSE,
    "delivery_status" VARCHAR(10) NOT NULL,
    "delivery_attempts" INTEGER NOT NULL DEFAULT 0, 
    "last_delivery_attempt" TIMESTAMP WITH TIME ZONE NULL,
    "is_edited" BOOLEAN NOT NULL DEFAULT FALSE, 
    "edited_timestamp" TIMESTAMP WITH TIME ZONE NULL,
    "is_deleted" BOOLEAN NOT NULL DEFAULT FALSE, 
    "deleted_timestamp" TIMESTAMP WITH TIME ZONE NULL,
    "file_attachment" VARCHAR(100) NULL,
    "file_type" VARCHAR(10) NULL,
    "file_name" VARCHAR(255) NULL,
    "file_size" BIGINT NULL CHECK ("file_size" >= 0),
    "conversation_id" BIGINT NOT NULL REFERENCES "chatting_conversation" ("id") ON DELETE CASCADE, 
    "sender_id" BIGINT NOT NULL REFERENCES "authentication_customuser" ("id") ON DELETE CASCADE 
);

CREATE INDEX "chatting_message_timestamp_6f1e081d" ON "chatting_message" ("timestamp");
CREATE INDEX "chatting_message_is_read_47af4003" ON "chatting_message" ("is_read");
CREATE INDEX "chatting_message_delivery_status_c3e61191" ON "chatting_message" ("delivery_status");
CREATE INDEX "chatting_message_is_edited_f97f351c" ON "chatting_message" ("is_edited");
CREATE INDEX "chatting_message_is_deleted_10f81927" ON "chatting_message" ("is_deleted");
CREATE INDEX "chatting_message_conversation_id_21978cd7" ON "chatting_message" ("conversation_id");
CREATE INDEX "chatting_message_sender_id_bba5d829" ON "chatting_message" ("sender_id");
CREATE INDEX "chatting_message_conversation_id_timestamp_idx" ON "chatting_message" ("conversation_id", "timestamp" DESC);



CREATE TABLE "chatting_userstatus" (
    "id" SERIAL PRIMARY KEY,
    "is_online" BOOLEAN NOT NULL DEFAULT FALSE,
    "last_active" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "user_id" BIGINT NOT NULL UNIQUE REFERENCES "authentication_customuser" ("id") ON DELETE CASCADE
);

CREATE INDEX "chatting_userstatus_is_online_a15a5136" ON "chatting_userstatus" ("is_online");
CREATE INDEX "chatting_userstatus_last_active_4b43f2cd" ON "chatting_userstatus" ("last_active");

