package com.edu.agent.module.schedule.entity;

import com.edu.agent.common.base.BaseEntity;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.time.LocalDate;

@Data
@EqualsAndHashCode(callSuper = true)
@TableName("schedule_config")
public class ScheduleConfig extends BaseEntity {
    private Long userId;
    private LocalDate semesterStartDate;
    /** JSON: [{name, startTime, endTime}] */
    private String periodConfig;
}
