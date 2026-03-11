package com.microservices.market.repository;

import com.microservices.market.entity.AssetClass;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface AssetClassRepository extends JpaRepository<AssetClass, Integer> {

    Optional<AssetClass> findByNameIgnoreCase(String name);

}
