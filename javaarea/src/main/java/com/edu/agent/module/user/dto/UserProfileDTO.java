package com.edu.agent.module.user.dto;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class UserProfileDTO {

    private Long id;

    private String username;

    private String nickname;

    private String email;

    private String phone;

    private String avatar;

    private String role;

    private Integer status;

    private LocalDateTime lastLoginTime;

    /** 累计学习时长（小时） */
    private Double totalStudyHours;

    /** 已加入课程数 */
    private Integer courseCount;

    /** 学习路径数 */
    private Integer pathCount;

    /** 对话次数 */
    private Integer chatCount;
}
