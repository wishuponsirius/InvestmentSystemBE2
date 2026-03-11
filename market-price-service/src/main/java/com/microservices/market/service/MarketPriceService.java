package com.microservices.market.service;

import com.microservices.market.dto.response.PriceResponseDTO;
import com.microservices.market.entity.*;
import com.microservices.market.exception.ResourceNotFoundException;
import com.microservices.market.repository.*;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
public class MarketPriceService {

    private final MarketPriceRepository marketRepo;
    private final RegionRepository regionRepo;
    private final AssetClassRepository assetRepo;

    public List<PriceResponseDTO> getPrices(String regionCode, String assetName, String range) {

        Region region = regionRepo.findByRegionCodeIgnoreCase(regionCode)
                .orElseThrow(() ->  new ResourceNotFoundException("Region '" + regionCode + "' not found"));

        AssetClass asset = assetRepo.findByNameIgnoreCase(assetName)
                .orElseThrow(() -> new ResourceNotFoundException("Asset '" + assetName + "' not found"));

        List<MarketPriceRaw> prices;

        if (range.equalsIgnoreCase("all")) {
            prices = marketRepo.findAllPrices(region.getRegionId(), asset.getAssetId());
        } else {

            LocalDateTime from = calculateFromTime(range);

            prices = marketRepo.findPrices(
                    region.getRegionId(),
                    asset.getAssetId(),
                    from
            );
        }

        if (prices.isEmpty()) {
            throw new ResourceNotFoundException(
                    "No price data found for asset '" + assetName +
                            "' in region '" + regionCode + "'"
            );
        }

        return prices.stream()
                .map(this::mapToDTO)
                .toList();
    }

    private LocalDateTime calculateFromTime(String range) {

        LocalDateTime now = LocalDateTime.now();

        switch (range.toLowerCase()) {
            case "1d":
                return now.minusDays(1);

            case "1w":
                return now.minusWeeks(1);

            case "1m":
                return now.minusMonths(1);

            case "1y":
                return now.minusYears(1);

            default:
                throw new IllegalArgumentException(
                        "Invalid range. Allowed values: all, 1d, 1w, 1m, 1y"
                );
        }
    }

    private PriceResponseDTO mapToDTO(MarketPriceRaw price) {

        return PriceResponseDTO.builder()
                .timestamp(price.getTimestamp())
                .buyPrice(price.getBuyPrice())
                .sellPrice(price.getSellPrice())
                .transferPrice(price.getTransferPrice())
                .spread(price.getSpread())
                .build();
    }
}