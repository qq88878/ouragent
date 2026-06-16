package com.edu.agent.module.schedule.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import lombok.Data;

import java.util.List;

@Data
public class SaveConfigRequest {
    @NotBlank(message = "开学日期不能为空")
    private String semesterStartDate;

    @NotEmpty(message = "时间段配置不能为空")
    private List<ScheduleConfigDTO.PeriodConfig> periodConfig;
}