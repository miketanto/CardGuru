# Post-pin card scripts (overlay on the Forge pin)

Forge card scripts that entered Forge after the dataset pin `670429bf`
(2026-08-06): every file `git diff --name-status 670429bf 639f8d98 --
forge-gui/res/cardsfolder` reports as added (`A`), copied verbatim from
Forge commit `639f8d98` (master, 2026-09-10). Modified (`M`) and renamed
(`R`) scripts are NOT overlaid: the pin's version stays authoritative for
any card that existed at the pin.

`rl/cards/build_index.py` parses this directory after the dataset and
registers the faces with `file = extra/<script>`, so a consumer can tell
overlay cards from pin cards. Two of them are needed by XMage ladder
decks (`Defense Force Aggressor` in rl/R0Novel.dck, `Head of Security`
in rl/W1Fst.dck); the rest exist so 2026 MTGO decklists resolve
(`rl/artifacts/decklists_v1`).

Moving the pin forward makes this directory empty, not wrong.

| script | card |
|---|---|
| 70_000_light_years_from_home.txt | 70,000 Light-Years from Home |
| a_good_day_to_die.txt | A Good Day to Die |
| arvad_of_the_weatherlight.txt | Arvad of the Weatherlight |
| assault_drone.txt | Assault Drone |
| automated_warfare_system.txt | Automated Warfare System |
| badgey_malicious_glitch.txt | Badgey, Malicious Glitch |
| batleth.txt | Bat'leth |
| battle_scarred_survivalist.txt | Battle-Scarred Survivalist |
| cantankerous_captain.txt | Cantankerous Captain |
| captains_tutelage.txt | Captain's Tutelage |
| cast_away_doubt.txt | Cast Away Doubt |
| ceti_eel.txt | Ceti Eel |
| chadich_investigator.txt | Cha'DIch Investigator |
| charge_the_sanctum.txt | Charge the Sanctum |
| chira_all_in.txt | Chira, All In |
| christine_chapel_combat_medic.txt | Christine Chapel, Combat Medic |
| cloistered_telepath.txt | Cloistered Telepath |
| cold_blooded_crew.txt | Cold-Blooded Crew |
| collective_drone.txt | Collective Drone |
| command_decision.txt | Command Decision |
| common_goal.txt | Common Goal |
| compel_brutality.txt | Compel Brutality |
| cryogenic_stasis.txt | Cryogenic Stasis |
| cybernetic_specialist.txt | Cybernetic Specialist |
| dathon_and_picard_at_el_adrel.txt | Dathon and Picard at El-Adrel |
| daxiver_izzet_electromancer.txt | Daxiver, Izzet Electromancer |
| defense_force_agressor.txt | Defense Force Aggressor |
| direct_hit.txt | Direct Hit |
| disruptor_pistol.txt | Disruptor Pistol |
| dominion_saboteur.txt | Dominion Saboteur |
| dominion_supervisor.txt | Dominion Supervisor |
| dot_7_repair_squad.txt | DOT-7 Repair Squad |
| eject_the_warp_core.txt | Eject the Warp Core |
| emergency_medical_hologram.txt | Emergency Medical Hologram |
| evasive_maneuvers.txt | Evasive Maneuvers |
| exocomp.txt | Exocomp |
| federation_field_medic.txt | Federation Field Medic |
| federation_probe.txt | Federation Probe |
| first_contact.txt | First Contact |
| free_borg_revolutionaries.txt | Free Borg Revolutionaries |
| general_chang_cold_warrior.txt | General Chang, Cold Warrior |
| generous_revival.txt | Generous Revival |
| ghalta_the_immovable.txt | Ghalta the Immovable |
| gintak_charge.txt | Gin'tak Charge |
| glava_five_advents_mage.txt | Glava, Five-Advents Mage |
| gorn_captain.txt | Gorn Captain |
| grizzlegom_hurloon_hero.txt | Grizzlegom, Hurloon Hero |
| guidance_failure.txt | Guidance Failure |
| gumato.txt | Gumato |
| hadran_naya_sunseeder.txt | Hadran, Naya Sunseeder |
| head_of_security.txt | Head of Security |
| hes_dead_jim.txt | He's Dead, Jim |
| hexhaven_invigorator.txt | Hexhaven Invigorator |
| hive_mind_coprocessor.txt | Hive Mind Coprocessor |
| horta.txt | Horta |
| humpback_whales.txt | Humpback Whales |
| icy_reception.txt | Icy Reception |
| im_a_doctor_not_a.txt | I'm a Doctor, Not a . . . |
| ingris_stingerquill.txt | Ingris Stingerquill |
| itazura_lingering_wick.txt | Itazura, Lingering Wick |
| jaces_machinations.txt | Jace's Machinations |
| keeper_of_the_quiet_hour.txt | Keeper of the Quiet Hour |
| khaaaaaaaaaaaannn.txt | Khaaaaaaaaaaaannn! |
| kolinahr_priest.txt | Kolinahr Priest |
| kruge_genesis_seeker.txt | Kruge, Genesis Seeker |
| la_forge_perceptive_engineer.txt | La Forge, Perceptive Engineer |
| laan_noonien_singh_security.txt | La'An Noonien-Singh, Security |
| loyal_tutor.txt | Loyal Tutor |
| malfunctioning_holodeck.txt | Malfunctioning Holodeck |
| marooned.txt | Marooned |
| massimo_the_magician.txt | Massimo, the Magician |
| matoc_lavamancer.txt | Matoc, Lavamancer |
| maular_the_next_evolution.txt | Maular, the Next Evolution |
| mekleth_berserker.txt | Mek'leth Berserker |
| memory_trap.txt | Memory Trap |
| miss_highwater.txt | Miss Highwater |
| moopsy.txt | Moopsy |
| mugato.txt | Mugato |
| open_communications.txt | Open Communications |
| organic_avulsion_unit.txt | Organic Avulsion Unit |
| pelia_immortal_innovator.txt | Pelia, Immortal Innovator |
| perfected_theory.txt | Perfected Theory |
| perils_of_the_past.txt | Perils of the Past |
| picard_leading_by_example.txt | Picard, Leading by Example |
| planetary_patrol.txt | Planetary Patrol |
| plasma_cascade.txt | Plasma Cascade |
| proteges_awakening.txt | Protege's Awakening |
| relentless_drednok.txt | Relentless Drednok |
| resistance_is_futile.txt | Resistance Is Futile |
| restore_with_empathy.txt | Restore with Empathy |
| return_to_the_light_realms.txt | Return to the Light Realms |
| rogue_artificial_intelligence.txt | Rogue Artificial Intelligence |
| saavik_stoic_student.txt | Saavik, Stoic Student |
| sahir_visitor_in_darkness.txt | Sahir, Visitor in Darkness |
| saurian_explorer.txt | Saurian Explorer |
| seluma_light_of_aysen.txt | Seluma, Light of Aysen |
| shields_up.txt | Shields Up! |
| shuttle_ace.txt | Shuttle Ace |
| shuttle_crew.txt | Shuttle Crew |
| sickbay_orderly.txt | Sickbay Orderly |
| silicate_surveyor.txt | Silicate Surveyor |
| solitary_cell.txt | Solitary Cell |
| something_worth_saving.txt | Something Worth Saving |
| starfleet_crew.txt | Starfleet Crew |
| support_mission.txt | Support Mission |
| syndicate_liquidators.txt | Syndicate Liquidators |
| tactical_officer.txt | Tactical Officer |
| talarian_hook_spider.txt | Talarian Hook Spider |
| the_everforger.txt | The Everforger |
| the_madcap_jester.txt | The Madcap Jester |
| the_unluckiest_planeswalker.txt | The Unluckiest Planeswalker |
| tolabow_loch_rascal.txt | Tolabow, Loch Rascal |
| tpol_vulcan_representative.txt | T'Pol, Vulcan Representative |
| valko_indorian.txt | Valko Indorian |
| valko_indorian_researcher.txt | Valko Indorian, Researcher |
| vger_the_intruder.txt | V'Ger, the Intruder |
| warship_flight_crew.txt | Warship Flight Crew |
| whtz_the_bibliophile.txt | Whtz, the Bibliophile |
| will_riker_assuming_command.txt | Will Riker, Assuming Command |
| worf_chief_tactical_officer.txt | Worf, Chief Tactical Officer |
| xenobotanist.txt | Xenobotanist |
| xindi_surveyors.txt | Xindi Surveyors |
| yume_chronicler_of_valor.txt | Yume, Chronicler of Valor |
