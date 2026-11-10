"""
Sample Dataset Generator
Generates realistic CSV datasets with varied distributions (skewed, normal, discrete),
categorical dimensions, dates, and intentional missing (null) values to test
Polars data processing, summary statistics computation, and dashboard visualizations.
"""

import os
import csv
import math
import random
from datetime import datetime, timedelta

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_data")


def ensure_sample_dir():
    os.makedirs(SAMPLE_DIR, exist_ok=True)


def generate_ecommerce_data(filename="ecommerce_orders.csv", num_records=2500):
    """
    Generates an e-commerce order dataset with deliberate right-skewed sales amounts,
    customer ratings with nulls, discounts with zero/null inflation, and profit margins.
    """
    filepath = os.path.join(SAMPLE_DIR, filename)
    random.seed(42)

    segments = ["Consumer", "Corporate", "Home Office", "Small Business"]
    regions = ["North", "South", "East", "West", "Central"]
    categories = {
        "Technology": ["Laptops", "Smartphones", "Accessories", "Printers", "Monitors"],
        "Furniture": ["Chairs", "Desks", "Bookcases", "Furnishings"],
        "Office Supplies": ["Paper", "Binders", "Storage", "Art", "Appliances"],
    }
    cat_keys = list(categories.keys())

    start_date = datetime(2024, 1, 1)

    fieldnames = [
        "order_id",
        "order_date",
        "customer_segment",
        "region",
        "category",
        "sub_category",
        "sales_amount",
        "quantity",
        "discount_pct",
        "profit",
        "shipping_cost",
        "shipping_days",
        "customer_rating",
        "return_status",
    ]

    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for i in range(1, num_records + 1):
            order_id = f"ORD-{10000 + i}"
            random_days = random.randint(0, 364)
            order_date = (start_date + timedelta(days=random_days)).strftime("%Y-%m-%d")

            segment = random.choices(segments, weights=[0.45, 0.30, 0.15, 0.10])[0]
            region = random.choice(regions)
            category = random.choices(cat_keys, weights=[0.40, 0.25, 0.35])[0]
            sub_category = random.choice(categories[category])

            # Positively skewed log-normal sales distribution
            # Produces many small sales ($20 - $200) and rare large sales ($1,000 - $4,500)
            raw_sales = math.exp(random.gauss(5.2, 0.95))
            sales_amount = round(max(9.99, min(raw_sales, 4999.0)), 2)

            # Discrete skewed quantity (1-12)
            quantity = random.choices(
                [1, 2, 3, 4, 5, 6, 8, 10, 12],
                weights=[0.35, 0.25, 0.15, 0.08, 0.06, 0.04, 0.03, 0.02, 0.02],
            )[0]

            # Discounts: 50% have no discount, 10% null, remaining 0.05-0.30
            disc_roll = random.random()
            if disc_roll < 0.45:
                discount_pct = 0.0
            elif disc_roll < 0.55:
                discount_pct = ""  # null count test
            else:
                discount_pct = round(random.choice([0.05, 0.10, 0.15, 0.20, 0.25, 0.30]), 2)

            # Profit calculation: margin depends on category, reduced by discount
            base_margin = 0.28 if category == "Technology" else (0.35 if category == "Office Supplies" else 0.18)
            eff_disc = float(discount_pct) if discount_pct != "" else 0.0
            actual_margin = base_margin - (eff_disc * 1.2) + random.uniform(-0.08, 0.08)
            profit = round(sales_amount * actual_margin, 2)

            # Shipping cost: right-skewed
            shipping_cost = round(max(3.50, min(math.exp(random.gauss(2.6, 0.6)), 120.0)), 2)
            shipping_days = random.choices([1, 2, 3, 4, 5, 6, 7, 10, 14], weights=[0.1, 0.2, 0.3, 0.2, 0.1, 0.05, 0.02, 0.02, 0.01])[0]

            # Customer rating: 1.0 to 5.0 with ~12% nulls (unrated orders)
            if random.random() < 0.12:
                customer_rating = ""  # null
            else:
                # Slightly left-skewed ratings (satisfied customers)
                raw_rating = random.choices([1.0, 2.0, 3.0, 4.0, 5.0], weights=[0.05, 0.07, 0.15, 0.38, 0.35])[0]
                customer_rating = round(raw_rating, 1)

            # Return status: 8% returned, 4% pending, rest completed
            return_roll = random.random()
            if return_roll < 0.08:
                return_status = "Returned"
            elif return_roll < 0.12:
                return_status = "Pending"
            else:
                return_status = "Completed"

            writer.writerow({
                "order_id": order_id,
                "order_date": order_date,
                "customer_segment": segment,
                "region": region,
                "category": category,
                "sub_category": sub_category,
                "sales_amount": sales_amount,
                "quantity": quantity,
                "discount_pct": discount_pct,
                "profit": profit,
                "shipping_cost": shipping_cost,
                "shipping_days": shipping_days,
                "customer_rating": customer_rating,
                "return_status": return_status,
            })

    print(f"Generated {num_records} records in: {filepath}")
    return filepath


def generate_employee_data(filename="employee_metrics.csv", num_records=1200):
    """
    Generates an HR & Employee Metrics dataset with salary distributions,
    experience levels, performance scores, overtime, and nulls in bonuses.
    """
    filepath = os.path.join(SAMPLE_DIR, filename)
    random.seed(99)

    departments = [
        "Engineering",
        "Sales",
        "Marketing",
        "Finance",
        "Human Resources",
        "Product",
        "Customer Support",
    ]
    roles = {
        "Engineering": ["Software Engineer", "DevOps Engineer", "QA Engineer", "Staff Engineer", "Engineering Manager"],
        "Sales": ["Account Executive", "Sales Representative", "SDR", "Sales Director"],
        "Marketing": ["Content Specialist", "Growth Marketer", "SEO Analyst", "Brand Manager"],
        "Finance": ["Financial Analyst", "Accountant", "Finance Manager", "Controller"],
        "Human Resources": ["HR Generalist", "Recruiter", "People Partner", "HR Director"],
        "Product": ["Product Manager", "UX Designer", "Product Ops", "VP Product"],
        "Customer Support": ["Support Specialist", "Tier 2 Support", "Support Lead"],
    }
    arrangements = ["Remote", "Hybrid", "On-site"]

    fieldnames = [
        "employee_id",
        "department",
        "job_title",
        "years_experience",
        "base_salary",
        "bonus_amount",
        "performance_score",
        "work_arrangement",
        "overtime_hours_month",
        "satisfaction_index",
    ]

    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for i in range(1, num_records + 1):
            employee_id = f"EMP-{1000 + i}"
            dept = random.choice(departments)
            title = random.choice(roles[dept])

            # Experience: 0 to 25 years with slight positive skew
            exp = round(max(0.5, min(random.expovariate(1 / 6.0), 28.0)), 1)

            # Base salary: positively skewed log-normal, influenced by experience & dept
            dept_factor = 1.25 if dept in ["Engineering", "Product"] else (1.10 if dept == "Finance" else 0.95)
            exp_factor = 1.0 + (exp * 0.04)
            base_noise = math.exp(random.gauss(10.9, 0.28))
            base_salary = round((base_noise * dept_factor * exp_factor) / 100) * 100
            base_salary = max(42000.0, min(base_salary, 285000.0))

            # Bonus amount: 22% have no bonus (null), others are positively skewed
            if random.random() < 0.22:
                bonus_amount = ""  # null value
            else:
                bonus_pct = random.uniform(0.05, 0.25)
                bonus_amount = round(base_salary * bonus_pct, 2)

            # Performance score: 1.0 to 5.0 (normal distribution centered around 3.6)
            perf = round(max(1.0, min(random.gauss(3.6, 0.7), 5.0)), 2)

            # Work arrangement
            arrangement = random.choices(arrangements, weights=[0.40, 0.45, 0.15])[0]

            # Overtime hours per month: zero-inflated and right skewed
            if random.random() < 0.50:
                overtime = 0.0
            else:
                overtime = round(max(1.0, min(random.expovariate(1 / 8.0), 60.0)), 1)

            # Satisfaction index (10-100) with 6% nulls
            if random.random() < 0.06:
                satisfaction = ""  # null
            else:
                satisfaction = round(max(15, min(random.gauss(74, 14), 100)))

            writer.writerow({
                "employee_id": employee_id,
                "department": dept,
                "job_title": title,
                "years_experience": exp,
                "base_salary": base_salary,
                "bonus_amount": bonus_amount,
                "performance_score": perf,
                "work_arrangement": arrangement,
                "overtime_hours_month": overtime,
                "satisfaction_index": satisfaction,
            })

    print(f"Generated {num_records} records in: {filepath}")
    return filepath


def main():
    print("=" * 60)
    print(" Generating Sample CSV Datasets for Polars Dashboard")
    print("=" * 60)
    ensure_sample_dir()
    f1 = generate_ecommerce_data()
    f2 = generate_employee_data()
    print("=" * 60)
    print("Datasets generated successfully in 'sample_data/' directory:")
    print(f"  1. {os.path.basename(f1)}")
    print(f"  2. {os.path.basename(f2)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
