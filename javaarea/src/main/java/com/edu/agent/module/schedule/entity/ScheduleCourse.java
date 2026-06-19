package com.edu.agent.module.schedule.entity;

import com.edu.agent.common.base.BaseEntity;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = true)
@TableName("schedule_course")
public class ScheduleCourse extends BaseEntity {
    private Long userId;
    private String name;
    /** JSON: [1,2,3,...] */
    private String weekNumbers;
    /** JSON: [1,2,3,4,5,6,7] 1=周一 */
    private String dayOfWeeks;
    /** JSON: [0,1,2,...] */
    private String periodIndexes;
    private String location;
    private String remark;
}
