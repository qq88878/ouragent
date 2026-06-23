package com.edu.agent.module.knowledge.entity;

import com.edu.agent.common.base.BaseEntity;
import com.baomidou.mybatisplus.annotation.TableName;

@TableName("knowledge_base")
public class KnowledgeBase extends BaseEntity {
    private Long courseId;
    private Long uploadedBy;
    private String name;
    private String description;
    private String filePath;
    private String fileType;
    private Long fileSize;
    private Integer status;
    private String approvalStatus;
    private String approvalRemark;
    private String remark;

    public KnowledgeBase() {}

    public Long getCourseId() { return this.courseId; }
    public Long getUploadedBy() { return this.uploadedBy; }
    public String getName() { return this.name; }
    public String getDescription() { return this.description; }
    public String getFilePath() { return this.filePath; }
    public String getFileType() { return this.fileType; }
    public Long getFileSize() { return this.fileSize; }
    public Integer getStatus() { return this.status; }
    public String getApprovalStatus() { return this.approvalStatus; }
    public String getApprovalRemark() { return this.approvalRemark; }
    public String getRemark() { return this.remark; }

    public void setCourseId(Long courseId) { this.courseId = courseId; }
    public void setUploadedBy(Long uploadedBy) { this.uploadedBy = uploadedBy; }
    public void setName(String name) { this.name = name; }
    public void setDescription(String description) { this.description = description; }
    public void setFilePath(String filePath) { this.filePath = filePath; }
    public void setFileType(String fileType) { this.fileType = fileType; }
    public void setFileSize(Long fileSize) { this.fileSize = fileSize; }
    public void setStatus(Integer status) { this.status = status; }
    public void setApprovalStatus(String approvalStatus) { this.approvalStatus = approvalStatus; }
    public void setApprovalRemark(String approvalRemark) { this.approvalRemark = approvalRemark; }
    public void setRemark(String remark) { this.remark = remark; }
}
