package com.edu.agent.module.course.entity;

import com.edu.agent.common.base.BaseEntity;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = true)
@TableName("course")
public class Course extends BaseEntity {
    private String title;
    private String description;
    private String coverImage;
    private Long teacherId;
    private String category;
    private String difficulty;  // BEGINNER / INTERMEDIATE / ADVANCED
    private Integer status;     // 1=published, 0=draft
    private Integer studentCount;
}
