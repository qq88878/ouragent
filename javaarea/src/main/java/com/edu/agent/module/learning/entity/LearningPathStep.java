package com.edu.agent.module.learning.entity;

import com.edu.agent.common.base.BaseEntity;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.math.BigDecimal;

@Data
@EqualsAndHashCode(callSuper = true)
@TableName("learning_path_step")
public class LearningPathStep extends BaseEntity {

    private Long pathId;

    private Integer stepOrder;

    private String title;

    private String description;

    /** READ / PRACTICE / QUIZ / PROJECT / VIDEO */
    private String stepType;

    private BigDecimal estimatedHours;

    /** PENDING / IN_PROGRESS / COMPLETED / SKIPPED */
    private String status;

    /** JSON array of knowledge IDs */
    private String knowledgeIds;
}
