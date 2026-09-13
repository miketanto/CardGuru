# 5b faithfulness on real dumps — 60 consults, 4 games, 1 recordings

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
| players | life | real | 0 | — | — | 0 | too few rows |
| players | poison | real | 0 | — | — | 0 | too few rows |
| players | hand | real | 0 | — | — | 0 | too few rows |
| players | library | real | 0 | — | — | 0 | too few rows |
| players | graveyard | real | 0 | — | — | 0 | too few rows |
| players | exile | real | 0 | — | — | 0 | too few rows |
| players | pool_W | real | 0 | — | — | 0 | too few rows |
| players | pool_U | real | 0 | — | — | 0 | too few rows |
| players | pool_B | real | 0 | — | — | 0 | too few rows |
| players | pool_R | real | 0 | — | — | 0 | too few rows |
| players | pool_G | real | 0 | — | — | 0 | too few rows |
| players | pool_C | real | 0 | — | — | 0 | too few rows |
| players | untapped_sources | real | 0 | — | — | 0 | too few rows |
| players | lands | real | 0 | — | — | 0 | too few rows |
| players | drawn_this_turn | real | 0 | — | — | 0 | too few rows |
| players | permanents | real | 0 | — | — | 0 | too few rows |
| ent | printed_power | real | 681 | 1.000 | 0.000 | 383 | pass |
| ent | entered | binary | 26 | — | — | 0 | not exercised |
| ent | zone_exile | binary | 0 | — | — | 0 | not exercised |
| ent | mv | real | 681 | 0.999 | 0.000 | 383 | pass |
| ent | damage | real | 0 | — | — | 0 | not exercised |
| ent | ctr_other | real | 0 | — | — | 0 | not exercised |
| ent | kw_deathtouch | binary | 0 | — | — | 0 | not exercised |
| ent | ctr_m1m1 | real | 0 | — | — | 0 | not exercised |
| ent | kw_shroud | binary | 0 | — | — | 0 | not exercised |
| ent | can_block | binary | 232 | 1.000 | 0.667 | 192 | pass |
| ent | toughness | real | 681 | 0.996 | 0.000 | 383 | pass |
| ent | sorcery | binary | 0 | — | — | 0 | not exercised |
| ent | kw_haste | binary | 0 | — | — | 0 | not exercised |
| ent | land | binary | 257 | 1.000 | 0.764 | 250 | pass |
| ent | kw_ward | binary | 0 | — | — | 0 | not exercised |
| ent | zone_hand | binary | 0 | — | — | 0 | not exercised |
| ent | blocking | binary | 0 | — | — | 0 | not exercised |
| ent | creature | binary | 257 | 1.000 | 0.764 | 250 | pass |
| ent | kw_double_strike | binary | 0 | — | — | 0 | not exercised |
| ent | ctr_p1p1 | real | 0 | — | — | 0 | not exercised |
| ent | castable | binary | 13 | — | — | 0 | not exercised |
| ent | kw_menace | binary | 0 | — | — | 0 | not exercised |
| ent | kw_reach | binary | 0 | — | — | 0 | not exercised |
| ent | zone_library_known | binary | 0 | — | — | 0 | not exercised |
| ent | zone_command | binary | 0 | — | — | 0 | not exercised |
| ent | kw_flying | binary | 0 | — | — | 0 | not exercised |
| ent | mana_left_if_cast | real | 86 | 0.999 | 0.000 | 58 | pass |
| ent | identity | cat | 626 | 0.997 | 0.533 | 383 | **FAIL** |
| ent | turns_on_bf | real | 581 | 1.000 | 0.000 | 192 | pass |
| ent | other_perm | binary | 0 | — | — | 0 | not exercised |
| ent | face_down | binary | 0 | — | — | 0 | not exercised |
| ent | kw_prowess | binary | 0 | — | — | 0 | not exercised |
| ent | stack_mine | binary | 0 | — | — | 0 | not exercised |
| ent | zone_graveyard | binary | 0 | — | — | 0 | not exercised |
| ent | printed_tough | real | 681 | 0.996 | 0.000 | 383 | pass |
| ent | stack_pos | real | 0 | — | — | 0 | not exercised |
| ent | kw_defender | binary | 0 | — | — | 0 | not exercised |
| ent | instant | binary | 0 | — | — | 0 | not exercised |
| ent | kw_flash | binary | 0 | — | — | 0 | not exercised |
| ent | attacking | binary | 0 | — | — | 0 | not exercised |
| ent | kw_first_strike | binary | 0 | — | — | 0 | not exercised |
| ent | zone_stack | binary | 0 | — | — | 0 | not exercised |
| ent | zone_battlefield | binary | 0 | — | — | 0 | not exercised |
| ent | loyalty | real | 0 | — | — | 0 | not exercised |
| ent | kw_lifelink | binary | 0 | — | — | 0 | not exercised |
| ent | mine | binary | 443 | 1.000 | 0.526 | 325 | pass |
| ent | kw_hexproof | binary | 0 | — | — | 0 | not exercised |
| ent | stack_X | real | 0 | — | — | 0 | not exercised |
| ent | kw_protection | binary | 0 | — | — | 0 | not exercised |
| ent | kw_trample | binary | 0 | — | — | 0 | not exercised |
| ent | sick | binary | 126 | 1.000 | 0.812 | 192 | pass |
| ent | legal_targets | real | 0 | — | — | 0 | not exercised |
| ent | stack_is_ability | binary | 0 | — | — | 0 | not exercised |
| ent | lethal_as_is | binary | 0 | — | — | 0 | not exercised |
| ent | ctr_loyalty | real | 0 | — | — | 0 | not exercised |
| ent | can_attack | binary | 280 | 1.000 | 0.526 | 192 | pass |
| ent | tough_left | real | 681 | 0.996 | 0.000 | 383 | pass |
| ent | kw_ninjutsu | binary | 0 | — | — | 0 | not exercised |
| ent | stack_modes | real | 0 | — | — | 0 | not exercised |
| ent | tapped | binary | 232 | 1.000 | 0.667 | 192 | pass |
| ent | token | binary | 0 | — | — | 0 | not exercised |
| ent | kw_vigilance | binary | 0 | — | — | 0 | not exercised |
| ent | power | real | 681 | 1.000 | 0.000 | 383 | pass |
| opp_hand | origin_opening | binary | 0 | — | — | 0 | too few rows |
| opp_hand | origin_drawn | binary | 0 | — | — | 0 | too few rows |
| opp_hand | origin_returned | binary | 0 | — | — | 0 | too few rows |
| opp_hand | origin_other | binary | 0 | — | — | 0 | too few rows |
| opp_hand | age | real | 0 | — | — | 0 | too few rows |
| opp_hand | known | binary | 0 | — | — | 0 | too few rows |
| opp_hand | seen | binary | 0 | — | — | 0 | too few rows |
| opp_hand | identity | cat | 0 | — | — | 0 | too few rows |
| opp_deck | count | real | 600 | 1.000 | 0.000 | 190 | pass |
| opp_deck | fraction | real | 600 | 0.995 | 0.000 | 190 | pass |
| opp_deck | castable_now | binary | 86 | 1.000 | 0.874 | 190 | pass |
| opp_deck | mv | real | 540 | 1.000 | 0.000 | 190 | pass |
| opp_deck | instant_speed | binary | 0 | — | — | 0 | not exercised |
| opp_deck | identity | cat | 540 | 1.000 | 0.100 | 190 | pass |
| opp_act | act_cast | binary | 216 | 1.000 | 0.591 | 164 | pass |
| opp_act | act_activate | binary | 0 | — | — | 0 | not exercised |
| opp_act | act_attack | binary | 224 | 1.000 | 0.573 | 164 | pass |
| opp_act | act_block | binary | 0 | — | — | 0 | not exercised |
| opp_act | act_declined_block | binary | 41 | 1.000 | 0.909 | 164 | pass |
| opp_act | act_passed_mana_up | binary | 28 | 1.000 | 0.927 | 164 | pass |
| opp_act | act_other | binary | 0 | — | — | 0 | not exercised |
| opp_act | consult_age | real | 509 | 1.000 | 0.000 | 164 | pass |
| cand | type_PASS | binary | 0 | — | — | 0 | too few rows |
| cand | type_LAND | binary | 0 | — | — | 0 | too few rows |
| cand | type_SPELL | binary | 0 | — | — | 0 | too few rows |
| cand | type_ACTIVATE | binary | 0 | — | — | 0 | too few rows |
| cand | type_TARGET | binary | 0 | — | — | 0 | too few rows |
| cand | type_ATTACK | binary | 0 | — | — | 0 | too few rows |
| cand | type_BLOCK | binary | 0 | — | — | 0 | too few rows |
| cand | type_OTHER | binary | 0 | — | — | 0 | too few rows |
| cand | LSA.mana_left_after | - | 0 | — | — | 0 | too few rows (122) |
| cand | LSA.targets_legal | - | 0 | — | — | 0 | too few rows (122) |
| cand | LSA.instant_speed | - | 0 | — | — | 0 | too few rows (122) |
| cand | LSA.sorcery_speed | - | 0 | — | — | 0 | too few rows (122) |
| cand | LSA.flash | - | 0 | — | — | 0 | too few rows (122) |
| cand | LSA.stack_above_n | - | 0 | — | — | 0 | too few rows (122) |
| cand | LSA.X_chosen | - | 0 | — | — | 0 | too few rows (122) |
| cand | TARGET.is_player | - | 0 | — | — | 0 | too few rows (0) |
| cand | TARGET.is_me | - | 0 | — | — | 0 | too few rows (0) |
| cand | TARGET.life_if_player | - | 0 | — | — | 0 | too few rows (0) |
| cand | TARGET.is_creature | - | 0 | — | — | 0 | too few rows (0) |
| cand | TARGET.power | - | 0 | — | — | 0 | too few rows (0) |
| cand | TARGET.toughness | - | 0 | — | — | 0 | too few rows (0) |
| cand | TARGET.mine | - | 0 | — | — | 0 | too few rows (0) |
| cand | ATTACK.damage_dealt | - | 0 | — | — | 0 | too few rows (0) |
| cand | ATTACK.their_kills | - | 0 | — | — | 0 | too few rows (0) |
| cand | ATTACK.my_losses | - | 0 | — | — | 0 | too few rows (0) |
| cand | ATTACK.lethal | - | 0 | — | — | 0 | too few rows (0) |
| cand | ATTACK.attackers_used | - | 0 | — | — | 0 | too few rows (0) |
| cand | ATTACK.opp_life_after | - | 0 | — | — | 0 | too few rows (0) |
| cand | ATTACK.bodies_retained | - | 0 | — | — | 0 | too few rows (0) |
| cand | ATTACK.power_retained | - | 0 | — | — | 0 | too few rows (0) |
| cand | ATTACK.tough_retained | - | 0 | — | — | 0 | too few rows (0) |
| cand | ATTACK.crack_back | - | 0 | — | — | 0 | too few rows (0) |
| cand | ATTACK.my_life_after | - | 0 | — | — | 0 | too few rows (0) |
| cand | BLOCK.damage_taken | - | 0 | — | — | 0 | too few rows (0) |
| cand | BLOCK.attackers_killed | - | 0 | — | — | 0 | too few rows (0) |
| cand | BLOCK.value_killed | - | 0 | — | — | 0 | too few rows (0) |
| cand | BLOCK.blockers_lost | - | 0 | — | — | 0 | too few rows (0) |
| cand | BLOCK.value_lost | - | 0 | — | — | 0 | too few rows (0) |
| cand | BLOCK.defender_dies | - | 0 | — | — | 0 | too few rows (0) |
| cand | BLOCK.blockers_used | - | 0 | — | — | 0 | too few rows (0) |
| cand | BLOCK.life_after | - | 0 | — | — | 0 | too few rows (0) |

entity rows by zone: `{'battlefield': 607, 'hand': 238, 'stack': 0, 'graveyard': 306, 'exile': 0, 'library_known': 0, 'command': 0}`; candidate rows by type: `{'PASS': 60, 'LAND': 47, 'SPELL': 75, 'ACTIVATE': 0, 'TARGET': 0, 'ATTACK': 0, 'BLOCK': 0, 'OTHER': 0}`

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
| players | life | real | 0 | — | — | 0 | too few rows |
| players | poison | real | 0 | — | — | 0 | too few rows |
| players | hand | real | 0 | — | — | 0 | too few rows |
| players | library | real | 0 | — | — | 0 | too few rows |
| players | graveyard | real | 0 | — | — | 0 | too few rows |
| players | exile | real | 0 | — | — | 0 | too few rows |
| players | pool_W | real | 0 | — | — | 0 | too few rows |
| players | pool_U | real | 0 | — | — | 0 | too few rows |
| players | pool_B | real | 0 | — | — | 0 | too few rows |
| players | pool_R | real | 0 | — | — | 0 | too few rows |
| players | pool_G | real | 0 | — | — | 0 | too few rows |
| players | pool_C | real | 0 | — | — | 0 | too few rows |
| players | untapped_sources | real | 0 | — | — | 0 | too few rows |
| players | lands | real | 0 | — | — | 0 | too few rows |
| players | drawn_this_turn | real | 0 | — | — | 0 | too few rows |
| players | permanents | real | 0 | — | — | 0 | too few rows |
| ent | printed_power | real | 681 | 0.999 | 0.000 | 383 | pass |
| ent | entered | binary | 26 | — | — | 0 | not exercised |
| ent | zone_exile | binary | 0 | — | — | 0 | not exercised |
| ent | mv | real | 681 | 0.997 | 0.000 | 383 | pass |
| ent | damage | real | 0 | — | — | 0 | not exercised |
| ent | ctr_other | real | 0 | — | — | 0 | not exercised |
| ent | kw_deathtouch | binary | 0 | — | — | 0 | not exercised |
| ent | ctr_m1m1 | real | 0 | — | — | 0 | not exercised |
| ent | kw_shroud | binary | 0 | — | — | 0 | not exercised |
| ent | can_block | binary | 232 | 1.000 | 0.667 | 192 | pass |
| ent | toughness | real | 681 | 0.994 | 0.000 | 383 | pass |
| ent | sorcery | binary | 0 | — | — | 0 | not exercised |
| ent | kw_haste | binary | 0 | — | — | 0 | not exercised |
| ent | land | binary | 257 | 1.000 | 0.764 | 250 | pass |
| ent | kw_ward | binary | 0 | — | — | 0 | not exercised |
| ent | zone_hand | binary | 0 | — | — | 0 | not exercised |
| ent | blocking | binary | 0 | — | — | 0 | not exercised |
| ent | creature | binary | 257 | 1.000 | 0.764 | 250 | pass |
| ent | kw_double_strike | binary | 0 | — | — | 0 | not exercised |
| ent | ctr_p1p1 | real | 0 | — | — | 0 | not exercised |
| ent | castable | binary | 13 | — | — | 0 | not exercised |
| ent | kw_menace | binary | 0 | — | — | 0 | not exercised |
| ent | kw_reach | binary | 0 | — | — | 0 | not exercised |
| ent | zone_library_known | binary | 0 | — | — | 0 | not exercised |
| ent | zone_command | binary | 0 | — | — | 0 | not exercised |
| ent | kw_flying | binary | 0 | — | — | 0 | not exercised |
| ent | mana_left_if_cast | real | 86 | 0.981 | 0.000 | 58 | pass |
| ent | identity | cat | 626 | 0.997 | 0.533 | 383 | pass |
| ent | turns_on_bf | real | 581 | 0.969 | 0.000 | 192 | pass |
| ent | other_perm | binary | 0 | — | — | 0 | not exercised |
| ent | face_down | binary | 0 | — | — | 0 | not exercised |
| ent | kw_prowess | binary | 0 | — | — | 0 | not exercised |
| ent | stack_mine | binary | 0 | — | — | 0 | not exercised |
| ent | zone_graveyard | binary | 0 | — | — | 0 | not exercised |
| ent | printed_tough | real | 681 | 0.994 | 0.000 | 383 | pass |
| ent | stack_pos | real | 0 | — | — | 0 | not exercised |
| ent | kw_defender | binary | 0 | — | — | 0 | not exercised |
| ent | instant | binary | 0 | — | — | 0 | not exercised |
| ent | kw_flash | binary | 0 | — | — | 0 | not exercised |
| ent | attacking | binary | 0 | — | — | 0 | not exercised |
| ent | kw_first_strike | binary | 0 | — | — | 0 | not exercised |
| ent | zone_stack | binary | 0 | — | — | 0 | not exercised |
| ent | zone_battlefield | binary | 0 | — | — | 0 | not exercised |
| ent | loyalty | real | 0 | — | — | 0 | not exercised |
| ent | kw_lifelink | binary | 0 | — | — | 0 | not exercised |
| ent | mine | binary | 443 | 1.000 | 0.526 | 325 | pass |
| ent | kw_hexproof | binary | 0 | — | — | 0 | not exercised |
| ent | stack_X | real | 0 | — | — | 0 | not exercised |
| ent | kw_protection | binary | 0 | — | — | 0 | not exercised |
| ent | kw_trample | binary | 0 | — | — | 0 | not exercised |
| ent | sick | binary | 126 | 1.000 | 0.812 | 192 | pass |
| ent | legal_targets | real | 0 | — | — | 0 | not exercised |
| ent | stack_is_ability | binary | 0 | — | — | 0 | not exercised |
| ent | lethal_as_is | binary | 0 | — | — | 0 | not exercised |
| ent | ctr_loyalty | real | 0 | — | — | 0 | not exercised |
| ent | can_attack | binary | 280 | 1.000 | 0.526 | 192 | pass |
| ent | tough_left | real | 681 | 0.994 | 0.000 | 383 | pass |
| ent | kw_ninjutsu | binary | 0 | — | — | 0 | not exercised |
| ent | stack_modes | real | 0 | — | — | 0 | not exercised |
| ent | tapped | binary | 232 | 1.000 | 0.667 | 192 | pass |
| ent | token | binary | 0 | — | — | 0 | not exercised |
| ent | kw_vigilance | binary | 0 | — | — | 0 | not exercised |
| ent | power | real | 681 | 0.999 | 0.000 | 383 | pass |
| opp_hand | origin_opening | binary | 0 | — | — | 0 | too few rows |
| opp_hand | origin_drawn | binary | 0 | — | — | 0 | too few rows |
| opp_hand | origin_returned | binary | 0 | — | — | 0 | too few rows |
| opp_hand | origin_other | binary | 0 | — | — | 0 | too few rows |
| opp_hand | age | real | 0 | — | — | 0 | too few rows |
| opp_hand | known | binary | 0 | — | — | 0 | too few rows |
| opp_hand | seen | binary | 0 | — | — | 0 | too few rows |
| opp_hand | identity | cat | 0 | — | — | 0 | too few rows |
| opp_deck | count | real | 600 | 0.953 | 0.000 | 190 | pass |
| opp_deck | fraction | real | 600 | 0.996 | 0.000 | 190 | pass |
| opp_deck | castable_now | binary | 86 | 1.000 | 0.874 | 190 | pass |
| opp_deck | mv | real | 540 | 0.999 | 0.000 | 190 | pass |
| opp_deck | instant_speed | binary | 0 | — | — | 0 | not exercised |
| opp_deck | identity | cat | 540 | 1.000 | 0.100 | 190 | pass |
| opp_act | act_cast | binary | 216 | 1.000 | 0.591 | 164 | pass |
| opp_act | act_activate | binary | 0 | — | — | 0 | not exercised |
| opp_act | act_attack | binary | 224 | 1.000 | 0.573 | 164 | pass |
| opp_act | act_block | binary | 0 | — | — | 0 | not exercised |
| opp_act | act_declined_block | binary | 41 | 1.000 | 0.909 | 164 | pass |
| opp_act | act_passed_mana_up | binary | 28 | 1.000 | 0.927 | 164 | pass |
| opp_act | act_other | binary | 0 | — | — | 0 | not exercised |
| opp_act | consult_age | real | 509 | 0.989 | 0.000 | 164 | pass |
| cand | type_PASS | binary | 0 | — | — | 0 | too few rows |
| cand | type_LAND | binary | 0 | — | — | 0 | too few rows |
| cand | type_SPELL | binary | 0 | — | — | 0 | too few rows |
| cand | type_ACTIVATE | binary | 0 | — | — | 0 | too few rows |
| cand | type_TARGET | binary | 0 | — | — | 0 | too few rows |
| cand | type_ATTACK | binary | 0 | — | — | 0 | too few rows |
| cand | type_BLOCK | binary | 0 | — | — | 0 | too few rows |
| cand | type_OTHER | binary | 0 | — | — | 0 | too few rows |
| cand | LSA.mana_left_after | - | 0 | — | — | 0 | too few rows (122) |
| cand | LSA.targets_legal | - | 0 | — | — | 0 | too few rows (122) |
| cand | LSA.instant_speed | - | 0 | — | — | 0 | too few rows (122) |
| cand | LSA.sorcery_speed | - | 0 | — | — | 0 | too few rows (122) |
| cand | LSA.flash | - | 0 | — | — | 0 | too few rows (122) |
| cand | LSA.stack_above_n | - | 0 | — | — | 0 | too few rows (122) |
| cand | LSA.X_chosen | - | 0 | — | — | 0 | too few rows (122) |
| cand | TARGET.is_player | - | 0 | — | — | 0 | too few rows (0) |
| cand | TARGET.is_me | - | 0 | — | — | 0 | too few rows (0) |
| cand | TARGET.life_if_player | - | 0 | — | — | 0 | too few rows (0) |
| cand | TARGET.is_creature | - | 0 | — | — | 0 | too few rows (0) |
| cand | TARGET.power | - | 0 | — | — | 0 | too few rows (0) |
| cand | TARGET.toughness | - | 0 | — | — | 0 | too few rows (0) |
| cand | TARGET.mine | - | 0 | — | — | 0 | too few rows (0) |
| cand | ATTACK.damage_dealt | - | 0 | — | — | 0 | too few rows (0) |
| cand | ATTACK.their_kills | - | 0 | — | — | 0 | too few rows (0) |
| cand | ATTACK.my_losses | - | 0 | — | — | 0 | too few rows (0) |
| cand | ATTACK.lethal | - | 0 | — | — | 0 | too few rows (0) |
| cand | ATTACK.attackers_used | - | 0 | — | — | 0 | too few rows (0) |
| cand | ATTACK.opp_life_after | - | 0 | — | — | 0 | too few rows (0) |
| cand | ATTACK.bodies_retained | - | 0 | — | — | 0 | too few rows (0) |
| cand | ATTACK.power_retained | - | 0 | — | — | 0 | too few rows (0) |
| cand | ATTACK.tough_retained | - | 0 | — | — | 0 | too few rows (0) |
| cand | ATTACK.crack_back | - | 0 | — | — | 0 | too few rows (0) |
| cand | ATTACK.my_life_after | - | 0 | — | — | 0 | too few rows (0) |
| cand | BLOCK.damage_taken | - | 0 | — | — | 0 | too few rows (0) |
| cand | BLOCK.attackers_killed | - | 0 | — | — | 0 | too few rows (0) |
| cand | BLOCK.value_killed | - | 0 | — | — | 0 | too few rows (0) |
| cand | BLOCK.blockers_lost | - | 0 | — | — | 0 | too few rows (0) |
| cand | BLOCK.value_lost | - | 0 | — | — | 0 | too few rows (0) |
| cand | BLOCK.defender_dies | - | 0 | — | — | 0 | too few rows (0) |
| cand | BLOCK.blockers_used | - | 0 | — | — | 0 | too few rows (0) |
| cand | BLOCK.life_after | - | 0 | — | — | 0 | too few rows (0) |

entity rows by zone: `{'battlefield': 607, 'hand': 238, 'stack': 0, 'graveyard': 306, 'exile': 0, 'library_known': 0, 'command': 0}`; candidate rows by type: `{'PASS': 60, 'LAND': 47, 'SPELL': 75, 'ACTIVATE': 0, 'TARGET': 0, 'ATTACK': 0, 'BLOCK': 0, 'OTHER': 0}`

## edges after L4 (balanced pairs)

| edge | positives | held-out | chance | result |
|---|---|---|---|---|
| blocks | 0 | — | — | not exercised |
| blocked_by | 0 | — | — | not exercised |
| attacking_player | 0 | — | — | not exercised |
| targets | 0 | — | — | not exercised |
| controls | 607 | 0.987 | 0.500 | pass |
| attached_to | 0 | — | — | not exercised |
| can_block | 0 | — | — | not exercised |
| stack_above | 0 | — | — | not exercised |
| refers_to | 194 | 0.990 | 0.500 | pass |
| referred_by | 194 | 0.971 | 0.500 | pass |

## consult-level

- after L3: remaining-deck count per name mean R² = -1.1445146111972917 (min -5.976520094071097, 10/10 names exercised; worst [(-5.976520094071097, 'Glory Seeker'), (-4.508419735687283, 'Silvercoat Lion'), (-1.4800250731663418, 'Shu Elite Infantry'), (-1.3127898602019052, 'Elite Vanguard'), (0.01669769746023908, 'Regal Unicorn')]); instant-speed threat count R² = None (exercised 0); known-card set: not exercised
- after L4: remaining-deck count per name mean R² = -1.281077879196957 (min -4.7116572060104565, 10/10 names exercised; worst [(-4.7116572060104565, 'Shu Elite Infantry'), (-3.1279098598401287, 'Silvercoat Lion'), (-2.848776695418629, 'Blade of the Sixth Pride'), (-1.893758946165054, 'Glory Seeker'), (-0.611809269971199, 'Foot Soldiers')]); instant-speed threat count R² = None (exercised 0); known-card set: not exercised
