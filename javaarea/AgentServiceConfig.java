// Spring Boot配置类
// 用于配置Agent服务客户端

package com.yourcompany.agent.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestTemplate;
import com.yourcompany.agent.client.AgentServiceClient;

/**
 * Agent服务配置
 */
@Configuration
@ConfigurationProperties(prefix = "agent.service")
public class AgentServiceConfig {

    private String url = "http://agent-service:8000";
    private int timeout = 5000;
    private RetryConfig retry = new RetryConfig();

    // Getters and Setters
    public String getUrl() { return url; }
    public void setUrl(String url) { this.url = url; }
    public int getTimeout() { return timeout; }
    public void setTimeout(int timeout) { this.timeout = timeout; }
    public RetryConfig getRetry() { return retry; }
    public void setRetry(RetryConfig retry) { this.retry = retry; }

    /**
     * 重试配置
     */
    public static class RetryConfig {
        private int maxAttempts = 3;
        private long delay = 1000;

        public int getMaxAttempts() { return maxAttempts; }
        public void setMaxAttempts(int maxAttempts) { this.maxAttempts = maxAttempts; }
        public long getDelay() { return delay; }
        public void setDelay(long delay) { this.delay = delay; }
    }

    /**
     * RestTemplate Bean
     */
    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }

    /**
     * Agent服务客户端 Bean
     */
    @Bean
    public AgentServiceClient agentServiceClient() {
        return new AgentServiceClient(url);
    }
}
