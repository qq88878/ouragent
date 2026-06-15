package com.edu.agent.module.knowledge.dto;

import lombok.Data;

import java.util.List;

@Data
public class BatchApproveDTO {
    private List<Long> ids;
    private boolean approved;
    private String remark;
}
