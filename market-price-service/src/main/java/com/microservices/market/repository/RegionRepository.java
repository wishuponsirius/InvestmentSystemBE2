package com.microservices.market.repository;

import com.microservices.market.entity.Region;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.*;

@Repository
public interface RegionRepository extends JpaRepository<Region, Integer> {

    Optional<Region> findByRegionCodeIgnoreCase(String regionCode);

}
