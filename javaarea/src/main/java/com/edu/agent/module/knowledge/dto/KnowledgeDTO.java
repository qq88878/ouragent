package com.edu.agent.module.knowledge.dto;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class KnowledgeDTO {
    private Long id;
    private Long courseId;
    private String title;
    private String filePath;
    private String fileType;
    private Long fileSize;
    private String processingStatus;
    private Long uploadedBy;
    private String uploadedByName;
    private LocalDateTime createTime;
}
