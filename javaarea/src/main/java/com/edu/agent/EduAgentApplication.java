package com.edu.agent;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@MapperScan("com.edu.agent.module.*.mapper")
@EnableAsync
@EnableScheduling
public class EduAgentApplication {

    public static void main(String[] args) {
        SpringApplication.run(EduAgentApplication.class, args);
    }
}
