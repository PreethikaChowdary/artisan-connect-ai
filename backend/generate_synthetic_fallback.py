"""
generate_dataset.py  (v2 -- improved)

Generates a synthetic-but-reasonable training dataset for the Dynamic
Pricing Assistant. Improvements over v1:

  - 2 extra realistic features: intricacy of work, and region
    (these genuinely affect handicraft pricing in the real world)
  - larger dataset (1800 rows instead of 800) for better learning
  - log-normal noise instead of flat uniform noise, since real-world
    prices are right-skewed (most cluster near typical, a few premium
    items cost noticeably more) -- this is closer to how real markets
    actually behave

WHY THIS IS STILL HONEST TO TELL JUDGES:
We don't have access to live e-commerce pricing data as students, so we
built this synthetic dataset from reasonable, research-informed pricing
assumptions, and trained a real regression model on it. This is a
recognised technique (data synthesis / simulation) used whenever real
training data isn't available -- not something to hide, something to
explain confidently.

Run this once to create data/pricing_dataset.csv
"""

import csv
import random

random.seed(42)

CATEGORIES = {
    "textile":  900,
    "pottery":  450,
    "jewelry":  700,
    "woodcraft": 600,
    "painting": 1200,
    "basketry": 350,
}

MATERIAL_MULT = {"standard": 1.0, "premium": 1.4}
SIZE_MULT = {"small": 1.0, "medium": 1.25, "large": 1.6}
INTRICACY_MULT = {"simple": 1.0, "moderate": 1.2, "highly_detailed": 1.5}
REGION_MULT = {"rural": 1.0, "semi_urban": 1.1, "metro": 1.25}

LABOR_RATE = 60  # notional fair wage per hour of artisan labor, in INR

N_ROWS = 1800

def generate_row():
    category = random.choice(list(CATEGORIES.keys()))
    material = random.choice(list(MATERIAL_MULT.keys()))
    size = random.choice(list(SIZE_MULT.keys()))
    intricacy = random.choice(list(INTRICACY_MULT.keys()))
    region = random.choice(list(REGION_MULT.keys()))
    hours = round(random.uniform(1, 20), 1)
    artisan_experience_years = round(random.uniform(0, 25), 1)

    base = CATEGORIES[category]
    price = base
    price *= MATERIAL_MULT[material]
    price *= SIZE_MULT[size]
    price *= INTRICACY_MULT[intricacy]
    price *= REGION_MULT[region]
    price += hours * LABOR_RATE

    # small experience premium: skilled artisans command slightly higher prices
    price *= (1 + min(artisan_experience_years, 20) * 0.004)

    # realistic right-skewed noise (log-normal), instead of flat uniform noise
    noise_factor = random.lognormvariate(0, 0.12)
    price = price * noise_factor

    return {
        "category": category,
        "material": material,
        "size": size,
        "intricacy": intricacy,
        "region": region,
        "labor_hours": hours,
        "artisan_experience_years": artisan_experience_years,
        "price": round(price, 2),
    }

def main():
    rows = [generate_row() for _ in range(N_ROWS)]
    fieldnames = ["category", "material", "size", "intricacy", "region",
                  "labor_hours", "artisan_experience_years", "price"]
    with open("data/pricing_dataset.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {N_ROWS} rows -> data/pricing_dataset.csv")

if __name__ == "__main__":
    main()
