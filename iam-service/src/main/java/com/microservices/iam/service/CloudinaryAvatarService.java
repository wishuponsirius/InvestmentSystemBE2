package com.microservices.iam.service;

import com.cloudinary.Cloudinary;
import com.microservices.iam.config.CloudinaryProperties;
import com.microservices.iam.exception.AvatarUploadException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.Map;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class CloudinaryAvatarService {

    private static final long MAX_BYTES = 5L * 1024 * 1024; // 5MB

    private final Cloudinary cloudinary;
    private final CloudinaryProperties properties;

    public UploadResult uploadAvatar(UUID userId, MultipartFile file) {
        if (file == null || file.isEmpty()) {
            throw new AvatarUploadException("Avatar file is required");
        }
        if (file.getSize() > MAX_BYTES) {
            throw new AvatarUploadException("Avatar file is too large (max 5MB)");
        }

        String contentType = file.getContentType();
        if (contentType == null || !(contentType.equalsIgnoreCase("image/jpeg")
                || contentType.equalsIgnoreCase("image/png")
                || contentType.equalsIgnoreCase("image/webp"))) {
            throw new AvatarUploadException("Unsupported avatar format. Use JPG, PNG, or WEBP");
        }

        String folder = (properties.folder() == null || properties.folder().isBlank())
                ? "investment-system/avatars"
                : properties.folder();

        try {
            Map<?, ?> result = cloudinary.uploader().upload(
                    file.getBytes(),
                    Map.of(
                            "folder", folder,
                            "public_id", "user-" + userId,
                            "overwrite", true,
                            "resource_type", "image"
                    )
            );

            Object secureUrl = result.get("secure_url");
            Object publicId = result.get("public_id");

            if (secureUrl == null || publicId == null) {
                throw new AvatarUploadException("Avatar upload failed");
            }

            return new UploadResult(secureUrl.toString(), publicId.toString());
        } catch (IOException e) {
            throw new AvatarUploadException("Failed to read avatar file", e);
        } catch (Exception e) {
            throw new AvatarUploadException("Avatar upload failed", e);
        }
    }

    public void deleteByPublicId(String publicId) {
        if (publicId == null || publicId.isBlank()) return;
        try {
            cloudinary.uploader().destroy(publicId, Map.of("invalidate", true, "resource_type", "image"));
        } catch (Exception ignored) {
            // best-effort delete
        }
    }

    public record UploadResult(String url, String publicId) {}
}