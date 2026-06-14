package com.edu.agent.module.learning.controller;

import com.edu.agent.common.result.Result;
import com.edu.agent.module.learning.entity.StudentProfile;
import com.edu.agent.module.learning.service.StudentProfileService;
import com.edu.agent.security.LoginUser;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/profile")
@RequiredArgsConstructor
@PreAuthorize("hasRole('STUDENT')")
public class StudentProfileController {

    private final StudentProfileService studentProfileService;

    @GetMapping("/")
    public Result<StudentProfile> getProfile() {
        LoginUser loginUser = (LoginUser) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        return Result.success(studentProfileService.getProfile(loginUser.getUser().getId()));
    }

    @PutMapping("/")
    public Result<Void> updateProfile(@RequestBody StudentProfile profile) {
        LoginUser loginUser = (LoginUser) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        studentProfileService.updateProfile(loginUser.getUser().getId(), profile);
        return Result.success();
    }

    @GetMapping("/radar")
    public Result<Map<String, Object>> getRadarData() {
        LoginUser loginUser = (LoginUser) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        return Result.success(studentProfileService.getRadarData(loginUser.getUser().getId()));
    }
}
