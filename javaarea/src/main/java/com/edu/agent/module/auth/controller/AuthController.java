package com.edu.agent.module.auth.controller;

import com.edu.agent.common.result.Result;
import com.edu.agent.module.auth.dto.LoginRequest;
import com.edu.agent.module.auth.dto.RegisterRequest;
import com.edu.agent.module.auth.dto.TokenResponse;
import com.edu.agent.module.auth.service.AuthService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    @PostMapping("/register")
    public Result<Void> register(@Valid @RequestBody RegisterRequest request) {
        // TODO: 阶段一 - 调用authService.register()
        throw new UnsupportedOperationException("Not implemented yet");
    }

    @PostMapping("/login")
    public Result<TokenResponse> login(@Valid @RequestBody LoginRequest request) {
        // TODO: 阶段一 - 调用authService.login()
        throw new UnsupportedOperationException("Not implemented yet");
    }

    @PostMapping("/logout")
    public Result<Void> logout(@RequestHeader("Authorization") String token) {
        // TODO: 阶段一 - 将token加入Redis黑名单
        throw new UnsupportedOperationException("Not implemented yet");
    }

    @GetMapping("/me")
    public Result<Object> getCurrentUser() {
        // TODO: 阶段一 - 从SecurityContext获取当前用户
        throw new UnsupportedOperationException("Not implemented yet");
    }
}
