package com.edu.agent.module.admin.service.impl;

import com.edu.agent.module.admin.dto.DashboardStatsDTO;
import com.edu.agent.module.admin.dto.SystemConfigDTO;
import com.edu.agent.module.admin.service.AdminService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Slf4j
@Service
public class AdminServiceImpl implements AdminService {

    @Override
    public DashboardStatsDTO getDashboardStats() {
        // TODO phase 4 - query UserMapper, CourseMapper, ConversationMapper, KnowledgeMapper for counts
        throw new UnsupportedOperationException("Not implemented yet - TODO phase 4");
    }

    @Override
    public SystemConfigDTO getSystemHealth() {
        // TODO phase 4 - check agent service health, DB connection, Redis connection, uptime
        throw new UnsupportedOperationException("Not implemented yet - TODO phase 4");
    }
}
