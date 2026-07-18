-- Combined migration: V2 + V3 for learning_path enhancements (MySQL 8.0 compatible)

DELIMITER $$

DROP PROCEDURE IF EXISTS add_col$$
CREATE PROCEDURE add_col(IN tbl VARCHAR(128), IN col VARCHAR(128), IN def TEXT)
BEGIN
    DECLARE cnt INT;
    SELECT COUNT(*) INTO cnt FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = tbl AND COLUMN_NAME = col;
    IF cnt = 0 THEN
        SET @sql = CONCAT('ALTER TABLE ', tbl, ' ADD COLUMN ', col, ' ', def);
        PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
    END IF;
END$$

DELIMITER ;

-- V2: learning_path
CALL add_col('learning_path', 'version', 'INT NOT NULL DEFAULT 1 COMMENT "路径版本号"');
CALL add_col('learning_path', 'archived', 'TINYINT NOT NULL DEFAULT 0 COMMENT "0=正常 1=已归档"');
CALL add_col('learning_path', 'starred', 'TINYINT NOT NULL DEFAULT 0 COMMENT "0=未收藏 1=已收藏"');

-- V2: learning_path_step
CALL add_col('learning_path_step', 'step_type', 'VARCHAR(32) DEFAULT NULL COMMENT "CONCEPT/PRACTICE/REVIEW/PROJECT"');
CALL add_col('learning_path_step', 'estimated_hours', 'INT DEFAULT NULL COMMENT "预估耗时(小时)"');

-- V3: learning_path
CALL add_col('learning_path', 'total_study_minutes', 'INT NOT NULL DEFAULT 0 COMMENT "累计学习时长(分钟)"');
CALL add_col('learning_path', 'total_exercises_done', 'INT NOT NULL DEFAULT 0 COMMENT "已完成练习题数"');
CALL add_col('learning_path', 'correct_rate', 'DECIMAL(5,2) DEFAULT NULL COMMENT "总体正确率"');
CALL add_col('learning_path', 'last_studied_at', 'DATETIME DEFAULT NULL COMMENT "最近学习时间"');

-- V3: learning_path_step
CALL add_col('learning_path_step', 'content', 'LONGTEXT DEFAULT NULL COMMENT "AI生成的学习内容"');
CALL add_col('learning_path_step', 'exercises', 'JSON DEFAULT NULL COMMENT "课内练习题集"');
CALL add_col('learning_path_step', 'exercise_results', 'JSON DEFAULT NULL COMMENT "学生练习结果"');
CALL add_col('learning_path_step', 'knowledge_ids', 'VARCHAR(512) DEFAULT NULL COMMENT "关联知识库ID列表"');
CALL add_col('learning_path_step', 'is_checkpoint', 'TINYINT NOT NULL DEFAULT 0 COMMENT "是否为阶段检查点"');
CALL add_col('learning_path_step', 'checkpoint_scope', 'VARCHAR(255) DEFAULT NULL COMMENT "自测覆盖步骤范围"');

DROP PROCEDURE IF EXISTS add_col;
