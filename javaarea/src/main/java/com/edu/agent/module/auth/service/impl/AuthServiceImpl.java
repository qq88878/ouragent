package com.edu.agent.module.auth.service.impl;

import com.edu.agent.common.exception.BizException;
import com.edu.agent.common.result.ResultCode;
import com.edu.agent.common.service.EmailService;
import com.edu.agent.module.auth.dto.LoginRequest;
import com.edu.agent.module.auth.dto.RegisterRequest;
import com.edu.agent.module.auth.dto.TokenResponse;
import com.edu.agent.module.auth.service.AuthService;
import com.edu.agent.module.user.entity.User;
import com.edu.agent.module.user.mapper.UserMapper;
import com.edu.agent.security.JwtProvider;
import com.edu.agent.security.LoginUser;
import io.jsonwebtoken.Claims;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.TimeUnit;

@Slf4j
@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {

    private final UserMapper userMapper;
    private final PasswordEncoder passwordEncoder;
    private final JwtProvider jwtProvider;
    private final RedisTemplate<String, Object> redisTemplate;
    private final EmailService emailService;

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
        userMapper.insert(user);

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

        if (!emailService.isConfigured()) {
            throw new BizException(ResultCode.INTERNAL_ERROR, "邮件服务未配置，请联系管理员");
        }

        String code = String.format("%06d", ThreadLocalRandom.current().nextInt(1000000));
        try {
            redisTemplate.opsForValue().set("email:code:" + email, code, 5, TimeUnit.MINUTES);
        } catch (Exception e) {
            log.debug("Redis unavailable during code storage: {}", e.getMessage());
        }
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

        String storedCode;
        try {
            storedCode = (String) redisTemplate.opsForValue().get("email:code:" + email);
        } catch (Exception e) {
            throw new BizException(ResultCode.INTERNAL_ERROR, "验证服务暂不可用，请稍后重试");
        }

        if (storedCode == null) {
            throw new BizException(ResultCode.BAD_REQUEST, "验证码已过期，请重新获取");
        }
        if (!storedCode.equals(code)) {
            throw new BizException(ResultCode.BAD_REQUEST, "验证码错误");
        }

        user.setEmailVerified(1);
        userMapper.updateById(user);

        try {
            redisTemplate.delete("email:code:" + email);
        } catch (Exception ignored) { }
    }
}