package com.edu.agent.module.learning.service;

import com.edu.agent.module.learning.dto.LearningPathDTO;
import com.edu.agent.module.learning.dto.LearningPathGenerateRequest;

import java.util.List;
import java.util.Map;

public interface LearningPathService {

    LearningPathDTO generatePath(Long userId, LearningPathGenerateRequest request);

    LearningPathDTO generatePathFromChat(Long userId, Long courseId, List<Map<String, String>> messages);

    List<LearningPathDTO> listPaths(Long userId);

    List<LearningPathDTO> listPaths(Long userId, boolean includeArchived);

    LearningPathDTO getPathById(Long pathId);

    void updateStepStatus(Long pathId, Long stepId, String status);

    void deletePath(Long pathId);

    void toggleStar(Long pathId);

    void toggleArchive(Long pathId);

    // ===== Step Content & Exercises =====

    LearningPathDTO generateStepContent(Long pathId, Long stepId);
    LearningPathDTO generateStepExercises(Long pathId, Long stepId, int count);
    Map<String, Object> evaluateStepExercises(Long pathId, Long stepId, Map<String, String> answers);
    LearningPathDTO generateCheckpointTest(Long pathId, Long stepId, int questionCount);
    Map<String, Object> evaluateCheckpointTest(Long pathId, Long stepId, Map<String, String> answers);
        LearningPathDTO regenerateStepExercises(Long pathId, Long stepId);
    void recordStudyTime(Long pathId, int minutes);

}
