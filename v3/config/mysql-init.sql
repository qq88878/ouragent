-- ============================================================
-- Python Agent Database Initialization
-- MySQL 8.x
-- ============================================================

-- 创建 agent_db 数据库
CREATE DATABASE IF NOT EXISTS agent_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建 agent 用户并授权
CREATE USER IF NOT EXISTS 'agent'@'%' IDENTIFIED BY 'agent_password';
GRANT ALL PRIVILEGES ON agent_db.* TO 'agent'@'%';

-- 刷新权限
FLUSH PRIVILEGES;
