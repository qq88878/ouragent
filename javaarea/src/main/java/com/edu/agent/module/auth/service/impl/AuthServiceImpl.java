package com.edu.agent.module.auth.service.impl;

import com.edu.agent.common.exception.BizException;
import com.edu.agent.common.result.ResultCode;
import com.edu.agent.common.service.EmailService;
import com.edu.agent.module.auth.dto.LoginRequest;
import com.edu.agent.module.auth.dto.RefreshRequest;
import com.edu.agent.module.auth.dto.RegisterRequest;
import com.edu.agent.module.auth.dto.TokenResponse;
import com.edu.agent.module.auth.service.AuthService;
import com.edu.agent.module.user.entity.User;
import com.edu.agent.module.user.mapper.UserMapper;
import com.edu.agent.security.JwtProvider;
import com.edu.agent.security.LoginUser;
import io.jsonwebtoken.Claims;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.TimeUnit;

@Service
public class AuthServiceImpl implements AuthService {
    private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(AuthServiceImpl.class);

    private final UserMapper userMapper;
    private final PasswordEncoder passwordEncoder;
    private final JwtProvider jwtProvider;
    private final RedisTemplate<String, Object> redisTemplate;
    private final EmailService emailService;
    public AuthServiceImpl(UserMapper userMapper, PasswordEncoder passwordEncoder, JwtProvider jwtProvider, RedisTemplate<String, Object> redisTemplate, EmailService emailService) {
        this.userMapper = userMapper;
        this.passwordEncoder = passwordEncoder;
        this.jwtProvider = jwtProvider;
        this.redisTemplate = redisTemplate;
        this.emailService = emailService;
    }

    @Override
    public void register(RegisterRequest request) {
        if (userMapper.selectByUsername(request.getUsername()) != null) {
            throw new BizException(ResultCode.USER_ALREADY_EXISTS);
        }
        if (userMapper.selectByEmail(request.getEmail()) != null) {
            throw new BizException(ResultCode.EMAIL_ALREADY_EXISTS);
        }
        if (request.getPassword() == null || request.getPassword().length() < 6) {
            throw new BizException(ResultCode.PASSWORD_TOO_WEAK);
        }

        User user = new User();
        user.setUsername(request.getUsername());
        user.setPassword(passwordEncoder.encode(request.getPassword()));
        user.setEmail(request.getEmail());
        user.setNickname(request.getNickname() != null ? request.getNickname() : request.getUsername());
        user.setRole(request.getRole() != null ? request.getRole() : "STUDENT");
        user.setEmailVerified(emailService.isConfigured() ? 0 : 1);

        try {
            userMapper.insert(user);
        } catch (DuplicateKeyException e) {
            if (e.getMessage() != null && e.getMessage().contains("uk_email")) {
                throw new BizException(ResultCode.EMAIL_ALREADY_EXISTS);
            }
            throw new BizException(ResultCode.USER_ALREADY_EXISTS);
        }

        try {
            sendVerificationCode(request.getEmail());
        } catch (Exception e) {
            log.warn("Failed to send verification email on register: {}", e.getMessage());
        }
    }

    @Override
    public TokenResponse login(LoginRequest request) {
        User user = userMapper.selectByUsername(request.getUsername());
        if (user == null || !passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            throw new BizException(ResultCode.INVALID_CREDENTIALS);
        }

        if (user.getStatus() != null && user.getStatus() == 0) {
            throw new BizException(ResultCode.FORBIDDEN, "账号已被禁用");
        }

        user.setLastLoginTime(LocalDateTime.now());
        if (user.getStatus() == null) {
            user.setStatus(1);
        }
        userMapper.updateById(user);

        String accessToken = jwtProvider.generateAccessToken(user);
        String refreshToken = jwtProvider.generateRefreshToken(user);

        return new TokenResponse(accessToken, refreshToken, user.getEmailVerified());
    }

    @Override
    public TokenResponse refresh(RefreshRequest request) {
        String refreshToken = request.getRefreshToken();

        // Check blacklist
        String blacklistKey = "blacklist:" + refreshToken;
        try {
        if (Boolean.TRUE.equals(redisTemplate.hasKey(blacklistKey))) {
            throw new BizException(ResultCode.UNAUTHORIZED, "Refresh Token已失效，请重新登录");
        }
        } catch (Exception e) {
            log.debug("Redis unavailable during refresh, skipping blacklist check: {}", e.getMessage());
        }

        // Validate refresh token
        if (jwtProvider.isTokenExpired(refreshToken)) {
            throw new BizException(ResultCode.UNAUTHORIZED, "Refresh Token已过期，请重新登录");
        }

        String username;
        try {
            username = jwtProvider.getUsernameFromToken(refreshToken);
        } catch (Exception e) {
            throw new BizException(ResultCode.UNAUTHORIZED, "Refresh Token无效");
        }

        User user = userMapper.selectByUsername(username);
        if (user == null) {
            throw new BizException(ResultCode.UNAUTHORIZED, "用户不存在");
        }

        if (user.getStatus() != null && user.getStatus() == 0) {
            throw new BizException(ResultCode.FORBIDDEN, "账号已被禁用");
        }

        // Blacklist old refresh token to prevent reuse
        try {
            Claims claims = jwtProvider.getClaimsFromToken(refreshToken);
            long expiration = claims.getExpiration().getTime();
            long ttl = expiration - System.currentTimeMillis();
            if (ttl > 0) {
                redisTemplate.opsForValue().set(blacklistKey, "1", ttl, TimeUnit.MILLISECONDS);
            }
        } catch (Exception e) {
            log.debug("Failed to blacklist old refresh token: {}", e.getMessage());
        }

        // Issue new tokens
        String newAccessToken = jwtProvider.generateAccessToken(user);
        String newRefreshToken = jwtProvider.generateRefreshToken(user);

        log.info("Token刷新成功: username={}", username);
        return new TokenResponse(newAccessToken, newRefreshToken, user.getEmailVerified());
    }

    @Override
    public void logout(String token) {
        String realToken = token.substring(7);
        try {
            Claims claims = jwtProvider.getClaimsFromToken(realToken);
            long expiration = claims.getExpiration().getTime();
            long ttl = expiration - System.currentTimeMillis();
            if (ttl > 0) {
                redisTemplate.opsForValue().set("blacklist:" + realToken, "1", ttl, TimeUnit.MILLISECONDS);
            }
        } catch (Exception e) {
            log.debug("Redis unavailable, token blacklist skipped: {}", e.getMessage());
        }
    }

    @Override
    public Object getCurrentUser() {
        Object principal = SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        if (principal instanceof LoginUser loginUser) {
            User user = loginUser.getUser();
            user.setPassword(null);
            return user;
        }
        return principal;
    }

    @Override
    public void sendVerificationCode(String email) {
        User user = userMapper.selectByEmail(email);
        if (user == null) {
            throw new BizException(ResultCode.NOT_FOUND, "该邮箱未注册");
        }
        if (user.getEmailVerified() != null && user.getEmailVerified() == 1) {
            throw new BizException(ResultCode.BAD_REQUEST, "邮箱已验证，无需重复验证");
        }

        String code = String.format("%06d", ThreadLocalRandom.current().nextInt(1000000));
        emailService.storeCode(email, code);
        emailService.sendVerificationCode(email, code);
    }

    @Override
    public void verifyEmail(String email, String code) {
        User user = userMapper.selectByEmail(email);
        if (user == null) {
            throw new BizException(ResultCode.NOT_FOUND, "该邮箱未注册");
        }
        if (user.getEmailVerified() != null && user.getEmailVerified() == 1) {
            throw new BizException(ResultCode.BAD_REQUEST, "邮箱已验证，无需重复验证");
        }

        String storedCode = emailService.getCode(email);
        if (storedCode == null) {
            throw new BizException(ResultCode.BAD_REQUEST, "验证码已过期，请重新获取");
        }
        if (!storedCode.equals(code)) {
            throw new BizException(ResultCode.BAD_REQUEST, "验证码错误");
        }

        user.setEmailVerified(1);
        userMapper.updateById(user);
        emailService.removeCode(email);
    }
}
