package com.edu.agent.common.exception;

import com.edu.agent.common.result.ResultCode;
import lombok.Getter;

/**
 * Business exception carrying a ResultCode.
 */
@Getter
public class BizException extends RuntimeException {

    private static final long serialVersionUID = 1L;

    /** Business error code */
    private final ResultCode resultCode;

    /**
     * Construct with a ResultCode.
     */
    public BizException(ResultCode resultCode) {
        super(resultCode.getMessage());
        this.resultCode = resultCode;
    }

    /**
     * Construct with a ResultCode and custom message.
     */
    public BizException(ResultCode resultCode, String message) {
        super(message);
        this.resultCode = resultCode;
    }

    /**
     * Construct with a ResultCode, custom message, and cause.
     */
    public BizException(ResultCode resultCode, String message, Throwable cause) {
        super(message, cause);
        this.resultCode = resultCode;
    }
}
