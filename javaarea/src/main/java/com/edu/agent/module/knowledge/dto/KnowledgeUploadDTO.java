package com.edu.agent.module.knowledge.dto;

import lombok.Data;

import javax.validation.constraints.NotNull;

@Data
public class KnowledgeUploadDTO {
    @NotNull
    private Long courseId;
    private String title;
    // Note: file is handled via MultipartFile in controller, not in this DTO
}
