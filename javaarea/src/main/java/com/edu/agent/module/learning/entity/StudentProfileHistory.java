package com.edu.agent.module.learning.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import com.edu.agent.common.base.BaseEntity;

@TableName("student_profile_history")
public class StudentProfileHistory extends BaseEntity {
    private Long userId;
    private String profileSnapshot; // JSON string
    private String changeSummary;
    private String triggerSource; // questionnaire|evaluation|chat|manual|ai_dimensions
    private Integer version;

    public Long getUserId() { return userId; }
    public void setUserId(Long userId) { this.userId = userId; }
    public String getProfileSnapshot() { return profileSnapshot; }
    public void setProfileSnapshot(String profileSnapshot) { this.profileSnapshot = profileSnapshot; }
    public String getChangeSummary() { return changeSummary; }
    public void setChangeSummary(String changeSummary) { this.changeSummary = changeSummary; }
    public String getTriggerSource() { return triggerSource; }
    public void setTriggerSource(String triggerSource) { this.triggerSource = triggerSource; }
    public Integer getVersion() { return version; }
    public void setVersion(Integer version) { this.version = version; }
}
