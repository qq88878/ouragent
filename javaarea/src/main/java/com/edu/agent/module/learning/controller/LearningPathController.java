package com.edu.agent.module.learning.controller;

import com.edu.agent.common.result.Result;
import com.edu.agent.module.learning.dto.LearningPathDTO;
import com.edu.agent.module.learning.dto.LearningPathGenerateRequest;
import com.edu.agent.module.learning.service.LearningPathService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/learning/paths")
@RequiredArgsConstructor
public class LearningPathController {

    private final LearningPathService learningPathService;

    @PostMapping("/generate")
    public Result<LearningPathDTO> generatePath(@Valid @RequestBody LearningPathGenerateRequest request) {
        // TODO phase 4 - get current userId from SecurityContext, call learningPathService.generatePath()
        throw new UnsupportedOperationException("Not implemented yet - TODO phase 4");
    }

    @GetMapping("/")
    public Result<List<LearningPathDTO>> listPaths() {
        // TODO phase 4 - get current userId from SecurityContext, call learningPathService.listPaths()
        throw new UnsupportedOperationException("Not implemented yet - TODO phase 4");
    }

    @GetMapping("/{id}")
    public Result<LearningPathDTO> getPathById(@PathVariable Long id) {
        // TODO phase 4 - call learningPathService.getPathById(id)
        throw new UnsupportedOperationException("Not implemented yet - TODO phase 4");
    }

    @PutMapping("/{pathId}/steps/{stepId}")
    public Result<Void> updateStepStatus(
            @PathVariable Long pathId,
            @PathVariable Long stepId,
            @RequestParam String status) {
        // TODO phase 4 - call learningPathService.updateStepStatus(pathId, stepId, status)
        throw new UnsupportedOperationException("Not implemented yet - TODO phase 4");
    }

    @DeleteMapping("/{id}")
    public Result<Void> deletePath(@PathVariable Long id) {
        // TODO phase 4 - call learningPathService.deletePath(id)
        throw new UnsupportedOperationException("Not implemented yet - TODO phase 4");
    }
}
