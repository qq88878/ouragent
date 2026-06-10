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
        return Result.success(userService.getCurrentUser());
    }

    @PutMapping("/me")
    public Result<Void> updateCurrentUser(@RequestBody UserDTO dto) {
        UserDTO current = userService.getCurrentUser();
        userService.updateUser(current.getId(), dto);
        return Result.success();
    }

    @GetMapping("/")
    public Result<IPage<UserDTO>> listUsers(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        return Result.success(userService.listUsers(page, size));
    }

    @GetMapping("/{id}")
    public Result<UserDTO> getUserById(@PathVariable Long id) {
        return Result.success(userService.getUserById(id));
    }

    @PutMapping("/{id}/status")
    public Result<Void> updateStatus(@PathVariable Long id, @RequestParam Integer status) {
        userService.updateStatus(id, status);
        return Result.success();
    }
}