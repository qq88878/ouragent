package com.edu.agent.config;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

@Slf4j
@Component
public class LoggingInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        request.setAttribute("startTime", System.currentTimeMillis());
        log.info("[{}] {} {}", request.getMethod(), request.getRequestURI(), request.getQueryString() != null ? "?" + request.getQueryString() : "");
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) {
        Long startTime = (Long) request.getAttribute("startTime");
        long duration = startTime != null ? System.currentTimeMillis() - startTime : -1;
        int status = response.getStatus();
        if (status >= 400) {
            log.warn("[{}] {} → {} ({}ms)", request.getMethod(), request.getRequestURI(), status, duration);
        } else {
            log.info("[{}] {} → {} ({}ms)", request.getMethod(), request.getRequestURI(), status, duration);
        }
    }
}
