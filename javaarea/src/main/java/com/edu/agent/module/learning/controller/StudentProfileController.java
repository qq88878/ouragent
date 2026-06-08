package com.edu.agent.module.learning.controller;

import com.edu.agent.common.result.Result;
import com.edu.agent.module.learning.entity.StudentProfile;
import com.edu.agent.module.learning.service.StudentProfileService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/profile")
@RequiredArgsConstructor
public class StudentProfileController {

    private final StudentProfileService studentProfileService;

    @GetMapping("/")
    public Result<StudentProfile> getProfile() {
        // TODO phase 4 - get current userId from SecurityContext, call studentProfileService.getProfile()
        throw new UnsupportedOperationException("Not implemented yet - TODO phase 4");
    }

    @PutMapping("/")
    public Result<Void> updateProfile(@RequestBody StudentProfile profile) {
        // TODO phase 4 - get current userId from SecurityContext, call studentProfileService.updateProfile()
        throw new UnsupportedOperationException("Not implemented yet - TODO phase 4");
    }

    @GetMapping("/radar")
    public Result<Map<String, Object>> getRadarData() {
        // TODO phase 4 - get current userId from SecurityContext, call studentProfileService.getRadarData()
        throw new UnsupportedOperationException("Not implemented yet - TODO phase 4");
    }
}