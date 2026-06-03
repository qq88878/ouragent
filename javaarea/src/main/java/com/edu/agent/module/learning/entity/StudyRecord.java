package com.edu.agent.module.learning.entity;

import com.edu.agent.common.base.BaseEntity;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.math.BigDecimal;

@Data
@EqualsAndHashCode(callSuper = true)
@TableName("study_record")
public class StudyRecord extends BaseEntity {

    private Long userId;

    private Long courseId;

    private Long knowledgeId;

    private Long pathStepId;

    /** CHAT / READ / PRACTICE / QUIZ */
    private String studyType;

    private Integer durationMinutes;

    private BigDecimal score;

    private String contentSummary;
}
