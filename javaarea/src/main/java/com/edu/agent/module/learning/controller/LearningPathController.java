package com.edu.agent.module.learning.controller;

import com.edu.agent.common.result.Result;
import com.edu.agent.module.learning.dto.LearningPathDTO;
import com.edu.agent.module.learning.dto.LearningPathGenerateRequest;
import com.edu.agent.module.learning.service.LearningPathService;
import com.edu.agent.security.LoginUser;
import jakarta.validation.Valid;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/learning/paths")
@PreAuthorize("hasRole('STUDENT')")
public class LearningPathController {

    private final LearningPathService learningPathService;
    public LearningPathController(LearningPathService learningPathService) {
        this.learningPathService = learningPathService;
    }

    @PostMapping("/generate")
    public Result<LearningPathDTO> generatePath(@Valid @RequestBody LearningPathGenerateRequest request) {
        LoginUser loginUser = (LoginUser) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        return Result.success(learningPathService.generatePath(loginUser.getUser().getId(), request));
    }

    @PostMapping("/generate-from-chat")
    public Result<LearningPathDTO> generatePathFromChat(@RequestBody Map<String, Object> body) {
        LoginUser loginUser = (LoginUser) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        Long courseId = body.get("courseId") != null ? Long.valueOf(body.get("courseId").toString()) : null;
        @SuppressWarnings("unchecked")
        List<Map<String, String>> messages = (List<Map<String, String>>) body.get("messages");
        return Result.success(learningPathService.generatePathFromChat(loginUser.getUser().getId(), courseId, messages));
    }

    @GetMapping("/")
    public Result<List<LearningPathDTO>> listPaths(
            @RequestParam(defaultValue = "false") boolean includeArchived) {
        LoginUser loginUser = (LoginUser) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        return Result.success(learningPathService.listPaths(loginUser.getUser().getId(), includeArchived));
    }

    @GetMapping("/{id}")
    public Result<LearningPathDTO> getPathById(@PathVariable Long id) {
        return Result.success(learningPathService.getPathById(id));
    }

    @PutMapping("/{pathId}/steps/{stepId}")
    public Result<Void> updateStepStatus(
            @PathVariable Long pathId,
            @PathVariable Long stepId,
            @RequestParam String status) {
        learningPathService.updateStepStatus(pathId, stepId, status);
        return Result.success();
    }

    @DeleteMapping("/{id}")
    public Result<Void> deletePath(@PathVariable Long id) {
        learningPathService.deletePath(id);
        return Result.success();
    }

    @PutMapping("/{id}/star")
    public Result<Void> toggleStar(@PathVariable Long id) {
        learningPathService.toggleStar(id);
        return Result.success();
    }

    @PutMapping("/{id}/archive")
    public Result<Void> toggleArchive(@PathVariable Long id) {
        learningPathService.toggleArchive(id);
        return Result.success();
    }


    // ===== Step Content & Exercises =====

    @PostMapping("/{pathId}/steps/{stepId}/content")
    public Result<LearningPathDTO> generateStepContent(
            @PathVariable Long pathId, @PathVariable Long stepId) {
        return Result.success(learningPathService.generateStepContent(pathId, stepId));
    }

    @PostMapping("/{pathId}/steps/{stepId}/exercises")
    public Result<LearningPathDTO> generateStepExercises(
            @PathVariable Long pathId, @PathVariable Long stepId,
            @RequestParam(defaultValue = "3") int count) {
        return Result.success(learningPathService.generateStepExercises(pathId, stepId, count));
    }

    @PostMapping("/{pathId}/steps/{stepId}/evaluate")
    public Result<Map<String, Object>> evaluateStepExercises(
            @PathVariable Long pathId, @PathVariable Long stepId,
            @RequestBody Map<String, String> answers) {
        return Result.success(learningPathService.evaluateStepExercises(pathId, stepId, answers));
    }

    @PostMapping("/{pathId}/steps/{stepId}/checkpoint")
    public Result<LearningPathDTO> generateCheckpointTest(
            @PathVariable Long pathId, @PathVariable Long stepId,
            @RequestParam(defaultValue = "10") int questionCount) {
        return Result.success(learningPathService.generateCheckpointTest(pathId, stepId, questionCount));
    }

    @PostMapping("/{pathId}/steps/{stepId}/exercises/regenerate")
    public Result<LearningPathDTO> regenerateStepExercises(
            @PathVariable Long pathId, @PathVariable Long stepId) {
        return Result.success(learningPathService.regenerateStepExercises(pathId, stepId));
    }

    @PostMapping("/{pathId}/steps/{stepId}/checkpoint/evaluate")
    public Result<Map<String, Object>> evaluateCheckpointTest(
            @PathVariable Long pathId, @PathVariable Long stepId,
            @RequestBody Map<String, String> answers) {
        return Result.success(learningPathService.evaluateCheckpointTest(pathId, stepId, answers));
    }

    @PostMapping("/{pathId}/study-time")
    public Result<Void> recordStudyTime(
            @PathVariable Long pathId,
            @RequestParam int minutes) {
        learningPathService.recordStudyTime(pathId, minutes);
        return Result.success();
    }

}
