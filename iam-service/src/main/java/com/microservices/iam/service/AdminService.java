package com.microservices.iam.service;

import com.microservices.iam.dto.request.AdminCreateUserRequest;
import com.microservices.iam.dto.request.UpdateUserRequest;
import com.microservices.iam.dto.response.PageResponse;
import com.microservices.iam.dto.response.UserResponse;
import com.microservices.iam.entity.InstitutionalUser;
import com.microservices.iam.entity.Role;
import com.microservices.iam.exception.EmailAlreadyExistsException;
import com.microservices.iam.exception.UserNotFoundException;
import com.microservices.iam.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class AdminService {

    private final UserRepository userRepository;
    private final EmailService emailService;
    private final PasswordEncoder passwordEncoder;

    public PageResponse<UserResponse> getUsers(
            String search, Role role, Boolean isActive, Boolean isDelete,
            int page, int size, String sortBy, String sortDir) {

        List<String> allowedSortFields = List.of("orgName", "contactEmail", "createDate");

        if (!allowedSortFields.contains(sortBy)) {
            sortBy = "createDate";
        }

        if (search != null && !search.isBlank()) {
            search = "%" + search.toLowerCase() + "%";
        } else {
            search = null;
        }

        Sort sort = "asc".equalsIgnoreCase(sortDir)
                ? Sort.by(sortBy).ascending()
                : Sort.by(sortBy).descending();

        Pageable pageable = PageRequest.of(page, size, sort);

        Page<InstitutionalUser> result = userRepository.findAllWithFilters(
                search, role, isActive, isDelete, pageable);

        return PageResponse.<UserResponse>builder()
                .content(result.getContent().stream().map(this::mapToUserResponse).toList())
                .page(result.getNumber())
                .size(result.getSize())
                .totalElements(result.getTotalElements())
                .totalPages(result.getTotalPages())
                .last(result.isLast())
                .build();
    }

    public UserResponse getUserById(UUID id) {
        InstitutionalUser user = userRepository.findById(id)
                .orElseThrow(() -> new UserNotFoundException(id.toString()));
        return mapToUserResponse(user);
    }

    @Transactional
    public UserResponse updateUser(UUID id, UpdateUserRequest request) {
        InstitutionalUser user = userRepository.findById(id)
                .orElseThrow(() -> new UserNotFoundException(id.toString()));;

        if (request.getOrgName() != null && !request.getOrgName().isBlank()) {
            user.setOrgName(request.getOrgName());
        }

        if (request.getRole() != null) {
            user.setRole(request.getRole());
        }

        if (request.getIsActive() != null) {
            user.setIsActive(request.getIsActive());
            // If activating the user, also restore from soft delete
            if (Boolean.TRUE.equals(request.getIsActive())) {
                user.setIsDelete(false);
            }
        }

        userRepository.save(user);
        log.info("Admin updated user: {}", user.getContactEmail());

        return mapToUserResponse(user);
    }

    @Transactional
    public void deleteUser(UUID id) {
        InstitutionalUser user = findActiveUser(id);
        user.setIsDelete(true);
        user.setIsActive(false);
        userRepository.save(user);
        log.info("Admin soft-deleted user: {}", user.getContactEmail());
    }

    private InstitutionalUser findActiveUser(UUID id) {
        return userRepository.findById(id)
                .filter(u -> !u.getIsDelete())
                .orElseThrow(() -> new UserNotFoundException("User not found: " + id));
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

    @Transactional
    public UserResponse createUserByAdmin(AdminCreateUserRequest request) {

        if (userRepository.existsByContactEmailIgnoreCase(request.getContactEmail())) {
            throw new EmailAlreadyExistsException(request.getContactEmail());
        }

        String tempPassword = UUID.randomUUID().toString().substring(0, 8);

        InstitutionalUser user = InstitutionalUser.builder()
                .orgName(request.getOrgName())
                .contactEmail(request.getContactEmail().toLowerCase())
                .password(passwordEncoder.encode(tempPassword))
                .role(request.getRole()) // admin decides role
                .isActive(true)
                .isDelete(false)
                .build();

        userRepository.save(user);

        emailService.sendAdminCreatedAccountEmail(
                user.getContactEmail(),
                user.getOrgName(),
                tempPassword
        );

        log.info("Admin created user: {}", user.getContactEmail());

        return mapToUserResponse(user);
    }
}
