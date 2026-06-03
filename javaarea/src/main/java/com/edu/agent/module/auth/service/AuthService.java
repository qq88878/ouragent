package com.edu.agent.module.auth.service;

import com.edu.agent.module.auth.dto.LoginRequest;
import com.edu.agent.module.auth.dto.RegisterRequest;
import com.edu.agent.module.auth.dto.TokenResponse;

public interface AuthService {

    /**
     * 用户注册
     *
     * @param request 注册请求
     */
    void register(RegisterRequest request);

    /**
     * 用户登录
     *
     * @param request 登录请求
     * @return Token响应
     */
    TokenResponse login(LoginRequest request);

    /**
     * 用户登出
     *
     * @param token JWT token
     */
    void logout(String token);

    /**
     * 获取当前登录用户信息
     *
     * @return 当前用户信息
     */
    Object getCurrentUser();
}
