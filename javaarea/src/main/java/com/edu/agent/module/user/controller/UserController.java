package com.edu.agent.module.user.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.edu.agent.common.result.Result;
import com.edu.agent.module.user.dto.UserDTO;
import com.edu.agent.module.user.service.UserService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/users")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    @GetMapping("/me")
    public Result<UserDTO> getCurrentUser() {
        // TODO: 阶段一 - 调用userService.getCurrentUser()
        throw new UnsupportedOperationException("Not implemented yet");
    }

    @PutMapping("/me")
    public Result<Void> updateCurrentUser(@RequestBody UserDTO dto) {
        // TODO: 阶段一 - 获取当前用户ID并调用userService.updateUser()
        throw new UnsupportedOperationException("Not implemented yet");
    }

    @GetMapping("/")
    public Result<IPage<UserDTO>> listUsers(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        // TODO: 阶段一 - 需要ADMIN角色，调用userService.listUsers()
        throw new UnsupportedOperationException("Not implemented yet");
    }

    @GetMapping("/{id}")
    public Result<UserDTO> getUserById(@PathVariable Long id) {
        // TODO: 阶段一 - 需要ADMIN角色，调用userService.getUserById()
        throw new UnsupportedOperationException("Not implemented yet");
    }

    @PutMapping("/{id}/status")
    public Result<Void> updateStatus(@PathVariable Long id, @RequestParam Integer status) {
        // TODO: 阶段一 - 需要ADMIN角色，调用userService.updateStatus()
        throw new UnsupportedOperationException("Not implemented yet");
    }
}