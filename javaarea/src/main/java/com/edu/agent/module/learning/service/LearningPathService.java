package com.edu.agent.module.learning.service;

import com.edu.agent.module.learning.dto.LearningPathDTO;
import com.edu.agent.module.learning.dto.LearningPathGenerateRequest;

import java.util.List;

public interface LearningPathService {

    /**
     * Generate a learning path for the given user and request.
     */
    LearningPathDTO generatePath(Long userId, LearningPathGenerateRequest request);

    /**
     * List all learning paths for a user.
     */
    List<LearningPathDTO> listPaths(Long userId);

    /**
     * Get a single learning path by ID.
     */
    LearningPathDTO getPathById(Long pathId);

    /**
     * Update the status of a step within a learning path.
     */
    void updateStepStatus(Long pathId, Long stepId, String status);

    /**
     * Delete a learning path.
     */
    void deletePath(Long pathId);
}
