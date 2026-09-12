# 5b faithfulness on real dumps — 15866 consults, 385 games, 56 recordings

Thresholds: `{"L3": {"binary": 0.99, "cat": 0.99, "real": 0.95}, "L4": {"binary": 0.95, "cat": 0.95, "real": 0.9}, "edge": 0.9, "consult": {"real": 0.9, "binary": 0.95}}`

## after L3

| part | field | kind | exercised | held-out | chance | n | result |
|---|---|---|---|---|---|---|---|
| game | turn | real | 15866 | 1.000 | 0.000 | 3303 | pass |
| game | i_am_active | binary | 2203 | 1.000 | 0.870 | 3303 | pass |
| game | step_upkeep | binary | 7336 | 1.000 | 0.502 | 3303 | pass |
| game | step_draw | binary | 0 | — | — | 0 | not exercised |
| game | step_main1 | binary | 5269 | 1.000 | 0.693 | 3303 | pass |
| game | step_decl_att | binary | 664 | 1.000 | 0.955 | 3303 | pass |
| game | step_decl_blk | binary | 1969 | 1.000 | 0.887 | 3303 | pass |
| game | step_combat_dmg | binary | 1 | — | — | 0 | not exercised |
| game | step_main2 | binary | 261 | 1.000 | 0.990 | 3303 | pass |
| game | step_end | binary | 366 | 1.000 | 0.977 | 3303 | pass |
| game | priority | binary | 886 | 1.000 | 0.940 | 3303 | pass |
| game | stack_depth | real | 1452 | 1.000 | 0.000 | 3303 | pass |
| game | dtype_PASS | binary | 1554 | 1.000 | 0.902 | 3303 | pass |
| game | dtype_LAND | binary | 2300 | 1.000 | 0.867 | 3303 | pass |
| game | dtype_SPELL | binary | 1773 | 1.000 | 0.930 | 3303 | pass |
| game | dtype_ACTIVATE | binary | 7435 | 1.000 | 0.593 | 3303 | pass |
| game | dtype_TARGET | binary | 729 | 1.000 | 0.953 | 3303 | pass |
| game | dtype_ATTACK | binary | 562 | 1.000 | 0.964 | 3303 | pass |
| game | dtype_BLOCK | binary | 517 | 1.000 | 0.976 | 3303 | pass |
| game | dtype_OTHER | binary | 0 | — | — | 0 | not exercised |
| game | n_cand | real | 15866 | 1.000 | 0.000 | 3303 | pass |
| game | consults_so_far | real | 15866 | 1.000 | 0.000 | 3303 | pass |
| game | my_deck_open | binary | 0 | — | — | 0 | not exercised |
| game | opp_deck_open | binary | 0 | — | — | 0 | not exercised |
| players | life | real | 31344 | 1.000 | 0.000 | 6606 | pass |
| players | poison | real | 0 | — | — | 0 | not exercised |
| players | hand | real | 28437 | 1.000 | 0.000 | 6606 | pass |
| players | library | real | 31732 | 1.000 | 0.000 | 6606 | pass |
| players | graveyard | real | 20120 | 1.000 | 0.000 | 6606 | pass |
| players | exile | real | 1006 | 1.000 | 0.000 | 6606 | pass |
| players | pool_W | real | 2105 | 1.000 | 0.000 | 6606 | pass |
| players | pool_U | real | 1368 | 1.000 | 0.000 | 6606 | pass |
| players | pool_B | real | 3043 | 1.000 | 0.000 | 6606 | pass |
| players | pool_R | real | 105 | 1.000 | 0.000 | 6606 | pass |
| players | pool_G | real | 243 | 1.000 | 0.000 | 6606 | pass |
| players | pool_C | real | 208 | 1.000 | 0.000 | 6606 | pass |
| players | untapped_sources | real | 19138 | 1.000 | 0.000 | 6606 | pass |
| players | lands | real | 30825 | 1.000 | 0.000 | 6606 | pass |
| players | drawn_this_turn | real | 0 | — | — | 0 | not exercised |
| players | permanents | real | 30825 | 1.000 | 0.000 | 6606 | pass |
| ent | legal_targets | real | 2035 | 1.000 | 0.000 | 8109 | pass |
| ent | ctr_p1p1 | real | 209 | 1.000 | 0.000 | 9033 | pass |
| ent | kw_menace | binary | 457 | 1.000 | 0.997 | 17142 | pass |
| ent | stack_X | real | 0 | — | — | 0 | not exercised |
| ent | kw_protection | binary | 749 | 1.000 | 0.991 | 17142 | pass |
| ent | tapped | binary | 19608 | 1.000 | 0.531 | 9033 | pass |
| ent | stack_is_ability | binary | 458 | 1.000 | 0.689 | 238 | pass |
| ent | kw_reach | binary | 834 | 1.000 | 0.995 | 17142 | pass |
| ent | zone_library_known | binary | 0 | — | — | 0 | not exercised |
| ent | sick | binary | 5957 | 1.000 | 0.867 | 9033 | pass |
| ent | sorcery | binary | 1352 | 1.000 | 0.982 | 12956 | pass |
| ent | lethal_as_is | binary | 0 | — | — | 0 | not exercised |
| ent | kw_first_strike | binary | 304 | 1.000 | 0.993 | 17142 | pass |
| ent | attacking | binary | 821 | 1.000 | 0.983 | 9033 | pass |
| ent | printed_tough | real | 61462 | 1.000 | 0.000 | 22227 | pass |
| ent | stack_modes | real | 1733 | 1.000 | 0.000 | 238 | pass |
| ent | printed_power | real | 61083 | 0.999 | 0.000 | 22227 | pass |
| ent | token | binary | 775 | 1.000 | 0.982 | 9033 | pass |
| ent | kw_ward | binary | 0 | — | — | 0 | not exercised |
| ent | zone_exile | binary | 0 | — | — | 0 | not exercised |
| ent | stack_pos | real | 281 | 1.000 | 0.000 | 238 | pass |
| ent | kw_flash | binary | 20015 | 0.999 | 0.883 | 22227 | pass |
| ent | kw_haste | binary | 344 | 1.000 | 0.990 | 9033 | pass |
| ent | land | binary | 19489 | 1.000 | 0.809 | 21989 | pass |
| ent | stack_mine | binary | 19 | — | — | 0 | not exercised |
| ent | ctr_m1m1 | real | 39 | — | — | 0 | not exercised |
| ent | kw_double_strike | binary | 339 | 1.000 | 0.997 | 17142 | pass |
| ent | kw_defender | binary | 379 | 1.000 | 0.991 | 17142 | pass |
| ent | zone_battlefield | binary | 0 | — | — | 0 | not exercised |
| ent | mv | real | 82440 | 1.000 | 0.000 | 22227 | pass |
| ent | kw_vigilance | binary | 2740 | 1.000 | 0.986 | 22227 | pass |
| ent | turns_on_bf | real | 38535 | 1.000 | 0.000 | 9033 | pass |
| ent | kw_shroud | binary | 256 | 1.000 | 0.997 | 9033 | pass |
| ent | other_perm | binary | 3980 | 1.000 | 0.971 | 21989 | pass |
| ent | can_attack | binary | 16079 | 1.000 | 0.571 | 9033 | pass |
| ent | loyalty | real | 101 | 1.000 | 0.000 | 9033 | pass |
| ent | kw_deathtouch | binary | 1583 | 1.000 | 0.991 | 21989 | pass |
| ent | zone_stack | binary | 0 | — | — | 0 | not exercised |
| ent | can_block | binary | 19608 | 1.000 | 0.531 | 9033 | pass |
| ent | kw_lifelink | binary | 1469 | 1.000 | 0.992 | 21989 | pass |
| ent | mine | binary | 36504 | 1.000 | 0.537 | 13880 | pass |
| ent | kw_prowess | binary | 344 | 1.000 | 0.990 | 9033 | pass |
| ent | castable | binary | 16682 | 1.000 | 0.607 | 8109 | pass |
| ent | face_down | binary | 0 | — | — | 0 | not exercised |
| ent | zone_command | binary | 0 | — | — | 0 | not exercised |
| ent | blocking | binary | 7 | — | — | 0 | not exercised |
| ent | power | real | 61313 | 0.999 | 0.000 | 22227 | pass |
| ent | instant | binary | 16491 | 1.000 | 0.805 | 13194 | pass |
| ent | toughness | real | 61692 | 1.000 | 0.000 | 22227 | pass |
| ent | tough_left | real | 61692 | 1.000 | 0.000 | 22227 | pass |
| ent | damage | real | 1 | — | — | 0 | not exercised |
| ent | kw_ninjutsu | binary | 2019 | 1.000 | 0.983 | 21989 | pass |
| ent | entered | binary | 1465 | 1.000 | 0.967 | 9033 | pass |
| ent | identity | cat | 105075 | 0.999 | 0.142 | 22153 | pass |
| ent | ctr_loyalty | real | 101 | 1.000 | 0.000 | 9033 | pass |
| ent | kw_hexproof | binary | 9 | — | — | 0 | not exercised |
| ent | ctr_other | real | 13 | — | — | 0 | not exercised |
| ent | mana_left_if_cast | real | 9052 | 1.000 | 0.000 | 8109 | pass |
| ent | creature | binary | 38748 | 1.000 | 0.676 | 22227 | pass |
| ent | zone_hand | binary | 0 | — | — | 0 | not exercised |
| ent | kw_trample | binary | 809 | 1.000 | 0.993 | 17142 | pass |
| ent | zone_graveyard | binary | 0 | — | — | 0 | not exercised |
| ent | kw_flying | binary | 16368 | 1.000 | 0.903 | 22227 | pass |
| opp_hand | origin_opening | binary | 16038 | 1.000 | 0.571 | 8179 | pass |
| opp_hand | origin_drawn | binary | 15723 | 1.000 | 0.579 | 8179 | pass |
| opp_hand | origin_returned | binary | 315 | 1.000 | 0.993 | 8179 | pass |
| opp_hand | origin_other | binary | 0 | — | — | 0 | not exercised |
| opp_hand | age | real | 39160 | 1.000 | 0.000 | 8179 | pass |
| opp_hand | known | binary | 315 | 1.000 | 0.993 | 8179 | pass |
| opp_hand | seen | binary | 315 | 1.000 | 0.993 | 8179 | pass |
| opp_hand | identity | cat | 264 | 1.000 | 0.230 | 61 | pass |
| opp_deck | count | real | 40000 | 1.000 | 0.000 | 8688 | pass |
| opp_deck | fraction | real | 40000 | 1.000 | 0.000 | 8688 | pass |
| opp_deck | castable_now | binary | 18189 | 1.000 | 0.581 | 8688 | pass |
| opp_deck | mv | real | 30203 | 1.000 | 0.000 | 8688 | pass |
| opp_deck | instant_speed | binary | 12606 | 1.000 | 0.628 | 8688 | pass |
| opp_deck | identity | cat | 38506 | 1.000 | 0.038 | 8688 | pass |
| opp_act | act_cast | binary | 14048 | 1.000 | 0.663 | 8725 | pass |
| opp_act | act_activate | binary | 260 | 1.000 | 0.995 | 8725 | pass |
| opp_act | act_attack | binary | 13480 | 1.000 | 0.700 | 8725 | pass |
| opp_act | act_block | binary | 310 | 1.000 | 0.982 | 8725 | pass |
| opp_act | act_declined_block | binary | 2467 | 1.000 | 0.925 | 8725 | pass |
| opp_act | act_passed_mana_up | binary | 9435 | 1.000 | 0.735 | 8725 | pass |
| opp_act | act_other | binary | 0 | — | — | 0 | not exercised |
| opp_act | consult_age | real | 40000 | 1.000 | 0.000 | 8725 | pass |
| cand | type_PASS | binary | 11516 | 1.000 | 0.724 | 8845 | pass |
| cand | type_LAND | binary | 4080 | 1.000 | 0.914 | 8845 | pass |
| cand | type_SPELL | binary | 4297 | 1.000 | 0.928 | 8845 | pass |
| cand | type_ACTIVATE | binary | 15812 | 1.000 | 0.563 | 8845 | pass |
| cand | type_TARGET | binary | 2548 | 1.000 | 0.939 | 8845 | pass |
| cand | type_ATTACK | binary | 1220 | 1.000 | 0.941 | 8845 | pass |
| cand | type_BLOCK | binary | 527 | 0.995 | 0.990 | 8845 | pass |
| cand | type_OTHER | binary | 0 | — | — | 0 | not exercised |
| cand | LSA.mana_left_after | real | 17883 | 1.000 | 0.000 | 5262 | pass |
| cand | LSA.targets_legal | real | 932 | 1.000 | 0.000 | 5262 | pass |
| cand | LSA.instant_speed | binary | 5846 | 1.000 | 0.838 | 5262 | pass |
| cand | LSA.sorcery_speed | binary | 5846 | 1.000 | 0.838 | 5262 | pass |
| cand | LSA.flash | binary | 1728 | 1.000 | 0.932 | 5262 | pass |
| cand | LSA.stack_above_n | real | 2772 | 1.000 | 0.000 | 5262 | pass |
| cand | LSA.X_chosen | real | 0 | — | — | 0 | not exercised |
| cand | TARGET.is_player | binary | 299 | 1.000 | 0.861 | 459 | pass |
| cand | TARGET.is_me | binary | 149 | 1.000 | 0.930 | 459 | pass |
| cand | TARGET.life_if_player | real | 0 | — | — | 0 | not exercised |
| cand | TARGET.is_creature | binary | 807 | 1.000 | 0.730 | 459 | pass |
| cand | TARGET.power | real | 1738 | 1.000 | 0.000 | 459 | pass |
| cand | TARGET.toughness | real | 1741 | 1.000 | 0.000 | 459 | pass |
| cand | TARGET.mine | binary | 950 | 1.000 | 0.649 | 459 | pass |
| cand | ATTACK.damage_dealt | real | 677 | 1.000 | 0.000 | 100 | pass |
| cand | ATTACK.their_kills | real | 809 | 1.000 | 0.000 | 100 | pass |
| cand | ATTACK.my_losses | real | 794 | 1.000 | 0.000 | 100 | pass |
| cand | ATTACK.lethal | binary | 100 | — | — | 0 | not exercised |
| cand | ATTACK.attackers_used | real | 1220 | 1.000 | 0.000 | 100 | pass |
| cand | ATTACK.opp_life_after | real | 1209 | 1.000 | 0.000 | 100 | pass |
| cand | ATTACK.bodies_retained | real | 791 | 1.000 | 0.000 | 100 | pass |
| cand | ATTACK.power_retained | real | 791 | 1.000 | 0.000 | 100 | pass |
| cand | ATTACK.tough_retained | real | 791 | 1.000 | 0.000 | 100 | pass |
| cand | ATTACK.crack_back | real | 349 | 1.000 | 0.000 | 100 | pass |
| cand | ATTACK.my_life_after | real | 1205 | 1.000 | 0.000 | 100 | pass |
| cand | BLOCK.damage_taken | real | 247 | 1.000 | 0.000 | 113 | pass |
| cand | BLOCK.attackers_killed | real | 386 | 1.000 | 0.000 | 113 | pass |
| cand | BLOCK.value_killed | real | 386 | 1.000 | 0.000 | 113 | pass |
| cand | BLOCK.blockers_lost | real | 466 | 1.000 | 0.000 | 113 | pass |
| cand | BLOCK.value_lost | real | 466 | 1.000 | 0.000 | 113 | pass |
| cand | BLOCK.defender_dies | binary | 30 | — | — | 0 | not exercised |
| cand | BLOCK.blockers_used | real | 527 | 1.000 | 0.000 | 113 | pass |
| cand | BLOCK.life_after | real | 521 | 1.000 | 0.000 | 113 | pass |

entity rows by zone: `{'battlefield': 40000, 'hand': 40000, 'stack': 1733, 'graveyard': 40000, 'exile': 0, 'library_known': 0, 'command': 0}`; candidate rows by type: `{'PASS': 15063, 'LAND': 5403, 'SPELL': 5710, 'ACTIVATE': 20673, 'TARGET': 3297, 'ATTACK': 1588, 'BLOCK': 692, 'OTHER': 0}`

## after L4

| part | field | kind | exercised | held-out | chance | n | result |
|---|---|---|---|---|---|---|---|
| game | turn | real | 15866 | 0.992 | 0.000 | 3303 | pass |
| game | i_am_active | binary | 2203 | 1.000 | 0.870 | 3303 | pass |
| game | step_upkeep | binary | 7336 | 1.000 | 0.502 | 3303 | pass |
| game | step_draw | binary | 0 | — | — | 0 | not exercised |
| game | step_main1 | binary | 5269 | 1.000 | 0.693 | 3303 | pass |
| game | step_decl_att | binary | 664 | 1.000 | 0.955 | 3303 | pass |
| game | step_decl_blk | binary | 1969 | 1.000 | 0.887 | 3303 | pass |
| game | step_combat_dmg | binary | 1 | — | — | 0 | not exercised |
| game | step_main2 | binary | 261 | 1.000 | 0.990 | 3303 | pass |
| game | step_end | binary | 366 | 1.000 | 0.977 | 3303 | pass |
| game | priority | binary | 886 | 1.000 | 0.940 | 3303 | pass |
| game | stack_depth | real | 1452 | 0.928 | 0.000 | 3303 | pass |
| game | dtype_PASS | binary | 1554 | 1.000 | 0.902 | 3303 | pass |
| game | dtype_LAND | binary | 2300 | 1.000 | 0.867 | 3303 | pass |
| game | dtype_SPELL | binary | 1773 | 1.000 | 0.930 | 3303 | pass |
| game | dtype_ACTIVATE | binary | 7435 | 1.000 | 0.593 | 3303 | pass |
| game | dtype_TARGET | binary | 729 | 0.999 | 0.953 | 3303 | pass |
| game | dtype_ATTACK | binary | 562 | 1.000 | 0.964 | 3303 | pass |
| game | dtype_BLOCK | binary | 517 | 0.998 | 0.976 | 3303 | pass |
| game | dtype_OTHER | binary | 0 | — | — | 0 | not exercised |
| game | n_cand | real | 15866 | 0.856 | 0.000 | 3303 | **FAIL** |
| game | consults_so_far | real | 15866 | 0.978 | 0.000 | 3303 | pass |
| game | my_deck_open | binary | 0 | — | — | 0 | not exercised |
| game | opp_deck_open | binary | 0 | — | — | 0 | not exercised |
| players | life | real | 31344 | 0.998 | 0.000 | 6606 | pass |
| players | poison | real | 0 | — | — | 0 | not exercised |
| players | hand | real | 28437 | 0.998 | 0.000 | 6606 | pass |
| players | library | real | 31732 | 0.993 | 0.000 | 6606 | pass |
| players | graveyard | real | 20120 | 0.995 | 0.000 | 6606 | pass |
| players | exile | real | 1006 | 0.728 | 0.000 | 6606 | **FAIL** |
| players | pool_W | real | 2105 | 0.989 | 0.000 | 6606 | pass |
| players | pool_U | real | 1368 | 0.983 | 0.000 | 6606 | pass |
| players | pool_B | real | 3043 | 0.997 | 0.000 | 6606 | pass |
| players | pool_R | real | 105 | 0.814 | 0.000 | 6606 | **FAIL** |
| players | pool_G | real | 243 | 0.951 | 0.000 | 6606 | pass |
| players | pool_C | real | 208 | 0.862 | 0.000 | 6606 | **FAIL** |
| players | untapped_sources | real | 19138 | 0.998 | 0.000 | 6606 | pass |
| players | lands | real | 30825 | 0.998 | 0.000 | 6606 | pass |
| players | drawn_this_turn | real | 0 | — | — | 0 | not exercised |
| players | permanents | real | 30825 | 0.997 | 0.000 | 6606 | pass |
| ent | legal_targets | real | 1933 | 0.951 | 0.000 | 8058 | pass |
| ent | ctr_p1p1 | real | 204 | 0.470 | 0.000 | 9152 | **FAIL** |
| ent | kw_menace | binary | 476 | 1.000 | 0.990 | 22413 | pass |
| ent | stack_X | real | 0 | — | — | 0 | not exercised |
| ent | kw_protection | binary | 736 | 0.999 | 0.986 | 22413 | pass |
| ent | tapped | binary | 19395 | 1.000 | 0.552 | 9152 | pass |
| ent | stack_is_ability | binary | 458 | 1.000 | 0.689 | 238 | pass |
| ent | kw_reach | binary | 779 | 1.000 | 0.985 | 22413 | pass |
| ent | zone_library_known | binary | 0 | — | — | 0 | not exercised |
| ent | sick | binary | 6007 | 1.000 | 0.863 | 9152 | pass |
| ent | sorcery | binary | 1323 | 1.000 | 0.989 | 13261 | pass |
| ent | lethal_as_is | binary | 0 | — | — | 0 | not exercised |
| ent | kw_first_strike | binary | 329 | 0.999 | 0.993 | 22413 | pass |
| ent | attacking | binary | 835 | 1.000 | 0.981 | 9152 | pass |
| ent | printed_tough | real | 61603 | 0.994 | 0.000 | 22651 | pass |
| ent | stack_modes | real | 1733 | 1.000 | 0.000 | 238 | pass |
| ent | printed_power | real | 61236 | 0.996 | 0.000 | 22651 | pass |
| ent | token | binary | 807 | 1.000 | 0.982 | 9152 | pass |
| ent | kw_ward | binary | 0 | — | — | 0 | not exercised |
| ent | zone_exile | binary | 0 | — | — | 0 | not exercised |
| ent | stack_pos | real | 281 | 0.892 | 0.000 | 238 | **FAIL** |
| ent | kw_flash | binary | 20003 | 1.000 | 0.856 | 22651 | pass |
| ent | kw_haste | binary | 333 | 1.000 | 0.993 | 14355 | pass |
| ent | land | binary | 19465 | 1.000 | 0.808 | 22413 | pass |
| ent | stack_mine | binary | 19 | — | — | 0 | not exercised |
| ent | ctr_m1m1 | real | 31 | — | — | 0 | not exercised |
| ent | kw_double_strike | binary | 364 | 0.999 | 0.992 | 22413 | pass |
| ent | kw_defender | binary | 367 | 1.000 | 0.992 | 22413 | pass |
| ent | zone_battlefield | binary | 0 | — | — | 0 | not exercised |
| ent | mv | real | 82502 | 0.995 | 0.000 | 22651 | pass |
| ent | kw_vigilance | binary | 2689 | 1.000 | 0.984 | 22651 | pass |
| ent | turns_on_bf | real | 38564 | 0.979 | 0.000 | 9152 | pass |
| ent | kw_shroud | binary | 262 | 1.000 | 0.991 | 14355 | pass |
| ent | other_perm | binary | 3970 | 1.000 | 0.973 | 22413 | pass |
| ent | can_attack | binary | 16231 | 1.000 | 0.556 | 9152 | pass |
| ent | loyalty | real | 105 | 0.961 | 0.000 | 9152 | pass |
| ent | kw_deathtouch | binary | 1589 | 1.000 | 0.993 | 22413 | pass |
| ent | zone_stack | binary | 0 | — | — | 0 | not exercised |
| ent | can_block | binary | 19395 | 1.000 | 0.552 | 9152 | pass |
| ent | kw_lifelink | binary | 1466 | 1.000 | 0.994 | 22413 | pass |
| ent | mine | binary | 36453 | 0.997 | 0.548 | 14355 | pass |
| ent | kw_prowess | binary | 333 | 1.000 | 0.993 | 14355 | pass |
| ent | castable | binary | 16687 | 1.000 | 0.604 | 8058 | pass |
| ent | face_down | binary | 0 | — | — | 0 | not exercised |
| ent | zone_command | binary | 0 | — | — | 0 | not exercised |
| ent | blocking | binary | 2 | — | — | 0 | not exercised |
| ent | power | real | 61443 | 0.979 | 0.000 | 22651 | pass |
| ent | instant | binary | 16483 | 1.000 | 0.815 | 13499 | pass |
| ent | toughness | real | 61811 | 0.985 | 0.000 | 22651 | pass |
| ent | tough_left | real | 61811 | 0.985 | 0.000 | 22651 | pass |
| ent | damage | real | 0 | — | — | 0 | not exercised |
| ent | kw_ninjutsu | binary | 1980 | 1.000 | 0.986 | 22413 | pass |
| ent | entered | binary | 1436 | 1.000 | 0.966 | 9152 | pass |
| ent | identity | cat | 105203 | 0.999 | 0.137 | 22577 | pass |
| ent | ctr_loyalty | real | 105 | 0.961 | 0.000 | 9152 | pass |
| ent | kw_hexproof | binary | 12 | — | — | 0 | not exercised |
| ent | ctr_other | real | 15 | — | — | 0 | not exercised |
| ent | mana_left_if_cast | real | 8996 | 0.956 | 0.000 | 8058 | pass |
| ent | creature | binary | 38573 | 1.000 | 0.687 | 22651 | pass |
| ent | zone_hand | binary | 0 | — | — | 0 | not exercised |
| ent | kw_trample | binary | 780 | 1.000 | 0.988 | 22413 | pass |
| ent | zone_graveyard | binary | 0 | — | — | 0 | not exercised |
| ent | kw_flying | binary | 16271 | 1.000 | 0.881 | 22651 | pass |
| opp_hand | origin_opening | binary | 16023 | 1.000 | 0.572 | 8162 | pass |
| opp_hand | origin_drawn | binary | 15696 | 1.000 | 0.581 | 8162 | pass |
| opp_hand | origin_returned | binary | 327 | 1.000 | 0.992 | 8162 | pass |
| opp_hand | origin_other | binary | 0 | — | — | 0 | not exercised |
| opp_hand | age | real | 39155 | 0.996 | 0.000 | 8162 | pass |
| opp_hand | known | binary | 327 | 1.000 | 0.992 | 8162 | pass |
| opp_hand | seen | binary | 327 | 1.000 | 0.992 | 8162 | pass |
| opp_hand | identity | cat | 277 | 1.000 | 0.309 | 68 | pass |
| opp_deck | count | real | 40000 | 0.969 | 0.000 | 8544 | pass |
| opp_deck | fraction | real | 40000 | 0.957 | 0.000 | 8544 | pass |
| opp_deck | castable_now | binary | 18126 | 1.000 | 0.585 | 8544 | pass |
| opp_deck | mv | real | 30138 | 0.997 | 0.000 | 8544 | pass |
| opp_deck | instant_speed | binary | 12621 | 1.000 | 0.640 | 8544 | pass |
| opp_deck | identity | cat | 38451 | 1.000 | 0.038 | 8544 | pass |
| opp_act | act_cast | binary | 14046 | 1.000 | 0.658 | 8640 | pass |
| opp_act | act_activate | binary | 256 | 1.000 | 0.996 | 8640 | pass |
| opp_act | act_attack | binary | 13373 | 1.000 | 0.695 | 8640 | pass |
| opp_act | act_block | binary | 305 | 1.000 | 0.981 | 8640 | pass |
| opp_act | act_declined_block | binary | 2442 | 1.000 | 0.924 | 8640 | pass |
| opp_act | act_passed_mana_up | binary | 9578 | 1.000 | 0.746 | 8640 | pass |
| opp_act | act_other | binary | 0 | — | — | 0 | not exercised |
| opp_act | consult_age | real | 40000 | 1.000 | 0.000 | 8640 | pass |
| cand | type_PASS | binary | 11495 | 1.000 | 0.731 | 8789 | pass |
| cand | type_LAND | binary | 4102 | 0.999 | 0.911 | 8789 | pass |
| cand | type_SPELL | binary | 4352 | 1.000 | 0.927 | 8789 | pass |
| cand | type_ACTIVATE | binary | 15847 | 1.000 | 0.558 | 8789 | pass |
| cand | type_TARGET | binary | 2460 | 1.000 | 0.942 | 8789 | pass |
| cand | type_ATTACK | binary | 1193 | 1.000 | 0.942 | 8789 | pass |
| cand | type_BLOCK | binary | 551 | 1.000 | 0.989 | 8789 | pass |
| cand | type_OTHER | binary | 0 | — | — | 0 | not exercised |
| cand | LSA.mana_left_after | real | 17904 | 0.999 | 0.000 | 5309 | pass |
| cand | LSA.targets_legal | real | 950 | 0.989 | 0.000 | 5309 | pass |
| cand | LSA.instant_speed | binary | 5873 | 1.000 | 0.834 | 5309 | pass |
| cand | LSA.sorcery_speed | binary | 5873 | 1.000 | 0.834 | 5309 | pass |
| cand | LSA.flash | binary | 1752 | 1.000 | 0.934 | 5309 | pass |
| cand | LSA.stack_above_n | real | 2781 | 0.987 | 0.000 | 5309 | pass |
| cand | LSA.X_chosen | real | 0 | — | — | 0 | not exercised |
| cand | TARGET.is_player | binary | 275 | 1.000 | 0.892 | 498 | pass |
| cand | TARGET.is_me | binary | 131 | 1.000 | 0.948 | 498 | pass |
| cand | TARGET.life_if_player | real | 0 | — | — | 0 | not exercised |
| cand | TARGET.is_creature | binary | 778 | 1.000 | 0.665 | 498 | pass |
| cand | TARGET.power | real | 1679 | 0.998 | 0.000 | 498 | pass |
| cand | TARGET.toughness | real | 1682 | 0.998 | 0.000 | 498 | pass |
| cand | TARGET.mine | binary | 923 | 1.000 | 0.612 | 498 | pass |
| cand | ATTACK.damage_dealt | real | 654 | 0.933 | 0.000 | 119 | pass |
| cand | ATTACK.their_kills | real | 801 | 0.993 | 0.000 | 119 | pass |
| cand | ATTACK.my_losses | real | 788 | 0.990 | 0.000 | 119 | pass |
| cand | ATTACK.lethal | binary | 94 | — | — | 0 | not exercised |
| cand | ATTACK.attackers_used | real | 1193 | 0.982 | 0.000 | 119 | pass |
| cand | ATTACK.opp_life_after | real | 1185 | 0.997 | 0.000 | 119 | pass |
| cand | ATTACK.bodies_retained | real | 796 | 0.991 | 0.000 | 119 | pass |
| cand | ATTACK.power_retained | real | 796 | 0.983 | 0.000 | 119 | pass |
| cand | ATTACK.tough_retained | real | 796 | 0.983 | 0.000 | 119 | pass |
| cand | ATTACK.crack_back | real | 331 | 0.876 | 0.000 | 119 | **FAIL** |
| cand | ATTACK.my_life_after | real | 1178 | 0.995 | 0.000 | 119 | pass |
| cand | BLOCK.damage_taken | real | 259 | 0.984 | 0.000 | 108 | pass |
| cand | BLOCK.attackers_killed | real | 409 | 0.982 | 0.000 | 108 | pass |
| cand | BLOCK.value_killed | real | 409 | 0.972 | 0.000 | 108 | pass |
| cand | BLOCK.blockers_lost | real | 485 | 0.962 | 0.000 | 108 | pass |
| cand | BLOCK.value_lost | real | 485 | 0.979 | 0.000 | 108 | pass |
| cand | BLOCK.defender_dies | binary | 34 | — | — | 0 | not exercised |
| cand | BLOCK.blockers_used | real | 551 | 0.832 | 0.000 | 108 | **FAIL** |
| cand | BLOCK.life_after | real | 542 | 0.997 | 0.000 | 108 | pass |

entity rows by zone: `{'battlefield': 40000, 'hand': 40000, 'stack': 1733, 'graveyard': 40000, 'exile': 0, 'library_known': 0, 'command': 0}`; candidate rows by type: `{'PASS': 15063, 'LAND': 5403, 'SPELL': 5710, 'ACTIVATE': 20673, 'TARGET': 3297, 'ATTACK': 1588, 'BLOCK': 692, 'OTHER': 0}`

## edges after L4 (balanced pairs)

| edge | positives | held-out | chance | result |
|---|---|---|---|---|
| blocks | 0 | — | — | not exercised |
| blocked_by | 19 | — | — | too few rows |
| attacking_player | 4108 | 0.999 | 0.500 | pass |
| targets | 361 | 0.989 | 0.500 | pass |
| controls | 20074 | 0.997 | 0.502 | pass |
| attached_to | 0 | — | — | not exercised |
| can_block | 1141 | 1.000 | 0.500 | pass |
| stack_above | 281 | 1.000 | 0.500 | pass |
| refers_to | 20037 | 0.984 | 0.503 | pass |
| referred_by | 20063 | 0.986 | 0.503 | pass |

## consult-level

- after L3: remaining-deck count per name mean R² = 0.12952241050089516 (min -11.957207950788874, 66/68 names exercised; worst [(-11.957207950788874, 'Wall of Omens'), (-5.1794213966579665, 'Quickling'), (-1.801926515833098, 'Deadly Insect'), (-1.1251032554423808, 'We Say Thee Nay!'), (-0.9964553634112139, 'Boggart Brute')]); instant-speed threat count R² = 0.8691843177736596 (exercised 5923); known-card set: 0.9882358590223759
- after L4: remaining-deck count per name mean R² = 0.09952130248691157 (min -11.696805331204292, 66/68 names exercised; worst [(-11.696805331204292, 'Wall of Omens'), (-4.798454861442253, 'Quickling'), (-3.337984305173208, 'Deadly Insect'), (-2.4581353787592755, 'Forest'), (-1.3218036553973507, 'Requiting Hex')]); instant-speed threat count R² = 0.9313286923767742 (exercised 5923); known-card set: 0.9821308529173698
