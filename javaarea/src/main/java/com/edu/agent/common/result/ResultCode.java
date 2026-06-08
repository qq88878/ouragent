package com.edu.agent.common.result;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * Enumeration of standard API result codes.
 */
@Getter
@AllArgsConstructor
public enum ResultCode {

    // Success
    SUCCESS(200, "操作成功"),

    // Generic Failure
    FAILURE(500, "操作失败"),

    // Client Errors
    BAD_REQUEST(400, "错误的请求"),
    UNAUTHORIZED(401, "未经授权"),
    FORBIDDEN(403, "禁止访问"),
    NOT_FOUND(404, "未找到资源"),
    USER_ALREADY_EXISTS(409, "用户已存在"),
    EMAIL_ALREADY_EXISTS(409, "邮箱已被注册"),
    INVALID_CREDENTIALS(401, "用户名或密码无效"),


    // Server Errors
    INTERNAL_ERROR(500, "服务器内部错误"),
    AGENT_UNAVAILABLE(503, "代理服务不可用");


    /** Numeric status code */
    private final int code;

    /** Human-readable message */
    private final String message;
}