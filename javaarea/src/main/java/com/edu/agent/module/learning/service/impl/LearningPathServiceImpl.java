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
import com.edu.agent.module.schedule.dto.ScheduleConfigDTO;
import com.edu.agent.module.schedule.dto.ScheduleCourseDTO;
import com.edu.agent.module.schedule.service.ScheduleService;
import com.edu.agent.module.knowledge.dto.KnowledgeDTO;
import com.edu.agent.module.knowledge.service.KnowledgeService;
import lombok.extern.slf4j.Slf4j;

import org.springframework.stereotype.Service;

import org.springframework.transaction.annotation.Transactional;

import java.util.*;
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
    private final ScheduleService scheduleService;
    private final StudentProfileQuestionnaireMapper questionnaireMapper;
    private final KnowledgeService knowledgeService;
    
    public LearningPathServiceImpl(LearningPathStepMapper stepMapper, AgentServiceClient agentServiceClient, StudentProfileService studentProfileService, CourseMapper courseMapper, ScheduleService scheduleService, StudentProfileQuestionnaireMapper questionnaireMapper, KnowledgeService knowledgeService) {
        this.stepMapper = stepMapper;
        this.agentServiceClient = agentServiceClient;
        this.studentProfileService = studentProfileService;
        this.courseMapper = courseMapper;
        this.scheduleService = scheduleService;
        this.questionnaireMapper = questionnaireMapper;
        this.knowledgeService = knowledgeService;
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

        // Build schedule context for the planner agent
        Map<String, Object> scheduleContext = null;
        try {
            List<ScheduleCourseDTO> courses = scheduleService.listCourses(userId);
            if (courses != null && !courses.isEmpty()) {
                ScheduleConfigDTO config = scheduleService.getConfig(userId);
                List<ScheduleConfigDTO.PeriodConfig> periods = config != null ? config.getPeriodConfig() : Collections.emptyList();
                String[] dayNames = {"", "周一", "周二", "周三", "周四", "周五", "周六", "周日"};

                Map<String, List<String>> daySchedule = new LinkedHashMap<>();
                for (ScheduleCourseDTO c : courses) {
                    String periodStr = formatPeriodRange(c.getPeriodIndexes(), periods);
                    String weekStr = formatWeekRange(c.getWeekNumbers());
                    if (c.getDayOfWeeks() != null) {
                        for (Integer dow : c.getDayOfWeeks()) {
                            if (dow >= 1 && dow <= 7) {
                                String day = dayNames[dow];
                                String desc = c.getName() + " " + periodStr;
                                if (!weekStr.isEmpty()) {
                                    desc += " " + weekStr;
                                }
                                daySchedule.computeIfAbsent(day, k -> new ArrayList<>()).add(desc);
                            }
                        }
                    }
                }
                if (!daySchedule.isEmpty()) {
                    scheduleContext = new HashMap<>(daySchedule);
                }
            }
        } catch (Exception e) {
            log.debug("获取课表信息失败: userId={}", userId, e);
        }

        // 获取课程关联的知识库内容
        List<Map<String, Object>> courseKnowledge = new ArrayList<>();
        try {
            List<KnowledgeDTO> knowledgeItems = knowledgeService.listByCourse(request.getCourseId());
            for (KnowledgeDTO k : knowledgeItems) {
                Map<String, Object> item = new HashMap<>();
                item.put("id", k.getId());
                item.put("title", k.getName());
                item.put("description", k.getDescription() != null ? k.getDescription() : "");
                courseKnowledge.add(item);
            }
        } catch (Exception e) {
            log.warn("获取知识库内容失败，将不包含知识库信息: {}", e.getMessage());
        }

        // 构建课程描述
        StringBuilder courseDesc = new StringBuilder();
        if (course.getDescription() != null && !course.getDescription().isEmpty()) {
            courseDesc.append(course.getDescription());
        }
        if (course.getCategory() != null && !course.getCategory().isEmpty()) {
            if (courseDesc.length() > 0) courseDesc.append("。");
            courseDesc.append("分类: ").append(course.getCategory());
        }
        if (course.getDifficulty() != null && !course.getDifficulty().isEmpty()) {
            if (courseDesc.length() > 0) courseDesc.append("。");
            courseDesc.append("难度: ").append(course.getDifficulty());
        }

        AgentLearningPathResponse agentResponse;
        try {
            agentResponse = agentServiceClient.generateLearningPath(
                    profileMap, request.getCourseId(),
                    request.getGoal() != null ? request.getGoal() : "掌握课程核心知识",
                    course.getTitle(), courseDesc.toString(),
                    courseKnowledge, scheduleContext);
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
        String respTitle = agentResponse.getTitle();
        path.setTitle(respTitle != null ? respTitle : course.getTitle() + " - 学习路径");
        String respDesc = agentResponse.getDescription();
        path.setDescription(respDesc != null ? respDesc : "基于AI生成的个性化学习路径");
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
            if (stepData.getKnowledgeIds() != null && !stepData.getKnowledgeIds().isEmpty()) {
                step.setKnowledgeIds(stepData.getKnowledgeIds().stream()
                        .map(String::valueOf).collect(java.util.stream.Collectors.joining(",")));
            }
            if (stepData.getEstimatedHours() != null) {
                step.setEstimatedHours(stepData.getEstimatedHours());
            }
            step.setStepType(inferStepType(stepData.getTitle(), stepData.getDescription()));
            step.setEstimatedHours(stepData.getEstimatedHours() != null ? stepData.getEstimatedHours() : 2);
            if (stepData.getKnowledgeIds() != null && !stepData.getKnowledgeIds().isEmpty()) {
                step.setKnowledgeBaseId(stepData.getKnowledgeIds().get(0).longValue());
            }
            stepMapper.insert(step);
        }

        log.info("学习路径生成成功: pathId={}, userId={}, version={}", path.getId(), userId, path.getVersion());
        return getPathById(path.getId());
    }

    @Override
    @Transactional
    public LearningPathDTO generatePathFromChat(Long userId, Long courseId, List<Map<String, String>> messages) {
        String courseTitle = "课程";
        String courseDesc = "";
        if (courseId != null) { Course c = courseMapper.selectById(courseId); if (c != null) { courseTitle = c.getTitle(); if (c.getDescription() != null) courseDesc = c.getDescription(); } }
        int mv = 0;
        LambdaQueryWrapper<LearningPath> ew = new LambdaQueryWrapper<>();
        ew.eq(LearningPath::getUserId, userId).eq(LearningPath::getArchived, 0);
        if (courseId != null) ew.eq(LearningPath::getCourseId, courseId); else ew.isNull(LearningPath::getCourseId);
        for (LearningPath old : list(ew)) { old.setArchived(1); if (old.getVersion() != null && old.getVersion() > mv) mv = old.getVersion(); updateById(old); }
        LearningPath path = new LearningPath();
        path.setUserId(userId); path.setCourseId(courseId);
        path.setTitle(courseTitle + " - 个性化学习路径");
        path.setDescription("AI正在分析对话内容，生成个性化学习路径...");
        path.setStatus(3); path.setVersion(mv + 1); path.setArchived(0); path.setStarred(0); path.setTotalSteps(0); path.setCompletedSteps(0);
        save(path);
        Long pid = path.getId();
        String cid = courseId != null ? String.valueOf(courseId) : null;

        // Sync LLM call
        AgentLearningPathResponse ar = null;
        try {
            ar = agentServiceClient.generatePathFromChat(messages, cid, courseTitle, courseDesc);
        } catch (Exception e) {
            log.error("LLM call failed for pathId={}, using fallback", pid, e);
        }
        if (ar == null) ar = generateDefaultPath(courseTitle);

        path.setTitle(ar.getTitle() != null ? ar.getTitle() : courseTitle + " - 学习路径");
        path.setDescription(ar.getDescription() != null ? ar.getDescription() : "基于对话生成");
        path.setStatus(0);
        List<AgentLearningPathResponse.Step> steps = ar.getStepsSafe();
        path.setTotalSteps(steps.size()); updateById(path);
        if (steps.isEmpty()) {
            // If LLM returned empty (timeout fallback), use default
            ar = generateDefaultPath(courseTitle);
            steps = ar.getStepsSafe();
            path.setTitle(ar.getTitle()); path.setTotalSteps(steps.size()); updateById(path);
        }
        for (int i = 0; i < steps.size(); i++) {
            AgentLearningPathResponse.Step sd = steps.get(i);
            LearningPathStep step = new LearningPathStep();
            step.setPathId(pid); step.setStepOrder(i + 1);
            step.setTitle(sd.getTitle() != null ? sd.getTitle() : "步骤 " + (i + 1));
            step.setDescription(sd.getDescription() != null ? sd.getDescription() : "");
            step.setStatus(0);
            if (sd.getKnowledgeIds() != null && !sd.getKnowledgeIds().isEmpty()) step.setKnowledgeIds(sd.getKnowledgeIds().stream().map(String::valueOf).collect(java.util.stream.Collectors.joining(",")));
            step.setEstimatedHours(sd.getEstimatedHours() != null ? sd.getEstimatedHours() : 2);
            step.setStepType(inferStepType(sd.getTitle(), sd.getDescription()));
            if (sd.getPhaseName() != null) step.setPhaseName(sd.getPhaseName());
            if (sd.getIsCheckpoint() != null) step.setIsCheckpoint(sd.getIsCheckpoint() ? 1 : 0);
            stepMapper.insert(step);
        }
        log.info("Path generation complete: pathId={}, steps={}", pid, steps.size());

        return getPathById(pid);
    }

    private void autoGenerateContentAndExercises(Long pathId) {
        List<LearningPathStep> steps = stepMapper.selectList(new LambdaQueryWrapper<LearningPathStep>().eq(LearningPathStep::getPathId, pathId));
        for (LearningPathStep step : steps) { try {
            if (step.getContent() == null || step.getContent().isEmpty()) {
                List<Integer> kids = parseKnowledgeIds(step.getKnowledgeIds());
                Map<String, Object> cr = agentServiceClient.generateStepContent(step.getTitle(), kids);
                step.setContent(cr.getOrDefault("content", "").toString());
            }
            if (step.getExercises() == null || step.getExercises().isEmpty() || "{}".equals(step.getExercises())) {
                String diff = "easy";
                if (step.getStepType() != null) switch (step.getStepType()) { case "CONCEPT": diff = "easy"; break; case "PRACTICE": case "REVIEW": diff = "medium"; break; case "PROJECT": diff = "hard"; break; }
                List<Integer> kids = parseKnowledgeIds(step.getKnowledgeIds());
                step.setExercises(new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(agentServiceClient.generateExercises(step.getTitle(), kids, diff, 3)));
            }
            step.setUpdateTime(java.time.LocalDateTime.now()); stepMapper.updateById(step);
        } catch (Exception e) { log.warn("Auto-gen step {}: {}", step.getId(), e.getMessage()); } }
        log.info("Auto-gen complete: pathId={}", pathId);
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
        dto.setTotalStudyMinutes(path.getTotalStudyMinutes());
        dto.setTotalExercisesDone(path.getTotalExercisesDone());
        dto.setCorrectRate(path.getCorrectRate());
        dto.setLastStudiedAt(path.getLastStudiedAt());

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
        dto.setContent(step.getContent());
        dto.setExercises(step.getExercises());
        dto.setExerciseResults(step.getExerciseResults());
        dto.setKnowledgeIds(step.getKnowledgeIds());
        dto.setIsCheckpoint(step.getIsCheckpoint());
        dto.setPhaseName(step.getPhaseName());
        dto.setCheckpointScope(step.getCheckpointScope());
        return dto;
    }



    // ==================== Step Content & Exercises ====================

    @Override
    @Transactional
    public LearningPathDTO generateStepContent(Long pathId, Long stepId) {
        LearningPathStep step = stepMapper.selectById(stepId);
        if (step == null || !step.getPathId().equals(pathId)) {
            throw new BizException(ResultCode.NOT_FOUND, "?????");
        }
        LearningPath path = getById(pathId);
        if (path == null) {
            throw new BizException(ResultCode.NOT_FOUND, "???????");
        }

        List<Integer> knowledgeIds = parseKnowledgeIds(step.getKnowledgeIds());
        Map<String, Object> contentResult = agentServiceClient.generateStepContent(step.getTitle(), knowledgeIds);

        String summary = contentResult.get("summary") != null ? contentResult.get("summary").toString() : "";

        if ((summary == null || summary.isEmpty()) && step.getKnowledgeBaseId() != null) {
            try {
                KnowledgeDTO knowledge = knowledgeService.getKnowledgeById(step.getKnowledgeBaseId());
                if (knowledge != null && knowledge.getDescription() != null) {
                    summary = knowledge.getDescription();
                }
            } catch (Exception e) {
                log.warn("?????????: knowledgeId={}", step.getKnowledgeBaseId());
            }
        }

        if (summary.isEmpty()) {
            summary = "## " + step.getTitle() + "\n\n" + step.getDescription() + "\n\n*?AI ?????????????????*";
        }

        step.setContent(summary);
        step.setUpdateTime(java.time.LocalDateTime.now());
        stepMapper.updateById(step);

        path.setLastStudiedAt(java.time.LocalDateTime.now());
        updateById(path);

        return getPathById(pathId);
    }

    @Override
    @Transactional
    public LearningPathDTO generateStepExercises(Long pathId, Long stepId, int count) {
        LearningPathStep step = stepMapper.selectById(stepId);
        if (step == null || !step.getPathId().equals(pathId)) {
            throw new BizException(ResultCode.NOT_FOUND, "?????");
        }
        LearningPath path = getById(pathId);

        if (step.getExercises() != null && !step.getExercises().isEmpty()) {
            return getPathById(pathId);
        }

        List<Integer> knowledgeIds = parseKnowledgeIds(step.getKnowledgeIds());
        String difficulty = "easy";
        if (step.getStepType() != null) {
            switch (step.getStepType()) {
                case "CONCEPT": difficulty = "easy"; break;
                case "PRACTICE": difficulty = "medium"; break;
                case "REVIEW": difficulty = "medium"; break;
                case "PROJECT": difficulty = "hard"; break;
            }
        }

        Map<String, Object> exercisesResult = agentServiceClient.generateExercises(
                step.getTitle(), knowledgeIds, difficulty, count > 0 ? count : 3);

        try {
            String exercisesJson = new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(exercisesResult);
            step.setExercises(exercisesJson);
        } catch (Exception e) {
            log.error("????????", e);
            step.setExercises("{}");
        }

        step.setUpdateTime(java.time.LocalDateTime.now());
        stepMapper.updateById(step);

        if (path != null) {
            path.setLastStudiedAt(java.time.LocalDateTime.now());
            updateById(path);
        }

        return getPathById(pathId);
    }

    @Override
    @Transactional
    public Map<String, Object> evaluateStepExercises(Long pathId, Long stepId, Map<String, String> answers) {
        LearningPathStep step = stepMapper.selectById(stepId);
        if (step == null || !step.getPathId().equals(pathId)) {
            throw new BizException(ResultCode.NOT_FOUND, "?????");
        }
        LearningPath path = getById(pathId);

        Map<String, Object> exercisesMap = parseJson(step.getExercises());
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> questions = (List<Map<String, Object>>) exercisesMap.getOrDefault("questions", java.util.Collections.emptyList());

        int totalScore = 0;
        int correctCount = 0;
        List<Map<String, Object>> results = new java.util.ArrayList<>();
        String knowledgeContext = step.getContent() != null ? step.getContent() : "";

        for (Map<String, Object> question : questions) {
            String qText = (String) question.get("question");
            String qCorrect = (String) question.get("answer");
            String userAnswer = answers.getOrDefault("q_" + question.hashCode(), "");

            Map<String, Object> evaluation = agentServiceClient.evaluateExerciseAnswer(
                    qText, userAnswer, qCorrect, knowledgeContext);

            int score = evaluation.get("score") != null ? ((Number) evaluation.get("score")).intValue() : 0;
            boolean isCorrect = evaluation.get("is_correct") != null && (Boolean) evaluation.get("is_correct");

            totalScore += score;
            if (isCorrect) correctCount++;

            Map<String, Object> result = new java.util.HashMap<>();
            result.put("question", qText);
            result.put("user_answer", userAnswer);
            result.put("correct_answer", qCorrect);
            result.put("score", score);
            result.put("is_correct", isCorrect);
            result.put("suggestions", evaluation.getOrDefault("suggestions", java.util.Collections.emptyList()));
            result.put("encouragement", evaluation.getOrDefault("encouragement", ""));
            results.add(result);
        }

        try {
            Map<String, Object> resultsWrapper = new java.util.HashMap<>();
            resultsWrapper.put("questions", results);
            resultsWrapper.put("total_score", totalScore);
            resultsWrapper.put("correct_count", correctCount);
            resultsWrapper.put("total_count", questions.size());
            String resultsJson = new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(resultsWrapper);
            step.setExerciseResults(resultsJson);
            stepMapper.updateById(step);
        } catch (Exception e) {
            log.error("????????", e);
        }

        if (path != null) {
            path.setTotalExercisesDone((path.getTotalExercisesDone() != null ? path.getTotalExercisesDone() : 0) + questions.size());
            if (questions.size() > 0) {
                double newRate = (double) correctCount / questions.size() * 100;
                path.setCorrectRate(java.math.BigDecimal.valueOf(newRate));
            }
            path.setLastStudiedAt(java.time.LocalDateTime.now());
            updateById(path);
        }

        Map<String, Object> response = new java.util.HashMap<>();
        response.put("results", results);
        response.put("total_score", totalScore);
        response.put("correct_count", correctCount);
        response.put("total_count", questions.size());
        response.put("passed", correctCount >= questions.size() * 0.6);

        return response;
    }

    @Override
    @Transactional
    public LearningPathDTO generateCheckpointTest(Long pathId, Long stepId, int questionCount) {
        LearningPathStep step = stepMapper.selectById(stepId);
        if (step == null || !step.getPathId().equals(pathId)) {
            throw new BizException(ResultCode.NOT_FOUND, "?????");
        }
        LearningPath path = getById(pathId);

        List<Integer> allKnowledgeIds = new java.util.ArrayList<>();
        if (step.getCheckpointScope() != null && !step.getCheckpointScope().isEmpty()) {
            String[] scopeSteps = step.getCheckpointScope().split("\s*,\s*");
            for (String scopeStep : scopeSteps) {
                try {
                    int stepOrder = Integer.parseInt(scopeStep.trim());
                    LambdaQueryWrapper<LearningPathStep> wrapper = new LambdaQueryWrapper<>();
                    wrapper.eq(LearningPathStep::getPathId, pathId).eq(LearningPathStep::getStepOrder, stepOrder);
                    LearningPathStep scopeStepEntity = stepMapper.selectOne(wrapper);
                    if (scopeStepEntity != null) {
                        allKnowledgeIds.addAll(parseKnowledgeIds(scopeStepEntity.getKnowledgeIds()));
                    }
                } catch (NumberFormatException ignored) {}
            }
        }
        if (allKnowledgeIds.isEmpty()) {
            allKnowledgeIds = parseKnowledgeIds(step.getKnowledgeIds());
        }

        String topic = "????: " + step.getTitle();
        Map<String, Object> testResult = agentServiceClient.generateCheckpointTest(topic, allKnowledgeIds, questionCount > 0 ? questionCount : 10);

        try {
            String exercisesJson = new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(testResult);
            step.setExercises(exercisesJson);
            step.setUpdateTime(java.time.LocalDateTime.now());
            stepMapper.updateById(step);
        } catch (Exception e) {
            log.error("?????????", e);
        }

        return getPathById(pathId);
    }

    @Override
    @Transactional
    public Map<String, Object> evaluateCheckpointTest(Long pathId, Long stepId, Map<String, String> answers) {
        Map<String, Object> result = evaluateStepExercises(pathId, stepId, answers);
        LearningPathStep step = stepMapper.selectById(stepId);
        LearningPath path = getById(pathId);

        int correctCount = ((Number) result.get("correct_count")).intValue();
        int totalCount = ((Number) result.get("total_count")).intValue();
        boolean passed = correctCount >= totalCount * 0.6;

        result.put("is_checkpoint", true);
        result.put("passed", passed);

        if (passed && step != null) {
            step.setStatus(2);
            step.setUpdateTime(java.time.LocalDateTime.now());
            stepMapper.updateById(step);

            if (path != null) {
                LambdaQueryWrapper<LearningPathStep> wrapper = new LambdaQueryWrapper<>();
                wrapper.eq(LearningPathStep::getPathId, pathId).eq(LearningPathStep::getStatus, 2);
                long completedCount = stepMapper.selectCount(wrapper);
                path.setCompletedSteps((int) completedCount);
                if (completedCount >= path.getTotalSteps()) {
                    path.setStatus(1);
                }
                path.setLastStudiedAt(java.time.LocalDateTime.now());
                updateById(path);
            }
        }

        return result;
    }

    @Override
    @Transactional
    public void recordStudyTime(Long pathId, int minutes) {
        LearningPath path = getById(pathId);
        if (path != null) {
            path.setTotalStudyMinutes((path.getTotalStudyMinutes() != null ? path.getTotalStudyMinutes() : 0) + minutes);
            path.setLastStudiedAt(java.time.LocalDateTime.now());
            updateById(path);
        }
    }

    // ==================== Helper Methods ====================

    private List<Integer> parseKnowledgeIds(String knowledgeIdsStr) {
        if (knowledgeIdsStr == null || knowledgeIdsStr.isEmpty()) {
            return java.util.Collections.emptyList();
        }
        List<Integer> ids = new java.util.ArrayList<>();
        for (String part : knowledgeIdsStr.split("\s*,\s*")) {
            try {
                ids.add(Integer.parseInt(part.trim()));
            } catch (NumberFormatException ignored) {}
        }
        return ids;
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> parseJson(String json) {
        if (json == null || json.isEmpty()) {
            return new java.util.HashMap<>();
        }
        try {
            return new com.fasterxml.jackson.databind.ObjectMapper().readValue(json, Map.class);
        } catch (Exception e) {
            return new java.util.HashMap<>();
        }
    }

    private String formatPeriodRange(List<Integer> indexes, List<ScheduleConfigDTO.PeriodConfig> periods) {
        if (indexes == null || indexes.isEmpty()) return "";
        if (indexes.size() == 1) {
            int idx = indexes.get(0);
            if (idx >= 0 && idx < periods.size()) {
                return "\u7b2c" + periods.get(idx).getName() + "\u8282";
            }
            return "\u7b2c" + (idx + 1) + "\u8282";
        }
        List<Integer> sorted = new ArrayList<>(indexes);
        Collections.sort(sorted);
        int first = sorted.get(0);
        int last = sorted.get(sorted.size() - 1);
        String firstName = (first >= 0 && first < periods.size()) ? periods.get(first).getName() : String.valueOf(first + 1);
        String lastName = (last >= 0 && last < periods.size()) ? periods.get(last).getName() : String.valueOf(last + 1);
        if (first == last) {
            return "\u7b2c" + firstName + "\u8282";
        }
        return "\u7b2c" + firstName + "-" + lastName + "\u8282";
    }

    private String formatWeekRange(List<Integer> weeks) {
        if (weeks == null || weeks.isEmpty()) return "";
        if (weeks.size() == 1) return "\u7b2c" + weeks.get(0) + "\u5468";
        List<Integer> sorted = new ArrayList<>(weeks);
        Collections.sort(sorted);
        int first = sorted.get(0);
        int last = sorted.get(sorted.size() - 1);
        if (first == last) return "\u7b2c" + first + "\u5468";
        return "\u7b2c" + first + "-" + last + "\u5468";
    }

    // ====== Profile Evolution Helper ======

    private void triggerProfileUpdateFromEvaluation(Long pathId, Long userId, Map<String, Object> evalResult) {
        try {
            LearningPath path = getById(pathId);
            if (path == null) return;

            StudentProfile profile = studentProfileService.getProfile(userId);
            Map<String, Object> currentProfile = new HashMap<>();
            currentProfile.put("learningStyle", profile.getLearningStyle());
            currentProfile.put("strengths", profile.getStrengths());
            currentProfile.put("weaknesses", profile.getWeaknesses());
            currentProfile.put("interests", profile.getInterests());
            currentProfile.put("gradeLevel", profile.getGradeLevel());

            // Build new signals from evaluation
            Map<String, Object> newSignals = new HashMap<>();
            newSignals.put("path_title", path.getTitle());
            int correctCount = evalResult.containsKey("correct_count") ?
                    ((Number) evalResult.get("correct_count")).intValue() : 0;
            int totalCount = evalResult.containsKey("total_count") ?
                    ((Number) evalResult.get("total_count")).intValue() : 0;
            newSignals.put("quiz_correct", correctCount);
            newSignals.put("quiz_total", totalCount);
            newSignals.put("quiz_passed", evalResult.getOrDefault("passed", false));
            newSignals.put("activity_type", "checkpoint_evaluation");

            // Call Python Agent to merge profile
            Map<String, Object> updatedProfile = agentServiceClient.updateProfileFromActivity(
                    String.valueOf(userId), currentProfile, newSignals, java.util.Collections.emptyList());

            // Apply updates to StudentProfile
            if (updatedProfile != null && !updatedProfile.isEmpty() && !updatedProfile.containsKey("error")) {
                boolean changed = false;
                if (updatedProfile.get("learning_style") != null) {
                    profile.setLearningStyle(updatedProfile.get("learning_style").toString());
                    changed = true;
                }
                if (updatedProfile.get("strengths") instanceof List) {
                    @SuppressWarnings("unchecked")
                    List<String> strs = (List<String>) updatedProfile.get("strengths");
                    profile.setStrengths(String.join(",", strs));
                    changed = true;
                }
                if (updatedProfile.get("weaknesses") instanceof List) {
                    @SuppressWarnings("unchecked")
                    List<String> wks = (List<String>) updatedProfile.get("weaknesses");
                    profile.setWeaknesses(String.join(",", wks));
                    changed = true;
                }
                if (changed) {
                    studentProfileService.updateProfile(userId, profile);
                    log.info("Profile evolved from evaluation: userId={}, pathId={}", userId, pathId);
                }
            }
        } catch (Exception e) {
            log.warn("Profile evolution trigger failed: userId={}, pathId={}", userId, pathId, e);
        }
    }

    @SuppressWarnings("unchecked")
    @Override
    @Transactional
    public LearningPathDTO regenerateStepExercises(Long pathId, Long stepId) {
        LearningPathStep step = stepMapper.selectById(stepId);
        if (step == null || !step.getPathId().equals(pathId)) {
            throw new BizException(ResultCode.NOT_FOUND, "Step not found");
        }
        LearningPath path = getById(pathId);

        // Analyse previous exercise results for weak topics
        String focusTopic = step.getTitle();
        if (step.getExerciseResults() != null && !step.getExerciseResults().isEmpty()) {
            Map<String, Object> prevResults = parseJson(step.getExerciseResults());
            List<Map<String, Object>> prevQuestions = (List<Map<String, Object>>)
                    prevResults.getOrDefault("questions", java.util.Collections.emptyList());
            List<String> wrongTopics = new java.util.ArrayList<>();
            for (Map<String, Object> q : prevQuestions) {
                Boolean ok = (Boolean) q.get("is_correct");
                if (ok == null || !ok) {
                    String qt = (String) q.get("question");
                    if (qt != null) { wrongTopics.add(qt.length() > 50 ? qt.substring(0, 50) : qt); }
                }
            }
            if (!wrongTopics.isEmpty()) {
                focusTopic = String.join(", ", wrongTopics.subList(0, Math.min(3, wrongTopics.size())));
            }
        }

        List<Integer> knowledgeIds = parseKnowledgeIds(step.getKnowledgeIds());
        String difficulty = "medium";
        if (step.getStepType() != null) {
            switch (step.getStepType()) {
                case "CONCEPT": difficulty = "easy"; break;
                case "PRACTICE": difficulty = "medium"; break;
                case "REVIEW": difficulty = "medium"; break;
                case "PROJECT": difficulty = "hard"; break;
            }
        }

        Map<String, Object> exercisesResult = agentServiceClient.generateExercises(
                focusTopic, knowledgeIds, difficulty, 3);

        try {
            step.setExercises(new com.fasterxml.jackson.databind.ObjectMapper()
                    .writeValueAsString(exercisesResult));
            step.setExerciseResults(null);
        } catch (Exception e) {
            log.error("Failed to serialize regenerated exercises", e);
            step.setExercises("{}");
        }

        step.setUpdateTime(java.time.LocalDateTime.now());
        stepMapper.updateById(step);

        if (path != null) {
            path.setLastStudiedAt(java.time.LocalDateTime.now());
            updateById(path);
        }

        log.info("Exercises regenerated for step: pathId={}, stepId={}", pathId, stepId);
        return getPathById(pathId);
    }

}