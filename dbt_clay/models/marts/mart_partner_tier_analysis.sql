-- mart: analysis-ready table answering "what distinguishes higher-tier partners?"
-- Uses window functions to rank and benchmark within tiers -- exactly the kind
-- of SQL the Clay JD calls out (CTEs, window functions, clear structure).

with features as (
    select * from {{ ref('int_partner_features') }}
),

tier_benchmarks as (
    select
        *,
        -- how does this partner's expertise breadth compare within its tier?
        avg(expertise_count) over (partition by tier)            as avg_expertise_in_tier,
        expertise_count
            - avg(expertise_count) over (partition by tier)      as expertise_vs_tier_avg,

        -- rank partners by description richness within their tier
        row_number() over (
            partition by tier order by description_len desc
        )                                                        as richness_rank_in_tier,

        -- share of ex-Clay founders within each tier
        avg(is_ex_clay_founder) over (partition by tier)         as pct_ex_clay_in_tier,

        -- region concentration: count of partners per region
        count(*) over (partition by region)                     as partners_in_region
    from features
)

select
    slug,
    partner_name,
    tier,
    tier_rank,
    is_elite,
    region,
    partners_in_region,
    expertise_count,
    round(avg_expertise_in_tier, 2)   as avg_expertise_in_tier,
    round(expertise_vs_tier_avg, 2)   as expertise_vs_tier_avg,
    richness_rank_in_tier,
    is_ex_clay_founder,
    round(pct_ex_clay_in_tier, 3)     as pct_ex_clay_in_tier,
    mentions_hubspot,
    mentions_salesforce,
    profile_url
from tier_benchmarks
order by tier_rank desc, richness_rank_in_tier
