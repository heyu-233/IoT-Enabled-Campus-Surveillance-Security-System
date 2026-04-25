package com.example.end_part.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import java.io.File;

@Configuration
public class WebSocketConfig implements WebMvcConfigurer {

    @Value("${image.upload.path:./uploads/images}")
    private String imageUploadPath;

    @Value("${image.access.url:/images}")
    private String imageAccessUrl;

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/**")
                .allowedOriginPatterns("http://localhost:*", "http://127.0.0.1:*")
                .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
                .allowedHeaders("*")
                .allowCredentials(true);
    }

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        registry.addResourceHandler("/results/**").addResourceLocations("file:results/");
        String uploadPath = new File(imageUploadPath).getAbsoluteFile().toURI().toString();
        registry.addResourceHandler(imageAccessUrl + "/**").addResourceLocations(uploadPath);
    }
}
