package com.edu.agent.module.learning.entity;

import com.edu.agent.common.base.BaseEntity;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = true)
@TableName("learning_path")
public class LearningPath extends BaseEntity {
    private Long userId;
    private Long courseId;
    private String title;
    private String description;
    private Integer totalSteps;
    private Integer completedSteps;
    private Integer status;  // 0=in_progress, 1=completed, 2=abandoned
}