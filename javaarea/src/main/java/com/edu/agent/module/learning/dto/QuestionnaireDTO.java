package com.edu.agent.module.learning.dto;

import lombok.Data;
import java.util.List;

@Data
public class QuestionnaireDTO {

    private Boolean isCompleted;

    // ========== 一、基础身份与背景 ==========
    private String educationLevel;      // HIGH_SCHOOL / ASSOCIATE / BACHELOR / MASTER / PHD / OTHER
    private String majorDirection;      // 专业方向
    private String ageRange;            // UNDER_18 / 18_22 / 23_30 / 31_40 / ABOVE_40

    // ========== 二、目标与动机 ==========
    private List<String> learningGoals; // EXAM / INTEREST / EMPLOYMENT / PROMOTION / SELF_IMPROVEMENT / OTHER
    private String goalClarity;         // CLEAR / VAGUE / UNDECIDED
    private String motivationLevel;     // STRONG / MODERATE / WEAK

    // ========== 三、知识储备与能力现状 ==========
    private String subjectLevel;        // ZERO_BASIC / BEGINNER / INTERMEDIATE / ADVANCED
    private List<String> selfStrengths; // LOGICAL / MEMORY / CREATIVITY / PRACTICAL / COMMUNICATION / MATH / LANGUAGE / PROGRAMMING
    private List<String> selfWeaknesses;// 同上选项

    // ========== 四、学习风格与偏好 ==========
    private List<String> learningMethods; // VIDEO / READING / HANDS_ON / DISCUSSION / LECTURE / QUIZ
    private List<String> studyTimeSlots;  // MORNING / FORENOON / AFTERNOON / EVENING / NIGHT
    private String sessionDuration;       // LESS_30MIN / 30_60MIN / 1_2HOURS / 2_4HOURS / MORE_4HOURS

    // ========== 五、元认知与自律性 ==========
    private String planningHabit;        // ALWAYS / OFTEN / SOMETIMES / RARELY / NEVER
    private String focusLevel;           // VERY_HIGH / HIGH / MODERATE / LOW / VERY_LOW
    private String reviewHabit;          // EVERY_TIME / OFTEN / SOMETIMES / RARELY / NEVER

    // ========== 六、环境与资源支持 ==========
    private String dailyStudyHours;      // LESS_1H / 1_2H / 2_4H / 4_6H / MORE_6H
    private List<String> devices;        // PHONE / TABLET / LAPTOP / DESKTOP / BOOKS / NONE
    private String hasMentor;            // YES / NO / WANT

    // ========== 七、心理障碍与过往失败史 ==========
    private String hasPastFailures;      // YES / NO / NOT_SURE
    private List<String> mainBarriers;   // LAZINESS / DISTRACTION / NO_METHOD / NO_CONFIDENCE / NO_TIME / NO_SUPPORT / BORING / ANXIETY
    private String confidenceLevel;      // VERY_HIGH / HIGH / MODERATE / LOW / VERY_LOW
}
