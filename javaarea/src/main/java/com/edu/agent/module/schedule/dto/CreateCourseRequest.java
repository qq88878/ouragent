package com.edu.agent.module.schedule.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import java.util.List;

public class CreateCourseRequest {
    @NotBlank(message = "课程名称不能为空")
    private String name;
    @NotEmpty(message = "周数不能为空")
    private List<Integer> weekNumbers;
    @NotEmpty(message = "星期不能为空")
    private List<Integer> dayOfWeeks;
    @NotEmpty(message = "时间段不能为空")
    private List<Integer> periodIndexes;

    public CreateCourseRequest() {}

    public String getName() { return this.name; }
    public List<Integer> getWeekNumbers() { return this.weekNumbers; }
    public List<Integer> getDayOfWeeks() { return this.dayOfWeeks; }
    public List<Integer> getPeriodIndexes() { return this.periodIndexes; }

    public void setName(String name) { this.name = name; }
    public void setWeekNumbers(List<Integer> weekNumbers) { this.weekNumbers = weekNumbers; }
    public void setDayOfWeeks(List<Integer> dayOfWeeks) { this.dayOfWeeks = dayOfWeeks; }
    public void setPeriodIndexes(List<Integer> periodIndexes) { this.periodIndexes = periodIndexes; }
}
