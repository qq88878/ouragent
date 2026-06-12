package com.edu.agent.module.learning.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.edu.agent.common.exception.BizException;
import com.edu.agent.common.result.ResultCode;
import com.edu.agent.module.chat.service.client.AgentServiceClient;
import com.edu.agent.module.course.entity.Course;
import com.edu.agent.module.course.mapper.CourseMapper;
import com.edu.agent.module.learning.dto.LearningPathDTO;
import com.edu.agent.module.learning.dto.LearningPathGenerateRequest;
import com.edu.agent.module.learning.dto.LearningPathStepDTO;
import com.edu.agent.module.learning.entity.LearningPath;
import com.edu.agent.module.learning.entity.LearningPathStep;
import com.edu.agent.module.learning.entity.StudentProfile;
import com.edu.agent.module.learning.mapper.LearningPathMapper;
import com.edu.agent.module.learning.mapper.LearningPathStepMapper;
import com.edu.agent.module.learning.service.LearningPathService;
import com.edu.agent.module.learning.service.StudentProfileService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class LearningPathServiceImpl
        extends ServiceImpl<LearningPathMapper, LearningPath>
        implements LearningPathService {

    private final LearningPathStepMapper stepMapper;
    private final AgentServiceClient agentServiceClient;
    private final StudentProfileService studentProfileService;
    private final CourseMapper courseMapper;

    @Override
    @Transactional
    public LearningPathDTO generatePath(Long userId, LearningPathGenerateRequest request) {
        Course course = courseMapper.selectById(request.getCourseId());
        if (course == null) {
            throw new BizException(ResultCode.NOT_FOUND, "课程不存在");
        }

        StudentProfile profile = studentProfileService.getProfile(userId);

        Map<String, Object> profileMap = new HashMap<>();
        profileMap.put("learningStyle", profile.getLearningStyle());
        profileMap.put("strengths", profile.getStrengths());
        profileMap.put("weaknesses", profile.getWeaknesses());
        profileMap.put("interests", profile.getInterests());
        profileMap.put("gradeLevel", profile.getGradeLevel());

        Map<String, Object> agentResponse;
        try {
            agentResponse = agentServiceClient.generateLearningPath(
                    profileMap, request.getCourseId(),
                    request.getGoal() != null ? request.getGoal() : "掌握课程核心知识");
        } catch (Exception e) {
            log.error("调用 Agent 生成学习路径失败", e);
            agentResponse = generateDefaultPath(course.getTitle());
        }

        LearningPath path = new LearningPath();
        path.setUserId(userId);
        path.setCourseId(request.getCourseId());
        path.setTitle(course.getTitle() + " - 学习路径");
        path.setDescription("基于AI生成的个性化学习路径");
        path.setStatus(0);
        save(path);

        List<Map<String, Object>> steps = extractSteps(agentResponse);
        int totalSteps = steps.size();
        path.setTotalSteps(totalSteps);
        path.setCompletedSteps(0);
        updateById(path);

        for (int i = 0; i < steps.size(); i++) {
            Map<String, Object> stepData = steps.get(i);
            LearningPathStep step = new LearningPathStep();
            step.setPathId(path.getId());
            step.setStepOrder(i + 1);
            step.setTitle((String) stepData.getOrDefault("title", "步骤 " + (i + 1)));
            step.setDescription((String) stepData.getOrDefault("description", ""));
            step.setStatus(0);
            stepMapper.insert(step);
        }

        log.info("学习路径生成成功: pathId={}, userId={}", path.getId(), userId);
        return getPathById(path.getId());
    }

    @Override
    public List<LearningPathDTO> listPaths(Long userId) {
        LambdaQueryWrapper<LearningPath> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(LearningPath::getUserId, userId)
                .orderByDesc(LearningPath::getCreateTime);
        List<LearningPath> paths = list(wrapper);
        return paths.stream()
                .map(path -> toDTO(path, false))
                .collect(Collectors.toList());
    }

    @Override
    public LearningPathDTO getPathById(Long pathId) {
        LearningPath path = getById(pathId);
        if (path == null) {
            throw new BizException(ResultCode.NOT_FOUND, "学习路径不存在");
        }
        return toDTO(path, true);
    }

    @Override
    @Transactional
    public void updateStepStatus(Long pathId, Long stepId, String status) {
        LearningPath path = getById(pathId);
        if (path == null) {
            throw new BizException(ResultCode.NOT_FOUND, "学习路径不存在");
        }

        LearningPathStep step = stepMapper.selectById(stepId);
        if (step == null || !step.getPathId().equals(pathId)) {
            throw new BizException(ResultCode.NOT_FOUND, "学习步骤不存在");
        }

        int statusCode = switch (status.toLowerCase()) {
            case "in_progress" -> 1;
            case "completed" -> 2;
            default -> 0;
        };
        step.setStatus(statusCode);
        stepMapper.updateById(step);

        if (statusCode == 2) {
            LambdaQueryWrapper<LearningPathStep> wrapper = new LambdaQueryWrapper<>();
            wrapper.eq(LearningPathStep::getPathId, pathId)
                    .eq(LearningPathStep::getStatus, 2);
            long completedCount = stepMapper.selectCount(wrapper);
            path.setCompletedSteps((int) completedCount);

            if (completedCount >= path.getTotalSteps()) {
                path.setStatus(1); // completed
            }
            updateById(path);
        }

        log.info("学习步骤状态更新: pathId={}, stepId={}, status={}", pathId, stepId, status);
    }

    @Override
    @Transactional
    public void deletePath(Long pathId) {
        LearningPath path = getById(pathId);
        if (path == null) {
            throw new BizException(ResultCode.NOT_FOUND, "学习路径不存在");
        }

        LambdaQueryWrapper<LearningPathStep> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(LearningPathStep::getPathId, pathId);
        stepMapper.delete(wrapper);

        removeById(pathId);
        log.info("学习路径删除成功: pathId={}", pathId);
    }

    @SuppressWarnings("unchecked")
    private List<Map<String, Object>> extractSteps(Map<String, Object> agentResponse) {
        if (agentResponse.containsKey("steps")) {
            Object stepsObj = agentResponse.get("steps");
            if (stepsObj instanceof List<?> list) {
                List<Map<String, Object>> result = new ArrayList<>();
                for (Object item : list) {
                    if (item instanceof Map) {
                        result.add((Map<String, Object>) item);
                    }
                }
                return result;
            }
        }
        if (agentResponse.containsKey("path")) {
            Object pathObj = agentResponse.get("path");
            if (pathObj instanceof Map<?, ?> pathMap && pathMap.containsKey("steps")) {
                Object stepsObj = pathMap.get("steps");
                if (stepsObj instanceof List<?> list) {
                    List<Map<String, Object>> result = new ArrayList<>();
                    for (Object item : list) {
                        if (item instanceof Map) {
                            result.add((Map<String, Object>) item);
                        }
                    }
                    return result;
                }
            }
        }
        return Collections.emptyList();
    }

    private Map<String, Object> generateDefaultPath(String courseTitle) {
        Map<String, Object> response = new HashMap<>();
        List<Map<String, Object>> steps = new ArrayList<>();

        Map<String, Object> step1 = new HashMap<>();
        step1.put("title", "基础概念学习");
        step1.put("description", "学习" + courseTitle + "的基础概念和核心知识");
        steps.add(step1);

        Map<String, Object> step2 = new HashMap<>();
        step2.put("title", "实践练习");
        step2.put("description", "通过实践练习巩固所学知识");
        steps.add(step2);

        Map<String, Object> step3 = new HashMap<>();
        step3.put("title", "进阶提升");
        step3.put("description", "深入学习高级内容，提升综合能力");
        steps.add(step3);

        response.put("steps", steps);
        return response;
    }

    private LearningPathDTO toDTO(LearningPath path, boolean includeSteps) {
        LearningPathDTO dto = new LearningPathDTO();
        dto.setId(path.getId());
        dto.setUserId(path.getUserId());
        dto.setCourseId(path.getCourseId());
        dto.setTitle(path.getTitle());
        dto.setDescription(path.getDescription());
        dto.setTotalSteps(path.getTotalSteps());
        dto.setCompletedSteps(path.getCompletedSteps());
        dto.setStatus(path.getStatus());
        dto.setCreateTime(path.getCreateTime());

        if (includeSteps) {
            LambdaQueryWrapper<LearningPathStep> wrapper = new LambdaQueryWrapper<>();
            wrapper.eq(LearningPathStep::getPathId, path.getId())
                    .orderByAsc(LearningPathStep::getStepOrder);
            List<LearningPathStep> steps = stepMapper.selectList(wrapper);
            dto.setSteps(steps.stream().map(this::toStepDTO).collect(Collectors.toList()));
        }

        return dto;
    }

    private LearningPathStepDTO toStepDTO(LearningPathStep step) {
        LearningPathStepDTO dto = new LearningPathStepDTO();
        dto.setId(step.getId());
        dto.setStepOrder(step.getStepOrder());
        dto.setTitle(step.getTitle());
        dto.setDescription(step.getDescription());
        dto.setKnowledgeBaseId(step.getKnowledgeBaseId());
        dto.setStatus(step.getStatus());
        return dto;
    }
}
