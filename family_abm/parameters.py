"""Web-facing parameter metadata and simulation resource limits.

The numeric defaults live with the model (``family_member.DEFAULT_PARAMS``).
This module adds only the editable ranges and presentation groups, so the API,
server-side validation, and dashboard controls share one source.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParamSpec:
    key: str
    group: str
    minimum: float
    maximum: float
    step: float
    kind: str = "number"

    def to_dict(self) -> dict[str, float | str]:
        return {
            "group": self.group,
            "min": self.minimum,
            "max": self.maximum,
            "step": self.step,
            "type": self.kind,
            "label_key": f"param.{self.key}",
        }


PARAM_GROUPS: dict[str, tuple[str, ...]] = {
    "Education": ("education_rate",),
    "Income": (
        "income_base", "income_edu_boost", "income_age_peak", "income_age_spread",
    ),
    "Health": (
        "health_floor", "health_decay_rate", "health_edu_protection",
    ),
    "Stress": (
        "stress_base", "stress_work_add", "stress_decay", "stress_neuro_sensitivity",
        "stress_pressure_gain", "income_baseline",
    ),
    "Happiness": (
        "happiness_baseline", "happiness_health_weight", "happiness_income_weight",
        "happiness_edu_weight", "happiness_stress_penalty", "happiness_recovery",
    ),
    "Noise": ("randomness",),
    "Family Support": (
        "influence_strength", "income_support", "use_life_stage_susceptibility",
        "role_switch",
    ),
    "Influence Shape": ("susceptibility_scale", "stage_shift_years"),
}

_SPEC_VALUES: dict[str, tuple[float, float, float, str]] = {
    "education_rate": (0.0, 0.1, 0.001, "number"),
    "income_base": (0.0, 5.0, 0.01, "number"),
    "income_edu_boost": (0.0, 5.0, 0.01, "number"),
    "income_age_peak": (0.0, 100.0, 1.0, "number"),
    "income_age_spread": (0.1, 50.0, 0.1, "number"),
    "health_floor": (0.0, 1.0, 0.01, "number"),
    "health_decay_rate": (0.0, 0.1, 0.0001, "number"),
    "health_edu_protection": (0.0, 1.0, 0.01, "number"),
    "stress_base": (0.0, 1.0, 0.001, "number"),
    "stress_work_add": (0.0, 1.0, 0.001, "number"),
    "stress_decay": (0.0, 1.0, 0.001, "number"),
    "stress_neuro_sensitivity": (0.0, 5.0, 0.01, "number"),
    "stress_pressure_gain": (0.0, 5.0, 0.01, "number"),
    "income_baseline": (0.0, 5.0, 0.01, "number"),
    "happiness_baseline": (0.0, 5.0, 0.01, "number"),
    "happiness_health_weight": (0.0, 5.0, 0.01, "number"),
    "happiness_income_weight": (0.0, 5.0, 0.01, "number"),
    "happiness_edu_weight": (0.0, 5.0, 0.01, "number"),
    "happiness_stress_penalty": (0.0, 5.0, 0.01, "number"),
    "happiness_recovery": (0.0, 1.0, 0.01, "number"),
    "randomness": (0.0, 1.0, 0.001, "number"),
    "influence_strength": (0.0, 5.0, 0.01, "number"),
    "income_support": (0.0, 5.0, 0.01, "number"),
    "use_life_stage_susceptibility": (0.0, 1.0, 1.0, "switch"),
    "role_switch": (0.0, 1.0, 1.0, "switch"),
    "susceptibility_scale": (0.0, 5.0, 0.01, "number"),
    "stage_shift_years": (-10.0, 10.0, 0.5, "number"),
}


def _build_specs() -> dict[str, ParamSpec]:
    specs: dict[str, ParamSpec] = {}
    for group, keys in PARAM_GROUPS.items():
        for key in keys:
            minimum, maximum, step, kind = _SPEC_VALUES[key]
            specs[key] = ParamSpec(
                key=key,
                group=group,
                minimum=minimum,
                maximum=maximum,
                step=step,
                kind=kind,
            )
    missing = sorted(set(_SPEC_VALUES) - set(specs))
    if missing:
        raise RuntimeError(f"参数缺少分组：{missing}")
    return specs


PARAM_SPECS: dict[str, ParamSpec] = _build_specs()

MAX_STEPS = 5000
MAX_FAMILIES = 20
MAX_MEMBERS_PER_FAMILY = 50
MAX_TOTAL_MEMBERS = 200

SIM_LIMITS: dict[str, dict[str, int]] = {
    "steps": {"min": 0, "max": MAX_STEPS},
    "families": {"min": 0, "max": MAX_FAMILIES},
    "members_per_family": {"min": 0, "max": MAX_MEMBERS_PER_FAMILY},
    "total_members": {"min": 0, "max": MAX_TOTAL_MEMBERS},
}
