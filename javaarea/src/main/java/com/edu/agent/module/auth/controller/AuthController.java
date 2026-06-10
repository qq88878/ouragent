package com.edu.agent.module.auth.controller;

import com.edu.agent.common.exception.BizException;
import com.edu.agent.common.result.Result;
import com.edu.agent.module.auth.dto.LoginRequest;
import com.edu.agent.module.auth.dto.RegisterRequest;
import com.edu.agent.module.auth.dto.TokenResponse;
import com.edu.agent.module.auth.service.AuthService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    @PostMapping("/register")
    public Result<Void> register(@Valid @RequestBody RegisterRequest request) {
        try {
            authService.register(request);
            return Result.success();
        } catch (BizException e) {
            return Result.fail(e.getResultCode());
        }
    }

    @PostMapping("/login")
    public Result<TokenResponse> login(@Valid @RequestBody LoginRequest request) {
        try {
            TokenResponse tokenResponse = authService.login(request);
            return Result.success(tokenResponse);
        } catch (BizException e) {
            return Result.fail(e.getResultCode());
        }
    }

    @PostMapping("/logout")
    public Result<Void> logout(@RequestHeader("Authorization") String token) {
        authService.logout(token);
        return Result.success();
    }

    @GetMapping("/me")
    public Result<Object> getCurrentUser() {
        return Result.success(authService.getCurrentUser());
    }

    @PostMapping("/send-verify-code")
    public Result<Void> sendVerifyCode(@RequestParam String email) {
        try {
            authService.sendVerificationCode(email);
            return Result.success();
        } catch (BizException e) {
            return Result.fail(e.getResultCode());
        }
    }

    @PostMapping("/verify-email")
    public Result<Void> verifyEmail(@RequestBody Map<String, String> body) {
        try {
            String email = body.get("email");
            String code = body.get("code");
            authService.verifyEmail(email, code);
            return Result.success();
        } catch (BizException e) {
            return Result.fail(e.getResultCode());
        }
    }
}