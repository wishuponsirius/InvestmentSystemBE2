package com.microservices.market.repository;

import com.microservices.market.dto.response.PremiumPriceResponseDTO;
import com.microservices.market.entity.MarketPriceRaw;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.*;

@Repository
public interface MarketPriceRepository extends JpaRepository<MarketPriceRaw, Integer> {

    @Query("""
        SELECT m
        FROM MarketPriceRaw m
        WHERE m.region.regionId = :regionId
        AND m.asset.assetId = :assetId
        AND m.timestamp >= :from
        ORDER BY m.timestamp ASC
    """)
    List<MarketPriceRaw> findPrices(
            Integer regionId,
            Integer assetId,
            LocalDateTime from
    );

    @Query("""
        SELECT m
        FROM MarketPriceRaw m
        WHERE m.region.regionId = :regionId
        AND m.asset.assetId = :assetId
        ORDER BY m.timestamp ASC
    """)
    List<MarketPriceRaw> findAllPrices(
            Integer regionId,
            Integer assetId
    );


    @Query(value = """
        SELECT
            asset_id,
            display_unit,
            vietnam_buy_price,
            global_buy_price,
            premium_price,
            vietnam_timestamp,
            global_timestamp
        FROM asset_premium_vn
        ORDER BY asset_id
        """, nativeQuery = true)
    List<Object[]> getLatestPremiumPrices();
}
