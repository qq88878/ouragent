package com.edu.agent.module.knowledge.dto;

import java.time.LocalDateTime;

public class KnowledgeDTO {
    private Long id;
    private Long courseId;
    private String courseName;
    private Long courseTeacherId;
    private String courseTeacherName;
    private Long uploadedBy;
    private String uploadedByName;
    private String name;
    private String description;
    private String filePath;
    private String fileType;
    private Long fileSize;
    private Integer status;
    private String approvalStatus;
    private String approvalRemark;
    private String remark;
    private LocalDateTime createTime;

    public KnowledgeDTO() {}

    public Long getId() { return this.id; }
    public Long getCourseId() { return this.courseId; }
    public String getCourseName() { return this.courseName; }
    public Long getCourseTeacherId() { return this.courseTeacherId; }
    public String getCourseTeacherName() { return this.courseTeacherName; }
    public Long getUploadedBy() { return this.uploadedBy; }
    public String getUploadedByName() { return this.uploadedByName; }
    public String getName() { return this.name; }
    public String getDescription() { return this.description; }
    public String getFilePath() { return this.filePath; }
    public String getFileType() { return this.fileType; }
    public Long getFileSize() { return this.fileSize; }
    public Integer getStatus() { return this.status; }
    public String getApprovalStatus() { return this.approvalStatus; }
    public String getApprovalRemark() { return this.approvalRemark; }
    public String getRemark() { return this.remark; }
    public LocalDateTime getCreateTime() { return this.createTime; }

    public void setId(Long id) { this.id = id; }
    public void setCourseId(Long courseId) { this.courseId = courseId; }
    public void setCourseName(String courseName) { this.courseName = courseName; }
    public void setCourseTeacherId(Long courseTeacherId) { this.courseTeacherId = courseTeacherId; }
    public void setCourseTeacherName(String courseTeacherName) { this.courseTeacherName = courseTeacherName; }
    public void setUploadedBy(Long uploadedBy) { this.uploadedBy = uploadedBy; }
    public void setUploadedByName(String uploadedByName) { this.uploadedByName = uploadedByName; }
    public void setName(String name) { this.name = name; }
    public void setDescription(String description) { this.description = description; }
    public void setFilePath(String filePath) { this.filePath = filePath; }
    public void setFileType(String fileType) { this.fileType = fileType; }
    public void setFileSize(Long fileSize) { this.fileSize = fileSize; }
    public void setStatus(Integer status) { this.status = status; }
    public void setApprovalStatus(String approvalStatus) { this.approvalStatus = approvalStatus; }
    public void setApprovalRemark(String approvalRemark) { this.approvalRemark = approvalRemark; }
    public void setRemark(String remark) { this.remark = remark; }
    public void setCreateTime(LocalDateTime createTime) { this.createTime = createTime; }
}
