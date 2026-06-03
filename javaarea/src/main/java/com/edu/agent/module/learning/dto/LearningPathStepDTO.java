package com.edu.agent.module.learning.dto;

import lombok.Data;

import java.math.BigDecimal;

@Data
public class LearningPathStepDTO {

    private Long id;

    private Integer stepOrder;

    private String title;

    private String description;

    private String stepType;

    private BigDecimal estimatedHours;

    private String status;

    private String knowledgeIds;
}
