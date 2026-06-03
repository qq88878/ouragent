package com.edu.agent.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * Web MVC interceptor configuration.
 */
@Configuration
public class WebMvcConfig implements WebMvcConfigurer {

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        // TODO: Add logging interceptor
        //   registry.addInterceptor(loggingInterceptor)
        //           .addPathPatterns("/api/**")
        //           .excludePathPatterns("/api/auth/**");
    }
}
