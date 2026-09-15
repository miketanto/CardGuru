# 5b faithfulness on real dumps — 100 consults, 24 games, 1 recordings

Thresholds: `{"L3": {"binary": 0.99, "cat": 0.99, "real": 0.95}, "L4": {"binary": 0.95, "cat": 0.95, "real": 0.9}, "edge": 0.9, "consult": {"real": 0.9, "binary": 0.95}}`

## after L3

| part | field | kind | exercised | held-out | chance | n | result |
|---|---|---|---|---|---|---|---|
| game | turn | real | 0 | — | — | 0 | too few rows |
| game | i_am_active | binary | 0 | — | — | 0 | too few rows |
| game | step_upkeep | binary | 0 | — | — | 0 | too few rows |
| game | step_draw | binary | 0 | — | — | 0 | too few rows |
| game | step_main1 | binary | 0 | — | — | 0 | too few rows |
| game | step_decl_att | binary | 0 | — | — | 0 | too few rows |
| game | step_decl_blk | binary | 0 | — | — | 0 | too few rows |
| game | step_combat_dmg | binary | 0 | — | — | 0 | too few rows |
| game | step_main2 | binary | 0 | — | — | 0 | too few rows |
| game | step_end | binary | 0 | — | — | 0 | too few rows |
| game | priority | binary | 0 | — | — | 0 | too few rows |
| game | stack_depth | real | 0 | — | — | 0 | too few rows |
| game | dtype_PASS | binary | 0 | — | — | 0 | too few rows |
| game | dtype_LAND | binary | 0 | — | — | 0 | too few rows |
| game | dtype_SPELL | binary | 0 | — | — | 0 | too few rows |
| game | dtype_ACTIVATE | binary | 0 | — | — | 0 | too few rows |
| game | dtype_TARGET | binary | 0 | — | — | 0 | too few rows |
| game | dtype_ATTACK | binary | 0 | — | — | 0 | too few rows |
| game | dtype_BLOCK | binary | 0 | — | — | 0 | too few rows |
| game | dtype_OTHER | binary | 0 | — | — | 0 | too few rows |
| game | n_cand | real | 0 | — | — | 0 | too few rows |
| game | consults_so_far | real | 0 | — | — | 0 | too few rows |
| game | my_deck_open | binary | 0 | — | — | 0 | too few rows |
| game | opp_deck_open | binary | 0 | — | — | 0 | too few rows |
| players | life | real | 196 | 1.000 | 0.000 | 38 | pass |
| players | poison | real | 0 | — | — | 0 | not exercised |
| players | hand | real | 183 | 1.000 | 0.000 | 38 | pass |
| players | library | real | 200 | 1.000 | 0.000 | 38 | pass |
| players | graveyard | real | 157 | 1.000 | 0.000 | 38 | pass |
| players | exile | real | 0 | — | — | 0 | not exercised |
| players | pool_W | real | 0 | — | — | 0 | not exercised |
| players | pool_U | real | 0 | — | — | 0 | not exercised |
| players | pool_B | real | 0 | — | — | 0 | not exercised |
| players | pool_R | real | 0 | — | — | 0 | not exercised |
| players | pool_G | real | 0 | — | — | 0 | not exercised |
| players | pool_C | real | 0 | — | — | 0 | not exercised |
| players | untapped_sources | real | 145 | 1.000 | 0.000 | 38 | pass |
| players | lands | real | 189 | 1.000 | 0.000 | 38 | pass |
| players | drawn_this_turn | real | 0 | — | — | 0 | not exercised |
| players | permanents | real | 189 | 1.000 | 0.000 | 38 | pass |
| ent | kw_first_strike | binary | 0 | — | — | 0 | not exercised |
| ent | stack_is_ability | binary | 0 | — | — | 0 | not exercised |
| ent | instant | binary | 452 | 1.000 | 0.599 | 182 | pass |
| ent | zone_exile | binary | 0 | — | — | 0 | not exercised |
| ent | zone_library_known | binary | 0 | — | — | 0 | not exercised |
| ent | kw_protection | binary | 0 | — | — | 0 | not exercised |
| ent | sick | binary | 189 | 1.000 | 0.847 | 229 | pass |
| ent | other_perm | binary | 288 | 1.000 | 0.838 | 229 | pass |
| ent | kw_flash | binary | 448 | 1.000 | 0.803 | 411 | pass |
| ent | can_block | binary | 410 | 1.000 | 0.668 | 229 | pass |
| ent | face_down | binary | 0 | — | — | 0 | not exercised |
| ent | mv | real | 1324 | 1.000 | 0.000 | 411 | pass |
| ent | zone_stack | binary | 0 | — | — | 0 | not exercised |
| ent | ctr_loyalty | real | 34 | 1.000 | 0.000 | 229 | pass |
| ent | ctr_p1p1 | real | 4 | — | — | 0 | not exercised |
| ent | loyalty | real | 34 | 1.000 | 0.000 | 229 | pass |
| ent | printed_power | real | 700 | 1.000 | 0.000 | 411 | pass |
| ent | kw_menace | binary | 0 | — | — | 0 | not exercised |
| ent | kw_shroud | binary | 0 | — | — | 0 | not exercised |
| ent | kw_flying | binary | 270 | 0.998 | 0.905 | 411 | pass |
| ent | kw_deathtouch | binary | 107 | — | — | 0 | not exercised |
| ent | kw_ward | binary | 0 | — | — | 0 | not exercised |
| ent | mana_left_if_cast | real | 187 | 1.000 | 0.000 | 74 | pass |
| ent | tough_left | real | 741 | 1.000 | 0.000 | 411 | pass |
| ent | sorcery | binary | 38 | — | — | 0 | not exercised |
| ent | creature | binary | 716 | 1.000 | 0.725 | 411 | pass |
| ent | tapped | binary | 410 | 1.000 | 0.668 | 229 | pass |
| ent | ctr_other | real | 9 | — | — | 0 | not exercised |
| ent | turns_on_bf | real | 1244 | 1.000 | 0.000 | 229 | pass |
| ent | kw_ninjutsu | binary | 75 | 1.000 | 0.952 | 229 | pass |
| ent | stack_modes | real | 0 | — | — | 0 | not exercised |
| ent | kw_trample | binary | 0 | — | — | 0 | not exercised |
| ent | kw_prowess | binary | 0 | — | — | 0 | not exercised |
| ent | damage | real | 0 | — | — | 0 | not exercised |
| ent | identity | cat | 2132 | 1.000 | 0.161 | 411 | pass |
| ent | kw_reach | binary | 0 | — | — | 0 | not exercised |
| ent | stack_mine | binary | 0 | — | — | 0 | not exercised |
| ent | mine | binary | 976 | 1.000 | 0.537 | 337 | pass |
| ent | kw_haste | binary | 0 | — | — | 0 | not exercised |
| ent | kw_defender | binary | 0 | — | — | 0 | not exercised |
| ent | toughness | real | 741 | 1.000 | 0.000 | 411 | pass |
| ent | power | real | 741 | 1.000 | 0.000 | 411 | pass |
| ent | attacking | binary | 19 | — | — | 0 | not exercised |
| ent | blocking | binary | 0 | — | — | 0 | not exercised |
| ent | can_attack | binary | 542 | 1.000 | 0.568 | 229 | pass |
| ent | zone_command | binary | 0 | — | — | 0 | not exercised |
| ent | stack_X | real | 0 | — | — | 0 | not exercised |
| ent | entered | binary | 60 | 1.000 | 0.948 | 229 | pass |
| ent | land | binary | 605 | 1.000 | 0.696 | 303 | pass |
| ent | legal_targets | real | 46 | 0.999 | 0.000 | 74 | pass |
| ent | zone_hand | binary | 0 | — | — | 0 | not exercised |
| ent | token | binary | 148 | 1.000 | 0.913 | 229 | pass |
| ent | kw_lifelink | binary | 72 | — | — | 0 | not exercised |
| ent | zone_battlefield | binary | 0 | — | — | 0 | not exercised |
| ent | printed_tough | real | 700 | 1.000 | 0.000 | 411 | pass |
| ent | ctr_m1m1 | real | 11 | — | — | 0 | not exercised |
| ent | kw_hexproof | binary | 19 | — | — | 0 | not exercised |
| ent | castable | binary | 180 | 1.000 | 0.770 | 74 | pass |
| ent | lethal_as_is | binary | 0 | — | — | 0 | not exercised |
| ent | zone_graveyard | binary | 0 | — | — | 0 | not exercised |
| ent | stack_pos | real | 0 | — | — | 0 | not exercised |
| ent | kw_double_strike | binary | 0 | — | — | 0 | not exercised |
| ent | kw_vigilance | binary | 190 | 0.997 | 0.917 | 337 | pass |
| opp_hand | origin_opening | binary | 140 | 1.000 | 0.592 | 76 | pass |
| opp_hand | origin_drawn | binary | 135 | 1.000 | 0.592 | 76 | pass |
| opp_hand | origin_returned | binary | 5 | — | — | 0 | not exercised |
| opp_hand | origin_other | binary | 0 | — | — | 0 | not exercised |
| opp_hand | age | real | 306 | 1.000 | 0.000 | 76 | pass |
| opp_hand | known | binary | 5 | — | — | 0 | not exercised |
| opp_hand | seen | binary | 5 | — | — | 0 | not exercised |
| opp_hand | identity | cat | 2 | — | — | 0 | not exercised |
| opp_deck | count | real | 2111 | 1.000 | 0.000 | 403 | pass |
| opp_deck | fraction | real | 2111 | 0.980 | 0.000 | 403 | pass |
| opp_deck | castable_now | binary | 666 | 1.000 | 0.635 | 403 | pass |
| opp_deck | mv | real | 1419 | 1.000 | 0.000 | 403 | pass |
| opp_deck | instant_speed | binary | 951 | 1.000 | 0.536 | 403 | pass |
| opp_deck | identity | cat | 2011 | 1.000 | 0.047 | 403 | pass |
| opp_act | act_cast | binary | 389 | 1.000 | 0.553 | 150 | pass |
| opp_act | act_activate | binary | 15 | — | — | 0 | not exercised |
| opp_act | act_attack | binary | 243 | 1.000 | 0.813 | 150 | pass |
| opp_act | act_block | binary | 6 | — | — | 0 | not exercised |
| opp_act | act_declined_block | binary | 53 | — | — | 0 | not exercised |
| opp_act | act_passed_mana_up | binary | 213 | 1.000 | 0.700 | 150 | pass |
| opp_act | act_other | binary | 0 | — | — | 0 | not exercised |
| opp_act | consult_age | real | 919 | 1.000 | 0.000 | 150 | pass |
| cand | type_PASS | binary | 87 | 1.000 | 0.757 | 74 | pass |
| cand | type_LAND | binary | 47 | — | — | 0 | not exercised |
| cand | type_SPELL | binary | 80 | 1.000 | 0.689 | 74 | pass |
| cand | type_ACTIVATE | binary | 74 | 1.000 | 0.716 | 74 | pass |
| cand | type_TARGET | binary | 32 | — | — | 0 | not exercised |
| cand | type_ATTACK | binary | 8 | — | — | 0 | not exercised |
| cand | type_BLOCK | binary | 5 | — | — | 0 | not exercised |
| cand | type_OTHER | binary | 0 | — | — | 0 | not exercised |
| cand | LSA.mana_left_after | real | 144 | 1.000 | 0.000 | 39 | pass |
| cand | LSA.targets_legal | real | 56 | 1.000 | 0.000 | 39 | pass |
| cand | LSA.instant_speed | binary | 73 | — | — | 0 | not exercised |
| cand | LSA.sorcery_speed | binary | 73 | — | — | 0 | not exercised |
| cand | LSA.flash | binary | 30 | — | — | 0 | not exercised |
| cand | LSA.stack_above_n | real | 0 | — | — | 0 | not exercised |
| cand | LSA.X_chosen | real | 0 | — | — | 0 | not exercised |
| cand | TARGET.is_player | - | 0 | — | — | 0 | too few rows (32) |
| cand | TARGET.is_me | - | 0 | — | — | 0 | too few rows (32) |
| cand | TARGET.life_if_player | - | 0 | — | — | 0 | too few rows (32) |
| cand | TARGET.is_creature | - | 0 | — | — | 0 | too few rows (32) |
| cand | TARGET.power | - | 0 | — | — | 0 | too few rows (32) |
| cand | TARGET.toughness | - | 0 | — | — | 0 | too few rows (32) |
| cand | TARGET.mine | - | 0 | — | — | 0 | too few rows (32) |
| cand | ATTACK.damage_dealt | - | 0 | — | — | 0 | too few rows (8) |
| cand | ATTACK.their_kills | - | 0 | — | — | 0 | too few rows (8) |
| cand | ATTACK.my_losses | - | 0 | — | — | 0 | too few rows (8) |
| cand | ATTACK.lethal | - | 0 | — | — | 0 | too few rows (8) |
| cand | ATTACK.attackers_used | - | 0 | — | — | 0 | too few rows (8) |
| cand | ATTACK.opp_life_after | - | 0 | — | — | 0 | too few rows (8) |
| cand | ATTACK.bodies_retained | - | 0 | — | — | 0 | too few rows (8) |
| cand | ATTACK.power_retained | - | 0 | — | — | 0 | too few rows (8) |
| cand | ATTACK.tough_retained | - | 0 | — | — | 0 | too few rows (8) |
| cand | ATTACK.crack_back | - | 0 | — | — | 0 | too few rows (8) |
| cand | ATTACK.my_life_after | - | 0 | — | — | 0 | too few rows (8) |
| cand | BLOCK.damage_taken | - | 0 | — | — | 0 | too few rows (5) |
| cand | BLOCK.attackers_killed | - | 0 | — | — | 0 | too few rows (5) |
| cand | BLOCK.value_killed | - | 0 | — | — | 0 | too few rows (5) |
| cand | BLOCK.blockers_lost | - | 0 | — | — | 0 | too few rows (5) |
| cand | BLOCK.value_lost | - | 0 | — | — | 0 | too few rows (5) |
| cand | BLOCK.defender_dies | - | 0 | — | — | 0 | too few rows (5) |
| cand | BLOCK.blockers_used | - | 0 | — | — | 0 | too few rows (5) |
| cand | BLOCK.life_after | - | 0 | — | — | 0 | too few rows (5) |

entity rows by zone: `{'battlefield': 1304, 'hand': 387, 'stack': 12, 'graveyard': 800, 'exile': 0, 'library_known': 0, 'command': 0}`; candidate rows by type: `{'PASS': 87, 'LAND': 47, 'SPELL': 80, 'ACTIVATE': 74, 'TARGET': 32, 'ATTACK': 8, 'BLOCK': 5, 'OTHER': 0}`

## after L4

| part | field | kind | exercised | held-out | chance | n | result |
|---|---|---|---|---|---|---|---|
| game | turn | real | 0 | — | — | 0 | too few rows |
| game | i_am_active | binary | 0 | — | — | 0 | too few rows |
| game | step_upkeep | binary | 0 | — | — | 0 | too few rows |
| game | step_draw | binary | 0 | — | — | 0 | too few rows |
| game | step_main1 | binary | 0 | — | — | 0 | too few rows |
| game | step_decl_att | binary | 0 | — | — | 0 | too few rows |
| game | step_decl_blk | binary | 0 | — | — | 0 | too few rows |
| game | step_combat_dmg | binary | 0 | — | — | 0 | too few rows |
| game | step_main2 | binary | 0 | — | — | 0 | too few rows |
| game | step_end | binary | 0 | — | — | 0 | too few rows |
| game | priority | binary | 0 | — | — | 0 | too few rows |
| game | stack_depth | real | 0 | — | — | 0 | too few rows |
| game | dtype_PASS | binary | 0 | — | — | 0 | too few rows |
| game | dtype_LAND | binary | 0 | — | — | 0 | too few rows |
| game | dtype_SPELL | binary | 0 | — | — | 0 | too few rows |
| game | dtype_ACTIVATE | binary | 0 | — | — | 0 | too few rows |
| game | dtype_TARGET | binary | 0 | — | — | 0 | too few rows |
| game | dtype_ATTACK | binary | 0 | — | — | 0 | too few rows |
| game | dtype_BLOCK | binary | 0 | — | — | 0 | too few rows |
| game | dtype_OTHER | binary | 0 | — | — | 0 | too few rows |
| game | n_cand | real | 0 | — | — | 0 | too few rows |
| game | consults_so_far | real | 0 | — | — | 0 | too few rows |
| game | my_deck_open | binary | 0 | — | — | 0 | too few rows |
| game | opp_deck_open | binary | 0 | — | — | 0 | too few rows |
| players | life | real | 196 | 0.997 | 0.000 | 38 | pass |
| players | poison | real | 0 | — | — | 0 | not exercised |
| players | hand | real | 183 | 0.996 | 0.000 | 38 | pass |
| players | library | real | 200 | 0.977 | 0.000 | 38 | pass |
| players | graveyard | real | 157 | 0.977 | 0.000 | 38 | pass |
| players | exile | real | 0 | — | — | 0 | not exercised |
| players | pool_W | real | 0 | — | — | 0 | not exercised |
| players | pool_U | real | 0 | — | — | 0 | not exercised |
| players | pool_B | real | 0 | — | — | 0 | not exercised |
| players | pool_R | real | 0 | — | — | 0 | not exercised |
| players | pool_G | real | 0 | — | — | 0 | not exercised |
| players | pool_C | real | 0 | — | — | 0 | not exercised |
| players | untapped_sources | real | 145 | 0.994 | 0.000 | 38 | pass |
| players | lands | real | 189 | 0.992 | 0.000 | 38 | pass |
| players | drawn_this_turn | real | 0 | — | — | 0 | not exercised |
| players | permanents | real | 189 | 0.987 | 0.000 | 38 | pass |
| ent | kw_first_strike | binary | 0 | — | — | 0 | not exercised |
| ent | stack_is_ability | binary | 0 | — | — | 0 | not exercised |
| ent | instant | binary | 452 | 1.000 | 0.599 | 182 | pass |
| ent | zone_exile | binary | 0 | — | — | 0 | not exercised |
| ent | zone_library_known | binary | 0 | — | — | 0 | not exercised |
| ent | kw_protection | binary | 0 | — | — | 0 | not exercised |
| ent | sick | binary | 189 | 1.000 | 0.847 | 229 | pass |
| ent | other_perm | binary | 288 | 1.000 | 0.838 | 229 | pass |
| ent | kw_flash | binary | 448 | 0.998 | 0.803 | 411 | pass |
| ent | can_block | binary | 410 | 1.000 | 0.668 | 229 | pass |
| ent | face_down | binary | 0 | — | — | 0 | not exercised |
| ent | mv | real | 1324 | 0.999 | 0.000 | 411 | pass |
| ent | zone_stack | binary | 0 | — | — | 0 | not exercised |
| ent | ctr_loyalty | real | 34 | 0.980 | 0.000 | 229 | pass |
| ent | ctr_p1p1 | real | 4 | — | — | 0 | not exercised |
| ent | loyalty | real | 34 | 0.980 | 0.000 | 229 | pass |
| ent | printed_power | real | 700 | 0.999 | 0.000 | 411 | pass |
| ent | kw_menace | binary | 0 | — | — | 0 | not exercised |
| ent | kw_shroud | binary | 0 | — | — | 0 | not exercised |
| ent | kw_flying | binary | 270 | 0.998 | 0.905 | 411 | pass |
| ent | kw_deathtouch | binary | 107 | — | — | 0 | not exercised |
| ent | kw_ward | binary | 0 | — | — | 0 | not exercised |
| ent | mana_left_if_cast | real | 187 | 0.896 | 0.000 | 74 | **FAIL** |
| ent | tough_left | real | 741 | 0.995 | 0.000 | 411 | pass |
| ent | sorcery | binary | 38 | — | — | 0 | not exercised |
| ent | creature | binary | 716 | 1.000 | 0.725 | 411 | pass |
| ent | tapped | binary | 410 | 1.000 | 0.668 | 229 | pass |
| ent | ctr_other | real | 9 | — | — | 0 | not exercised |
| ent | turns_on_bf | real | 1244 | 0.978 | 0.000 | 229 | pass |
| ent | kw_ninjutsu | binary | 75 | 1.000 | 0.952 | 229 | pass |
| ent | stack_modes | real | 0 | — | — | 0 | not exercised |
| ent | kw_trample | binary | 0 | — | — | 0 | not exercised |
| ent | kw_prowess | binary | 0 | — | — | 0 | not exercised |
| ent | damage | real | 0 | — | — | 0 | not exercised |
| ent | identity | cat | 2132 | 1.000 | 0.161 | 411 | pass |
| ent | kw_reach | binary | 0 | — | — | 0 | not exercised |
| ent | stack_mine | binary | 0 | — | — | 0 | not exercised |
| ent | mine | binary | 976 | 1.000 | 0.537 | 337 | pass |
| ent | kw_haste | binary | 0 | — | — | 0 | not exercised |
| ent | kw_defender | binary | 0 | — | — | 0 | not exercised |
| ent | toughness | real | 741 | 0.995 | 0.000 | 411 | pass |
| ent | power | real | 741 | 0.994 | 0.000 | 411 | pass |
| ent | attacking | binary | 19 | — | — | 0 | not exercised |
| ent | blocking | binary | 0 | — | — | 0 | not exercised |
| ent | can_attack | binary | 542 | 1.000 | 0.568 | 229 | pass |
| ent | zone_command | binary | 0 | — | — | 0 | not exercised |
| ent | stack_X | real | 0 | — | — | 0 | not exercised |
| ent | entered | binary | 60 | 1.000 | 0.948 | 229 | pass |
| ent | land | binary | 605 | 1.000 | 0.696 | 303 | pass |
| ent | legal_targets | real | 46 | 0.953 | 0.000 | 74 | pass |
| ent | zone_hand | binary | 0 | — | — | 0 | not exercised |
| ent | token | binary | 148 | 1.000 | 0.913 | 229 | pass |
| ent | kw_lifelink | binary | 72 | — | — | 0 | not exercised |
| ent | zone_battlefield | binary | 0 | — | — | 0 | not exercised |
| ent | printed_tough | real | 700 | 0.998 | 0.000 | 411 | pass |
| ent | ctr_m1m1 | real | 11 | — | — | 0 | not exercised |
| ent | kw_hexproof | binary | 19 | — | — | 0 | not exercised |
| ent | castable | binary | 180 | 1.000 | 0.770 | 74 | pass |
| ent | lethal_as_is | binary | 0 | — | — | 0 | not exercised |
| ent | zone_graveyard | binary | 0 | — | — | 0 | not exercised |
| ent | stack_pos | real | 0 | — | — | 0 | not exercised |
| ent | kw_double_strike | binary | 0 | — | — | 0 | not exercised |
| ent | kw_vigilance | binary | 190 | 0.997 | 0.917 | 337 | pass |
| opp_hand | origin_opening | binary | 140 | 1.000 | 0.592 | 76 | pass |
| opp_hand | origin_drawn | binary | 135 | 1.000 | 0.592 | 76 | pass |
| opp_hand | origin_returned | binary | 5 | — | — | 0 | not exercised |
| opp_hand | origin_other | binary | 0 | — | — | 0 | not exercised |
| opp_hand | age | real | 306 | 0.989 | 0.000 | 76 | pass |
| opp_hand | known | binary | 5 | — | — | 0 | not exercised |
| opp_hand | seen | binary | 5 | — | — | 0 | not exercised |
| opp_hand | identity | cat | 2 | — | — | 0 | not exercised |
| opp_deck | count | real | 2111 | 0.982 | 0.000 | 403 | pass |
| opp_deck | fraction | real | 2111 | 0.971 | 0.000 | 403 | pass |
| opp_deck | castable_now | binary | 666 | 1.000 | 0.635 | 403 | pass |
| opp_deck | mv | real | 1419 | 1.000 | 0.000 | 403 | pass |
| opp_deck | instant_speed | binary | 951 | 1.000 | 0.536 | 403 | pass |
| opp_deck | identity | cat | 2011 | 1.000 | 0.047 | 403 | pass |
| opp_act | act_cast | binary | 389 | 1.000 | 0.553 | 150 | pass |
| opp_act | act_activate | binary | 15 | — | — | 0 | not exercised |
| opp_act | act_attack | binary | 243 | 1.000 | 0.813 | 150 | pass |
| opp_act | act_block | binary | 6 | — | — | 0 | not exercised |
| opp_act | act_declined_block | binary | 53 | — | — | 0 | not exercised |
| opp_act | act_passed_mana_up | binary | 213 | 1.000 | 0.700 | 150 | pass |
| opp_act | act_other | binary | 0 | — | — | 0 | not exercised |
| opp_act | consult_age | real | 919 | 0.999 | 0.000 | 150 | pass |
| cand | type_PASS | binary | 87 | 1.000 | 0.757 | 74 | pass |
| cand | type_LAND | binary | 47 | — | — | 0 | not exercised |
| cand | type_SPELL | binary | 80 | 1.000 | 0.689 | 74 | pass |
| cand | type_ACTIVATE | binary | 74 | 1.000 | 0.716 | 74 | pass |
| cand | type_TARGET | binary | 32 | — | — | 0 | not exercised |
| cand | type_ATTACK | binary | 8 | — | — | 0 | not exercised |
| cand | type_BLOCK | binary | 5 | — | — | 0 | not exercised |
| cand | type_OTHER | binary | 0 | — | — | 0 | not exercised |
| cand | LSA.mana_left_after | real | 144 | 0.978 | 0.000 | 39 | pass |
| cand | LSA.targets_legal | real | 56 | 0.990 | 0.000 | 39 | pass |
| cand | LSA.instant_speed | binary | 73 | — | — | 0 | not exercised |
| cand | LSA.sorcery_speed | binary | 73 | — | — | 0 | not exercised |
| cand | LSA.flash | binary | 30 | — | — | 0 | not exercised |
| cand | LSA.stack_above_n | real | 0 | — | — | 0 | not exercised |
| cand | LSA.X_chosen | real | 0 | — | — | 0 | not exercised |
| cand | TARGET.is_player | - | 0 | — | — | 0 | too few rows (32) |
| cand | TARGET.is_me | - | 0 | — | — | 0 | too few rows (32) |
| cand | TARGET.life_if_player | - | 0 | — | — | 0 | too few rows (32) |
| cand | TARGET.is_creature | - | 0 | — | — | 0 | too few rows (32) |
| cand | TARGET.power | - | 0 | — | — | 0 | too few rows (32) |
| cand | TARGET.toughness | - | 0 | — | — | 0 | too few rows (32) |
| cand | TARGET.mine | - | 0 | — | — | 0 | too few rows (32) |
| cand | ATTACK.damage_dealt | - | 0 | — | — | 0 | too few rows (8) |
| cand | ATTACK.their_kills | - | 0 | — | — | 0 | too few rows (8) |
| cand | ATTACK.my_losses | - | 0 | — | — | 0 | too few rows (8) |
| cand | ATTACK.lethal | - | 0 | — | — | 0 | too few rows (8) |
| cand | ATTACK.attackers_used | - | 0 | — | — | 0 | too few rows (8) |
| cand | ATTACK.opp_life_after | - | 0 | — | — | 0 | too few rows (8) |
| cand | ATTACK.bodies_retained | - | 0 | — | — | 0 | too few rows (8) |
| cand | ATTACK.power_retained | - | 0 | — | — | 0 | too few rows (8) |
| cand | ATTACK.tough_retained | - | 0 | — | — | 0 | too few rows (8) |
| cand | ATTACK.crack_back | - | 0 | — | — | 0 | too few rows (8) |
| cand | ATTACK.my_life_after | - | 0 | — | — | 0 | too few rows (8) |
| cand | BLOCK.damage_taken | - | 0 | — | — | 0 | too few rows (5) |
| cand | BLOCK.attackers_killed | - | 0 | — | — | 0 | too few rows (5) |
| cand | BLOCK.value_killed | - | 0 | — | — | 0 | too few rows (5) |
| cand | BLOCK.blockers_lost | - | 0 | — | — | 0 | too few rows (5) |
| cand | BLOCK.value_lost | - | 0 | — | — | 0 | too few rows (5) |
| cand | BLOCK.defender_dies | - | 0 | — | — | 0 | too few rows (5) |
| cand | BLOCK.blockers_used | - | 0 | — | — | 0 | too few rows (5) |
| cand | BLOCK.life_after | - | 0 | — | — | 0 | too few rows (5) |

entity rows by zone: `{'battlefield': 1304, 'hand': 387, 'stack': 12, 'graveyard': 800, 'exile': 0, 'library_known': 0, 'command': 0}`; candidate rows by type: `{'PASS': 87, 'LAND': 47, 'SPELL': 80, 'ACTIVATE': 74, 'TARGET': 32, 'ATTACK': 8, 'BLOCK': 5, 'OTHER': 0}`

## edges after L4 (balanced pairs)

| edge | positives | held-out | chance | result |
|---|---|---|---|---|
| blocks | 0 | — | — | not exercised |
| blocked_by | 0 | — | — | not exercised |
| attacking_player | 19 | — | — | too few rows |
| targets | 8 | — | — | too few rows |
| controls | 1304 | 0.998 | 0.500 | pass |
| attached_to | 0 | — | — | not exercised |
| can_block | 6 | — | — | too few rows |
| stack_above | 3 | — | — | too few rows |
| refers_to | 235 | 0.973 | 0.500 | pass |
| referred_by | 235 | 0.929 | 0.500 | pass |

## consult-level

- after L3: remaining-deck count per name mean R² = -0.8745310183855943 (min -4.338851271978868, 20/22 names exercised; worst [(-4.338851271978868, 'We Say Thee Nay!'), (-2.476592420365134, 'Restless Reef'), (-2.4554707612471516, 'Requiting Hex'), (-2.1037404568181226, 'Hidden Lair'), (-1.4069601384370851, 'Island')]); instant-speed threat count R² = 0.8024440194108735 (exercised 69); known-card set: not exercised
- after L4: remaining-deck count per name mean R² = -0.7075879085791985 (min -3.3717427588621547, 20/22 names exercised; worst [(-3.3717427588621547, 'We Say Thee Nay!'), (-2.781561309683398, 'Requiting Hex'), (-1.5958403216679842, 'Hidden Lair'), (-1.5040103970560628, 'Restless Reef'), (-1.1043716752188435, 'Bitter Triumph')]); instant-speed threat count R² = 0.7855581594938511 (exercised 69); known-card set: not exercised
