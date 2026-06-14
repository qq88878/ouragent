package com.edu.agent.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import java.util.concurrent.Executor;

/**
 * Async thread pool configuration for agent tasks.
 */
@Configuration
@EnableAsync
public class AsyncConfig {

    /**
     * Thread pool executor for async agent operations.
     * core=5, max=10, queue=25, thread name prefix="Agent-"
     */
    @Bean(name = "agentExecutor")
    public Executor agentExecutor() {        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(5);
        executor.setMaxPoolSize(10);
        executor.setQueueCapacity(25);
        executor.setThreadNamePrefix("Agent-");
        executor.initialize();
        return executor;
    }
}
