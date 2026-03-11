package com.microservices.market.repository;

import com.microservices.market.entity.Unit;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface UnitRepository extends JpaRepository<Unit, Integer> {

    Optional<Unit> findByUnitNameIgnoreCase(String unitName);
}
