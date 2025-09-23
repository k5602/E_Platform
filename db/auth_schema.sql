CREATE TABLE "authentication_customuser" (
    "id" BIGSERIAL PRIMARY KEY, 
    "password" VARCHAR(128) NOT NULL,
    "last_login" TIMESTAMP WITH TIME ZONE NULL,
    "is_superuser" BOOLEAN NOT NULL,
    "username" VARCHAR(150) NOT NULL UNIQUE,
    "first_name" VARCHAR(150) NOT NULL,
    "last_name" VARCHAR(150) NOT NULL,
    "email" VARCHAR(254) NOT NULL,
    "is_staff" BOOLEAN NOT NULL,
    "is_active" BOOLEAN NOT NULL,
    "date_joined" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "user_type" VARCHAR(20) NOT NULL,
    "birthdate" DATE NULL,
    "profile_picture" VARCHAR(100) NULL
);

CREATE INDEX "authentication_customuser_username_idx" ON "authentication_customuser" ("username"); 
CREATE INDEX "authentication_customuser_email_idx" ON "authentication_customuser" ("email");   
CREATE INDEX "authentication_customuser_user_type_idx" ON "authentication_customuser" ("user_type");

CREATE TABLE "authentication_customuser_groups" (
    "id" SERIAL PRIMARY KEY,
    "customuser_id" BIGINT NOT NULL REFERENCES "authentication_customuser" ("id") ON DELETE CASCADE,
    "group_id" INTEGER NOT NULL REFERENCES "auth_group" ("id") ON DELETE CASCADE, 
    UNIQUE ("customuser_id", "group_id") 
);

CREATE INDEX "authentication_customuser_groups_customuser_id_a7d1343c" ON "authentication_customuser_groups" ("customuser_id");
CREATE INDEX "authentication_customuser_groups_group_id_c5ef1d10" ON "authentication_customuser_groups" ("group_id");

CREATE TABLE "authentication_customuser_user_permissions" (
    "id" SERIAL PRIMARY KEY,
    "customuser_id" BIGINT NOT NULL REFERENCES "authentication_customuser" ("id") ON DELETE CASCADE, 
    "permission_id" INTEGER NOT NULL REFERENCES "auth_permission" ("id") ON DELETE CASCADE, 
    UNIQUE ("customuser_id", "permission_id") 
);

CREATE INDEX "authentication_customuser_user_permissions_customuser_id_33d2a5f7" ON "authentication_customuser_user_permissions" ("customuser_id");
CREATE INDEX "authentication_customuser_user_permissions_permission_id_e47332af" ON "authentication_customuser_user_permissions" ("permission_id");
