package com.edu.agent.module.course.dto;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class CourseDTO {
    private Long id;
    private String title;
    private String description;
    private String coverImage;
    private Long teacherId;
    private String teacherName;
    private String category;
    private String difficulty;
    private Integer status;
    private Integer studentCount;
    private LocalDateTime createTime;
}
