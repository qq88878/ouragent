package com.edu.agent.module.learning.service;

import com.edu.agent.module.learning.dto.LearningPathDTO;
import com.edu.agent.module.learning.dto.LearningPathGenerateRequest;

import java.util.List;

public interface LearningPathService {

    LearningPathDTO generatePath(Long userId, LearningPathGenerateRequest request);

    List<LearningPathDTO> listPaths(Long userId);

    List<LearningPathDTO> listPaths(Long userId, boolean includeArchived);

    LearningPathDTO getPathById(Long pathId);

    void updateStepStatus(Long pathId, Long stepId, String status);

    void deletePath(Long pathId);

    void toggleStar(Long pathId);

    void toggleArchive(Long pathId);
}
