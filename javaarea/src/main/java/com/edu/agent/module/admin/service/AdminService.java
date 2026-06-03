package com.edu.agent.module.admin.service;

import com.edu.agent.module.admin.dto.DashboardStatsDTO;
import com.edu.agent.module.admin.dto.SystemConfigDTO;

public interface AdminService {

    /**
     * Get aggregated dashboard statistics.
     */
    DashboardStatsDTO getDashboardStats();

    /**
     * Get system health and configuration status.
     */
    SystemConfigDTO getSystemHealth();
}
