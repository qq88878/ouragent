package com.edu.agent.module.knowledge.controller;

import com.edu.agent.common.result.Result;
import com.edu.agent.module.knowledge.dto.KnowledgeDTO;
import com.edu.agent.module.knowledge.dto.KnowledgeUploadDTO;
import com.edu.agent.module.knowledge.service.KnowledgeService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

@RestController
@RequestMapping("/knowledge")
@RequiredArgsConstructor
public class KnowledgeController {

    private final KnowledgeService knowledgeService;

    @PostMapping("/upload")
    public Result<KnowledgeDTO> upload(@RequestParam("file") MultipartFile file,
                                       @ModelAttribute KnowledgeUploadDTO dto) {
        return Result.success(knowledgeService.uploadKnowledge(file, dto));
    }

    @GetMapping
    public Result<List<KnowledgeDTO>> list(@RequestParam Long courseId) {
        return Result.success(knowledgeService.listByCourse(courseId));
    }

    @GetMapping("/{id}")
    public Result<KnowledgeDTO> getById(@PathVariable Long id) {
        return Result.success(knowledgeService.getKnowledgeById(id));
    }

    @DeleteMapping("/{id}")
    public Result<Void> delete(@PathVariable Long id) {
        knowledgeService.deleteKnowledge(id);
        return Result.success();
    }

    @PostMapping("/{id}/reprocess")
    public Result<Void> reprocess(@PathVariable Long id) {
        knowledgeService.reprocessKnowledge(id);
        return Result.success();
    }
}
