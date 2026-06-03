package com.edu.agent.module.learning.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class LearningPathGenerateRequest {

    @NotNull
    private Long courseId;

    private String goal;

    private String currentLevel;
}
