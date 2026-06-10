package com.edu.agent.module.user.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import com.edu.agent.common.base.BaseEntity;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.time.LocalDateTime;

@Data
@EqualsAndHashCode(callSuper = true)
@TableName("user")
public class User extends BaseEntity {

    private String username;

    private String password;

    private String nickname;

    private String email;

    private String phone;

    private String avatar;

    private String role;

    private Integer status;

    private Integer emailVerified;

    private LocalDateTime lastLoginTime;
}