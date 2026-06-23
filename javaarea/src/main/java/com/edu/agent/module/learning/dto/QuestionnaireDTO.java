package com.edu.agent.module.learning.dto;

import java.util.List;

/**
 * 简洁问卷 DTO — 6 字段基础画像（跨课程共享）
 *
 * 四个分区：
 *   一、基础身份  — educationLevel, majorDirection
 *   二、学习目标  — learningGoals
 *   三、学习风格  — learningMethods
 *   四、自我认知  — selfStrengths, selfWeaknesses
 */
public class QuestionnaireDTO {
    private Boolean isCompleted;

    // 一、基础身份
    private String educationLevel;   // HIGH_SCHOOL / ASSOCIATE / BACHELOR / MASTER / PHD / OTHER
    private String majorDirection;   // 自由输入

    // 二、学习目标（多选）
    private List<String> learningGoals;  // EXAM / POSTGRADUATE / EMPLOYMENT / SELF_IMPROVEMENT

    // 三、学习风格（多选）
    private List<String> learningMethods; // VIDEO / READING / DISCUSSION / QUIZ

    // 四、自我认知（多选）
    private List<String> selfStrengths;   // COMPREHENSION / MEMORY / FOCUS / DISCIPLINE / EXPRESSION
    private List<String> selfWeaknesses;  // 同上

    public QuestionnaireDTO() {}

    public Boolean getIsCompleted() { return isCompleted; }
    public void setIsCompleted(Boolean isCompleted) { this.isCompleted = isCompleted; }

    public String getEducationLevel() { return educationLevel; }
    public void setEducationLevel(String educationLevel) { this.educationLevel = educationLevel; }

    public String getMajorDirection() { return majorDirection; }
    public void setMajorDirection(String majorDirection) { this.majorDirection = majorDirection; }

    public List<String> getLearningGoals() { return learningGoals; }
    public void setLearningGoals(List<String> learningGoals) { this.learningGoals = learningGoals; }

    public List<String> getLearningMethods() { return learningMethods; }
    public void setLearningMethods(List<String> learningMethods) { this.learningMethods = learningMethods; }

    public List<String> getSelfStrengths() { return selfStrengths; }
    public void setSelfStrengths(List<String> selfStrengths) { this.selfStrengths = selfStrengths; }

    public List<String> getSelfWeaknesses() { return selfWeaknesses; }
    public void setSelfWeaknesses(List<String> selfWeaknesses) { this.selfWeaknesses = selfWeaknesses; }
}
