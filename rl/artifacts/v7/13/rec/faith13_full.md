# 5b faithfulness on real dumps — 1271 consults, 25 games, 1 recordings

Thresholds: `{"L3": {"binary": 0.99, "cat": 0.99, "real": 0.95}, "L4": {"binary": 0.95, "cat": 0.95, "real": 0.9}, "edge": 0.9, "consult": {"real": 0.9, "binary": 0.95}}`

## after L3

| part | field | kind | exercised | held-out | chance | n | result |
|---|---|---|---|---|---|---|---|
| game | turn | real | 1271 | 1.000 | 0.000 | 288 | pass |
| game | i_am_active | binary | 166 | 1.000 | 0.854 | 288 | pass |
| game | step_upkeep | binary | 112 | 1.000 | 0.913 | 288 | pass |
| game | step_draw | binary | 122 | 1.000 | 0.903 | 288 | pass |
| game | step_main1 | binary | 606 | 1.000 | 0.531 | 288 | pass |
| game | step_decl_att | binary | 152 | 1.000 | 0.896 | 288 | pass |
| game | step_decl_blk | binary | 94 | 1.000 | 0.899 | 288 | pass |
| game | step_combat_dmg | binary | 62 | 1.000 | 0.965 | 288 | pass |
| game | step_main2 | binary | 82 | 1.000 | 0.920 | 288 | pass |
| game | step_end | binary | 41 | — | — | 0 | not exercised |
| game | priority | binary | 123 | 1.000 | 0.920 | 288 | pass |
| game | stack_depth | real | 169 | 1.000 | 0.000 | 288 | pass |
| game | dtype_PASS | binary | 54 | 1.000 | 0.934 | 288 | pass |
| game | dtype_LAND | binary | 184 | 1.000 | 0.837 | 288 | pass |
| game | dtype_SPELL | binary | 498 | 1.000 | 0.622 | 288 | pass |
| game | dtype_ACTIVATE | binary | 265 | 1.000 | 0.809 | 288 | pass |
| game | dtype_TARGET | binary | 134 | 1.000 | 0.899 | 288 | pass |
| game | dtype_ATTACK | binary | 102 | 1.000 | 0.931 | 288 | pass |
| game | dtype_BLOCK | binary | 34 | — | — | 0 | not exercised |
| game | dtype_OTHER | binary | 0 | — | — | 0 | not exercised |
| game | n_cand | real | 1271 | 1.000 | 0.000 | 288 | pass |
| game | consults_so_far | real | 1246 | 1.000 | 0.000 | 288 | pass |
| game | my_deck_open | binary | 0 | — | — | 0 | not exercised |
| game | opp_deck_open | binary | 0 | — | — | 0 | not exercised |
| players | life | real | 2516 | 1.000 | 0.000 | 576 | pass |
| players | poison | real | 0 | — | — | 0 | not exercised |
| players | hand | real | 2319 | 1.000 | 0.000 | 576 | pass |
| players | library | real | 2542 | 1.000 | 0.000 | 576 | pass |
| players | graveyard | real | 2055 | 1.000 | 0.000 | 576 | pass |
| players | exile | real | 0 | — | — | 0 | not exercised |
| players | pool_W | real | 0 | — | — | 0 | not exercised |
| players | pool_U | real | 0 | — | — | 0 | not exercised |
| players | pool_B | real | 0 | — | — | 0 | not exercised |
| players | pool_R | real | 0 | — | — | 0 | not exercised |
| players | pool_G | real | 0 | — | — | 0 | not exercised |
| players | pool_C | real | 0 | — | — | 0 | not exercised |
| players | untapped_sources | real | 1980 | 1.000 | 0.000 | 576 | pass |
| players | lands | real | 2472 | 1.000 | 0.000 | 576 | pass |
| players | drawn_this_turn | real | 0 | — | — | 0 | not exercised |
| players | permanents | real | 2472 | 1.000 | 0.000 | 576 | pass |
| ent | ctr_loyalty | real | 467 | 1.000 | 0.000 | 4726 | pass |
| ent | damage | real | 7 | — | — | 0 | not exercised |
| ent | toughness | real | 9785 | 1.000 | 0.000 | 9626 | pass |
| ent | kw_prowess | binary | 0 | — | — | 0 | not exercised |
| ent | printed_tough | real | 9157 | 1.000 | 0.000 | 9626 | pass |
| ent | printed_power | real | 9157 | 0.997 | 0.000 | 9626 | **FAIL** |
| ent | face_down | binary | 0 | — | — | 0 | not exercised |
| ent | legal_targets | real | 645 | 1.000 | 0.000 | 1232 | pass |
| ent | kw_protection | binary | 0 | — | — | 0 | not exercised |
| ent | kw_menace | binary | 0 | — | — | 0 | not exercised |
| ent | kw_ninjutsu | binary | 994 | 1.000 | 0.970 | 9577 | pass |
| ent | kw_lifelink | binary | 965 | 1.000 | 0.967 | 9577 | pass |
| ent | turns_on_bf | real | 16328 | 1.000 | 0.000 | 4726 | pass |
| ent | kw_reach | binary | 0 | — | — | 0 | not exercised |
| ent | tapped | binary | 5456 | 1.000 | 0.742 | 4726 | pass |
| ent | mine | binary | 12968 | 0.995 | 0.592 | 8394 | **FAIL** |
| ent | kw_haste | binary | 0 | — | — | 0 | not exercised |
| ent | kw_defender | binary | 0 | — | — | 0 | not exercised |
| ent | zone_graveyard | binary | 0 | — | — | 0 | not exercised |
| ent | stack_X | real | 0 | — | — | 0 | not exercised |
| ent | sick | binary | 2523 | 1.000 | 0.882 | 4726 | pass |
| ent | zone_command | binary | 0 | — | — | 0 | not exercised |
| ent | zone_stack | binary | 0 | — | — | 0 | not exercised |
| ent | zone_hand | binary | 0 | — | — | 0 | not exercised |
| ent | instant | binary | 5841 | 1.000 | 0.648 | 4900 | pass |
| ent | loyalty | real | 467 | 1.000 | 0.000 | 4726 | pass |
| ent | stack_pos | real | 36 | 0.941 | 0.000 | 49 | **FAIL** |
| ent | can_attack | binary | 7220 | 1.000 | 0.660 | 4726 | pass |
| ent | kw_deathtouch | binary | 1410 | 1.000 | 0.953 | 9577 | pass |
| ent | zone_battlefield | binary | 0 | — | — | 0 | not exercised |
| ent | kw_flash | binary | 5904 | 1.000 | 0.860 | 9626 | pass |
| ent | lethal_as_is | binary | 7 | — | — | 0 | not exercised |
| ent | kw_flying | binary | 3635 | 1.000 | 0.869 | 9577 | pass |
| ent | kw_trample | binary | 0 | — | — | 0 | not exercised |
| ent | sorcery | binary | 454 | 1.000 | 0.959 | 4851 | pass |
| ent | stack_mine | binary | 49 | 1.000 | 0.694 | 49 | pass |
| ent | ctr_p1p1 | real | 41 | — | — | 0 | not exercised |
| ent | zone_library_known | binary | 0 | — | — | 0 | not exercised |
| ent | kw_vigilance | binary | 2425 | 1.000 | 0.954 | 9577 | pass |
| ent | attacking | binary | 256 | 1.000 | 0.989 | 4726 | pass |
| ent | mv | real | 17167 | 0.999 | 0.000 | 9626 | **FAIL** |
| ent | stack_modes | real | 205 | — | — | 0 | not exercised |
| ent | stack_is_ability | binary | 70 | 1.000 | 0.776 | 49 | pass |
| ent | kw_shroud | binary | 0 | — | — | 0 | not exercised |
| ent | blocking | binary | 3 | — | — | 0 | not exercised |
| ent | can_block | binary | 5456 | 1.000 | 0.742 | 4726 | pass |
| ent | ctr_m1m1 | real | 138 | 0.999 | 0.000 | 4726 | pass |
| ent | mana_left_if_cast | real | 2385 | 1.000 | 0.000 | 1232 | pass |
| ent | ctr_other | real | 98 | — | — | 0 | not exercised |
| ent | identity | cat | 27704 | 1.000 | 0.196 | 9615 | **FAIL** |
| ent | land | binary | 7809 | 1.000 | 0.777 | 9577 | pass |
| ent | kw_double_strike | binary | 0 | — | — | 0 | not exercised |
| ent | kw_first_strike | binary | 0 | — | — | 0 | not exercised |
| ent | other_perm | binary | 3646 | 1.000 | 0.840 | 9577 | pass |
| ent | tough_left | real | 9785 | 1.000 | 0.000 | 9626 | pass |
| ent | zone_exile | binary | 0 | — | — | 0 | not exercised |
| ent | entered | binary | 834 | 1.000 | 0.964 | 4726 | pass |
| ent | creature | binary | 9496 | 1.000 | 0.728 | 9626 | pass |
| ent | kw_ward | binary | 0 | — | — | 0 | not exercised |
| ent | kw_hexproof | binary | 302 | 1.000 | 0.994 | 4726 | pass |
| ent | castable | binary | 2275 | 1.000 | 0.537 | 1232 | pass |
| ent | power | real | 9789 | 0.997 | 0.000 | 9626 | **FAIL** |
| ent | token | binary | 1903 | 1.000 | 0.802 | 4726 | pass |
| opp_hand | origin_opening | binary | 1890 | 1.000 | 0.529 | 512 | pass |
| opp_hand | origin_drawn | binary | 1854 | 1.000 | 0.506 | 512 | pass |
| opp_hand | origin_returned | binary | 36 | 1.000 | 0.977 | 512 | pass |
| opp_hand | origin_other | binary | 0 | — | — | 0 | not exercised |
| opp_hand | age | real | 3815 | 0.857 | 0.000 | 512 | **FAIL** |
| opp_hand | known | binary | 36 | 1.000 | 0.977 | 512 | pass |
| opp_hand | seen | binary | 36 | 1.000 | 0.977 | 512 | pass |
| opp_hand | identity | cat | 18 | — | — | 0 | not exercised |
| opp_deck | count | real | 26804 | 1.000 | 0.000 | 5849 | pass |
| opp_deck | fraction | real | 26804 | 0.982 | 0.000 | 5849 | pass |
| opp_deck | castable_now | binary | 7885 | 1.000 | 0.772 | 5849 | pass |
| opp_deck | mv | real | 18016 | 1.000 | 0.000 | 5849 | pass |
| opp_deck | instant_speed | binary | 12087 | 1.000 | 0.546 | 5849 | pass |
| opp_deck | identity | cat | 25533 | 1.000 | 0.049 | 5849 | pass |
| opp_act | act_cast | binary | 5128 | 1.000 | 0.656 | 3437 | pass |
| opp_act | act_activate | binary | 180 | 1.000 | 0.976 | 3437 | pass |
| opp_act | act_attack | binary | 3208 | 1.000 | 0.654 | 3437 | pass |
| opp_act | act_block | binary | 90 | — | — | 0 | not exercised |
| opp_act | act_declined_block | binary | 743 | 1.000 | 0.949 | 3437 | pass |
| opp_act | act_passed_mana_up | binary | 2772 | 1.000 | 0.765 | 3437 | pass |
| opp_act | act_other | binary | 0 | — | — | 0 | not exercised |
| opp_act | consult_age | real | 12121 | 1.000 | 0.000 | 3437 | pass |
| cand | type_PASS | binary | 1136 | 1.000 | 0.697 | 856 | pass |
| cand | type_LAND | binary | 481 | 1.000 | 0.874 | 856 | pass |
| cand | type_SPELL | binary | 888 | 1.000 | 0.764 | 856 | pass |
| cand | type_ACTIVATE | binary | 795 | 1.000 | 0.806 | 856 | pass |
| cand | type_TARGET | binary | 346 | 1.000 | 0.922 | 856 | pass |
| cand | type_ATTACK | binary | 245 | 1.000 | 0.953 | 856 | pass |
| cand | type_BLOCK | binary | 55 | 1.000 | 0.984 | 856 | pass |
| cand | type_OTHER | binary | 0 | — | — | 0 | not exercised |
| cand | LSA.mana_left_after | real | 1570 | 1.000 | 0.000 | 476 | pass |
| cand | LSA.targets_legal | real | 684 | 1.000 | 0.000 | 476 | pass |
| cand | LSA.instant_speed | binary | 671 | 1.000 | 0.655 | 476 | pass |
| cand | LSA.sorcery_speed | binary | 671 | 1.000 | 0.655 | 476 | pass |
| cand | LSA.flash | binary | 314 | 1.000 | 0.845 | 476 | pass |
| cand | LSA.stack_above_n | real | 83 | 1.000 | 0.000 | 476 | pass |
| cand | LSA.X_chosen | real | 0 | — | — | 0 | not exercised |
| cand | TARGET.is_player | binary | 58 | 1.000 | 0.821 | 67 | pass |
| cand | TARGET.is_me | binary | 29 | — | — | 0 | not exercised |
| cand | TARGET.life_if_player | real | 32 | — | — | 0 | not exercised |
| cand | TARGET.is_creature | binary | 132 | 1.000 | 0.672 | 67 | pass |
| cand | TARGET.power | real | 211 | 1.000 | 0.000 | 67 | pass |
| cand | TARGET.toughness | real | 207 | 1.000 | 0.000 | 67 | pass |
| cand | TARGET.mine | binary | 156 | 1.000 | 0.522 | 67 | pass |
| cand | ATTACK.damage_dealt | real | 193 | 1.000 | 0.000 | 59 | pass |
| cand | ATTACK.their_kills | real | 84 | 1.000 | 0.000 | 59 | pass |
| cand | ATTACK.my_losses | real | 63 | 1.000 | 0.000 | 59 | pass |
| cand | ATTACK.lethal | binary | 38 | — | — | 0 | not exercised |
| cand | ATTACK.attackers_used | real | 245 | 1.000 | 0.000 | 59 | pass |
| cand | ATTACK.opp_life_after | real | 239 | 1.000 | 0.000 | 59 | pass |
| cand | ATTACK.bodies_retained | real | 145 | 1.000 | 0.000 | 59 | pass |
| cand | ATTACK.power_retained | real | 145 | 1.000 | 0.000 | 59 | pass |
| cand | ATTACK.tough_retained | real | 145 | 1.000 | 0.000 | 59 | pass |
| cand | ATTACK.crack_back | real | 24 | — | — | 0 | not exercised |
| cand | ATTACK.my_life_after | real | 245 | 1.000 | 0.000 | 59 | pass |
| cand | BLOCK.damage_taken | - | 0 | — | — | 0 | too few rows (55) |
| cand | BLOCK.attackers_killed | - | 0 | — | — | 0 | too few rows (55) |
| cand | BLOCK.value_killed | - | 0 | — | — | 0 | too few rows (55) |
| cand | BLOCK.blockers_lost | - | 0 | — | — | 0 | too few rows (55) |
| cand | BLOCK.value_lost | - | 0 | — | — | 0 | too few rows (55) |
| cand | BLOCK.defender_dies | - | 0 | — | — | 0 | too few rows (55) |
| cand | BLOCK.blockers_used | - | 0 | — | — | 0 | too few rows (55) |
| cand | BLOCK.life_after | - | 0 | — | — | 0 | too few rows (55) |

entity rows by zone: `{'battlefield': 17162, 'hand': 4618, 'stack': 205, 'graveyard': 10466, 'exile': 0, 'library_known': 0, 'command': 0}`; candidate rows by type: `{'PASS': 1136, 'LAND': 481, 'SPELL': 888, 'ACTIVATE': 795, 'TARGET': 346, 'ATTACK': 245, 'BLOCK': 55, 'OTHER': 0}`

## after L4

| part | field | kind | exercised | held-out | chance | n | result |
|---|---|---|---|---|---|---|---|
| game | turn | real | 1271 | 0.953 | 0.000 | 288 | pass |
| game | i_am_active | binary | 166 | 1.000 | 0.854 | 288 | pass |
| game | step_upkeep | binary | 112 | 1.000 | 0.913 | 288 | pass |
| game | step_draw | binary | 122 | 1.000 | 0.903 | 288 | pass |
| game | step_main1 | binary | 606 | 1.000 | 0.531 | 288 | pass |
| game | step_decl_att | binary | 152 | 1.000 | 0.896 | 288 | pass |
| game | step_decl_blk | binary | 94 | 1.000 | 0.899 | 288 | pass |
| game | step_combat_dmg | binary | 62 | 1.000 | 0.965 | 288 | pass |
| game | step_main2 | binary | 82 | 1.000 | 0.920 | 288 | pass |
| game | step_end | binary | 41 | — | — | 0 | not exercised |
| game | priority | binary | 123 | 1.000 | 0.920 | 288 | pass |
| game | stack_depth | real | 169 | 0.925 | 0.000 | 288 | pass |
| game | dtype_PASS | binary | 54 | 1.000 | 0.934 | 288 | pass |
| game | dtype_LAND | binary | 184 | 1.000 | 0.837 | 288 | pass |
| game | dtype_SPELL | binary | 498 | 1.000 | 0.622 | 288 | pass |
| game | dtype_ACTIVATE | binary | 265 | 1.000 | 0.809 | 288 | pass |
| game | dtype_TARGET | binary | 134 | 1.000 | 0.899 | 288 | pass |
| game | dtype_ATTACK | binary | 102 | 1.000 | 0.931 | 288 | pass |
| game | dtype_BLOCK | binary | 34 | — | — | 0 | not exercised |
| game | dtype_OTHER | binary | 0 | — | — | 0 | not exercised |
| game | n_cand | real | 1271 | 0.894 | 0.000 | 288 | **FAIL** |
| game | consults_so_far | real | 1246 | 0.922 | 0.000 | 288 | pass |
| game | my_deck_open | binary | 0 | — | — | 0 | not exercised |
| game | opp_deck_open | binary | 0 | — | — | 0 | not exercised |
| players | life | real | 2516 | 0.998 | 0.000 | 576 | pass |
| players | poison | real | 0 | — | — | 0 | not exercised |
| players | hand | real | 2319 | 0.998 | 0.000 | 576 | pass |
| players | library | real | 2542 | 0.995 | 0.000 | 576 | pass |
| players | graveyard | real | 2055 | 0.997 | 0.000 | 576 | pass |
| players | exile | real | 0 | — | — | 0 | not exercised |
| players | pool_W | real | 0 | — | — | 0 | not exercised |
| players | pool_U | real | 0 | — | — | 0 | not exercised |
| players | pool_B | real | 0 | — | — | 0 | not exercised |
| players | pool_R | real | 0 | — | — | 0 | not exercised |
| players | pool_G | real | 0 | — | — | 0 | not exercised |
| players | pool_C | real | 0 | — | — | 0 | not exercised |
| players | untapped_sources | real | 1980 | 0.998 | 0.000 | 576 | pass |
| players | lands | real | 2472 | 0.995 | 0.000 | 576 | pass |
| players | drawn_this_turn | real | 0 | — | — | 0 | not exercised |
| players | permanents | real | 2472 | 0.998 | 0.000 | 576 | pass |
| ent | ctr_loyalty | real | 467 | 0.971 | 0.000 | 4726 | pass |
| ent | damage | real | 7 | — | — | 0 | not exercised |
| ent | toughness | real | 9785 | 0.991 | 0.000 | 9626 | pass |
| ent | kw_prowess | binary | 0 | — | — | 0 | not exercised |
| ent | printed_tough | real | 9157 | 0.999 | 0.000 | 9626 | pass |
| ent | printed_power | real | 9157 | 0.999 | 0.000 | 9626 | pass |
| ent | face_down | binary | 0 | — | — | 0 | not exercised |
| ent | legal_targets | real | 645 | 0.933 | 0.000 | 1232 | pass |
| ent | kw_protection | binary | 0 | — | — | 0 | not exercised |
| ent | kw_menace | binary | 0 | — | — | 0 | not exercised |
| ent | kw_ninjutsu | binary | 994 | 1.000 | 0.970 | 9577 | pass |
| ent | kw_lifelink | binary | 965 | 1.000 | 0.967 | 9577 | pass |
| ent | turns_on_bf | real | 16328 | 0.957 | 0.000 | 4726 | pass |
| ent | kw_reach | binary | 0 | — | — | 0 | not exercised |
| ent | tapped | binary | 5456 | 1.000 | 0.742 | 4726 | pass |
| ent | mine | binary | 12968 | 0.995 | 0.592 | 8394 | **FAIL** |
| ent | kw_haste | binary | 0 | — | — | 0 | not exercised |
| ent | kw_defender | binary | 0 | — | — | 0 | not exercised |
| ent | zone_graveyard | binary | 0 | — | — | 0 | not exercised |
| ent | stack_X | real | 0 | — | — | 0 | not exercised |
| ent | sick | binary | 2523 | 1.000 | 0.882 | 4726 | pass |
| ent | zone_command | binary | 0 | — | — | 0 | not exercised |
| ent | zone_stack | binary | 0 | — | — | 0 | not exercised |
| ent | zone_hand | binary | 0 | — | — | 0 | not exercised |
| ent | instant | binary | 5841 | 1.000 | 0.648 | 4900 | pass |
| ent | loyalty | real | 467 | 0.971 | 0.000 | 4726 | pass |
| ent | stack_pos | real | 36 | 0.629 | 0.000 | 49 | **FAIL** |
| ent | can_attack | binary | 7220 | 1.000 | 0.660 | 4726 | pass |
| ent | kw_deathtouch | binary | 1410 | 0.999 | 0.953 | 9577 | pass |
| ent | zone_battlefield | binary | 0 | — | — | 0 | not exercised |
| ent | kw_flash | binary | 5904 | 1.000 | 0.860 | 9626 | **FAIL** |
| ent | lethal_as_is | binary | 7 | — | — | 0 | not exercised |
| ent | kw_flying | binary | 3635 | 1.000 | 0.869 | 9577 | pass |
| ent | kw_trample | binary | 0 | — | — | 0 | not exercised |
| ent | sorcery | binary | 454 | 1.000 | 0.959 | 4851 | pass |
| ent | stack_mine | binary | 49 | 0.939 | 0.694 | 49 | **FAIL** |
| ent | ctr_p1p1 | real | 41 | — | — | 0 | not exercised |
| ent | zone_library_known | binary | 0 | — | — | 0 | not exercised |
| ent | kw_vigilance | binary | 2425 | 1.000 | 0.954 | 9577 | pass |
| ent | attacking | binary | 256 | 1.000 | 0.989 | 4726 | pass |
| ent | mv | real | 17167 | 0.999 | 0.000 | 9626 | pass |
| ent | stack_modes | real | 205 | — | — | 0 | not exercised |
| ent | stack_is_ability | binary | 70 | 1.000 | 0.776 | 49 | pass |
| ent | kw_shroud | binary | 0 | — | — | 0 | not exercised |
| ent | blocking | binary | 3 | — | — | 0 | not exercised |
| ent | can_block | binary | 5456 | 1.000 | 0.742 | 4726 | pass |
| ent | ctr_m1m1 | real | 138 | 0.077 | 0.000 | 4726 | **FAIL** |
| ent | mana_left_if_cast | real | 2385 | 0.979 | 0.000 | 1232 | pass |
| ent | ctr_other | real | 98 | — | — | 0 | not exercised |
| ent | identity | cat | 27704 | 1.000 | 0.196 | 9615 | **FAIL** |
| ent | land | binary | 7809 | 1.000 | 0.777 | 9577 | pass |
| ent | kw_double_strike | binary | 0 | — | — | 0 | not exercised |
| ent | kw_first_strike | binary | 0 | — | — | 0 | not exercised |
| ent | other_perm | binary | 3646 | 1.000 | 0.840 | 9577 | pass |
| ent | tough_left | real | 9785 | 0.991 | 0.000 | 9626 | pass |
| ent | zone_exile | binary | 0 | — | — | 0 | not exercised |
| ent | entered | binary | 834 | 1.000 | 0.964 | 4726 | pass |
| ent | creature | binary | 9496 | 1.000 | 0.728 | 9626 | **FAIL** |
| ent | kw_ward | binary | 0 | — | — | 0 | not exercised |
| ent | kw_hexproof | binary | 302 | 1.000 | 0.994 | 4726 | pass |
| ent | castable | binary | 2275 | 1.000 | 0.537 | 1232 | pass |
| ent | power | real | 9789 | 0.991 | 0.000 | 9626 | pass |
| ent | token | binary | 1903 | 1.000 | 0.802 | 4726 | pass |
| opp_hand | origin_opening | binary | 1890 | 0.988 | 0.529 | 512 | pass |
| opp_hand | origin_drawn | binary | 1854 | 1.000 | 0.506 | 512 | pass |
| opp_hand | origin_returned | binary | 36 | 1.000 | 0.977 | 512 | pass |
| opp_hand | origin_other | binary | 0 | — | — | 0 | not exercised |
| opp_hand | age | real | 3815 | 0.681 | 0.000 | 512 | **FAIL** |
| opp_hand | known | binary | 36 | 1.000 | 0.977 | 512 | pass |
| opp_hand | seen | binary | 36 | 1.000 | 0.977 | 512 | pass |
| opp_hand | identity | cat | 18 | — | — | 0 | not exercised |
| opp_deck | count | real | 26804 | 0.983 | 0.000 | 5849 | pass |
| opp_deck | fraction | real | 26804 | 0.904 | 0.000 | 5849 | pass |
| opp_deck | castable_now | binary | 7885 | 1.000 | 0.772 | 5849 | pass |
| opp_deck | mv | real | 18016 | 1.000 | 0.000 | 5849 | pass |
| opp_deck | instant_speed | binary | 12087 | 1.000 | 0.546 | 5849 | pass |
| opp_deck | identity | cat | 25533 | 1.000 | 0.049 | 5849 | pass |
| opp_act | act_cast | binary | 5128 | 1.000 | 0.656 | 3437 | pass |
| opp_act | act_activate | binary | 180 | 1.000 | 0.976 | 3437 | pass |
| opp_act | act_attack | binary | 3208 | 1.000 | 0.654 | 3437 | pass |
| opp_act | act_block | binary | 90 | — | — | 0 | not exercised |
| opp_act | act_declined_block | binary | 743 | 1.000 | 0.949 | 3437 | pass |
| opp_act | act_passed_mana_up | binary | 2772 | 1.000 | 0.765 | 3437 | pass |
| opp_act | act_other | binary | 0 | — | — | 0 | not exercised |
| opp_act | consult_age | real | 12121 | 0.999 | 0.000 | 3437 | pass |
| cand | type_PASS | binary | 1136 | 1.000 | 0.697 | 856 | pass |
| cand | type_LAND | binary | 481 | 1.000 | 0.874 | 856 | pass |
| cand | type_SPELL | binary | 888 | 1.000 | 0.764 | 856 | pass |
| cand | type_ACTIVATE | binary | 795 | 1.000 | 0.806 | 856 | pass |
| cand | type_TARGET | binary | 346 | 1.000 | 0.922 | 856 | pass |
| cand | type_ATTACK | binary | 245 | 1.000 | 0.953 | 856 | pass |
| cand | type_BLOCK | binary | 55 | 1.000 | 0.984 | 856 | pass |
| cand | type_OTHER | binary | 0 | — | — | 0 | not exercised |
| cand | LSA.mana_left_after | real | 1570 | 0.997 | 0.000 | 476 | pass |
| cand | LSA.targets_legal | real | 684 | 0.992 | 0.000 | 476 | pass |
| cand | LSA.instant_speed | binary | 671 | 1.000 | 0.655 | 476 | pass |
| cand | LSA.sorcery_speed | binary | 671 | 1.000 | 0.655 | 476 | pass |
| cand | LSA.flash | binary | 314 | 1.000 | 0.845 | 476 | pass |
| cand | LSA.stack_above_n | real | 83 | 0.971 | 0.000 | 476 | pass |
| cand | LSA.X_chosen | real | 0 | — | — | 0 | not exercised |
| cand | TARGET.is_player | binary | 58 | 1.000 | 0.821 | 67 | pass |
| cand | TARGET.is_me | binary | 29 | — | — | 0 | not exercised |
| cand | TARGET.life_if_player | real | 32 | — | — | 0 | not exercised |
| cand | TARGET.is_creature | binary | 132 | 1.000 | 0.672 | 67 | pass |
| cand | TARGET.power | real | 211 | 0.996 | 0.000 | 67 | pass |
| cand | TARGET.toughness | real | 207 | 0.993 | 0.000 | 67 | pass |
| cand | TARGET.mine | binary | 156 | 1.000 | 0.522 | 67 | pass |
| cand | ATTACK.damage_dealt | real | 193 | 0.984 | 0.000 | 59 | pass |
| cand | ATTACK.their_kills | real | 84 | 0.969 | 0.000 | 59 | pass |
| cand | ATTACK.my_losses | real | 63 | 0.944 | 0.000 | 59 | pass |
| cand | ATTACK.lethal | binary | 38 | — | — | 0 | not exercised |
| cand | ATTACK.attackers_used | real | 245 | 0.977 | 0.000 | 59 | pass |
| cand | ATTACK.opp_life_after | real | 239 | 0.997 | 0.000 | 59 | pass |
| cand | ATTACK.bodies_retained | real | 145 | 0.980 | 0.000 | 59 | pass |
| cand | ATTACK.power_retained | real | 145 | 0.986 | 0.000 | 59 | pass |
| cand | ATTACK.tough_retained | real | 145 | 0.988 | 0.000 | 59 | pass |
| cand | ATTACK.crack_back | real | 24 | — | — | 0 | not exercised |
| cand | ATTACK.my_life_after | real | 245 | 0.991 | 0.000 | 59 | pass |
| cand | BLOCK.damage_taken | - | 0 | — | — | 0 | too few rows (55) |
| cand | BLOCK.attackers_killed | - | 0 | — | — | 0 | too few rows (55) |
| cand | BLOCK.value_killed | - | 0 | — | — | 0 | too few rows (55) |
| cand | BLOCK.blockers_lost | - | 0 | — | — | 0 | too few rows (55) |
| cand | BLOCK.value_lost | - | 0 | — | — | 0 | too few rows (55) |
| cand | BLOCK.defender_dies | - | 0 | — | — | 0 | too few rows (55) |
| cand | BLOCK.blockers_used | - | 0 | — | — | 0 | too few rows (55) |
| cand | BLOCK.life_after | - | 0 | — | — | 0 | too few rows (55) |

entity rows by zone: `{'battlefield': 17162, 'hand': 4618, 'stack': 205, 'graveyard': 10466, 'exile': 0, 'library_known': 0, 'command': 0}`; candidate rows by type: `{'PASS': 1136, 'LAND': 481, 'SPELL': 888, 'ACTIVATE': 795, 'TARGET': 346, 'ATTACK': 245, 'BLOCK': 55, 'OTHER': 0}`

## edges after L4 (balanced pairs)

| edge | positives | held-out | chance | result |
|---|---|---|---|---|
| blocks | 3 | — | — | too few rows |
| blocked_by | 3 | — | — | too few rows |
| attacking_player | 256 | 0.962 | 0.500 | pass |
| targets | 103 | 0.977 | 0.500 | pass |
| controls | 17162 | 0.998 | 0.500 | pass |
| attached_to | 0 | — | — | not exercised |
| can_block | 52 | 1.000 | 0.500 | pass |
| stack_above | 36 | — | — | not exercised |
| refers_to | 8235 | 0.983 | 0.500 | pass |
| referred_by | 8235 | 0.989 | 0.500 | pass |

## consult-level

- after L3: remaining-deck count per name mean R² = 0.01541585989929614 (min -3.2467155613763996, 22/22 names exercised; worst [(-3.2467155613763996, 'Island'), (-1.4231017440213862, 'Enduring Curiosity'), (-0.9320479183217396, 'Cecil, Dark Knight'), (-0.7468971517454834, 'Nowhere to Run'), (-0.20845487132030982, 'We Say Thee Nay!')]); instant-speed threat count R² = 0.7351664320809177 (exercised 930); known-card set: not exercised
- after L4: remaining-deck count per name mean R² = 0.19381827906665725 (min -1.5575983503155117, 22/22 names exercised; worst [(-1.5575983503155117, 'Cecil, Dark Knight'), (-1.5337878707778518, 'Island'), (-0.013874166874974003, 'Spell Pierce'), (0.03704184652298259, 'Gloomlake Verge'), (0.09331333887810178, 'Enduring Curiosity')]); instant-speed threat count R² = 0.9162636241997438 (exercised 930); known-card set: not exercised
