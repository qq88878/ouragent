package com.edu.agent.module.schedule.entity;

import com.edu.agent.common.base.BaseEntity;
import com.baomidou.mybatisplus.annotation.TableName;

@TableName("schedule_course")
public class ScheduleCourse extends BaseEntity {
    private Long userId;
    private String name;
    private String weekNumbers;
    private String dayOfWeeks;
    private String periodIndexes;

    public ScheduleCourse() {}

    public Long getUserId() { return this.userId; }
    public String getName() { return this.name; }
    public String getWeekNumbers() { return this.weekNumbers; }
    public String getDayOfWeeks() { return this.dayOfWeeks; }
    public String getPeriodIndexes() { return this.periodIndexes; }

    public void setUserId(Long userId) { this.userId = userId; }
    public void setName(String name) { this.name = name; }
    public void setWeekNumbers(String weekNumbers) { this.weekNumbers = weekNumbers; }
    public void setDayOfWeeks(String dayOfWeeks) { this.dayOfWeeks = dayOfWeeks; }
    public void setPeriodIndexes(String periodIndexes) { this.periodIndexes = periodIndexes; }
}
