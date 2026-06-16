package com.edu.agent.module.learning.dto;

import lombok.Data;

import java.util.List;
import java.util.Collections;

/**
 * Typed response from Python Agent /agent/plan endpoint.
 * Replaces untyped Map<String, Object> to catch field-name drift at compile time.
 */
@Data
public class AgentLearningPathResponse {

    private String title;

    private String description;

    private Integer totalSteps;

    private List<Step> steps;

    @Data
    public static class Step {
        private Integer order;
        private String title;
        private String description;
        private List<Integer> knowledgeIds;
        private Integer estimatedHours;
        private List<String> resources;
    }

    public List<Step> getStepsSafe() {
        return steps != null ? steps : Collections.emptyList();
    }
}
