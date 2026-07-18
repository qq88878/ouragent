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

        Map<String, Object> dimensions = new HashMap<>();

        // Try AI-powered dimension scoring from Python Agent
        try {
            Map<String, Object> profileMap = new HashMap<>();
            profileMap.put("learning_style", profile.getLearningStyle());
            profileMap.put("grade_level", profile.getGradeLevel());
            profileMap.put("strengths", profile.getStrengths());
            profileMap.put("weaknesses", profile.getWeaknesses());
            profileMap.put("interests", profile.getInterests());
            Map<String, Object> aiResult = agentServiceClient.analyzeProfileDimensions(
                String.valueOf(userId), profileMap,
                java.util.Collections.emptyList(),
                java.util.Collections.emptyList(),
                java.util.Collections.emptyMap(),
                java.util.Collections.emptyMap()
            );
            if (aiResult != null && aiResult.containsKey("dimensions")) {
                @SuppressWarnings("unchecked")
                Map<String, Object> aiDims = (Map<String, Object>) aiResult.get("dimensions");
                if (aiDims != null && !aiDims.isEmpty()) {
                    // Map English dimension keys to Chinese for frontend display
                    java.util.Map<String, String> keyMap = new HashMap<>();
                    keyMap.put("theoretical_knowledge", "理论知识");
                    keyMap.put("practical_ability", "实践能力");
                    keyMap.put("problem_solving", "问题解决");
                    keyMap.put("innovative_thinking", "创新思维");
                    keyMap.put("collaboration", "协作能力");
                    for (Map.Entry<String, Object> entry : aiDims.entrySet()) {
                        Object val = entry.getValue();
                        String key = keyMap.getOrDefault(entry.getKey(), entry.getKey());
                        if (val instanceof Map) {
                            @SuppressWarnings("unchecked")
                            Map<String, Object> dimObj = (Map<String, Object>) val;
                            Object score = dimObj.get("score");
                            dimensions.put(key, score != null ? score : 50);
                        } else {
                            dimensions.put(key, val != null ? val : 50);
                        }
                    }
                    radarData.put("source", "ai");
                    if (aiResult.containsKey("overall_assessment")) {
                        radarData.put("assessment", aiResult.get("overall_assessment"));
                    }
                }
            }
        } catch (Exception e) {
            log.warn("AI dimension scoring failed, falling back to keyword heuristic: userId={}", userId, e);
        }

        // Fallback: keyword-based dimensions if AI fails
        if (dimensions.isEmpty()) {
            String strengths = profile.getStrengths() != null ? profile.getStrengths() : "";
            String weaknesses = profile.getWeaknesses() != null ? profile.getWeaknesses() : "";
            dimensions.put("理论知识", calculateDimension(strengths, weaknesses, "理论"));
            dimensions.put("实践能力", calculateDimension(strengths, weaknesses, "实践"));
            dimensions.put("问题解决", calculateDimension(strengths, weaknesses, "问题"));
            dimensions.put("创新思维", calculateDimension(strengths, weaknesses, "创新"));
            dimensions.put("协作能力", calculateDimension(strengths, weaknesses, "协作"));
            radarData.put("source", "keyword");
        }

        radarData.put("dimensions", dimensions);
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
