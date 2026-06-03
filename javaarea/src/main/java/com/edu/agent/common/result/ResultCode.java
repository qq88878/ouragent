package com.edu.agent.common.result;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * Enumeration of standard API result codes.
 */
@Getter
@AllArgsConstructor
public enum ResultCode {

    SUCCESS(200, "success"),
    BAD_REQUEST(400, "bad request"),
    UNAUTHORIZED(401, "unauthorized"),
    FORBIDDEN(403, "forbidden"),
    NOT_FOUND(404, "not found"),
    INTERNAL_ERROR(500, "internal server error"),
    AGENT_UNAVAILABLE(503, "agent service unavailable");

    /** Numeric status code */
    private final int code;

    /** Human-readable message */
    private final String message;
}
