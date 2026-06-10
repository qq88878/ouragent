package com.edu.agent.module.auth.service;

import com.edu.agent.module.auth.dto.LoginRequest;
import com.edu.agent.module.auth.dto.RegisterRequest;
import com.edu.agent.module.auth.dto.TokenResponse;

public interface AuthService {

    void register(RegisterRequest request);

    TokenResponse login(LoginRequest request);

    void logout(String token);

    Object getCurrentUser();

    void sendVerificationCode(String email);

    void verifyEmail(String email, String code);
}