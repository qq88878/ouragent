package com.edu.agent.module.course.dto;

import lombok.Data;

@Data
public class CourseQueryDTO {
    private String category;
    private String difficulty;
    private String keyword;
    private Integer page = 1;
    private Integer size = 10;

    private Long teacherId;
}
