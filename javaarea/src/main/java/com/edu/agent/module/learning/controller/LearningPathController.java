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
}
