-- ============================================================
-- 11. schedule_config (学生课表配置)
-- ============================================================
CREATE TABLE IF NOT EXISTS schedule_config (
    id                  BIGINT        NOT NULL AUTO_INCREMENT,
    user_id             BIGINT        NOT NULL,
    semester_start_date DATE          DEFAULT NULL COMMENT '开学日期，用于计算第几周',
    period_config       TEXT          DEFAULT NULL COMMENT '时间段配置 [{name,startTime,endTime}]',
    create_time         DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time         DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted             TINYINT       NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    UNIQUE KEY uk_schedule_config_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 12. schedule_course (学生课表课程)
-- ============================================================
CREATE TABLE IF NOT EXISTS schedule_course (
    id              BIGINT        NOT NULL AUTO_INCREMENT,
    user_id         BIGINT        NOT NULL,
    
ame            VARCHAR(128)  NOT NULL COMMENT '课程名称',
    week_numbers    TEXT          DEFAULT NULL COMMENT '哪些周 [1,2,3,...]',
    day_of_weeks    TEXT          DEFAULT NULL COMMENT '哪些天：1=周一...7=周日',
    period_indexes  TEXT          DEFAULT NULL COMMENT '哪些时间段（索引从0开始）',
    create_time     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted         TINYINT       NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    INDEX idx_schedule_course_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;