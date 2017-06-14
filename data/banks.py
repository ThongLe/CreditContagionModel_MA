params = [
    {
        "code": "A",
        "asset": {
            "total": 200, "cash": 20, "interbank_asset": 50, "external_asset": 130
        },
        "liability": {
            "total": 200, "deposit": 140,  "interbank_liability": 20, "equity": 40
        },
        "growth_rate": {
            "deposit": { "mean": 0.01, "var": 0.02},
            "external_asset": { "mean": 0.015, "var": 0.025},
            "equity": { "mean": 0.02, "var": 0.01}
        },
        "short_term_lending_rate": 0.8,
        "short_term_borrowing_rate": 0.8,
        "lending_target_rate": 0.2,
        "borrowing_target_rate": 0.2,
        "recover_rate": { "min": 0.5, "max": 0.8 },
        "large_bank": True
    },
    {
        "code": "B",
        "asset": { "total": 100, "cash": 15, "interbank_asset": 10, "external_asset":  75},
        "liability": { "total": 100, "deposit":  60,  "interbank_liability": 25, "equity": 15},
        "growth_rate": {
            "deposit": { "mean": 0.01, "var": 0.02},
            "external_asset": { "mean": 0.015, "var": 0.025},
            "equity": { "mean": 0.02, "var": 0.01}
        },
        "short_term_lending_rate": 0.8,
        "short_term_borrowing_rate": 0.8,
        "lending_target_rate": 0.2,
        "borrowing_target_rate": 0.2,
        "recover_rate": {"min": 0.5, "max": 0.8},
        "large_bank": False
    },
    {
        "code": "C",
        "asset": { "total": 150, "cash": 15, "interbank_asset": 15, "external_asset": 120},
        "liability": { "total": 150, "deposit":  95,  "interbank_liability": 30, "equity": 25},
        "growth_rate": {
            "deposit": { "mean": 0.01, "var": 0.02},
            "external_asset": { "mean": 0.015, "var": 0.025},
            "equity": { "mean": 0.02, "var": 0.01}
        }, "short_term_lending_rate": 0.8,
        "short_term_borrowing_rate": 0.8,
        "lending_target_rate": 0.2,
        "borrowing_target_rate": 0.2,
        "recover_rate": {"min": 0.5, "max": 0.8},
        "large_bank": False
    }
]

lending_borrowing_matrix = {
    "A": { "A": 0, 	"B": 20, "C": 30 },
    "B": { "A": 10, "B":  0, "C":  0 },
    "C": { "A": 10, "B":  5, "C":  0 }
}