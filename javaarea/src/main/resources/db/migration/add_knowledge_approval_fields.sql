-- Add uploaded_by, approval_status, and approval_remark fields to knowledge_base table
-- This migration adds role-based access control for knowledge management

USE edu;

-- Add uploaded_by field to track who uploaded the file
ALTER TABLE `knowledge_base`
ADD COLUMN `uploaded_by` BIGINT DEFAULT NULL AFTER `course_id`;

-- Add approval_status field: PENDING/APPROVED/REJECTED
ALTER TABLE `knowledge_base`
ADD COLUMN `approval_status` VARCHAR(20) NOT NULL DEFAULT 'APPROVED' AFTER `status`;

-- Add approval_remark field for admin to add notes when approving/rejecting
ALTER TABLE `knowledge_base`
ADD COLUMN `approval_remark` VARCHAR(500) DEFAULT NULL AFTER `approval_status`;

-- Add index for faster queries by uploader and approval status
CREATE INDEX `idx_uploaded_by` ON `knowledge_base` (`uploaded_by`);
CREATE INDEX `idx_approval_status` ON `knowledge_base` (`approval_status`);

-- Update existing records: set uploaded_by from course teacher (best effort)
UPDATE `knowledge_base` kb
JOIN `course` c ON kb.course_id = c.id
SET kb.uploaded_by = c.teacher_id
WHERE kb.course_id IS NOT NULL;
