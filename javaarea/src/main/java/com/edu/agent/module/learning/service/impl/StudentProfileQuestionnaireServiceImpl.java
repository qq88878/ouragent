package com.edu.agent.module.learning.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.edu.agent.module.learning.dto.QuestionnaireDTO;
import com.edu.agent.module.learning.entity.StudentProfileQuestionnaire;
import com.edu.agent.module.learning.mapper.StudentProfileQuestionnaireMapper;
import com.edu.agent.module.learning.service.StudentProfileQuestionnaireService;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import com.edu.agent.module.chat.service.client.AgentServiceClient;
import com.edu.agent.module.learning.entity.StudentProfile;
import com.edu.agent.module.learning.service.StudentProfileService;
import org.springframework.transaction.annotation.Transactional;
import java.util.*;
import java.util.List;
import java.util.HashMap;
import java.util.Map;

@Service
public class StudentProfileQuestionnaireServiceImpl
        extends ServiceImpl<StudentProfileQuestionnaireMapper, StudentProfileQuestionnaire>
        implements StudentProfileQuestionnaireService {

    private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(StudentProfileQuestionnaireServiceImpl.class);

    private final ObjectMapper objectMapper = new ObjectMapper();
    private final AgentServiceClient agentServiceClient;
    private final StudentProfileService studentProfileService;

    public StudentProfileQuestionnaireServiceImpl(AgentServiceClient agentServiceClient, StudentProfileService studentProfileService) {
        this.agentServiceClient = agentServiceClient;
        this.studentProfileService = studentProfileService;
    }

    @Override
    public QuestionnaireDTO getQuestionnaire(Long userId) {
        LambdaQueryWrapper<StudentProfileQuestionnaire> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(StudentProfileQuestionnaire::getUserId, userId);
        StudentProfileQuestionnaire entity = getOne(wrapper);

        if (entity == null || entity.getQuestionnaireData() == null || entity.getQuestionnaireData().isEmpty()) {
            QuestionnaireDTO dto = new QuestionnaireDTO();
            dto.setIsCompleted(false);
            return dto;
        }

        try {
            QuestionnaireDTO dto = objectMapper.readValue(entity.getQuestionnaireData(), QuestionnaireDTO.class);
            dto.setIsCompleted(entity.getIsCompleted() != null && entity.getIsCompleted() == 1);
            return dto;
        } catch (JsonProcessingException e) {
            log.error("解析问卷数据失败: userId={}", userId, e);
            QuestionnaireDTO dto = new QuestionnaireDTO();
            dto.setIsCompleted(false);
            return dto;
        }
    }

    @Override
    @Transactional
    public void saveQuestionnaire(Long userId, QuestionnaireDTO dto) {
        LambdaQueryWrapper<StudentProfileQuestionnaire> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(StudentProfileQuestionnaire::getUserId, userId);
        StudentProfileQuestionnaire entity = getOne(wrapper);

        try {
            String json = objectMapper.writeValueAsString(dto);

            if (entity == null) {
                entity = new StudentProfileQuestionnaire();
                entity.setUserId(userId);
                entity.setQuestionnaireData(json);
                entity.setIsCompleted(1);
                save(entity);
            } else {
                entity.setQuestionnaireData(json);
                entity.setIsCompleted(1);
                updateById(entity);
            }

            log.info("问卷已保存: userId={}", userId);

            // 调用 Python Agent 生成基础画像
            try {
                Map<String, Object> basicProfile = agentServiceClient.analyzeBasicProfile(userId, dto);
                if (basicProfile != null && !basicProfile.isEmpty() && !basicProfile.containsKey("error")) {
                    // 将 LLM 分析结果更新到 StudentProfile
                    StudentProfile profile = studentProfileService.getProfile(userId);
                    if (profile != null) {
                        if (basicProfile.get("learning_style") != null) {
                            profile.setLearningStyle(basicProfile.get("learning_style").toString());
                        }
                        if (basicProfile.get("grade_level") != null) {
                            profile.setGradeLevel(basicProfile.get("grade_level").toString());
                        }
                        if (basicProfile.get("interests") != null) {
                            profile.setInterests(String.join(",", (List<String>) basicProfile.get("interests")));
                        }
                        if (basicProfile.get("strengths") != null) {
                            profile.setStrengths(String.join(",", (List<String>) basicProfile.get("strengths")));
                        }
                        if (basicProfile.get("weaknesses") != null) {
                            profile.setWeaknesses(String.join(",", (List<String>) basicProfile.get("weaknesses")));
                        }
                        // 扩展信息存入 preferences JSON
                        Map<String, Object> prefs = new HashMap<>();
                        if (basicProfile.get("recommended_methods") != null) {
                            prefs.put("recommended_methods", basicProfile.get("recommended_methods"));
                        }
                        if (basicProfile.get("recommended_strategy") != null) {
                            prefs.put("recommended_strategy", basicProfile.get("recommended_strategy"));
                        }
                        if (basicProfile.get("study_pace") != null) {
                            prefs.put("study_pace", basicProfile.get("study_pace"));
                        }
                        if (basicProfile.get("education_level") != null) {
                            prefs.put("education_level", basicProfile.get("education_level"));
                        }
                        if (basicProfile.get("major") != null) {
                            prefs.put("major", basicProfile.get("major"));
                        }
                        if (!prefs.isEmpty()) {
                            profile.setPreferences(objectMapper.writeValueAsString(prefs));
                        }
                        studentProfileService.updateProfile(userId, profile);
                        log.info("基础画像已通过 LLM 分析更新: userId={}, learning_style={}", 
                                userId, basicProfile.get("learning_style"));
                    }
                }
            } catch (Exception e) {
                log.warn("基础画像 LLM 分析失败（不影响问卷保存）: userId={}", userId, e);
            }
        } catch (JsonProcessingException e) {
            log.error("序列化问卷数据失败: userId={}", userId, e);
            throw new RuntimeException("保存问卷失败", e);
        }
    }

    @Override
    public boolean isCompleted(Long userId) {
        LambdaQueryWrapper<StudentProfileQuestionnaire> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(StudentProfileQuestionnaire::getUserId, userId);
        StudentProfileQuestionnaire entity = getOne(wrapper);
        return entity != null && entity.getIsCompleted() != null && entity.getIsCompleted() == 1;
    }
}
