package com.edu.agent.module.schedule.dto;

import lombok.Data;

import java.time.LocalDate;
import java.util.List;

@Data
public class ScheduleWeekViewDTO {
    private Integer weekNumber;
    private LocalDate weekStartDate;
    private LocalDate weekEndDate;
    private List<DaySchedule> days;

    @Data
    public static class DaySchedule {
        private Integer dayOfWeek;          // 1=周一, 7=周日
        private LocalDate date;             // 实际日期
        private String dayLabel;            // 周几 或 "非本周"
        private List<PeriodSlot> periods;
    }

    @Data
    public static class PeriodSlot {
        private Integer periodIndex;
        private String periodName;
        private String startTime;
        private String endTime;
        private String courseName;          // null表示空闲
    }
}
