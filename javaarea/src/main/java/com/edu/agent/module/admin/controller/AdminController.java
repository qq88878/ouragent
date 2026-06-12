package com.edu.agent.module.admin.controller;

import com.edu.agent.common.result.Result;
import com.edu.agent.module.admin.dto.DashboardStatsDTO;
import com.edu.agent.module.admin.dto.SystemConfigDTO;
import com.edu.agent.module.admin.service.AdminService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/admin")
@RequiredArgsConstructor
public class AdminController {

    private final AdminService adminService;

    @GetMapping("/dashboard")
    public Result<DashboardStatsDTO> getDashboardStats() {
        return Result.success(adminService.getDashboardStats());
    }

    @GetMapping("/system/health")
    public Result<SystemConfigDTO> getSystemHealth() {
        return Result.success(adminService.getSystemHealth());
    }
}
