package com.edu.agent.common.exception;

import com.edu.agent.common.result.Result;
import com.edu.agent.common.result.ResultCode;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@Slf4j
@RestControllerAdvice("com.edu.agent")
public class GlobalExceptionHandler {

    /**
     * Handle business exceptions.
     */
    @ExceptionHandler(BizException.class)
    public Result<Void> handleBizException(BizException e) {
        log.warn("Business Exception: code={}, message={}", e.getResultCode().getCode(), e.getMessage());
        return Result.fail(e.getResultCode());
    }

    /**
     * Handle validation exceptions from @Valid annotations.
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public Result<Void> handleValidException(MethodArgumentNotValidException e) {
        // Extract the first validation error message
        String message = e.getBindingResult().getAllErrors().get(0).getDefaultMessage();
        log.warn("Validation Exception: {}", message);
        return Result.fail(ResultCode.BAD_REQUEST.getCode(), message);
    }

    /**
     * Handle all other uncaught exceptions.
     */
    @ExceptionHandler(Exception.class)
    public Result<Void> handleException(Exception e) {
        log.error("Unhandled Exception: ", e);
        return Result.fail(ResultCode.INTERNAL_ERROR);
    }
}