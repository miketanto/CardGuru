# 5b faithfulness on real dumps — 2972 consults, 25 games, 1 recordings

Thresholds: `{"L3": {"binary": 0.99, "cat": 0.99, "real": 0.95}, "L4": {"binary": 0.95, "cat": 0.95, "real": 0.9}, "edge": 0.9, "consult": {"real": 0.9, "binary": 0.95}}`

## after L3

| part | field | kind | exercised | held-out | chance | n | result |
|---|---|---|---|---|---|---|---|
| game | turn | real | 2972 | 1.000 | 0.000 | 411 | pass |
| game | i_am_active | binary | 1405 | 1.000 | 0.557 | 411 | pass |
| game | step_upkeep | binary | 258 | 1.000 | 0.917 | 411 | pass |
| game | step_draw | binary | 248 | 1.000 | 0.915 | 411 | pass |
| game | step_main1 | binary | 695 | 1.000 | 0.745 | 411 | pass |
| game | step_decl_att | binary | 303 | 1.000 | 0.905 | 411 | pass |
| game | step_decl_blk | binary | 243 | 1.000 | 0.905 | 411 | pass |
| game | step_combat_dmg | binary | 641 | 1.000 | 0.810 | 411 | pass |
| game | step_main2 | binary | 366 | 1.000 | 0.873 | 411 | pass |
| game | step_end | binary | 218 | 1.000 | 0.929 | 411 | pass |
| game | priority | binary | 82 | — | — | 0 | not exercised |
| game | stack_depth | real | 446 | 1.000 | 0.000 | 411 | pass |
| game | dtype_PASS | binary | 96 | 1.000 | 0.949 | 411 | pass |
| game | dtype_LAND | binary | 98 | 1.000 | 0.934 | 411 | pass |
| game | dtype_SPELL | binary | 400 | 1.000 | 0.820 | 411 | pass |
| game | dtype_ACTIVATE | binary | 74 | — | — | 0 | not exercised |
| game | dtype_TARGET | binary | 51 | — | — | 0 | not exercised |
| game | dtype_ATTACK | binary | 57 | — | — | 0 | not exercised |
| game | dtype_BLOCK | binary | 24 | — | — | 0 | not exercised |
| game | dtype_OTHER | binary | 0 | — | — | 0 | not exercised |
| game | n_cand | real | 2972 | 1.000 | 0.000 | 411 | pass |
| game | consults_so_far | real | 2972 | 1.000 | 0.000 | 411 | pass |
| game | my_deck_open | binary | 0 | — | — | 0 | not exercised |
| game | opp_deck_open | binary | 0 | — | — | 0 | not exercised |
| players | life | real | 5918 | 1.000 | 0.000 | 822 | pass |
| players | poison | real | 0 | — | — | 0 | not exercised |
| players | hand | real | 5884 | 1.000 | 0.000 | 822 | pass |
| players | library | real | 5944 | 1.000 | 0.000 | 822 | pass |
| players | graveyard | real | 4877 | 1.000 | 0.000 | 822 | pass |
| players | exile | real | 0 | — | — | 0 | not exercised |
| players | pool_W | real | 0 | — | — | 0 | not exercised |
| players | pool_U | real | 0 | — | — | 0 | not exercised |
| players | pool_B | real | 0 | — | — | 0 | not exercised |
| players | pool_R | real | 0 | — | — | 0 | not exercised |
| players | pool_G | real | 0 | — | — | 0 | not exercised |
| players | pool_C | real | 0 | — | — | 0 | not exercised |
| players | untapped_sources | real | 4670 | 1.000 | 0.000 | 822 | pass |
| players | lands | real | 5864 | 1.000 | 0.000 | 822 | pass |
| players | drawn_this_turn | real | 0 | — | — | 0 | not exercised |
| players | permanents | real | 5864 | 1.000 | 0.000 | 822 | pass |
| ent | printed_tough | real | 21889 | 1.000 | 0.000 | 10106 | pass |
| ent | identity | cat | 60132 | 1.000 | 0.155 | 10023 | pass |
| ent | land | binary | 16898 | 1.000 | 0.715 | 9992 | pass |
| ent | can_block | binary | 13142 | 1.000 | 0.659 | 5503 | pass |
| ent | zone_library_known | binary | 0 | — | — | 0 | not exercised |
| ent | loyalty | real | 1325 | 1.000 | 0.000 | 5503 | pass |
| ent | stack_pos | real | 120 | 1.000 | 0.000 | 114 | pass |
| ent | kw_flash | binary | 13322 | 1.000 | 0.852 | 10106 | pass |
| ent | legal_targets | real | 4081 | 1.000 | 0.000 | 2240 | pass |
| ent | sorcery | binary | 550 | 1.000 | 0.979 | 4489 | pass |
| ent | kw_shroud | binary | 0 | — | — | 0 | not exercised |
| ent | kw_menace | binary | 0 | — | — | 0 | not exercised |
| ent | ctr_p1p1 | real | 46 | — | — | 0 | not exercised |
| ent | tapped | binary | 13142 | 1.000 | 0.659 | 5503 | pass |
| ent | stack_X | real | 0 | — | — | 0 | not exercised |
| ent | turns_on_bf | real | 35763 | 1.000 | 0.000 | 5503 | pass |
| ent | castable | binary | 5890 | 1.000 | 0.552 | 2240 | pass |
| ent | token | binary | 4113 | 1.000 | 0.908 | 5503 | pass |
| ent | printed_power | real | 21889 | 1.000 | 0.000 | 10106 | pass |
| ent | zone_graveyard | binary | 0 | — | — | 0 | not exercised |
| ent | mana_left_if_cast | real | 9402 | 1.000 | 0.000 | 2240 | pass |
| ent | kw_trample | binary | 0 | — | — | 0 | not exercised |
| ent | mv | real | 39995 | 1.000 | 0.000 | 10106 | pass |
| ent | mine | binary | 26817 | 1.000 | 0.643 | 7866 | pass |
| ent | kw_protection | binary | 0 | — | — | 0 | not exercised |
| ent | face_down | binary | 0 | — | — | 0 | not exercised |
| ent | kw_reach | binary | 0 | — | — | 0 | not exercised |
| ent | blocking | binary | 31 | — | — | 0 | not exercised |
| ent | ctr_loyalty | real | 1325 | 1.000 | 0.000 | 5503 | pass |
| ent | ctr_other | real | 408 | 1.000 | 0.000 | 5503 | pass |
| ent | kw_hexproof | binary | 763 | 1.000 | 0.976 | 5503 | pass |
| ent | toughness | real | 23304 | 1.000 | 0.000 | 10106 | pass |
| ent | instant | binary | 12484 | 1.000 | 0.641 | 4489 | pass |
| ent | kw_haste | binary | 0 | — | — | 0 | not exercised |
| ent | stack_mine | binary | 187 | 1.000 | 0.754 | 114 | pass |
| ent | zone_battlefield | binary | 0 | — | — | 0 | not exercised |
| ent | stack_modes | real | 0 | — | — | 0 | not exercised |
| ent | zone_command | binary | 0 | — | — | 0 | not exercised |
| ent | kw_flying | binary | 7965 | 1.000 | 0.902 | 10106 | pass |
| ent | sick | binary | 5993 | 1.000 | 0.854 | 5503 | pass |
| ent | kw_vigilance | binary | 5549 | 1.000 | 0.959 | 9992 | pass |
| ent | kw_prowess | binary | 0 | — | — | 0 | not exercised |
| ent | tough_left | real | 23304 | 1.000 | 0.000 | 10106 | pass |
| ent | kw_double_strike | binary | 0 | — | — | 0 | not exercised |
| ent | other_perm | binary | 9552 | 1.000 | 0.851 | 9992 | pass |
| ent | kw_ward | binary | 0 | — | — | 0 | not exercised |
| ent | ctr_m1m1 | real | 205 | — | — | 0 | not exercised |
| ent | lethal_as_is | binary | 0 | — | — | 0 | not exercised |
| ent | damage | real | 69 | — | — | 0 | not exercised |
| ent | kw_lifelink | binary | 2930 | 1.000 | 0.959 | 9992 | pass |
| ent | power | real | 23304 | 1.000 | 0.000 | 10106 | pass |
| ent | kw_defender | binary | 0 | — | — | 0 | not exercised |
| ent | zone_hand | binary | 0 | — | — | 0 | not exercised |
| ent | can_attack | binary | 17509 | 1.000 | 0.553 | 5503 | pass |
| ent | creature | binary | 20642 | 1.000 | 0.738 | 10106 | pass |
| ent | zone_exile | binary | 0 | — | — | 0 | not exercised |
| ent | kw_ninjutsu | binary | 3519 | 1.000 | 0.936 | 10106 | pass |
| ent | kw_first_strike | binary | 0 | — | — | 0 | not exercised |
| ent | zone_stack | binary | 0 | — | — | 0 | not exercised |
| ent | entered | binary | 2438 | 1.000 | 0.940 | 5503 | pass |
| ent | stack_is_ability | binary | 182 | 1.000 | 0.728 | 114 | pass |
| ent | attacking | binary | 1128 | 1.000 | 0.967 | 5503 | pass |
| ent | kw_deathtouch | binary | 4058 | 1.000 | 0.935 | 10106 | pass |
| opp_hand | origin_opening | binary | 5584 | 1.000 | 0.664 | 1188 | pass |
| opp_hand | origin_drawn | binary | 5643 | 1.000 | 0.664 | 1188 | pass |
| opp_hand | origin_returned | binary | 59 | — | — | 0 | not exercised |
| opp_hand | origin_other | binary | 0 | — | — | 0 | not exercised |
| opp_hand | age | real | 10621 | 1.000 | 0.000 | 1188 | pass |
| opp_hand | known | binary | 145 | — | — | 0 | not exercised |
| opp_hand | seen | binary | 145 | — | — | 0 | not exercised |
| opp_hand | identity | cat | 70 | — | — | 0 | not exercised |
| opp_deck | count | real | 40000 | 1.000 | 0.000 | 5641 | pass |
| opp_deck | fraction | real | 40000 | 0.999 | 0.000 | 5641 | pass |
| opp_deck | castable_now | binary | 17678 | 1.000 | 0.643 | 5641 | pass |
| opp_deck | mv | real | 27221 | 1.000 | 0.000 | 5641 | pass |
| opp_deck | instant_speed | binary | 18268 | 1.000 | 0.542 | 5641 | pass |
| opp_deck | identity | cat | 38122 | 1.000 | 0.049 | 5641 | pass |
| opp_act | act_cast | binary | 10445 | 1.000 | 0.777 | 4548 | pass |
| opp_act | act_activate | binary | 4385 | 1.000 | 0.813 | 4548 | pass |
| opp_act | act_attack | binary | 9146 | 1.000 | 0.538 | 4548 | pass |
| opp_act | act_block | binary | 1235 | — | — | 0 | not exercised |
| opp_act | act_declined_block | binary | 1532 | — | — | 0 | not exercised |
| opp_act | act_passed_mana_up | binary | 5106 | 1.000 | 0.872 | 4548 | pass |
| opp_act | act_other | binary | 0 | — | — | 0 | not exercised |
| opp_act | consult_age | real | 31849 | 1.000 | 0.000 | 4548 | pass |
| cand | type_PASS | binary | 2917 | 1.000 | 0.671 | 1219 | pass |
| cand | type_LAND | binary | 300 | 1.000 | 0.943 | 1219 | pass |
| cand | type_SPELL | binary | 4945 | 1.000 | 0.509 | 1219 | pass |
| cand | type_ACTIVATE | binary | 1392 | 1.000 | 0.935 | 1219 | pass |
| cand | type_TARGET | binary | 190 | 1.000 | 0.975 | 1219 | pass |
| cand | type_ATTACK | binary | 113 | — | — | 0 | not exercised |
| cand | type_BLOCK | binary | 33 | — | — | 0 | not exercised |
| cand | type_OTHER | binary | 0 | — | — | 0 | not exercised |
| cand | LSA.mana_left_after | real | 6334 | 1.000 | 0.000 | 769 | pass |
| cand | LSA.targets_legal | real | 3681 | 1.000 | 0.000 | 769 | pass |
| cand | LSA.instant_speed | binary | 461 | 1.000 | 0.870 | 769 | pass |
| cand | LSA.sorcery_speed | binary | 461 | 1.000 | 0.870 | 769 | pass |
| cand | LSA.flash | binary | 2222 | 1.000 | 0.672 | 769 | pass |
| cand | LSA.stack_above_n | real | 1241 | 1.000 | 0.000 | 769 | pass |
| cand | LSA.X_chosen | real | 0 | — | — | 0 | not exercised |
| cand | TARGET.is_player | - | 0 | — | — | 0 | too few rows (190) |
| cand | TARGET.is_me | - | 0 | — | — | 0 | too few rows (190) |
| cand | TARGET.life_if_player | - | 0 | — | — | 0 | too few rows (190) |
| cand | TARGET.is_creature | - | 0 | — | — | 0 | too few rows (190) |
| cand | TARGET.power | - | 0 | — | — | 0 | too few rows (190) |
| cand | TARGET.toughness | - | 0 | — | — | 0 | too few rows (190) |
| cand | TARGET.mine | - | 0 | — | — | 0 | too few rows (190) |
| cand | ATTACK.damage_dealt | - | 0 | — | — | 0 | too few rows (113) |
| cand | ATTACK.their_kills | - | 0 | — | — | 0 | too few rows (113) |
| cand | ATTACK.my_losses | - | 0 | — | — | 0 | too few rows (113) |
| cand | ATTACK.lethal | - | 0 | — | — | 0 | too few rows (113) |
| cand | ATTACK.attackers_used | - | 0 | — | — | 0 | too few rows (113) |
| cand | ATTACK.opp_life_after | - | 0 | — | — | 0 | too few rows (113) |
| cand | ATTACK.bodies_retained | - | 0 | — | — | 0 | too few rows (113) |
| cand | ATTACK.power_retained | - | 0 | — | — | 0 | too few rows (113) |
| cand | ATTACK.tough_retained | - | 0 | — | — | 0 | too few rows (113) |
| cand | ATTACK.crack_back | - | 0 | — | — | 0 | too few rows (113) |
| cand | ATTACK.my_life_after | - | 0 | — | — | 0 | too few rows (113) |
| cand | BLOCK.damage_taken | - | 0 | — | — | 0 | too few rows (33) |
| cand | BLOCK.attackers_killed | - | 0 | — | — | 0 | too few rows (33) |
| cand | BLOCK.value_killed | - | 0 | — | — | 0 | too few rows (33) |
| cand | BLOCK.blockers_lost | - | 0 | — | — | 0 | too few rows (33) |
| cand | BLOCK.value_lost | - | 0 | — | — | 0 | too few rows (33) |
| cand | BLOCK.defender_dies | - | 0 | — | — | 0 | too few rows (33) |
| cand | BLOCK.blockers_used | - | 0 | — | — | 0 | too few rows (33) |
| cand | BLOCK.life_after | - | 0 | — | — | 0 | too few rows (33) |

entity rows by zone: `{'battlefield': 38201, 'hand': 14636, 'stack': 566, 'graveyard': 17839, 'exile': 0, 'library_known': 0, 'command': 0}`; candidate rows by type: `{'PASS': 2917, 'LAND': 300, 'SPELL': 5791, 'ACTIVATE': 1392, 'TARGET': 190, 'ATTACK': 113, 'BLOCK': 33, 'OTHER': 0}`

## after L4

| part | field | kind | exercised | held-out | chance | n | result |
|---|---|---|---|---|---|---|---|
| game | turn | real | 2972 | 0.908 | 0.000 | 411 | pass |
| game | i_am_active | binary | 1405 | 1.000 | 0.557 | 411 | pass |
| game | step_upkeep | binary | 258 | 1.000 | 0.917 | 411 | pass |
| game | step_draw | binary | 248 | 1.000 | 0.915 | 411 | pass |
| game | step_main1 | binary | 695 | 1.000 | 0.745 | 411 | pass |
| game | step_decl_att | binary | 303 | 1.000 | 0.905 | 411 | pass |
| game | step_decl_blk | binary | 243 | 1.000 | 0.905 | 411 | pass |
| game | step_combat_dmg | binary | 641 | 1.000 | 0.810 | 411 | pass |
| game | step_main2 | binary | 366 | 1.000 | 0.873 | 411 | pass |
| game | step_end | binary | 218 | 1.000 | 0.929 | 411 | pass |
| game | priority | binary | 82 | — | — | 0 | not exercised |
| game | stack_depth | real | 446 | 0.901 | 0.000 | 411 | pass |
| game | dtype_PASS | binary | 96 | 1.000 | 0.949 | 411 | pass |
| game | dtype_LAND | binary | 98 | 1.000 | 0.934 | 411 | pass |
| game | dtype_SPELL | binary | 400 | 1.000 | 0.820 | 411 | pass |
| game | dtype_ACTIVATE | binary | 74 | — | — | 0 | not exercised |
| game | dtype_TARGET | binary | 51 | — | — | 0 | not exercised |
| game | dtype_ATTACK | binary | 57 | — | — | 0 | not exercised |
| game | dtype_BLOCK | binary | 24 | — | — | 0 | not exercised |
| game | dtype_OTHER | binary | 0 | — | — | 0 | not exercised |
| game | n_cand | real | 2972 | 0.958 | 0.000 | 411 | pass |
| game | consults_so_far | real | 2972 | 0.960 | 0.000 | 411 | pass |
| game | my_deck_open | binary | 0 | — | — | 0 | not exercised |
| game | opp_deck_open | binary | 0 | — | — | 0 | not exercised |
| players | life | real | 5918 | 0.998 | 0.000 | 822 | pass |
| players | poison | real | 0 | — | — | 0 | not exercised |
| players | hand | real | 5884 | 0.998 | 0.000 | 822 | pass |
| players | library | real | 5944 | 0.987 | 0.000 | 822 | pass |
| players | graveyard | real | 4877 | 0.994 | 0.000 | 822 | pass |
| players | exile | real | 0 | — | — | 0 | not exercised |
| players | pool_W | real | 0 | — | — | 0 | not exercised |
| players | pool_U | real | 0 | — | — | 0 | not exercised |
| players | pool_B | real | 0 | — | — | 0 | not exercised |
| players | pool_R | real | 0 | — | — | 0 | not exercised |
| players | pool_G | real | 0 | — | — | 0 | not exercised |
| players | pool_C | real | 0 | — | — | 0 | not exercised |
| players | untapped_sources | real | 4670 | 0.999 | 0.000 | 822 | pass |
| players | lands | real | 5864 | 0.998 | 0.000 | 822 | pass |
| players | drawn_this_turn | real | 0 | — | — | 0 | not exercised |
| players | permanents | real | 5864 | 0.998 | 0.000 | 822 | pass |
| ent | printed_tough | real | 21889 | 0.999 | 0.000 | 10106 | pass |
| ent | identity | cat | 60132 | 1.000 | 0.155 | 10023 | pass |
| ent | land | binary | 16898 | 1.000 | 0.715 | 9992 | pass |
| ent | can_block | binary | 13142 | 1.000 | 0.659 | 5503 | pass |
| ent | zone_library_known | binary | 0 | — | — | 0 | not exercised |
| ent | loyalty | real | 1325 | 0.985 | 0.000 | 5503 | pass |
| ent | stack_pos | real | 120 | 0.883 | 0.000 | 114 | **FAIL** |
| ent | kw_flash | binary | 13322 | 1.000 | 0.852 | 10106 | pass |
| ent | legal_targets | real | 4081 | 0.991 | 0.000 | 2240 | pass |
| ent | sorcery | binary | 550 | 1.000 | 0.979 | 4489 | pass |
| ent | kw_shroud | binary | 0 | — | — | 0 | not exercised |
| ent | kw_menace | binary | 0 | — | — | 0 | not exercised |
| ent | ctr_p1p1 | real | 46 | — | — | 0 | not exercised |
| ent | tapped | binary | 13142 | 1.000 | 0.659 | 5503 | pass |
| ent | stack_X | real | 0 | — | — | 0 | not exercised |
| ent | turns_on_bf | real | 35763 | 0.974 | 0.000 | 5503 | pass |
| ent | castable | binary | 5890 | 1.000 | 0.552 | 2240 | pass |
| ent | token | binary | 4113 | 1.000 | 0.908 | 5503 | pass |
| ent | printed_power | real | 21889 | 0.999 | 0.000 | 10106 | pass |
| ent | zone_graveyard | binary | 0 | — | — | 0 | not exercised |
| ent | mana_left_if_cast | real | 9402 | 0.983 | 0.000 | 2240 | pass |
| ent | kw_trample | binary | 0 | — | — | 0 | not exercised |
| ent | mv | real | 39995 | 0.999 | 0.000 | 10106 | pass |
| ent | mine | binary | 26817 | 1.000 | 0.643 | 7866 | pass |
| ent | kw_protection | binary | 0 | — | — | 0 | not exercised |
| ent | face_down | binary | 0 | — | — | 0 | not exercised |
| ent | kw_reach | binary | 0 | — | — | 0 | not exercised |
| ent | blocking | binary | 31 | — | — | 0 | not exercised |
| ent | ctr_loyalty | real | 1325 | 0.985 | 0.000 | 5503 | pass |
| ent | ctr_other | real | 408 | -0.004 | 0.000 | 5503 | **FAIL** |
| ent | kw_hexproof | binary | 763 | 1.000 | 0.976 | 5503 | pass |
| ent | toughness | real | 23304 | 0.992 | 0.000 | 10106 | pass |
| ent | instant | binary | 12484 | 1.000 | 0.641 | 4489 | pass |
| ent | kw_haste | binary | 0 | — | — | 0 | not exercised |
| ent | stack_mine | binary | 187 | 1.000 | 0.754 | 114 | pass |
| ent | zone_battlefield | binary | 0 | — | — | 0 | not exercised |
| ent | stack_modes | real | 0 | — | — | 0 | not exercised |
| ent | zone_command | binary | 0 | — | — | 0 | not exercised |
| ent | kw_flying | binary | 7965 | 1.000 | 0.902 | 10106 | pass |
| ent | sick | binary | 5993 | 1.000 | 0.854 | 5503 | pass |
| ent | kw_vigilance | binary | 5549 | 1.000 | 0.959 | 9992 | pass |
| ent | kw_prowess | binary | 0 | — | — | 0 | not exercised |
| ent | tough_left | real | 23304 | 0.992 | 0.000 | 10106 | pass |
| ent | kw_double_strike | binary | 0 | — | — | 0 | not exercised |
| ent | other_perm | binary | 9552 | 1.000 | 0.851 | 9992 | pass |
| ent | kw_ward | binary | 0 | — | — | 0 | not exercised |
| ent | ctr_m1m1 | real | 205 | — | — | 0 | not exercised |
| ent | lethal_as_is | binary | 0 | — | — | 0 | not exercised |
| ent | damage | real | 69 | — | — | 0 | not exercised |
| ent | kw_lifelink | binary | 2930 | 1.000 | 0.959 | 9992 | pass |
| ent | power | real | 23304 | 0.990 | 0.000 | 10106 | pass |
| ent | kw_defender | binary | 0 | — | — | 0 | not exercised |
| ent | zone_hand | binary | 0 | — | — | 0 | not exercised |
| ent | can_attack | binary | 17509 | 1.000 | 0.553 | 5503 | pass |
| ent | creature | binary | 20642 | 1.000 | 0.738 | 10106 | pass |
| ent | zone_exile | binary | 0 | — | — | 0 | not exercised |
| ent | kw_ninjutsu | binary | 3519 | 1.000 | 0.936 | 10106 | pass |
| ent | kw_first_strike | binary | 0 | — | — | 0 | not exercised |
| ent | zone_stack | binary | 0 | — | — | 0 | not exercised |
| ent | entered | binary | 2438 | 1.000 | 0.940 | 5503 | pass |
| ent | stack_is_ability | binary | 182 | 1.000 | 0.728 | 114 | pass |
| ent | attacking | binary | 1128 | 1.000 | 0.967 | 5503 | pass |
| ent | kw_deathtouch | binary | 4058 | 1.000 | 0.935 | 10106 | pass |
| opp_hand | origin_opening | binary | 5584 | 1.000 | 0.664 | 1188 | pass |
| opp_hand | origin_drawn | binary | 5643 | 1.000 | 0.664 | 1188 | pass |
| opp_hand | origin_returned | binary | 59 | — | — | 0 | not exercised |
| opp_hand | origin_other | binary | 0 | — | — | 0 | not exercised |
| opp_hand | age | real | 10621 | 0.995 | 0.000 | 1188 | pass |
| opp_hand | known | binary | 145 | — | — | 0 | not exercised |
| opp_hand | seen | binary | 145 | — | — | 0 | not exercised |
| opp_hand | identity | cat | 70 | — | — | 0 | not exercised |
| opp_deck | count | real | 40000 | 0.988 | 0.000 | 5619 | pass |
| opp_deck | fraction | real | 40000 | 0.979 | 0.000 | 5619 | pass |
| opp_deck | castable_now | binary | 17609 | 1.000 | 0.645 | 5619 | pass |
| opp_deck | mv | real | 27102 | 1.000 | 0.000 | 5619 | pass |
| opp_deck | instant_speed | binary | 18173 | 1.000 | 0.547 | 5619 | pass |
| opp_deck | identity | cat | 38063 | 1.000 | 0.049 | 5619 | pass |
| opp_act | act_cast | binary | 10445 | 1.000 | 0.777 | 4548 | pass |
| opp_act | act_activate | binary | 4385 | 1.000 | 0.813 | 4548 | pass |
| opp_act | act_attack | binary | 9146 | 1.000 | 0.538 | 4548 | pass |
| opp_act | act_block | binary | 1235 | — | — | 0 | not exercised |
| opp_act | act_declined_block | binary | 1532 | — | — | 0 | not exercised |
| opp_act | act_passed_mana_up | binary | 5106 | 1.000 | 0.872 | 4548 | pass |
| opp_act | act_other | binary | 0 | — | — | 0 | not exercised |
| opp_act | consult_age | real | 31849 | 1.000 | 0.000 | 4548 | pass |
| cand | type_PASS | binary | 2917 | 1.000 | 0.671 | 1219 | pass |
| cand | type_LAND | binary | 300 | 1.000 | 0.943 | 1219 | pass |
| cand | type_SPELL | binary | 4945 | 1.000 | 0.509 | 1219 | pass |
| cand | type_ACTIVATE | binary | 1392 | 1.000 | 0.935 | 1219 | pass |
| cand | type_TARGET | binary | 190 | 1.000 | 0.975 | 1219 | pass |
| cand | type_ATTACK | binary | 113 | — | — | 0 | not exercised |
| cand | type_BLOCK | binary | 33 | — | — | 0 | not exercised |
| cand | type_OTHER | binary | 0 | — | — | 0 | not exercised |
| cand | LSA.mana_left_after | real | 6334 | 0.997 | 0.000 | 769 | pass |
| cand | LSA.targets_legal | real | 3681 | 0.998 | 0.000 | 769 | pass |
| cand | LSA.instant_speed | binary | 461 | 1.000 | 0.870 | 769 | pass |
| cand | LSA.sorcery_speed | binary | 461 | 1.000 | 0.870 | 769 | pass |
| cand | LSA.flash | binary | 2222 | 1.000 | 0.672 | 769 | pass |
| cand | LSA.stack_above_n | real | 1241 | 0.978 | 0.000 | 769 | pass |
| cand | LSA.X_chosen | real | 0 | — | — | 0 | not exercised |
| cand | TARGET.is_player | - | 0 | — | — | 0 | too few rows (190) |
| cand | TARGET.is_me | - | 0 | — | — | 0 | too few rows (190) |
| cand | TARGET.life_if_player | - | 0 | — | — | 0 | too few rows (190) |
| cand | TARGET.is_creature | - | 0 | — | — | 0 | too few rows (190) |
| cand | TARGET.power | - | 0 | — | — | 0 | too few rows (190) |
| cand | TARGET.toughness | - | 0 | — | — | 0 | too few rows (190) |
| cand | TARGET.mine | - | 0 | — | — | 0 | too few rows (190) |
| cand | ATTACK.damage_dealt | - | 0 | — | — | 0 | too few rows (113) |
| cand | ATTACK.their_kills | - | 0 | — | — | 0 | too few rows (113) |
| cand | ATTACK.my_losses | - | 0 | — | — | 0 | too few rows (113) |
| cand | ATTACK.lethal | - | 0 | — | — | 0 | too few rows (113) |
| cand | ATTACK.attackers_used | - | 0 | — | — | 0 | too few rows (113) |
| cand | ATTACK.opp_life_after | - | 0 | — | — | 0 | too few rows (113) |
| cand | ATTACK.bodies_retained | - | 0 | — | — | 0 | too few rows (113) |
| cand | ATTACK.power_retained | - | 0 | — | — | 0 | too few rows (113) |
| cand | ATTACK.tough_retained | - | 0 | — | — | 0 | too few rows (113) |
| cand | ATTACK.crack_back | - | 0 | — | — | 0 | too few rows (113) |
| cand | ATTACK.my_life_after | - | 0 | — | — | 0 | too few rows (113) |
| cand | BLOCK.damage_taken | - | 0 | — | — | 0 | too few rows (33) |
| cand | BLOCK.attackers_killed | - | 0 | — | — | 0 | too few rows (33) |
| cand | BLOCK.value_killed | - | 0 | — | — | 0 | too few rows (33) |
| cand | BLOCK.blockers_lost | - | 0 | — | — | 0 | too few rows (33) |
| cand | BLOCK.value_lost | - | 0 | — | — | 0 | too few rows (33) |
| cand | BLOCK.defender_dies | - | 0 | — | — | 0 | too few rows (33) |
| cand | BLOCK.blockers_used | - | 0 | — | — | 0 | too few rows (33) |
| cand | BLOCK.life_after | - | 0 | — | — | 0 | too few rows (33) |

entity rows by zone: `{'battlefield': 38201, 'hand': 14636, 'stack': 566, 'graveyard': 17839, 'exile': 0, 'library_known': 0, 'command': 0}`; candidate rows by type: `{'PASS': 2917, 'LAND': 300, 'SPELL': 5791, 'ACTIVATE': 1392, 'TARGET': 190, 'ATTACK': 113, 'BLOCK': 33, 'OTHER': 0}`

## edges after L4 (balanced pairs)

| edge | positives | held-out | chance | result |
|---|---|---|---|---|
| blocks | 16 | — | — | too few rows |
| blocked_by | 29 | — | — | not exercised |
| attacking_player | 1116 | 1.000 | 0.500 | pass |
| targets | 81 | 1.000 | 0.500 | pass |
| controls | 19965 | 0.997 | 0.506 | pass |
| attached_to | 0 | — | — | not exercised |
| can_block | 63 | 1.000 | 0.500 | pass |
| stack_above | 120 | 1.000 | 0.500 | pass |
| refers_to | 19964 | 0.989 | 0.501 | pass |
| referred_by | 20052 | 0.989 | 0.503 | pass |

## consult-level

- after L3: remaining-deck count per name mean R² = -0.232356120294432 (min -2.2437157698523804, 16/22 names exercised; worst [(-2.2437157698523804, 'Watery Grave'), (-1.7265023165163065, 'Floodpits Drowner'), (-0.9028239218723635, 'Soulstone Sanctuary'), (-0.38186982634262745, 'Island'), (-0.356584627650252, 'Spyglass Siren')]); instant-speed threat count R² = 0.9340042840333121 (exercised 1803); known-card set: not exercised
- after L4: remaining-deck count per name mean R² = 0.13130873365404233 (min -2.3306550217353093, 16/22 names exercised; worst [(-2.3306550217353093, 'Floodpits Drowner'), (-0.5625177870607287, 'Soulstone Sanctuary'), (-0.47108979621663827, 'Watery Grave'), (-0.16492783441030223, 'Nowhere to Run'), (-0.1520640039497334, 'Island')]); instant-speed threat count R² = 0.9459643673073485 (exercised 1803); known-card set: not exercised
