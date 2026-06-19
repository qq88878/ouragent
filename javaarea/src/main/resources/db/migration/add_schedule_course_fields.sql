-- Migration: add location and remark fields to schedule_course
-- Run this if the schedule_course table already exists without these columns
ALTER TABLE schedule_course
    ADD COLUMN IF NOT EXISTS location VARCHAR(255) DEFAULT NULL COMMENT '教室/地点',
    ADD COLUMN IF NOT EXISTS remark VARCHAR(512) DEFAULT NULL COMMENT '备注';
