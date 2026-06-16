package com.edu.agent.module.schedule.service;

import com.edu.agent.module.schedule.dto.*;

import java.util.List;

public interface ScheduleService {

    /** 获取课表配置 */
    ScheduleConfigDTO getConfig(Long userId);

    /** 保存课表配置（开学日期+时间段） */
    void saveConfig(Long userId, SaveConfigRequest request);

    /** 列出所有课程 */
    List<ScheduleCourseDTO> listCourses(Long userId);

    /** 创建课程 */
    ScheduleCourseDTO createCourse(Long userId, CreateCourseRequest request);

    /** 更新课程 */
    ScheduleCourseDTO updateCourse(Long userId, Long courseId, CreateCourseRequest request);

    /** 删除课程 */
    void deleteCourse(Long userId, Long courseId);

    /** 获取某一周的课表视图 */
    ScheduleWeekViewDTO getWeekView(Long userId, Integer weekOffset);
}
