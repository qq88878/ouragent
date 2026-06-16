package com.edu.agent.module.schedule.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class ScheduleCourseDTO {
    private Long id;
    private String name;
    private List<Integer> weekNumbers;
    private List<Integer> dayOfWeeks;
    private List<Integer> periodIndexes;
}
