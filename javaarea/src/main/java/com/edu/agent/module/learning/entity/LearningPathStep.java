package com.edu.agent.module.learning.entity;

import com.edu.agent.common.base.BaseEntity;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = true)
@TableName("learning_path_step")
public class LearningPathStep extends BaseEntity {
    private Long pathId;
    private Integer stepOrder;
    private String title;
    private String description;
    private Long knowledgeBaseId;
    private Integer status;  // 0=pending, 1=in_progress, 2=completed
}