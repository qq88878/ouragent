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

    // TODO: Implement static factory methods

    /**
     * Return a success result with data.
     */
    public static <T> Result<T> ok(T data) {
        // TODO: Implement - set code=200, message="success", data=data
        return null;
    }

    /**
     * Return a success result without data.
     */
    public static <T> Result<T> ok() {
        // TODO: Implement - set code=200, message="success"
        return null;
    }

    /**
     * Return a failure result with message.
     */
    public static <T> Result<T> fail(String message) {
        // TODO: Implement - set code=500, message=message
        return null;
    }

    /**
     * Return a failure result from a ResultCode.
     */
    public static <T> Result<T> fail(ResultCode code) {
        // TODO: Implement - extract code and message from ResultCode
        return null;
    }

    /**
     * Return a failure result with custom code and message.
     */
    public static <T> Result<T> fail(int code, String message) {
        // TODO: Implement - set code=code, message=message
        return null;
    }
}
