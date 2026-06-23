package com.edu.agent.module.learning.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.edu.agent.common.exception.BizException;
import com.edu.agent.common.result.ResultCode;
import com.edu.agent.module.chat.service.client.AgentServiceClient;
import com.edu.agent.module.course.entity.Course;
import com.edu.agent.module.course.mapper.CourseMapper;
import com.edu.agent.module.learning.dto.AgentLearningPathResponse;
import com.edu.agent.module.learning.dto.LearningPathDTO;
import com.edu.agent.module.learning.dto.LearningPathGenerateRequest;
import com.edu.agent.module.learning.dto.LearningPathStepDTO;
import com.edu.agent.module.learning.entity.LearningPath;
import com.edu.agent.module.learning.entity.LearningPathStep;
import com.edu.agent.module.learning.entity.StudentProfile;
import com.edu.agent.module.learning.entity.StudentProfileQuestionnaire;
import com.edu.agent.module.learning.mapper.LearningPathMapper;
import com.edu.agent.module.learning.mapper.LearningPathStepMapper;
import com.edu.agent.module.learning.mapper.StudentProfileQuestionnaireMapper;
import com.edu.agent.module.learning.service.LearningPathService;
import com.edu.agent.module.learning.service.StudentProfileService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class LearningPathServiceImpl
        extends ServiceImpl<LearningPathMapper, LearningPath>
        implements LearningPathService {
    private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(LearningPathServiceImpl.class);

    private final LearningPathStepMapper stepMapper;
    private final AgentServiceClient agentServiceClient;
    private final StudentProfileService studentProfileService;
    private final CourseMapper courseMapper;
    private final StudentProfileQuestionnaireMapper questionnaireMapper;
    public LearningPathServiceImpl(LearningPathStepMapper stepMapper, AgentServiceClient agentServiceClient, StudentProfileService studentProfileService, CourseMapper courseMapper, StudentProfileQuestionnaireMapper questionnaireMapper) {
        this.stepMapper = stepMapper;
        this.agentServiceClient = agentServiceClient;
        this.studentProfileService = studentProfileService;
        this.courseMapper = courseMapper;
        this.questionnaireMapper = questionnaireMapper;
    }

    @Override
    @Transactional
    public LearningPathDTO generatePath(Long userId, LearningPathGenerateRequest request) {
        Course course = courseMapper.selectById(request.getCourseId());
        if (course == null) {
            throw new BizException(ResultCode.NOT_FOUND, "课程不存在");
        }

        // 检查问卷完成状态（仅记录日志，不阻塞生成）
        LambdaQueryWrapper<StudentProfileQuestionnaire> qWrapper = new LambdaQueryWrapper<>();
        qWrapper.eq(StudentProfileQuestionnaire::getUserId, userId);
        StudentProfileQuestionnaire questionnaire = questionnaireMapper.selectOne(qWrapper);
        if (questionnaire == null || questionnaire.getIsCompleted() == null || questionnaire.getIsCompleted() == 0) {
            log.warn("用户 {} 未完成问卷，使用默认画像生成路径", userId);
        }

        StudentProfile profile = studentProfileService.getProfile(userId);

        Map<String, Object> profileMap = new HashMap<>();
        profileMap.put("learningStyle", profile.getLearningStyle());
        profileMap.put("strengths", profile.getStrengths());
        profileMap.put("weaknesses", profile.getWeaknesses());
        profileMap.put("interests", profile.getInterests());
        profileMap.put("gradeLevel", profile.getGradeLevel());

        AgentLearningPathResponse agentResponse;
        try {
            agentResponse = agentServiceClient.generateLearningPath(
                    profileMap, request.getCourseId(),
                    request.getGoal() != null ? request.getGoal() : "掌握课程核心知识");
        } catch (Exception e) {
            log.error("调用 Agent 生成学习路径失败", e);
            agentResponse = generateDefaultPath(course.getTitle());
        }

        // 版本管理：归档同课程已有路径
        LambdaQueryWrapper<LearningPath> existingWrapper = new LambdaQueryWrapper<>();
        existingWrapper.eq(LearningPath::getUserId, userId)
                .eq(LearningPath::getCourseId, request.getCourseId())
                .eq(LearningPath::getArchived, 0);
        List<LearningPath> existingPaths = list(existingWrapper);
        int maxVersion = 0;
        for (LearningPath old : existingPaths) {
            old.setArchived(1);
            if (old.getVersion() != null && old.getVersion() > maxVersion) {
                maxVersion = old.getVersion();
            }
            updateById(old);
        }

        LearningPath path = new LearningPath();
        path.setUserId(userId);
        path.setCourseId(request.getCourseId());
        path.setTitle(course.getTitle() + " - 学习路径");
        path.setDescription("基于AI生成的个性化学习路径");
        path.setStatus(0);
        path.setVersion(maxVersion + 1);
        path.setArchived(0);
        path.setStarred(0);
        save(path);

        List<AgentLearningPathResponse.Step> steps = agentResponse.getStepsSafe();
        int totalSteps = steps.size();
        path.setTotalSteps(totalSteps);
        path.setCompletedSteps(0);
        updateById(path);

        for (int i = 0; i < steps.size(); i++) {
            AgentLearningPathResponse.Step stepData = steps.get(i);
            LearningPathStep step = new LearningPathStep();
            step.setPathId(path.getId());
            step.setStepOrder(i + 1);
            step.setTitle(stepData.getTitle() != null ? stepData.getTitle() : "步骤 " + (i + 1));
            step.setDescription(stepData.getDescription() != null ? stepData.getDescription() : "");
            step.setStatus(0);
            step.setStepType(inferStepType(stepData.getTitle(), stepData.getDescription()));
            step.setEstimatedHours(stepData.getEstimatedHours() != null ? stepData.getEstimatedHours() : 2);
            stepMapper.insert(step);
        }

        log.info("学习路径生成成功: pathId={}, userId={}, version={}", path.getId(), userId, path.getVersion());
        return getPathById(path.getId());
    }

    @Override
    public List<LearningPathDTO> listPaths(Long userId) {
        return listPaths(userId, false);
    }

    @Override
    public List<LearningPathDTO> listPaths(Long userId, boolean includeArchived) {
        LambdaQueryWrapper<LearningPath> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(LearningPath::getUserId, userId);
        if (!includeArchived) {
            wrapper.eq(LearningPath::getArchived, 0);
        }
        wrapper.orderByDesc(LearningPath::getCreateTime);
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

    @Override
    public void toggleStar(Long pathId) {
        LearningPath path = getById(pathId);
        if (path == null) {
            throw new BizException(ResultCode.NOT_FOUND, "学习路径不存在");
        }
        path.setStarred(path.getStarred() != null && path.getStarred() == 1 ? 0 : 1);
        updateById(path);
    }

    @Override
    public void toggleArchive(Long pathId) {
        LearningPath path = getById(pathId);
        if (path == null) {
            throw new BizException(ResultCode.NOT_FOUND, "学习路径不存在");
        }
        path.setArchived(path.getArchived() != null && path.getArchived() == 1 ? 0 : 1);
        updateById(path);
    }

    private String inferStepType(String title, String desc) {
        String text = ((title != null ? title : "") + " " + (desc != null ? desc : "")).toLowerCase();
        if (text.contains("练习") || text.contains("实践") || text.contains("动手")) return "PRACTICE";
        if (text.contains("复习") || text.contains("回顾") || text.contains("巩固")) return "REVIEW";
        if (text.contains("项目") || text.contains("实战") || text.contains("综合")) return "PROJECT";
        return "CONCEPT";
    }

    private AgentLearningPathResponse generateDefaultPath(String courseTitle) {
        AgentLearningPathResponse response = new AgentLearningPathResponse();
        response.setTitle(courseTitle + " - 默认学习路径");

        List<AgentLearningPathResponse.Step> steps = new ArrayList<>();

        AgentLearningPathResponse.Step step1 = new AgentLearningPathResponse.Step();
        step1.setTitle("基础概念学习");
        step1.setDescription("学习" + courseTitle + "的基础概念和核心知识");
        steps.add(step1);

        AgentLearningPathResponse.Step step2 = new AgentLearningPathResponse.Step();
        step2.setTitle("实践练习");
        step2.setDescription("通过实践练习巩固所学知识");
        steps.add(step2);

        AgentLearningPathResponse.Step step3 = new AgentLearningPathResponse.Step();
        step3.setTitle("进阶提升");
        step3.setDescription("深入学习高级内容，提升综合能力");
        steps.add(step3);

        response.setSteps(steps);
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
        dto.setVersion(path.getVersion());
        dto.setArchived(path.getArchived());
        dto.setStarred(path.getStarred());

        if (includeSteps) {
            LambdaQueryWrapper<LearningPathStep> wrapper = new LambdaQueryWrapper<>();
            wrapper.eq(LearningPathStep::getPathId, path.getId())
                    .orderByAsc(LearningPathStep::getStepOrder);
            List<LearningPathStep> steps = stepMapper.selectList(wrapper);
            List<LearningPathStepDTO> stepDTOs = steps.stream().map(this::toStepDTO).collect(Collectors.toList());

            int currentIdx = -1;
            for (int i = 0; i < stepDTOs.size(); i++) {
                if (stepDTOs.get(i).getStatus() != 2) {
                    currentIdx = i;
                    stepDTOs.get(i).setIsCurrent(true);
                    break;
                }
            }
            if (currentIdx == -1 && !stepDTOs.isEmpty()) {
                currentIdx = stepDTOs.size() - 1;
            }
            dto.setCurrentStepIndex(currentIdx);

            int remainingHours = stepDTOs.stream()
                    .filter(s -> s.getStatus() != 2)
                    .mapToInt(s -> s.getEstimatedHours() != null ? s.getEstimatedHours() : 2)
                    .sum();
            dto.setEstimatedRemainingHours(remainingHours);

            dto.setSteps(stepDTOs);
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
        dto.setStepType(step.getStepType());
        dto.setEstimatedHours(step.getEstimatedHours());
        return dto;
    }
}
