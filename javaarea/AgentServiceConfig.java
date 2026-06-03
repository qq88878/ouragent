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
 *
 * 从 application.yml 读取配置:
 *   agent.service.url=http://agent-service:8000
 *   agent.service.timeout=5000
 *   agent.service.retry.max-attempts=3
 *   agent.service.retry.delay=1000
 *
 * TODO: 阶段四 - 增强配置
 *   - 添加连接池配置 (最大连接数、空闲超时)
 *   - 添加熔断器配置 (Resilience4j)
 *   - 添加重试策略配置 (指数退避、最大重试间隔)
 */
@Configuration
@ConfigurationProperties(prefix = "agent.service")
public class AgentServiceConfig {

    private String url = "http://agent-service:8000";
    private int timeout = 5000;
    private RetryConfig retry = new RetryConfig();

    public String getUrl() { return url; }
    public void setUrl(String url) { this.url = url; }
    public int getTimeout() { return timeout; }
    public void setTimeout(int timeout) { this.timeout = timeout; }
    public RetryConfig getRetry() { return retry; }
    public void setRetry(RetryConfig retry) { this.retry = retry; }

    public static class RetryConfig {
        private int maxAttempts = 3;
        private long delay = 1000;

        public int getMaxAttempts() { return maxAttempts; }
        public void setMaxAttempts(int maxAttempts) { this.maxAttempts = maxAttempts; }
        public long getDelay() { return delay; }
        public void setDelay(long delay) { this.delay = delay; }
    }

    /**
     * TODO: 阶段一 - 配置RestTemplate
     *   - 设置超时 (connectTimeout, readTimeout)
     *   - 配置消息转换器 (Jackson)
     *   - 配置拦截器 (日志、认证)
     */
    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }

    /**
     * TODO: 阶段一 - 配置Agent客户端
     */
    @Bean
    public AgentServiceClient agentServiceClient() {
        return new AgentServiceClient(url);
    }
}
