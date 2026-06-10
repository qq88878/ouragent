CREATE DATABASE edu;
USE edu;

-- ============================================================
-- edu-agent Database Schema
-- MySQL 8.x / DDL
-- ============================================================

-- -----------------------------------------------------------
-- 1. user
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS `user` (
    `id`             BIGINT       NOT NULL AUTO_INCREMENT,
    `username`       VARCHAR(64)  NOT NULL,
    `password`       VARCHAR(255) NOT NULL,
    `nickname`       VARCHAR(64)  DEFAULT NULL,
    `email`          VARCHAR(128) DEFAULT NULL,
    `phone`          VARCHAR(32)  DEFAULT NULL,
    `avatar`         VARCHAR(255) DEFAULT NULL,
    `role`           VARCHAR(32)  NOT NULL DEFAULT 'STUDENT' COMMENT 'STUDENT / TEACHER / ADMIN',
    `status`         TINYINT      NOT NULL DEFAULT 1 COMMENT '1=active 0=disabled',
    `email_verified` TINYINT      NOT NULL DEFAULT 0 COMMENT '0=unverified 1=verified',
    `last_login_time` DATETIME    DEFAULT NULL,
    `create_time`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted`        TINYINT      NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_username` (`username`),
    UNIQUE KEY `uk_email` (`email`),
    INDEX `idx_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------
-- 2. course
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS `course` (
    `id`             BIGINT        NOT NULL AUTO_INCREMENT,
    `title`          VARCHAR(255)  NOT NULL,
    `description`    TEXT          DEFAULT NULL,
    `cover_image`    VARCHAR(255)  DEFAULT NULL,
    `category`       VARCHAR(64)   DEFAULT NULL,
    `difficulty`     VARCHAR(32)   DEFAULT NULL COMMENT 'BEGINNER / INTERMEDIATE / ADVANCED',
    `teacher_id`     BIGINT        NOT NULL,
    `status`         TINYINT       NOT NULL DEFAULT 0 COMMENT '0=draft 1=published',
    `create_time`    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time`    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted`        TINYINT       NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    INDEX `idx_teacher_id` (`teacher_id`),
    INDEX `idx_category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------
-- 3. knowledge_base
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS `knowledge_base` (
    `id`             BIGINT        NOT NULL AUTO_INCREMENT,
    `name`           VARCHAR(128)  NOT NULL,
    `description`    TEXT          DEFAULT NULL,
    `course_id`      BIGINT        DEFAULT NULL,
    `file_path`      VARCHAR(512)  NOT NULL,
    `file_type`      VARCHAR(32)   DEFAULT NULL COMMENT 'pdf / docx / md / txt',
    `file_size`      BIGINT        DEFAULT NULL,
    `status`         TINYINT       NOT NULL DEFAULT 0 COMMENT '0=pending 1=indexed 2=failed',
    `create_time`    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time`    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted`        TINYINT       NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    INDEX `idx_course_id` (`course_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------
-- 4. chat_session
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS `chat_session` (
    `id`             BIGINT        NOT NULL AUTO_INCREMENT,
    `user_id`        BIGINT        NOT NULL,
    `course_id`      BIGINT        DEFAULT NULL,
    `title`          VARCHAR(255)  DEFAULT NULL,
    `create_time`    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time`    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted`        TINYINT       NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_course_id` (`course_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------
-- 5. chat_message
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS `chat_message` (
    `id`             BIGINT        NOT NULL AUTO_INCREMENT,
    `session_id`     BIGINT        NOT NULL,
    `role`           VARCHAR(32)   NOT NULL COMMENT 'USER / ASSISTANT / SYSTEM',
    `content`        TEXT          NOT NULL,
    `token_count`    INT           DEFAULT NULL,
    `create_time`    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time`    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted`        TINYINT       NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    INDEX `idx_session_id` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------
-- 6. learning_path
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS `learning_path` (
    `id`             BIGINT        NOT NULL AUTO_INCREMENT,
    `user_id`        BIGINT        NOT NULL,
    `course_id`      BIGINT        NOT NULL,
    `title`          VARCHAR(255)  NOT NULL,
    `description`    TEXT          DEFAULT NULL,
    `total_steps`    INT           NOT NULL DEFAULT 0,
    `completed_steps` INT          NOT NULL DEFAULT 0,
    `status`         TINYINT       NOT NULL DEFAULT 0 COMMENT '0=in_progress 1=completed 2=abandoned',
    `create_time`    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time`    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted`        TINYINT       NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_course_id` (`course_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------
-- 7. learning_path_step
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS `learning_path_step` (
    `id`             BIGINT        NOT NULL AUTO_INCREMENT,
    `path_id`        BIGINT        NOT NULL,
    `step_order`     INT           NOT NULL,
    `title`          VARCHAR(255)  NOT NULL,
    `description`    TEXT          DEFAULT NULL,
    `knowledge_base_id` BIGINT     DEFAULT NULL,
    `status`         TINYINT       NOT NULL DEFAULT 0 COMMENT '0=pending 1=in_progress 2=completed',
    `create_time`    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time`    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted`        TINYINT       NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    INDEX `idx_path_id` (`path_id`),
    INDEX `idx_knowledge_base_id` (`knowledge_base_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------
-- 8. study_record
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS `study_record` (
    `id`             BIGINT        NOT NULL AUTO_INCREMENT,
    `user_id`        BIGINT        NOT NULL,
    `course_id`      BIGINT        NOT NULL,
    `session_id`     BIGINT        DEFAULT NULL,
    `duration`       INT           DEFAULT NULL COMMENT 'seconds',
    `interaction_count` INT        DEFAULT NULL,
    `summary`        TEXT          DEFAULT NULL,
    `create_time`    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time`    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted`        TINYINT       NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_course_id` (`course_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------
-- 9. student_profile
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS `student_profile` (
    `id`             BIGINT        NOT NULL AUTO_INCREMENT,
    `user_id`        BIGINT        NOT NULL,
    `learning_style` VARCHAR(64)   DEFAULT NULL COMMENT 'VISUAL / AUDITORY / READING / KINESTHETIC',
    `strengths`      VARCHAR(512)  DEFAULT NULL,
    `weaknesses`     VARCHAR(512)  DEFAULT NULL,
    `interests`      VARCHAR(512)  DEFAULT NULL,
    `grade_level`    VARCHAR(32)   DEFAULT NULL,
    `preferences`    JSON          DEFAULT NULL,
    `create_time`    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time`    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted`        TINYINT       NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;