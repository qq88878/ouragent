package com.edu.agent.common.result;

import lombok.Data;
import java.io.Serializable;

/**
 * Generic API response wrapper.
 *
 * @param <T> the type of the data payload
 */
@Data
public class Result<T> implements Serializable {

    private static final long serialVersionUID = 1L;

    /** Response status code */
    private int code;

    /** Response message */
    private String message;

    /** Response data payload */
    private T data;

    private Result() {}

    private Result(int code, String message) {
        this.code = code;
        this.message = message;
    }

    private Result(int code, String message, T data) {
        this.code = code;
        this.message = message;
        this.data = data;
    }

    /**
     * Return a success result with data.
     */
    public static <T> Result<T> success(T data) {
        return new Result<>(ResultCode.SUCCESS.getCode(), ResultCode.SUCCESS.getMessage(), data);
    }

    /**
     * Return a success result without data.
     */
    public static <T> Result<T> success() {
        return new Result<>(ResultCode.SUCCESS.getCode(), ResultCode.SUCCESS.getMessage());
    }

    /**
     * Return a failure result with message.
     */
    public static <T> Result<T> fail(String message) {
        return new Result<>(ResultCode.FAILURE.getCode(), message);
    }

    /**
     * Return a failure result from a ResultCode.
     */
    public static <T> Result<T> fail(ResultCode code) {
        return new Result<>(code.getCode(), code.getMessage());
    }

    /**
     * Return a failure result with custom code and message.
     */
    public static <T> Result<T> fail(int code, String message) {
        return new Result<>(code, message);
    }
}