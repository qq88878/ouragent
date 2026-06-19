package com.edu.agent.module.learning.controller;

import com.edu.agent.common.result.Result;
import com.edu.agent.module.learning.service.StudentProfileQuestionnaireService;
import com.edu.agent.security.LoginUser;
import com.edu.agent.module.learning.dto.QuestionnaireDTO;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/profile/questionnaire")
@PreAuthorize("hasRole('STUDENT')")
public class StudentProfileQuestionnaireController {

    private final StudentProfileQuestionnaireService questionnaireService;
    public StudentProfileQuestionnaireController(StudentProfileQuestionnaireService questionnaireService) {
        this.questionnaireService = questionnaireService;
    }

    @GetMapping("/")
    public Result<QuestionnaireDTO> getQuestionnaire() {
        LoginUser loginUser = (LoginUser) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        return Result.success(questionnaireService.getQuestionnaire(loginUser.getUser().getId()));
    }

    @PutMapping("/")
    public Result<Void> saveQuestionnaire(@RequestBody QuestionnaireDTO dto) {
        LoginUser loginUser = (LoginUser) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        questionnaireService.saveQuestionnaire(loginUser.getUser().getId(), dto);
        return Result.success();
    }

    @GetMapping("/status")
    public Result<Map<String, Boolean>> getStatus() {
        LoginUser loginUser = (LoginUser) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        boolean completed = questionnaireService.isCompleted(loginUser.getUser().getId());
        return Result.success(Map.of("completed", completed));
    }
}
