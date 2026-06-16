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
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
public class StudentProfileQuestionnaireServiceImpl
        extends ServiceImpl<StudentProfileQuestionnaireMapper, StudentProfileQuestionnaire>
        implements StudentProfileQuestionnaireService {

    private final ObjectMapper objectMapper = new ObjectMapper();

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
