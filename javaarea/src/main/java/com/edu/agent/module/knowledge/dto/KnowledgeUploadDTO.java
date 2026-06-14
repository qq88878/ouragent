package com.edu.agent.module.knowledge.dto;

import lombok.Data;

@Data
public class KnowledgeUploadDTO {
    private Long courseId;
    private String name;
    private String description;
    // Note: file is handled via MultipartFile in controller, not in this DTO
}