package com.edu.agent.module.knowledge.dto;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class KnowledgeDTO {
    private Long id;
    private Long courseId;
    private String name;
    private String description;
    private String filePath;
    private String fileType;
    private Long fileSize;
    private Integer status;  // 0=pending, 1=indexed, 2=failed
    private LocalDateTime createTime;
}
