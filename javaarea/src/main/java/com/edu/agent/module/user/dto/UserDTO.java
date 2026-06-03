package com.edu.agent.module.user.dto;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class UserDTO {

    private Long id;

    private String username;

    private String nickname;

    private String email;

    private String phone;

    private String avatar;

    private String role;

    private Integer status;

    private LocalDateTime lastLoginTime;
}
