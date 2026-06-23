package com.edu.agent.module.schedule.dto;

import java.util.List;

public class ScheduleCourseDTO {
    private Long id;
    private String name;
    private List<Integer> weekNumbers;
    private List<Integer> dayOfWeeks;
    private List<Integer> periodIndexes;

    public ScheduleCourseDTO() {}

    public ScheduleCourseDTO(Long id, String name, List<Integer> weekNumbers, List<Integer> dayOfWeeks, List<Integer> periodIndexes) {
        this.id = id;
        this.name = name;
        this.weekNumbers = weekNumbers;
        this.dayOfWeeks = dayOfWeeks;
        this.periodIndexes = periodIndexes;
    }

    public Long getId() { return this.id; }
    public String getName() { return this.name; }
    public List<Integer> getWeekNumbers() { return this.weekNumbers; }
    public List<Integer> getDayOfWeeks() { return this.dayOfWeeks; }
    public List<Integer> getPeriodIndexes() { return this.periodIndexes; }

    public void setId(Long id) { this.id = id; }
    public void setName(String name) { this.name = name; }
    public void setWeekNumbers(List<Integer> weekNumbers) { this.weekNumbers = weekNumbers; }
    public void setDayOfWeeks(List<Integer> dayOfWeeks) { this.dayOfWeeks = dayOfWeeks; }
    public void setPeriodIndexes(List<Integer> periodIndexes) { this.periodIndexes = periodIndexes; }
}
