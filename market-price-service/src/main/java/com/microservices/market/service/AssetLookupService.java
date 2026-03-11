package com.microservices.market.service;

import com.microservices.market.entity.AssetClass;
import com.microservices.market.exception.ResourceNotFoundException;
import com.microservices.market.repository.AssetClassRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class AssetLookupService {

    private final AssetClassRepository assetRepository;

    @Cacheable(value = "assets", key = "#p0.toUpperCase()")
    public AssetClass getAsset(String assetName) {

        String normalized = assetName.toUpperCase();

        return assetRepository.findByNameIgnoreCase(normalized)
                .orElseThrow(() ->
                        new ResourceNotFoundException("Asset " + normalized + " not found"));
    }
}