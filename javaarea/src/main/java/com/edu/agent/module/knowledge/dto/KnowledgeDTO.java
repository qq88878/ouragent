package com.edu.agent.module.knowledge.dto;

import lombok.Data;

import java.time.LocalDateTime;

@Data
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
    private LocalDateTime createTime;
}