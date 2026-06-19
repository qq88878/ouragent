package com.edu.agent.module.admin.controller;

import com.edu.agent.module.admin.dto.DashboardStatsDTO;
import com.edu.agent.module.admin.dto.SystemConfigDTO;
import com.edu.agent.module.admin.service.AdminService;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import com.edu.agent.common.result.Result;

@RestController
@RequestMapping("/admin")
public class AdminController {

    private final AdminService adminService;
    public AdminController(AdminService adminService) {
        this.adminService = adminService;
    }

    @PreAuthorize("hasAnyRole('ADMIN','TEACHER')")
    @GetMapping("/dashboard")
    public Result<DashboardStatsDTO> getDashboardStats() {
        return Result.success(adminService.getDashboardStats());
    }

    @PreAuthorize("hasRole('ADMIN')")
    @GetMapping("/system/health")
    public Result<SystemConfigDTO> getSystemHealth() {
        return Result.success(adminService.getSystemHealth());
    }
}
