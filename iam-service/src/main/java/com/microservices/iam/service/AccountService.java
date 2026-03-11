package com.microservices.iam.service;

import com.microservices.iam.dto.request.ChangePasswordRequest;
import com.microservices.iam.dto.request.UpdateAccountRequest;
import com.microservices.iam.dto.response.UserResponse;
import com.microservices.iam.entity.InstitutionalUser;
import com.microservices.iam.exception.UserNotFoundException;
import com.microservices.iam.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
public class AccountService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final CloudinaryAvatarService cloudinaryAvatarService;

    public UserResponse getAccount(String email) {
        InstitutionalUser user = userRepository.findByContactEmailIgnoreCase(email)
                .orElseThrow(() -> new UserNotFoundException(email));

        return mapToUserResponse(user);
    }

    @Transactional
    public UserResponse updateAccount(String email, UpdateAccountRequest request) {

        InstitutionalUser user = userRepository.findByContactEmailIgnoreCase(email)
                .orElseThrow(() -> new UserNotFoundException(email));

        if (request.getOrgName() != null && !request.getOrgName().isBlank()) {
            user.setOrgName(request.getOrgName());
        }

        if (request.getAvatarUrl() != null && !request.getAvatarUrl().isBlank()) {
            user.setAvatarUrl(request.getAvatarUrl());
        }

        userRepository.save(user);

        log.info("User updated own account: {}", user.getContactEmail());

        return mapToUserResponse(user);
    }

    @Transactional
    public UserResponse updateAvatar(String email, org.springframework.web.multipart.MultipartFile file) {
        InstitutionalUser user = userRepository.findByContactEmailIgnoreCase(email)
                .orElseThrow(() -> new UserNotFoundException(email));

        String oldPublicId = user.getAvatarPublicId();

        CloudinaryAvatarService.UploadResult upload = cloudinaryAvatarService.uploadAvatar(user.getId(), file);
        user.setAvatarUrl(upload.url());
        user.setAvatarPublicId(upload.publicId());

        userRepository.save(user);

        if (oldPublicId != null && !oldPublicId.isBlank() && !oldPublicId.equals(upload.publicId())) {
            cloudinaryAvatarService.deleteByPublicId(oldPublicId);
        }

        log.info("User updated avatar: {}", user.getContactEmail());
        return mapToUserResponse(user);
    }

    private UserResponse mapToUserResponse(InstitutionalUser user) {
        return UserResponse.builder()
                .id(user.getId())
                .orgName(user.getOrgName())
                .contactEmail(user.getContactEmail())
                .avatarUrl(user.getAvatarUrl())
                .role(user.getRole())
                .isActive(user.getIsActive())
                .isDelete(user.getIsDelete())
                .createDate(user.getCreateDate())
                .build();
    }
}