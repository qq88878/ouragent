package com.edu.agent.module.learning.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import com.edu.agent.common.base.BaseEntity;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = true)
@TableName("student_profile_questionnaire")
public class StudentProfileQuestionnaire extends BaseEntity {
    private Long userId;
    private String questionnaireData;  // JSON string for MyBatis-Plus
    private Integer isCompleted;       // 0=未完成 1=已完成
}
