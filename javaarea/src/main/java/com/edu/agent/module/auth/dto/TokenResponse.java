package com.edu.agent.module.auth.dto;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class TokenResponse {

    private String accessToken;

    private String refreshToken;

    private Integer emailVerified;

    public TokenResponse(String accessToken, String refreshToken) {
        this(accessToken, refreshToken, null);
    }
}