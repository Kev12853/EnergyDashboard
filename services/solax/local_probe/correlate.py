# services/solax/local_probe/correlate.py

from pathlib import Path

import pandas as pd


SCAN_FILE = Path(
    "scan.csv"
)

GROUND_FILE = Path(
    "services/solax/local_probe/ground_truth.csv"
)

OUTPUT_FILE = Path(
    "candidate_registers.csv"
)


TARGETS = {

    "pv_power_w": 50,

    "battery_power_w": 50,

    "battery_soc_pct": 2,

    "house_load_w": 50,

    "grid_power_w": 50,

}


def signed16(
    value,
):

    if value > 32767:

        return value - 65536

    return value


def uint32(
    hi,
    lo,
):

    return (
        hi << 16
    ) | lo


def signed32(
    hi,
    lo,
):

    value = uint32(
        hi,
        lo,
    )

    if value > 2147483647:

        value -= 4294967296

    return value


def decode_candidates(
    registers,
):

    r0 = registers[0]

    candidates = {

        "uint16": r0,

        "uint16_x0.1": r0 / 10,

        "uint16_x0.01": r0 / 100,

        "signed16": signed16(
            r0
        ),

        "signed16_x0.1": signed16(
            r0
        ) / 10,

        "signed16_x0.01": signed16(
            r0
        ) / 100,

    }

    if len(registers) >= 2:

        hi = registers[0]

        lo = registers[1]

        u32 = uint32(
            hi,
            lo,
        )

        s32 = signed32(
            hi,
            lo,
        )

        candidates.update(

            {

                "uint32": u32,

                "uint32_x0.1": u32 / 10,

                "uint32_x0.01": u32 / 100,

                "signed32": s32,

                "signed32_x0.1": s32 / 10,

                "signed32_x0.01": s32 / 100,

            }

        )

    return candidates


def parse_registers(
    value,
):

    value = (

        value
        .replace(
            "[",
            "",
        )
        .replace(
            "]",
            "",
        )

    )

    return [

        int(
            x.strip()
        )

        for x

        in value.split(",")

    ]


print(
    "Loading files..."
)

scan = pd.read_csv(
    SCAN_FILE
)

ground = pd.read_csv(
    GROUND_FILE
)

scan[
    "timestamp"
] = pd.to_datetime(

    scan[
        "timestamp"
    ]

)

ground[
    "timestamp"
] = pd.to_datetime(

    ground[
        "timestamp"
    ]

)

merged = pd.merge_asof(

    scan.sort_values(
        "timestamp"
    ),

    ground.sort_values(
        "timestamp"
    ),

    on="timestamp",

    direction="nearest",

    tolerance=pd.Timedelta(
        seconds=60
    ),

)

results = []

print(
    "Correlating..."
)

for (

    register_type,
    register,

), group in merged.groupby(

    [
        "type",
        "register",
    ]

):

    decoded = []

    for raw in group[
        "raw"
    ]:

        try:

            regs = parse_registers(
                raw
            )

            decoded.append(

                decode_candidates(
                    regs
                )

            )

        except:

            decoded.append(
                {}
            )

    for decoder in [

        k

        for d

        in decoded

        for k

        in d.keys()

    ]:

        values = [

            d.get(
                decoder
            )

            for d

            in decoded

        ]

        if all(

            v is None

            for v

            in values

        ):

            continue

        temp = group.copy()

        temp[
            "candidate"
        ] = values

        for target in TARGETS:

            tolerance = TARGETS[
                target
            ]

            valid = temp.dropna(

                subset=[
                    "candidate",
                    target,
                ]

            )

            if len(
                valid
            ) < 5:

                continue

            diff = (

                valid[
                    "candidate"
                ]

                -

                valid[
                    target
                ]

            ).abs()

            matches = (

                diff
                < tolerance

            ).mean()

            corr = valid[
                [
                    "candidate",
                    target,
                ]
            ].corr().iloc[
                0,
                1,
            ]

            results.append(

                {

                    "register_type": register_type,

                    "register": register,

                    "decoder": decoder,

                    "target": target,

                    "match_pct": round(
                        matches,
                        3,
                    ),

                    "correlation": round(
                        corr,
                        3,
                    )

                    if pd.notna(
                        corr
                    )

                    else None,

                }

            )

results = pd.DataFrame(
    results
)

results = results.sort_values(

    [

        "target",
        "correlation",
        "match_pct",

    ],

    ascending=False,

)

results.to_csv(

    OUTPUT_FILE,

    index=False,

)

print(
    results.head(
        50
    )
)

print(
    f"\nSaved {OUTPUT_FILE}"
)