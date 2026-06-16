package com.edu.agent.module.learning.service;

import com.edu.agent.module.learning.dto.QuestionnaireDTO;

public interface StudentProfileQuestionnaireService {
    QuestionnaireDTO getQuestionnaire(Long userId);
    void saveQuestionnaire(Long userId, QuestionnaireDTO dto);
    boolean isCompleted(Long userId);
}
