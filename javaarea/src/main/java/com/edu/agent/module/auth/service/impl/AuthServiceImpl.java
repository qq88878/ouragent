package com.edu.agent.module.auth.service.impl;

import com.edu.agent.module.auth.dto.LoginRequest;
import com.edu.agent.module.auth.dto.RegisterRequest;
import com.edu.agent.module.auth.dto.TokenResponse;
import com.edu.agent.module.auth.service.AuthService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {

    // TODO: 注入 UserMapper
    // TODO: 注入 PasswordEncoder (BCrypt)
    // TODO: 注入 JwtProvider
    // TODO: 注入 RedisTemplate

    @Override
    public void register(RegisterRequest request) {
        // TODO: 阶段一 - 验证用户名唯一性
        // TODO: 阶段一 - 验证邮箱唯一性
        // TODO: 阶段一 - 使用BCrypt加密密码
        // TODO: 阶段一 - 构建User实体并插入数据库
        throw new UnsupportedOperationException("Not implemented yet");
    }

    @Override
    public TokenResponse login(LoginRequest request) {
        // TODO: 阶段一 - 根据用户名查询用户
        // TODO: 阶段一 - 验证密码 (BCrypt matches)
        // TODO: 阶段一 - 生成JWT accessToken
        // TODO: 阶段一 - 生成JWT refreshToken
        // TODO: 阶段一 - 更新最后登录时间
        // TODO: 阶段一 - 返回TokenResponse
        throw new UnsupportedOperationException("Not implemented yet");
    }

    @Override
    public void logout(String token) {
        // TODO: 阶段一 - 解析token获取过期时间
        // TODO: 阶段一 - 将token加入Redis黑名单，设置与token相同的TTL
        throw new UnsupportedOperationException("Not implemented yet");
    }

    @Override
    public Object getCurrentUser() {
        // TODO: 阶段一 - 从SecurityContext获取当前认证信息
        // TODO: 阶段一 - 根据用户ID查询用户详情
        // TODO: 阶段一 - 返回UserDTO（排除密码字段）
        throw new UnsupportedOperationException("Not implemented yet");
    }
}
