-- V2: 学习路径功能增强
-- learning_path 新增字段
ALTER TABLE learning_path ADD COLUMN version INT NOT NULL DEFAULT 1 COMMENT '路径版本号';
ALTER TABLE learning_path ADD COLUMN archived TINYINT NOT NULL DEFAULT 0 COMMENT '0=正常 1=已归档';
ALTER TABLE learning_path ADD COLUMN starred TINYINT NOT NULL DEFAULT 0 COMMENT '0=未收藏 1=已收藏';

-- learning_path_step 新增字段
ALTER TABLE learning_path_step ADD COLUMN step_type VARCHAR(32) DEFAULT NULL COMMENT 'CONCEPT/PRACTICE/REVIEW/PROJECT';
ALTER TABLE learning_path_step ADD COLUMN estimated_hours INT DEFAULT NULL COMMENT '预估耗时(小时)';
