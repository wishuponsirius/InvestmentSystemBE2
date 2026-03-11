package com.microservices.market.repository;

import com.microservices.market.entity.AssetPortfolio;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface PortfolioRepository extends JpaRepository<AssetPortfolio, Integer> {

    List<AssetPortfolio> findByUserId(UUID userId);

    Optional<AssetPortfolio> findByUserIdAndAsset_NameIgnoreCase(UUID userId, String asset);
    void deleteByUserIdAndAsset_NameIgnoreCase(UUID userId, String name);
}
