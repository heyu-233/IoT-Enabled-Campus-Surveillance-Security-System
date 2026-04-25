package com.example.end_part.utils;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Base64;

@Component
public class ImageUtils {

    private static final Logger logger = LoggerFactory.getLogger(ImageUtils.class);

    @Value("${image.upload.path:./uploads/images}")
    private String imageUploadPath;

    @Value("${image.access.url:/images}")
    private String imageAccessUrl;

    public String saveBase64Image(String base64Image, String prefix) {
        if (base64Image == null || base64Image.isBlank()) {
            return null;
        }

        try {
            String imageData = base64Image.contains(",") ? base64Image.split(",", 2)[1] : base64Image;
            byte[] imageBytes = Base64.getDecoder().decode(imageData);

            File uploadDir = new File(imageUploadPath).getAbsoluteFile();
            if (!uploadDir.exists() && !uploadDir.mkdirs()) {
                logger.error("Unable to create image upload directory {}", uploadDir.getAbsolutePath());
                return null;
            }

            String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss_SSS"));
            String fileName = prefix + "_" + timestamp + ".jpg";
            Path filePath = uploadDir.toPath().resolve(fileName);

            try (FileOutputStream fos = new FileOutputStream(filePath.toFile())) {
                fos.write(imageBytes);
            }

            return imageAccessUrl + "/" + fileName;
        } catch (IOException | IllegalArgumentException e) {
            logger.error("Failed to save image", e);
            return null;
        }
    }

    public String getImageUploadPath() {
        return new File(imageUploadPath).getAbsolutePath();
    }
}
