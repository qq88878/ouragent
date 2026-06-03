package com.edu.agent.config;

import com.fasterxml.jackson.annotation.JsonAutoDetect;
import com.fasterxml.jackson.annotation.PropertyAccessor;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.jsontype.impl.LaissezFaireSubTypeValidator;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.serializer.Jackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.StringRedisSerializer;

/**
 * Redis configuration with Jackson JSON value serializer and String key serializer.
 */
@Configuration
public class RedisConfig {

    // TODO: Extract Redis host/port/password from application properties if needed

    @Bean
    public RedisTemplate<String, Object> redisTemplate(RedisConnectionFactory connectionFactory) {
        // TODO: Implement RedisTemplate setup
        //   1. Create Jackson2JsonRedisSerializer with ObjectMapper
        //   2. Configure ObjectMapper: visibility ALL, activate-default typing with LaissezFaireSubTypeValidator
        //   3. Set StringRedisSerializer for key serializer
        //   4. Set Jackson2JsonRedisSerializer for value serializer
        //   5. Set hash key/value serializers
        //   6. Set connection factory and return
        RedisTemplate<String, Object> template = new RedisTemplate<>();
        template.setConnectionFactory(connectionFactory);
        return template;
    }
}
