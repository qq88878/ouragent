-- ============================================================
-- Migration: Fix logical delete + unique constraint for user table
-- ============================================================

USE edu_agent;

-- 1. Drop old unique indexes (ignore error if not exist)
DROP INDEX uk_username ON `user`;
DROP INDEX uk_email ON `user`;

-- 2. Add virtual columns (NULL when logically deleted)
ALTER TABLE `user` ADD COLUMN `active_username` VARCHAR(64)
    GENERATED ALWAYS AS (IF(deleted = 0, username, NULL)) VIRTUAL;

ALTER TABLE `user` ADD COLUMN `active_email` VARCHAR(128)
    GENERATED ALWAYS AS (IF(deleted = 0, email, NULL)) VIRTUAL;

-- 3. Create new unique indexes on virtual columns
-- MySQL unique indexes ignore NULLs, so deleted users can share username/email
CREATE UNIQUE INDEX uk_active_username ON `user` (`active_username`);
CREATE UNIQUE INDEX uk_active_email ON `user` (`active_email`);
