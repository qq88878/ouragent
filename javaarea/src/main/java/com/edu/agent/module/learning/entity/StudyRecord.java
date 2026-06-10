package com.edu.agent.module.learning.entity;

import com.edu.agent.common.base.BaseEntity;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = true)
@TableName("study_record")
public class StudyRecord extends BaseEntity {
    private Long userId;
    private Long courseId;
    private Long sessionId;
    private Integer duration;  // seconds
    private Integer interactionCount;
    private String summary;
}