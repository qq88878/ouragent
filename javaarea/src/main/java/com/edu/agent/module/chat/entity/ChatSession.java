package com.edu.agent.module.chat.entity;

import com.edu.agent.common.base.BaseEntity;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = true)
@TableName("chat_session")
public class ChatSession extends BaseEntity {
    private Long userId;
    private String title;
    private String sessionType;  // GENERAL / LEARNING / EVALUATION
    private Long courseId;
    private Integer status;      // 1=active, 0=closed
    private Integer messageCount;
}
