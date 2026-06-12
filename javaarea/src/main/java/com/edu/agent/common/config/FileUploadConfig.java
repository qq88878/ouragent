package com.edu.agent.common.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;

@Configuration
public class FileUploadConfig {

    @Value("${file.upload.path:./uploads}")
    private String uploadPath;

    @Value("${file.upload.url-prefix:/files}")
    private String urlPrefix;

    public String getUploadPath() {
        return uploadPath;
    }

    public String getUrlPrefix() {
        return urlPrefix;
    }
}
