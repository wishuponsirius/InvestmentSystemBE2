package com.microservices.iam.config;

import com.microservices.iam.entity.InstitutionalUser;
import com.microservices.iam.entity.Role;
import com.microservices.iam.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class DataSeeder implements CommandLineRunner {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    @Override
    public void run(String... args) {

        if (userRepository.count() > 0) {
            return; // DB already has users → skip seeding
        }

        seedUsers();
    }

    private void seedUsers() {

        InstitutionalUser admin = new InstitutionalUser();
        admin.setOrgName("Investment System Admin");
        admin.setContactEmail("admin@investmentsystem.com");
        admin.setPassword(passwordEncoder.encode("Admin@123"));
        admin.setIsActive(true);
        admin.setRole(Role.ADMIN);

        InstitutionalUser demo = new InstitutionalUser();
        demo.setOrgName("Hú hú Lạc Đông nè mọi người");
        demo.setContactEmail("demo@institution.com");
        demo.setPassword(passwordEncoder.encode("Demo@123"));
        demo.setIsActive(true);
        demo.setRole(Role.INSTITUTION);

        InstitutionalUser alphaCapital = new InstitutionalUser();
        alphaCapital.setOrgName("Alpha Capital Management");
        alphaCapital.setContactEmail("contact@alphacapital.com");
        alphaCapital.setPassword(passwordEncoder.encode("Alpha@123"));
        alphaCapital.setIsActive(true);
        alphaCapital.setRole(Role.INSTITUTION);

        InstitutionalUser mekongAsset = new InstitutionalUser();
        mekongAsset.setOrgName("Mekong Asset Partners");
        mekongAsset.setContactEmail("info@mekongasset.com");
        mekongAsset.setPassword(passwordEncoder.encode("Mekong@123"));
        mekongAsset.setIsActive(true);
        mekongAsset.setRole(Role.INSTITUTION);

        InstitutionalUser saigonWealth = new InstitutionalUser();
        saigonWealth.setOrgName("Saigon Wealth Advisory");
        saigonWealth.setContactEmail("support@saigonwealth.com");
        saigonWealth.setPassword(passwordEncoder.encode("Saigon@123"));
        saigonWealth.setIsActive(true);
        saigonWealth.setRole(Role.INSTITUTION);

        InstitutionalUser lotusHoldings = new InstitutionalUser();
        lotusHoldings.setOrgName("Lotus Strategic Holdings");
        lotusHoldings.setContactEmail("admin@lotusholdings.com");
        lotusHoldings.setPassword(passwordEncoder.encode("Lotus@123"));
        lotusHoldings.setIsActive(true);
        lotusHoldings.setRole(Role.INSTITUTION);

        InstitutionalUser horizonInvest = new InstitutionalUser();
        horizonInvest.setOrgName("Horizon Institutional Investments");
        horizonInvest.setContactEmail("operations@horizoninvest.com");
        horizonInvest.setPassword(passwordEncoder.encode("Horizon@123"));
        horizonInvest.setIsActive(true);
        horizonInvest.setRole(Role.INSTITUTION);


        userRepository.save(admin);
        userRepository.save(demo);
        userRepository.save(alphaCapital);
        userRepository.save(mekongAsset);
        userRepository.save(saigonWealth);
        userRepository.save(lotusHoldings);
        userRepository.save(horizonInvest);
    }
}
