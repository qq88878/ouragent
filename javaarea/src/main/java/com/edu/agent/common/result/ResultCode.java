package com.edu.agent.common.result;

import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public enum ResultCode {

    SUCCESS(200, "操作成功"),

    FAILURE(500, "操作失败"),

    BAD_REQUEST(400, "错误的请求"),
    UNAUTHORIZED(401, "未经授权"),
    FORBIDDEN(403, "禁止访问"),
    NOT_FOUND(404, "未找到资源"),
    USER_ALREADY_EXISTS(409, "用户已存在"),
    EMAIL_ALREADY_EXISTS(409, "邮箱已被注册"),
    INVALID_CREDENTIALS(401, "用户名或密码无效"),
    PASSWORD_TOO_WEAK(400, "密码强度不足，至少需要6个字符"),

    INTERNAL_ERROR(500, "服务器内部错误"),
    AGENT_UNAVAILABLE(503, "代理服务不可用");

    private final int code;

    private final String message;
}