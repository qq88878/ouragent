package com.edu.agent.module.learning.dto;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class StudyRecordDTO {

    private Long id;

    private Long courseId;

    private String courseName;

    private String studyType;

    private Integer durationMinutes;

    private BigDecimal score;

    private String contentSummary;

    private LocalDateTime createTime;
}
