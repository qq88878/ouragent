package com.edu.agent.module.learning.entity;

import com.edu.agent.common.base.BaseEntity;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = true)
@TableName("student_profile")
public class StudentProfile extends BaseEntity {
    private Long userId;
    private String learningStyle;  // VISUAL / AUDITORY / READING / KINESTHETIC
    private String strengths;
    private String weaknesses;
    private String interests;
    private String gradeLevel;
    private String preferences;  // JSON
}