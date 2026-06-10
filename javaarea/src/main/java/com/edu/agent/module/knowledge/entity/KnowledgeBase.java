package com.edu.agent.module.knowledge.entity;

import com.edu.agent.common.base.BaseEntity;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = true)
@TableName("knowledge_base")
public class KnowledgeBase extends BaseEntity {
    private Long courseId;
    private String name;
    private String description;
    private String filePath;
    private String fileType;
    private Long fileSize;
    private Integer status;  // 0=pending, 1=indexed, 2=failed
}