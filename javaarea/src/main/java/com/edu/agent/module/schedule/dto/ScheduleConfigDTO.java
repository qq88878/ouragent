package com.edu.agent.module.schedule.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class ScheduleConfigDTO {
    private Long id;
    private LocalDate semesterStartDate;
    private List<PeriodConfig> periodConfig;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class PeriodConfig {
        private String name;
        private String startTime;  // HH:mm
        private String endTime;    // HH:mm
    }
}
