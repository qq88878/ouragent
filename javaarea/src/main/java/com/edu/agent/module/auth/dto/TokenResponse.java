package com.edu.agent.module.auth.dto;

import lombok.Data;

@Data
public class TokenResponse {

    private String accessToken;

    private String refreshToken;

    private Long expiresIn;
}
