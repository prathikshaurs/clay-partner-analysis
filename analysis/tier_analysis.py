"""
Partner Tier Analysis -- standalone (no warehouse required)
===========================================================
"""

from pathlib import Path
import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"


def main():
    list_csv = PROCESSED / "partners_list.csv"
    detail_csv = PROCESSED / "partners_detail.csv"

    if not list_csv.exists():
        raise SystemExit("Run scraper/scrape_partners.py --detail first.")

    con = duckdb.connect()
    con.execute(f"create table plist as select * from read_csv_auto('{list_csv}')")
    con.execute(f"create table pdetail as select * from read_csv_auto('{detail_csv}')")

    print("\n=== 1. Tier pyramid ===")
    print(con.execute("""
        select tier, count(*) as n_partners,
               round(count(*) * 100.0 / sum(count(*)) over (), 1) as pct_of_total
        from plist
        group by tier, tier_rank
        order by tier_rank desc
    """).fetchdf().to_string(index=False))

    print("\n=== 2. Expertise breadth by tier ===")
    print(con.execute("""
        select l.tier, l.tier_rank,
               round(avg(
                   length(d.expertise) - length(replace(d.expertise, ',', '')) + 1
               ), 1) as avg_expertise_tags,
               round(avg(d.description_len), 0) as avg_profile_length
        from plist l
        join pdetail d on l.slug = d.slug
        where d.expertise != ''
        group by l.tier, l.tier_rank
        order by l.tier_rank desc
    """).fetchdf().to_string(index=False))

    print("\n=== 3. Language coverage by tier (multilingual = more global?) ===")
    print(con.execute("""
        select l.tier, l.tier_rank,
               round(avg(
                   length(d.language) - length(replace(d.language, ',', '')) + 1
               ), 2) as avg_languages
        from plist l
        join pdetail d on l.slug = d.slug
        where d.language != ''
        group by l.tier, l.tier_rank
        order by l.tier_rank desc
    """).fetchdf().to_string(index=False))

    print("\n=== 4. Most common ICPs at Elite vs Artisan tier ===")
    print(con.execute("""
        select l.tier, d.icps
        from plist l
        join pdetail d on l.slug = d.slug
        where l.tier in ('Elite Studio', 'Artisan')
          and d.icps != ''
        order by l.tier desc
    """).fetchdf().to_string(index=False))

    print("\n=== 5. HubSpot + Salesforce mentions by tier ===")
    print(con.execute("""
        select l.tier, l.tier_rank,
               round(avg(d.mentions_hubspot), 3)    as pct_mentions_hubspot,
               round(avg(d.mentions_salesforce), 3) as pct_mentions_salesforce
        from plist l
        join pdetail d on l.slug = d.slug
        group by l.tier, l.tier_rank
        order by l.tier_rank desc
    """).fetchdf().to_string(index=False))

    print("\n=== 6. Min engagement by tier (commitment level proxy) ===")
    print(con.execute("""
        select l.tier, l.tier_rank,
               split_part(d.min_engagement, ',', 1) as min_engagement_raw,
               count(*) as n
        from plist l
        join pdetail d on l.slug = d.slug
        where d.min_engagement != ''
        group by l.tier, l.tier_rank, min_engagement_raw
        order by l.tier_rank desc, n desc
    """).fetchdf().to_string(index=False))


if __name__ == "__main__":
    main()