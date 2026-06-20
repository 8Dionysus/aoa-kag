# Agon Legacy Index

This index maps former root paths and historical names to current active Agon
part routes.

| Former path or name | Active route | Posture |
| --- | --- | --- |
| `config/agon_kag_promotion_candidates.seed.json` | `mechanics/agon/parts/promotion-candidates/config/promotion-candidate-registry.source.json` | former root config path; active key is `review_stage` |
| `config/agon_sophian_kag_packets.seed.json` | `mechanics/agon/parts/sophian-threshold-packets/config/sophian-threshold-packet-registry.source.json` | former root config path; active key is `review_stage` |
| `manifests/recurrence/component.agon.wave17.aoa_kag.json` | `mechanics/agon/parts/promotion-candidates/manifests/recurrence/component.agon.promotion-candidates.json` | former recurrence source-control path; active key is `review_stage` |
| `manifests/recurrence/hooks/component.agon.wave17.aoa_kag.hooks.json` | `mechanics/agon/parts/promotion-candidates/manifests/recurrence/hooks/component.agon.promotion-candidates.hooks.json` | former recurrence hook path |
| `manifests/recurrence/component.agon.sophian-kag-packet-surfaces.json` | `mechanics/agon/parts/sophian-threshold-packets/manifests/recurrence/component.agon.sophian-threshold-packets.json` | former recurrence source-control path; active key is `review_stage` |
| `manifests/recurrence/hooks/component.agon.sophian-kag-packet-surfaces.hooks.json` | `mechanics/agon/parts/sophian-threshold-packets/manifests/recurrence/hooks/component.agon.sophian-threshold-packets.hooks.json` | former recurrence hook path |
| `scripts/build_agon_kag_promotion_candidate_registry.py` | `mechanics/agon/parts/promotion-candidates/scripts/build_promotion_candidate_registry.py` | former root builder path |
| `scripts/validate_agon_kag_promotion_candidate_registry.py` | `mechanics/agon/parts/promotion-candidates/scripts/validate_promotion_candidate_registry.py` | former root validator path |
| `scripts/build_agon_sophian_kag_packet_registry.py` | `mechanics/agon/parts/sophian-threshold-packets/scripts/build_sophian_threshold_packet_registry.py` | former root builder path |
| `scripts/validate_agon_sophian_kag_packet_registry.py` | `mechanics/agon/parts/sophian-threshold-packets/scripts/validate_sophian_threshold_packet_registry.py` | former root validator path |
| `tests/test_agon_kag_promotion_candidate_registry.py` | `mechanics/agon/parts/promotion-candidates/tests/test_promotion_candidate_registry.py` | former root focused test path |
| `tests/test_agon_sophian_kag_packet_registry.py` | `mechanics/agon/parts/sophian-threshold-packets/tests/test_sophian_threshold_packet_registry.py` | former root focused test path |
| `docs/AGON_KAG_PROMOTION_CANDIDATES.md` | `mechanics/agon/parts/promotion-candidates/docs/promotion-candidates.md` | former root doc path |
| `docs/AGON_KAG_DERIVED_SUBSTRATE_BOUNDARY.md` | `mechanics/agon/parts/promotion-candidates/docs/derived-substrate-boundary.md` | former root doc path |
| `docs/AGON_WAVE17_KAG_LANDING.md` | `mechanics/agon/parts/promotion-candidates/docs/promotion-candidate-route.md` | former landing name, active-distilled route note |
| `docs/AGON_SOPHIAN_KAG_PACKET_BRIDGE.md` | `mechanics/agon/parts/sophian-threshold-packets/docs/packet-bridge.md` | former root doc path |
| `docs/AGON_KAG_TO_TOS_BOUNDARY.md` | `mechanics/agon/parts/sophian-threshold-packets/docs/sophian-canon-boundary.md` | former root doc path |
| `docs/AGON_KAG_TOS_THRESHOLD_BOUNDARY.md` | `mechanics/agon/parts/sophian-threshold-packets/docs/threshold-boundary.md` | former root doc path |
| `docs/AGON_WAVE18_KAG_LANDING.md` | `mechanics/agon/parts/sophian-threshold-packets/docs/sophian-threshold-review.md` | former landing name, active-distilled review note |
| `quests/AOKAG-Q-AGON-0001-kag-promotion-candidates.md` | `mechanics/agon/parts/promotion-candidates/VALIDATION.md` | former unvalidated quest sidecar; active proof is the part validator and test |
| `quests/AOKAG-Q-AGON-0002-sophian-threshold-packets.md` | `mechanics/agon/parts/sophian-threshold-packets/VALIDATION.md` | former unvalidated quest sidecar; active proof is the part validator and test |
