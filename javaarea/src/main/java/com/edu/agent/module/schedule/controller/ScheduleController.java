package com.edu.agent.module.schedule.controller;

import com.edu.agent.common.result.Result;
import com.edu.agent.common.result.ResultCode;
import com.edu.agent.module.schedule.dto.*;
import com.edu.agent.module.schedule.service.ScheduleService;
import com.edu.agent.security.LoginUser;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Slf4j
@RestController
@RequestMapping("/schedule")
@RequiredArgsConstructor
@PreAuthorize("hasRole('STUDENT')")
public class ScheduleController {

    private final ScheduleService scheduleService;

    @GetMapping("/ping")
    public Result<String> ping() {
        return Result.success("ok");
    }

    @GetMapping("/config")
    public Result<?> getConfig() {
        try {
            Long userId = getUserId();
            return Result.success(scheduleService.getConfig(userId));
        } catch (Exception e) {
            log.error("getConfig error", e);
            return Result.fail(ResultCode.INTERNAL_ERROR.getCode(), e.getClass().getSimpleName() + ": " + e.getMessage());
        }
    }

    @PutMapping("/config")
    public Result<?> saveConfig(@Valid @RequestBody SaveConfigRequest request) {
        try {
            Long userId = getUserId();
            scheduleService.saveConfig(userId, request);
            return Result.success();
        } catch (Exception e) {
            log.error("saveConfig error", e);
            return Result.fail(ResultCode.INTERNAL_ERROR.getCode(), e.getClass().getSimpleName() + ": " + e.getMessage());
        }
    }

    @GetMapping("/courses")
    public Result<?> listCourses() {
        try {
            Long userId = getUserId();
            return Result.success(scheduleService.listCourses(userId));
        } catch (Exception e) {
            log.error("listCourses error", e);
            return Result.fail(ResultCode.INTERNAL_ERROR.getCode(), e.getClass().getSimpleName() + ": " + e.getMessage());
        }
    }

    @PostMapping("/courses")
    public Result<?> createCourse(@Valid @RequestBody CreateCourseRequest request) {
        try {
            Long userId = getUserId();
            return Result.success(scheduleService.createCourse(userId, request));
        } catch (Exception e) {
            log.error("createCourse error", e);
            return Result.fail(ResultCode.INTERNAL_ERROR.getCode(), e.getClass().getSimpleName() + ": " + e.getMessage());
        }
    }

    @PutMapping("/courses/{courseId}")
    public Result<?> updateCourse(@PathVariable Long courseId,
                                   @Valid @RequestBody CreateCourseRequest request) {
        try {
            Long userId = getUserId();
            return Result.success(scheduleService.updateCourse(userId, courseId, request));
        } catch (Exception e) {
            log.error("updateCourse error", e);
            return Result.fail(ResultCode.INTERNAL_ERROR.getCode(), e.getClass().getSimpleName() + ": " + e.getMessage());
        }
    }

    @DeleteMapping("/courses/{courseId}")
    public Result<?> deleteCourse(@PathVariable Long courseId) {
        try {
            Long userId = getUserId();
            scheduleService.deleteCourse(userId, courseId);
            return Result.success();
        } catch (Exception e) {
            log.error("deleteCourse error", e);
            return Result.fail(ResultCode.INTERNAL_ERROR.getCode(), e.getClass().getSimpleName() + ": " + e.getMessage());
        }
    }

    @GetMapping("/week-view")
    public Result<?> getWeekView(@RequestParam(defaultValue = "0") Integer weekOffset) {
        try {
            Long userId = getUserId();
            return Result.success(scheduleService.getWeekView(userId, weekOffset));
        } catch (Exception e) {
            log.error("getWeekView error", e);
            return Result.fail(ResultCode.INTERNAL_ERROR.getCode(), e.getClass().getSimpleName() + ": " + e.getMessage());
        }
    }

    private Long getUserId() {
        LoginUser loginUser = (LoginUser) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        return loginUser.getUser().getId();
    }
}