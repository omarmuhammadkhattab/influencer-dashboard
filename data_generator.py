import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# ── Influencer Definitions ────────────────────────────────────────────────────
# Each influencer has a tier that drives their order volume and return rate.
# Tier A: large, engaged audience → high volume, low returns
# Tier B: medium audience        → medium volume, medium returns
# Tier C: misaligned audience    → low volume, high returns (not worth it)

INFLUENCERS = [
    # Tier A — worth it
    {"name": "Sarah",   "code": "SARAH15",  "discount": 15, "tier": "A", "monthly_orders": 420, "return_rate": 0.07},
    {"name": "Emma",    "code": "EMMA20",   "discount": 20, "tier": "A", "monthly_orders": 380, "return_rate": 0.09},
    {"name": "Lena",    "code": "LENA12",   "discount": 12, "tier": "A", "monthly_orders": 310, "return_rate": 0.08},
    {"name": "Max",     "code": "MAX10",    "discount": 10, "tier": "A", "monthly_orders": 290, "return_rate": 0.06},
    {"name": "Julia",   "code": "JULIA15",  "discount": 15, "tier": "A", "monthly_orders": 270, "return_rate": 0.10},
    {"name": "Felix",   "code": "FELIX10",  "discount": 10, "tier": "A", "monthly_orders": 250, "return_rate": 0.08},
    {"name": "Hannah",  "code": "HANNAH20", "discount": 20, "tier": "A", "monthly_orders": 230, "return_rate": 0.09},
    {"name": "Nico",    "code": "NICO12",   "discount": 12, "tier": "A", "monthly_orders": 210, "return_rate": 0.07},
    {"name": "Sophie",  "code": "SOPHIE15", "discount": 15, "tier": "A", "monthly_orders": 200, "return_rate": 0.11},
    {"name": "Tom",     "code": "TOM10",    "discount": 10, "tier": "A", "monthly_orders": 190, "return_rate": 0.06},
    # Tier B — border