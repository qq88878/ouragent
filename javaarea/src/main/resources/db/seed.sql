-- ============================================================
-- Seed Data for Development
-- Default passwords are BCrypt-hashed: "123456"
-- Run after schema.sql
-- ============================================================

USE edu_agent;

-- Admin account: admin / 123456
INSERT IGNORE INTO `user` (`username`, `password`, `nickname`, `email`, `role`, `status`, `email_verified`)
VALUES ('admin', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iKTVKIUi', '系统管理员', 'admin@ouragent.com', 'ADMIN', 1, 1);

-- Teacher account: teacher / 123456
INSERT IGNORE INTO `user` (`username`, `password`, `nickname`, `email`, `role`, `status`, `email_verified`)
VALUES ('teacher', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iKTVKIUi', '张老师', 'teacher@ouragent.com', 'TEACHER', 1, 1);

-- Student account: student / 123456
INSERT IGNORE INTO `user` (`username`, `password`, `nickname`, `email`, `role`, `status`, `email_verified`)
VALUES ('student', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iKTVKIUi', '李同学', 'student@ouragent.com', 'STUDENT', 1, 1);