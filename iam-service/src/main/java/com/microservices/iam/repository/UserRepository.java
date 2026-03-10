package com.microservices.iam.repository;

import com.microservices.iam.entity.InstitutionalUser;
import com.microservices.iam.entity.Role;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface UserRepository extends JpaRepository<InstitutionalUser, UUID> {

    Optional<InstitutionalUser> findByContactEmailIgnoreCase(String email);

    Optional<InstitutionalUser> findByActivationToken(String token);

    boolean existsByContactEmailIgnoreCase(String email);

    // Pagination + optional filters — all params nullable
    @Query("""
SELECT u FROM InstitutionalUser u
WHERE (:search IS NULL OR
     LOWER(u.orgName) LIKE :search OR
     LOWER(u.contactEmail) LIKE :search)
AND (:role IS NULL OR u.role = :role)
AND (:isActive IS NULL OR u.isActive = :isActive)
AND (:isDelete IS NULL OR u.isDelete = :isDelete)
""")
    Page<InstitutionalUser> findAllWithFilters(
            @Param("search") String search,
            @Param("role") Role role,
            @Param("isActive") Boolean isActive,
            @Param("isDelete") Boolean isDelete,
            Pageable pageable
    );
}
