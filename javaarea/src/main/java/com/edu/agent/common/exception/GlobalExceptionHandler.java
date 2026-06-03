package com.edu.agent.common.exception;

import com.edu.agent.common.result.Result;
import com.edu.agent.common.result.ResultCode;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * Global exception handler for REST controllers.
 */
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    // TODO: Inject any required dependencies (e.g. i18n message source)

    /**
     * Handle business exceptions.
     */
    @ExceptionHandler(BizException.class)
    public Result<Void> handleBizException(BizException e) {
        // TODO: Log and return Result.fail with e.getResultCode()
        return null;
    }

    /**
     * Handle validation exceptions from @Valid annotations.
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public Result<Void> handleValidException(MethodArgumentNotValidException e) {
        // TODO: Extract first field error message, return Result.fail(400, message)
        return null;
    }

    /**
     * Handle all other uncaught exceptions.
     */
    @ExceptionHandler(Exception.class)
    public Result<Void> handleException(Exception e) {
        // TODO: Log error stack, return Result.fail(500, "internal server error")
        return null;
    }
}
