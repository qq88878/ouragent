package com.edu.agent.module.schedule.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import lombok.Data;

import java.util.List;

@Data
public class CreateCourseRequest {
    @NotBlank(message = "课程名称不能为空")
    private String name;

    @NotEmpty(message = "周数不能为空")
    private List<Integer> weekNumbers;

    @NotEmpty(message = "星期不能为空")
    private List<Integer> dayOfWeeks;

    @NotEmpty(message = "时间段不能为空")
    private List<Integer> periodIndexes;
    private String location;
    private String remark;
}
