package com.edu.agent.module.admin.dto;

import lombok.Data;

@Data
public class SystemConfigDTO {

    private String agentStatus;

    private String agentUrl;

    private String dbStatus;

    private String redisStatus;

    private String uptime;
}
