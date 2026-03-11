package com.microservices.market.service;

import com.microservices.market.dto.request.*;
import com.microservices.market.dto.response.*;
import com.microservices.market.entity.*;
import com.microservices.market.entity.Currency;
import com.microservices.market.exception.ResourceNotFoundException;
import com.microservices.market.repository.*;
import lombok.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;

@Service
@RequiredArgsConstructor
public class PortfolioService {

    private final PortfolioRepository portfolioRepo;
    private final AssetClassRepository assetRepo;
    private final UnitRepository unitRepo;
    private final CurrencyRepository currencyRepo;
    private final AssetLookupService assetLookup;
    private final UnitLookupService unitLookup;
    private final CurrencyLookupService currencyLookup;

    @Transactional(readOnly = true)
    public List<PortfolioResponseDTO> getPortfolio(UUID userId) {

        List<AssetPortfolio> portfolios = portfolioRepo.findByUserId(userId);

        if (portfolios.isEmpty()) {
            throw new ResourceNotFoundException(
                    "Portfolio not found for user " + userId);
        }

        return portfolios.stream()
                .map(this::toDTO)
                .toList();
    }

    public PortfolioResponseDTO addOrUpdate(PortfolioRequestDTO request) {

        AssetClass asset = assetLookup.getAsset(request.getAsset());

        Unit unit = unitLookup.getUnit(request.getUnit());

        Currency currency = currencyLookup.getCurrency(request.getCurrency());

        AssetPortfolio portfolio = portfolioRepo
                .findByUserIdAndAsset_NameIgnoreCase(request.getUserId(), request.getAsset())
                .orElse(new AssetPortfolio());

        portfolio.setUserId(request.getUserId());
        portfolio.setAsset(asset);
        portfolio.setQuantity(request.getQuantity());
        portfolio.setUnit(unit);
        portfolio.setEntryPrice(request.getEntryPrice());
        portfolio.setCurrency(currency);

        portfolioRepo.save(portfolio);

        return toDTO(portfolio);
    }

    @Transactional
    public String deleteAsset(UUID userId, String asset) {

        AssetPortfolio portfolio = portfolioRepo
                .findByUserIdAndAsset_NameIgnoreCase(userId, asset.toUpperCase())
                .orElseThrow(() ->
                        new ResourceNotFoundException("Asset " + asset + " not found in portfolio"));

        portfolioRepo.delete(portfolio);

        return "Asset deleted successfully";
    }

    private PortfolioResponseDTO toDTO(AssetPortfolio portfolio) {

        return PortfolioResponseDTO.builder()
                .asset(portfolio.getAsset().getName())
                .quantity(portfolio.getQuantity())
                .unit(portfolio.getUnit().getUnitName())
                .entryPrice(portfolio.getEntryPrice())
                .currency(portfolio.getCurrency().getCurrencyCode())
                .build();
    }
}
