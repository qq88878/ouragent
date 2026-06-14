package com.edu.agent.module.admin.dto;

import lombok.Data;

@Data
public class DashboardStatsDTO {

    private Integer totalUsers;

    private Integer totalTeachers;

    private Integer totalStudents;

    private Integer totalCourses;

    private Long totalConversations;

    private Integer activeStudentsToday;

    private Integer totalKnowledgeItems;
    
    private Integer totalPaths;
}
