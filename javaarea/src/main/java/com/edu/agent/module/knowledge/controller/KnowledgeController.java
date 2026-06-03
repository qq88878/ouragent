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
@RequestMapping("/api/knowledge")
@RequiredArgsConstructor
public class KnowledgeController {

    private final KnowledgeService knowledgeService;

    // TODO phase 2: teacher role check
    @PostMapping("/upload")
    public Result<KnowledgeDTO> upload(@RequestParam("file") MultipartFile file,
                                       @ModelAttribute KnowledgeUploadDTO dto) {
        // TODO phase 2: upload knowledge file for a course
        throw new UnsupportedOperationException("Not implemented yet - phase 2");
    }

    @GetMapping
    public Result<List<KnowledgeDTO>> list(@RequestParam Long courseId) {
        // TODO phase 2: list knowledge entries by course
        throw new UnsupportedOperationException("Not implemented yet - phase 2");
    }

    @GetMapping("/{id}")
    public Result<KnowledgeDTO> getById(@PathVariable Long id) {
        // TODO phase 2: get knowledge detail by id
        throw new UnsupportedOperationException("Not implemented yet - phase 2");
    }

    // TODO phase 2: teacher role check
    @DeleteMapping("/{id}")
    public Result<Void> delete(@PathVariable Long id) {
        // TODO phase 2: delete knowledge entry (teacher only)
        throw new UnsupportedOperationException("Not implemented yet - phase 2");
    }

    // TODO phase 2: teacher role check
    @PostMapping("/{id}/reprocess")
    public Result<Void> reprocess(@PathVariable Long id) {
        // TODO phase 2: re-trigger vectorization for the knowledge entry
        throw new UnsupportedOperationException("Not implemented yet - phase 2");
    }
}
