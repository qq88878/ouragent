package com.edu.agent.module.learning.dto;

import lombok.Data;

import java.math.BigDecimal;

@Data
public class LearningPathStepDTO {

    private Long id;

    private Integer stepOrder;

    private String title;

    private String description;

    private Long knowledgeBaseId;

    private Integer status;  // 0=pending, 1=in_progress, 2=completed
}
