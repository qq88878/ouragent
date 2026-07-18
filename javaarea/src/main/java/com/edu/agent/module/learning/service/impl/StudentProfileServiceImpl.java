package com.edu.agent.module.learning.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.edu.agent.common.exception.BizException;
import com.edu.agent.common.result.ResultCode;
import com.edu.agent.module.learning.entity.StudentProfile;
import com.edu.agent.module.learning.mapper.StudentProfileMapper;
import com.edu.agent.module.learning.service.StudentProfileService;
import com.edu.agent.module.chat.service.client.AgentServiceClient;
import com.edu.agent.module.learning.service.ProfileHistoryService;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashMap;
import java.util.Map;

@Service
public class StudentProfileServiceImpl
        extends ServiceImpl<StudentProfileMapper, StudentProfile>
        implements StudentProfileService {
    private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(StudentProfileServiceImpl.class);
    private final AgentServiceClient agentServiceClient;
    private ProfileHistoryService profileHistoryService;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public StudentProfileServiceImpl(AgentServiceClient agentServiceClient) {
        this.agentServiceClient = agentServiceClient;
    }

    @org.springframework.beans.factory.annotation.Autowired(required = false)
    public void setProfileHistoryService(ProfileHistoryService profileHistoryService) {
        this.profileHistoryService = profileHistoryService;
    }

    @Override
    public StudentProfile getProfile(Long userId) {
        LambdaQueryWrapper<StudentProfile> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(StudentProfile::getUserId, userId);
        StudentProfile profile = getOne(wrapper);
        if (profile == null) {
            profile = new StudentProfile();
            profile.setUserId(userId);
            profile.setLearningStyle("VISUAL");
            profile.setStrengths("");
            profile.setWeaknesses("");
            profile.setInterests("");
            profile.setGradeLevel("BEGINNER");
            save(profile);
        }
        return profile;
    }

    @Override
    @Transactional
    public void updateProfile(Long userId, StudentProfile profile) {
        LambdaQueryWrapper<StudentProfile> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(StudentProfile::getUserId, userId);
        StudentProfile existing = getOne(wrapper);

        if (existing == null) {
            profile.setUserId(userId);
            save(profile);
        } else {
            if (profile.getLearningStyle() != null) {
                existing.setLearningStyle(profile.getLearningStyle());
            }
            if (profile.getStrengths() != null) {
                existing.setStrengths(profile.getStrengths());
            }
            if (profile.getWeaknesses() != null) {
                existing.setWeaknesses(profile.getWeaknesses());
            }
            if (profile.getInterests() != null) {
                existing.setInterests(profile.getInterests());
            }
            if (profile.getGradeLevel() != null) {
                existing.setGradeLevel(profile.getGradeLevel());
            }
            if (profile.getPreferences() != null) {
                existing.setPreferences(profile.getPreferences());
            }
            // Save profile history snapshot before update
            saveProfileHistory(userId, existing, "manual");
            updateById(existing);
        }

        log.info("学生画像更新成功: userId={}", userId);
    }

    @Override
    public Map<String, Object> getRadarData(Long userId) {
        StudentProfile profile = getProfile(userId);

        Map<String, Object> radarData = new HashMap<>();
        radarData.put("learningStyle", profile.getLearningStyle());
        radarData.put("strengths", profile.getStrengths());
        radarData.put("weaknesses", profile.getWeaknesses());
        radarData.put("interests", profile.getInterests());
        radarData.put("gradeLevel", profile.getGradeLevel());

        // Fast-path: use keyword-based dimensions for instant response
        // AI deep analysis available via /agent/profile/dimensions
        Map<String, Object> dimensions = new HashMap<>();
        String strengths = profile.getStrengths() != null ? profile.getStrengths() : "";
        String weaknesses = profile.getWeaknesses() != null ? profile.getWeaknesses() : "";
        dimensions.put("\u7406\u8bba\u77e5\u8bc6", calculateDimension(strengths, weaknesses, "\u7406\u8bba"));
        dimensions.put("\u5b9e\u8df5\u80fd\u529b", calculateDimension(strengths, weaknesses, "\u5b9e\u8df5"));
        dimensions.put("\u95ee\u9898\u89e3\u51b3", calculateDimension(strengths, weaknesses, "\u95ee\u9898"));
        dimensions.put("\u521b\u65b0\u601d\u7ef4", calculateDimension(strengths, weaknesses, "\u521b\u65b0"));
        dimensions.put("\u534f\u4f5c\u80fd\u529b", calculateDimension(strengths, weaknesses, "\u534f\u4f5c"));

        radarData.put("dimensions", dimensions);
        radarData.put("source", "keyword");
        return radarData;
    }




    private void saveProfileHistory(Long userId, StudentProfile profile, String triggerSource) {
        if (profileHistoryService == null) return;
        try {
            Map<String, Object> snapshot = new HashMap<>();
            snapshot.put("learningStyle", profile.getLearningStyle());
            snapshot.put("strengths", profile.getStrengths());
            snapshot.put("weaknesses", profile.getWeaknesses());
            snapshot.put("interests", profile.getInterests());
            snapshot.put("gradeLevel", profile.getGradeLevel());
            snapshot.put("preferences", profile.getPreferences());
            String json = objectMapper.writeValueAsString(snapshot);
            profileHistoryService.saveHistory(userId, json, "Profile updated via " + triggerSource, triggerSource);
        } catch (Exception e) {
            log.warn("Failed to save profile history: {}", e.getMessage());
        }
    }

    private int calculateDimension(String strengths, String weaknesses, String keyword) {
        int base = 60;
        if (strengths.contains(keyword)) {
            base += 20;
        }
        if (weaknesses.contains(keyword)) {
            base -= 20;
        }
        return Math.max(0, Math.min(100, base));
    }
}
