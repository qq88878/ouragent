package com.edu.agent.module.learning.entity;

import com.edu.agent.common.base.BaseEntity;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@EqualsAndHashCode(callSuper = true)
@TableName("student_profile")
public class StudentProfile extends BaseEntity {

    private Long userId;

    /** BEGINNER / INTERMEDIATE / ADVANCED */
    private String knowledgeLevel;

    /** VISUAL / READING / HANDS_ON / MIXED */
    private String learningStyle;

    /** JSON array */
    private String strongPoints;

    /** JSON array */
    private String weakPoints;

    /** JSON array */
    private String interests;

    private BigDecimal totalStudyHours;

    private Integer profileVersion;

    private LocalDateTime lastAssessmentTime;
}
