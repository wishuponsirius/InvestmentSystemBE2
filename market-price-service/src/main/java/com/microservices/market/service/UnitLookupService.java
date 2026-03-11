package com.microservices.market.service;

import com.microservices.market.entity.Unit;
import com.microservices.market.exception.ResourceNotFoundException;
import com.microservices.market.repository.UnitRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class UnitLookupService {

    private final UnitRepository unitRepository;

    @Cacheable(value = "units", key = "#p0.toUpperCase()")
    public Unit getUnit(String unitName) {

        String normalized = unitName.toUpperCase();

        return unitRepository.findByUnitNameIgnoreCase(normalized)
                .orElseThrow(() ->
                        new ResourceNotFoundException("Unit " + normalized + " not found"));
    }
}