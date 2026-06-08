package com.edu.agent.module.auth.service.impl;

import com.edu.agent.common.exception.BizException;
import com.edu.agent.common.result.ResultCode;
import com.edu.agent.module.auth.dto.LoginRequest;
import com.edu.agent.module.auth.dto.RegisterRequest;
import com.edu.agent.module.auth.dto.TokenResponse;
import com.edu.agent.module.auth.service.AuthService;
import com.edu.agent.module.user.entity.User;
import com.edu.agent.module.user.mapper.UserMapper;
import com.edu.agent.security.JwtProvider;
import io.jsonwebtoken.Claims;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.concurrent.TimeUnit;

@Slf4j
@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {

    private final UserMapper userMapper;
    private final PasswordEncoder passwordEncoder;
    private final JwtProvider jwtProvider;
    private final RedisTemplate<String, Object> redisTemplate;

    @Override
    public void register(RegisterRequest request) {
        if (userMapper.selectByUsername(request.getUsername()) != null) {
            throw new BizException(ResultCode.USER_ALREADY_EXISTS);
        }
        if (userMapper.selectByEmail(request.getEmail()) != null) {
            throw new BizException(ResultCode.EMAIL_ALREADY_EXISTS);
        }

        User user = new User();
        user.setUsername(request.getUsername());
        user.setPassword(passwordEncoder.encode(request.getPassword()));
        user.setEmail(request.getEmail());
        userMapper.insert(user);
    }

    @Override
    public TokenResponse login(LoginRequest request) {
        User user = userMapper.selectByUsername(request.getUsername());
        if (user == null || !passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            throw new BizException(ResultCode.INVALID_CREDENTIALS);
        }

        String accessToken = jwtProvider.generateAccessToken(user);
        String refreshToken = jwtProvider.generateRefreshToken(user);

        return new TokenResponse(accessToken, refreshToken);
    }

    @Override
    public void logout(String token) {
        String realToken = token.substring(7);
        Claims claims = jwtProvider.getClaimsFromToken(realToken);
        long expiration = claims.getExpiration().getTime();
        long ttl = expiration - System.currentTimeMillis();
        if (ttl > 0) {
            redisTemplate.opsForValue().set("blacklist:" + realToken, "1", ttl, TimeUnit.MILLISECONDS);
        }
    }

    @Override
    public Object getCurrentUser() {
        return SecurityContextHolder.getContext().getAuthentication().getPrincipal();
    }
}