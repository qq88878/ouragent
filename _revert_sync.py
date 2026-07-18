with open("javaarea/src/main/java/com/edu/agent/module/learning/service/impl/LearningPathServiceImpl.java","r",encoding="utf-8") as f:
    content = f.read()

# Replace the entire generatePathFromChat + helper methods with a simpler sync version
start_marker = "public LearningPathDTO generatePathFromChat(Long userId, Long courseId"
end_marker = "    @Override\n    public List<LearningPathDTO> listPaths(Long userId) {"

old_method_start = content.find(start_marker)
old_method_end = content.find(end_marker)

# Clean sync method (same logic, no async)
sync_method = '''public LearningPathDTO generatePathFromChat(Long userId, Long courseId, List<Map<String, String>> messages) {
        String courseTitle = "\u8bfe\u7a0b";
        String courseDesc = "";
        if (courseId != null) { Course c = courseMapper.selectById(courseId); if (c != null) { courseTitle = c.getTitle(); if (c.getDescription() != null) courseDesc = c.getDescription(); } }
        int mv = 0;
        LambdaQueryWrapper<LearningPath> ew = new LambdaQueryWrapper<>();
        ew.eq(LearningPath::getUserId, userId).eq(LearningPath::getArchived, 0);
        if (courseId != null) ew.eq(LearningPath::getCourseId, courseId); else ew.isNull(LearningPath::getCourseId);
        for (LearningPath old : list(ew)) { old.setArchived(1); if (old.getVersion() != null && old.getVersion() > mv) mv = old.getVersion(); updateById(old); }
        LearningPath path = new LearningPath();
        path.setUserId(userId); path.setCourseId(courseId);
        path.setTitle(courseTitle + " - \u4e2a\u6027\u5316\u5b66\u4e60\u8def\u5f84");
        path.setDescription("AI\u6b63\u5728\u5206\u6790\u5bf9\u8bdd\u5185\u5bb9\uff0c\u751f\u6210\u4e2a\u6027\u5316\u5b66\u4e60\u8def\u5f84...");
        path.setStatus(3); path.setVersion(mv + 1); path.setArchived(0); path.setStarred(0); path.setTotalSteps(0); path.setCompletedSteps(0);
        save(path);
        Long pid = path.getId();
        String cid = courseId != null ? String.valueOf(courseId) : null;

        // Sync LLM call
        AgentLearningPathResponse ar = null;
        try {
            ar = agentServiceClient.generatePathFromChat(messages, cid, courseTitle, courseDesc);
        } catch (Exception e) {
            log.error("LLM call failed for pathId={}, using fallback", pid, e);
        }
        if (ar == null) ar = generateDefaultPath(courseTitle);

        path.setTitle(ar.getTitle() != null ? ar.getTitle() : courseTitle + " - \u5b66\u4e60\u8def\u5f84");
        path.setDescription(ar.getDescription() != null ? ar.getDescription() : "\u57fa\u4e8e\u5bf9\u8bdd\u751f\u6210");
        path.setStatus(0);
        List<AgentLearningPathResponse.Step> steps = ar.getStepsSafe();
        path.setTotalSteps(steps.size()); updateById(path);
        if (steps.isEmpty()) {
            // If LLM returned empty (timeout fallback), use default
            ar = generateDefaultPath(courseTitle);
            steps = ar.getStepsSafe();
            path.setTitle(ar.getTitle()); path.setTotalSteps(steps.size()); updateById(path);
        }
        for (int i = 0; i < steps.size(); i++) {
            AgentLearningPathResponse.Step sd = steps.get(i);
            LearningPathStep step = new LearningPathStep();
            step.setPathId(pid); step.setStepOrder(i + 1);
            step.setTitle(sd.getTitle() != null ? sd.getTitle() : "\u6b65\u9aa4 " + (i + 1));
            step.setDescription(sd.getDescription() != null ? sd.getDescription() : "");
            step.setStatus(0);
            if (sd.getKnowledgeIds() != null && !sd.getKnowledgeIds().isEmpty()) step.setKnowledgeIds(sd.getKnowledgeIds().stream().map(String::valueOf).collect(java.util.stream.Collectors.joining(",")));
            step.setEstimatedHours(sd.getEstimatedHours() != null ? sd.getEstimatedHours() : 2);
            step.setStepType(inferStepType(sd.getTitle(), sd.getDescription()));
            stepMapper.insert(step);
        }
        log.info("Path generation complete: pathId={}, steps={}", pid, steps.size());

        // Auto-generate content and exercises in background
        try {
            autoGenerateContentAndExercises(pid);
        } catch (Exception e) { log.warn("Auto-gen failed for pathId={}: {}", pid, e.getMessage()); }

        return getPathById(pid);
    }

    private void autoGenerateContentAndExercises(Long pathId) {
        List<LearningPathStep> steps = stepMapper.selectList(new LambdaQueryWrapper<LearningPathStep>().eq(LearningPathStep::getPathId, pathId));
        for (LearningPathStep step : steps) { try {
            if (step.getContent() == null || step.getContent().isEmpty()) {
                List<Integer> kids = parseKnowledgeIds(step.getKnowledgeIds());
                Map<String, Object> cr = agentServiceClient.generateStepContent(step.getTitle(), kids);
                step.setContent(cr.getOrDefault("content", "").toString());
            }
            if (step.getExercises() == null || step.getExercises().isEmpty() || "{}".equals(step.getExercises())) {
                String diff = "easy";
                if (step.getStepType() != null) switch (step.getStepType()) { case "CONCEPT": diff = "easy"; break; case "PRACTICE": case "REVIEW": diff = "medium"; break; case "PROJECT": diff = "hard"; break; }
                List<Integer> kids = parseKnowledgeIds(step.getKnowledgeIds());
                step.setExercises(new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(agentServiceClient.generateExercises(step.getTitle(), kids, diff, 3)));
            }
            step.setUpdateTime(java.time.LocalDateTime.now()); stepMapper.updateById(step);
        } catch (Exception e) { log.warn("Auto-gen step {}: {}", step.getId(), e.getMessage()); } }
        log.info("Auto-gen complete: pathId={}", pathId);
    }

'''

content = content[:old_method_start] + sync_method + "\n" + content[old_method_end:]

# Clean up unused imports
content = content.replace("import java.util.concurrent.CompletableFuture;\n", "")
content = content.replace("import java.util.concurrent.Executor;\n", "")

# Clean up unused fields
content = content.replace("    private final Executor agentExecutor;\n", "")

# Clean up constructor
content = content.replace(",\n            @Qualifier(\"agentExecutor\") Executor agentExecutor", "")
content = content.replace("        this.agentExecutor = agentExecutor;\n", "")

with open("javaarea/src/main/java/com/edu/agent/module/learning/service/impl/LearningPathServiceImpl.java","w",encoding="utf-8") as f:
    f.write(content)

b = content.count("{")
print(f"Braces: {b} vs {content.count('}')}, diff={b-content.count('}')}")
