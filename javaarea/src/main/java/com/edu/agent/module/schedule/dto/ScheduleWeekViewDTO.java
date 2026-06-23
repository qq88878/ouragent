package com.edu.agent.module.schedule.dto;

import java.time.LocalDate;
import java.util.List;

public class ScheduleWeekViewDTO {
    private Integer weekNumber;
    private LocalDate weekStartDate;
    private LocalDate weekEndDate;
    private List<DaySchedule> days;

    public static class DaySchedule {
        private Integer dayOfWeek;
        private LocalDate date;
        private String dayLabel;
        private List<PeriodSlot> periods;

        public DaySchedule() {}
        public Integer getDayOfWeek() { return this.dayOfWeek; }
        public LocalDate getDate() { return this.date; }
        public String getDayLabel() { return this.dayLabel; }
        public List<PeriodSlot> getPeriods() { return this.periods; }
        public void setDayOfWeek(Integer dayOfWeek) { this.dayOfWeek = dayOfWeek; }
        public void setDate(LocalDate date) { this.date = date; }
        public void setDayLabel(String dayLabel) { this.dayLabel = dayLabel; }
        public void setPeriods(List<PeriodSlot> periods) { this.periods = periods; }
    }

    public static class PeriodSlot {
        private Integer periodIndex;
        private String periodName;
        private String startTime;
        private String endTime;
        private String courseName;
        private Long courseId;

        public PeriodSlot() {}
        public Integer getPeriodIndex() { return this.periodIndex; }
        public String getPeriodName() { return this.periodName; }
        public String getStartTime() { return this.startTime; }
        public String getEndTime() { return this.endTime; }
        public String getCourseName() { return this.courseName; }
        public Long getCourseId() { return this.courseId; }
        public void setPeriodIndex(Integer periodIndex) { this.periodIndex = periodIndex; }
        public void setPeriodName(String periodName) { this.periodName = periodName; }
        public void setStartTime(String startTime) { this.startTime = startTime; }
        public void setEndTime(String endTime) { this.endTime = endTime; }
        public void setCourseName(String courseName) { this.courseName = courseName; }
        public void setCourseId(Long courseId) { this.courseId = courseId; }
    }

    public ScheduleWeekViewDTO() {}
    public Integer getWeekNumber() { return this.weekNumber; }
    public LocalDate getWeekStartDate() { return this.weekStartDate; }
    public LocalDate getWeekEndDate() { return this.weekEndDate; }
    public List<DaySchedule> getDays() { return this.days; }
    public void setWeekNumber(Integer weekNumber) { this.weekNumber = weekNumber; }
    public void setWeekStartDate(LocalDate weekStartDate) { this.weekStartDate = weekStartDate; }
    public void setWeekEndDate(LocalDate weekEndDate) { this.weekEndDate = weekEndDate; }
    public void setDays(List<DaySchedule> days) { this.days = days; }
}
