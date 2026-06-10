package com.edu.agent.module.learning.dto;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class StudyRecordDTO {

    private Long id;

    private Long courseId;

    private String courseName;

    private Long sessionId;

    private Integer duration;  // seconds

    private Integer interactionCount;

    private String summary;

    private LocalDateTime createTime;
}
