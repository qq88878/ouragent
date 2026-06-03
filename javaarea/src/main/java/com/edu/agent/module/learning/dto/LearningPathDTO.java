package com.edu.agent.module.learning.dto;

import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

@Data
public class LearningPathDTO {

    private Long id;

    private Long userId;

    private Long courseId;

    private String title;

    private String description;

    private Integer totalSteps;

    private Integer completedSteps;

    private String status;

    private String generatedBy;

    private List<LearningPathStepDTO> steps;

    private LocalDateTime createTime;
}
