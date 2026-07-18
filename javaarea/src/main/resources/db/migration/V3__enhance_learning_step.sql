-- V3: 学习路径步骤深度增强 - MySQL 8.0 兼容版本
-- 使用存储过程安全添加列，如果列已存在则跳过

DELIMITER $$

DROP PROCEDURE IF EXISTS add_column_if_not_exists$$
CREATE PROCEDURE add_column_if_not_exists(
    IN tbl_name VARCHAR(128),
    IN col_name VARCHAR(128),
    IN col_def TEXT
)
BEGIN
    DECLARE col_count INT;
    SELECT COUNT(*) INTO col_count
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = tbl_name
      AND COLUMN_NAME = col_name;
    
    IF col_count = 0 THEN
        SET @sql = CONCAT('ALTER TABLE ', tbl_name, ' ADD COLUMN ', col_name, ' ', col_def);
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END$$

DELIMITER ;

-- learning_path 新增字段
CALL add_column_if_not_exists('learning_path', 'total_study_minutes', 'INT NOT NULL DEFAULT 0 COMMENT "累计学习时长(分钟)"');
CALL add_column_if_not_exists('learning_path', 'total_exercises_done', 'INT NOT NULL DEFAULT 0 COMMENT "已完成练习题数"');
CALL add_column_if_not_exists('learning_path', 'correct_rate', 'DECIMAL(5,2) DEFAULT NULL COMMENT "总体正确率"');
CALL add_column_if_not_exists('learning_path', 'last_studied_at', 'DATETIME DEFAULT NULL COMMENT "最近学习时间"');

-- learning_path_step 新增字段
CALL add_column_if_not_exists('learning_path_step', 'content', 'LONGTEXT DEFAULT NULL COMMENT "AI生成的学习内容(Markdown)"');
CALL add_column_if_not_exists('learning_path_step', 'exercises', 'JSON DEFAULT NULL COMMENT "课内练习题集"');
CALL add_column_if_not_exists('learning_path_step', 'exercise_results', 'JSON DEFAULT NULL COMMENT "学生练习结果"');
CALL add_column_if_not_exists('learning_path_step', 'knowledge_ids', 'VARCHAR(512) DEFAULT NULL COMMENT "关联的知识库ID列表"');
CALL add_column_if_not_exists('learning_path_step', 'is_checkpoint', 'TINYINT NOT NULL DEFAULT 0 COMMENT "是否为阶段检查点"');
CALL add_column_if_not_exists('learning_path_step', 'checkpoint_scope', 'VARCHAR(255) DEFAULT NULL COMMENT "自测覆盖的步骤范围"');

DROP PROCEDURE IF EXISTS add_column_if_not_exists;
