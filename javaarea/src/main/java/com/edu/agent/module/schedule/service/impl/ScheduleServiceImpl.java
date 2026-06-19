package com.edu.agent.module.schedule.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.edu.agent.common.exception.BizException;
import com.edu.agent.common.result.ResultCode;
import com.edu.agent.module.schedule.dto.*;
import com.edu.agent.module.schedule.entity.ScheduleConfig;
import com.edu.agent.module.schedule.entity.ScheduleCourse;
import com.edu.agent.module.schedule.mapper.ScheduleConfigMapper;
import com.edu.agent.module.schedule.mapper.ScheduleCourseMapper;
import com.edu.agent.module.schedule.service.ScheduleService;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class ScheduleServiceImpl implements ScheduleService {

    private final ScheduleConfigMapper configMapper;
    private final ScheduleCourseMapper courseMapper;
    private final ObjectMapper objectMapper;
    public ScheduleServiceImpl(ScheduleConfigMapper configMapper, ScheduleCourseMapper courseMapper, ObjectMapper objectMapper) {
        this.configMapper = configMapper;
        this.courseMapper = courseMapper;
        this.objectMapper = objectMapper;
    }

    @Override
    public ScheduleConfigDTO getConfig(Long userId) {
        ScheduleConfig config = configMapper.selectOne(
                new LambdaQueryWrapper<ScheduleConfig>().eq(ScheduleConfig::getUserId, userId));
        if (config == null) {
            return new ScheduleConfigDTO(null, null, defaultPeriods());
        }
        return toConfigDTO(config);
    }

    @Override
    @Transactional
    public void saveConfig(Long userId, SaveConfigRequest request) {
        ScheduleConfig existing = configMapper.selectOne(
                new LambdaQueryWrapper<ScheduleConfig>().eq(ScheduleConfig::getUserId, userId));
        try {
            String periodJson = objectMapper.writeValueAsString(request.getPeriodConfig());
            LocalDate startDate = LocalDate.parse(request.getSemesterStartDate());
            if (existing != null) {
                existing.setSemesterStartDate(startDate);
                existing.setPeriodConfig(periodJson);
                configMapper.updateById(existing);
            } else {
                ScheduleConfig config = new ScheduleConfig();
                config.setUserId(userId);
                config.setSemesterStartDate(startDate);
                config.setPeriodConfig(periodJson);
                configMapper.insert(config);
            }
        } catch (JsonProcessingException e) {
            throw new BizException(ResultCode.INTERNAL_ERROR, "时间段配置序列化失败");
        }
    }

    @Override
    public List<ScheduleCourseDTO> listCourses(Long userId) {
        List<ScheduleCourse> courses = courseMapper.selectList(
                new LambdaQueryWrapper<ScheduleCourse>().eq(ScheduleCourse::getUserId, userId));
        return courses.stream().map(this::toCourseDTO).collect(Collectors.toList());
    }

    @Override
    @Transactional
    public ScheduleCourseDTO createCourse(Long userId, CreateCourseRequest request) {
        ScheduleCourse course = new ScheduleCourse();
        course.setUserId(userId);
        course.setName(request.getName());
        try {
            course.setWeekNumbers(objectMapper.writeValueAsString(request.getWeekNumbers()));
            course.setDayOfWeeks(objectMapper.writeValueAsString(request.getDayOfWeeks()));
            course.setPeriodIndexes(objectMapper.writeValueAsString(request.getPeriodIndexes()));
        } catch (JsonProcessingException e) {
            throw new BizException(ResultCode.INTERNAL_ERROR, "课程数据序列化失败");
        }
        courseMapper.insert(course);
        return toCourseDTO(course);
    }

    @Override
    @Transactional
    public ScheduleCourseDTO updateCourse(Long userId, Long courseId, CreateCourseRequest request) {
        ScheduleCourse course = courseMapper.selectById(courseId);
        if (course == null || !course.getUserId().equals(userId)) {
            throw new BizException(ResultCode.NOT_FOUND, "课程不存在");
        }
        course.setName(request.getName());
        try {
            course.setWeekNumbers(objectMapper.writeValueAsString(request.getWeekNumbers()));
            course.setDayOfWeeks(objectMapper.writeValueAsString(request.getDayOfWeeks()));
            course.setPeriodIndexes(objectMapper.writeValueAsString(request.getPeriodIndexes()));
        } catch (JsonProcessingException e) {
            throw new BizException(ResultCode.INTERNAL_ERROR, "课程数据序列化失败");
        }
        courseMapper.updateById(course);
        return toCourseDTO(course);
    }

    @Override
    @Transactional
    public void deleteCourse(Long userId, Long courseId) {
        ScheduleCourse course = courseMapper.selectById(courseId);
        if (course == null || !course.getUserId().equals(userId)) {
            throw new BizException(ResultCode.NOT_FOUND, "课程不存在");
        }
        courseMapper.deleteById(courseId);
    }

    @Override
    public ScheduleWeekViewDTO getWeekView(Long userId, Integer weekOffset) {
        ScheduleConfig config = configMapper.selectOne(
                new LambdaQueryWrapper<ScheduleConfig>().eq(ScheduleConfig::getUserId, userId));
        if (config == null || config.getSemesterStartDate() == null) {
            throw new BizException(ResultCode.BAD_REQUEST, "请先设置开学日期和时间段配置");
        }

        List<ScheduleConfigDTO.PeriodConfig> periods = parsePeriodConfig(config.getPeriodConfig());
        LocalDate semesterStart = config.getSemesterStartDate();

        LocalDate firstMonday = semesterStart.with(DayOfWeek.MONDAY);
        LocalDate weekMonday = semesterStart.plusWeeks(weekOffset).with(DayOfWeek.MONDAY);

        if (weekMonday.isBefore(firstMonday)) {
            weekMonday = firstMonday;
        }

        LocalDate weekSunday = weekMonday.plusDays(6);
        int weekNumber = (int) ChronoUnit.WEEKS.between(firstMonday, weekMonday) + 1;

        List<ScheduleCourse> courses = courseMapper.selectList(
                new LambdaQueryWrapper<ScheduleCourse>().eq(ScheduleCourse::getUserId, userId));

        List<ScheduleWeekViewDTO.DaySchedule> days = new ArrayList<>();
        for (int i = 0; i < 7; i++) {
            LocalDate date = weekMonday.plusDays(i);
            int dayOfWeek = i + 1;

            String dayLabel;
            if (!date.isBefore(semesterStart) && ChronoUnit.WEEKS.between(firstMonday, date.with(DayOfWeek.MONDAY)) + 1 == weekNumber) {
                dayLabel = dayOfWeekName(dayOfWeek);
            } else {
                dayLabel = "非本周";
            }

            List<ScheduleWeekViewDTO.PeriodSlot> slots = new ArrayList<>();
            for (int pi = 0; pi < periods.size(); pi++) {
                ScheduleConfigDTO.PeriodConfig pc = periods.get(pi);
                String courseName = findCourseAt(courses, weekNumber, dayOfWeek, pi);
                ScheduleWeekViewDTO.PeriodSlot slot = new ScheduleWeekViewDTO.PeriodSlot();
                slot.setPeriodIndex(pi);
                slot.setPeriodName(pc.getName());
                slot.setStartTime(pc.getStartTime());
                slot.setEndTime(pc.getEndTime());
                slot.setCourseName(courseName);
                slots.add(slot);
            }

            ScheduleWeekViewDTO.DaySchedule day = new ScheduleWeekViewDTO.DaySchedule();
            day.setDayOfWeek(dayOfWeek);
            day.setDate(date);
            day.setDayLabel(dayLabel);
            day.setPeriods(slots);
            days.add(day);
        }

        ScheduleWeekViewDTO view = new ScheduleWeekViewDTO();
        view.setWeekNumber(weekNumber);
        view.setWeekStartDate(weekMonday);
        view.setWeekEndDate(weekSunday);
        view.setDays(days);
        return view;
    }

    private String findCourseAt(List<ScheduleCourse> courses, int weekNumber, int dayOfWeek, int periodIndex) {
        for (ScheduleCourse c : courses) {
            List<Integer> weeks = parseJsonList(c.getWeekNumbers());
            List<Integer> days = parseJsonList(c.getDayOfWeeks());
            List<Integer> periods = parseJsonList(c.getPeriodIndexes());
            if (weeks.contains(weekNumber) && days.contains(dayOfWeek) && periods.contains(periodIndex)) {
                return c.getName();
            }
        }
        return null;
    }

    private List<Integer> parseJsonList(String json) {
        try {
            return objectMapper.readValue(json, new TypeReference<List<Integer>>() {});
        } catch (Exception e) {
            return Collections.emptyList();
        }
    }

    private List<ScheduleConfigDTO.PeriodConfig> parsePeriodConfig(String json) {
        try {
            return objectMapper.readValue(json, new TypeReference<List<ScheduleConfigDTO.PeriodConfig>>() {});
        } catch (Exception e) {
            return defaultPeriods();
        }
    }

    private List<ScheduleConfigDTO.PeriodConfig> defaultPeriods() {
        List<ScheduleConfigDTO.PeriodConfig> periods = new ArrayList<>();
        periods.add(new ScheduleConfigDTO.PeriodConfig("第1节", "08:00", "08:45"));
        periods.add(new ScheduleConfigDTO.PeriodConfig("第2节", "08:55", "09:40"));
        periods.add(new ScheduleConfigDTO.PeriodConfig("第3节", "10:00", "10:45"));
        periods.add(new ScheduleConfigDTO.PeriodConfig("第4节", "10:55", "11:40"));
        periods.add(new ScheduleConfigDTO.PeriodConfig("第5节", "14:00", "14:45"));
        periods.add(new ScheduleConfigDTO.PeriodConfig("第6节", "14:55", "15:40"));
        periods.add(new ScheduleConfigDTO.PeriodConfig("第7节", "16:00", "16:45"));
        periods.add(new ScheduleConfigDTO.PeriodConfig("第8节", "16:55", "17:40"));
        return periods;
    }

    private String dayOfWeekName(int dow) {
        switch (dow) {
            case 1: return "周一";
            case 2: return "周二";
            case 3: return "周三";
            case 4: return "周四";
            case 5: return "周五";
            case 6: return "周六";
            case 7: return "周日";
            default: return "";
        }
    }

    private ScheduleConfigDTO toConfigDTO(ScheduleConfig config) {
        ScheduleConfigDTO dto = new ScheduleConfigDTO();
        dto.setId(config.getId());
        dto.setSemesterStartDate(config.getSemesterStartDate());
        dto.setPeriodConfig(parsePeriodConfig(config.getPeriodConfig()));
        return dto;
    }

    private ScheduleCourseDTO toCourseDTO(ScheduleCourse course) {
        ScheduleCourseDTO dto = new ScheduleCourseDTO();
        dto.setId(course.getId());
        dto.setName(course.getName());
        dto.setWeekNumbers(parseJsonList(course.getWeekNumbers()));
        dto.setDayOfWeeks(parseJsonList(course.getDayOfWeeks()));
        dto.setPeriodIndexes(parseJsonList(course.getPeriodIndexes()));
        return dto;
    }
}
