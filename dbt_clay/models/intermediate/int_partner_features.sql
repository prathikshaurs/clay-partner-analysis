-- intermediate: join list + detail and derive the features we'll analyze.
-- This is where the "why" features live: the signals that might predict tier.

with partners as (
    select * from {{ ref('stg_partners') }}
),

detail as (
    select * from {{ ref('stg_partner_detail') }}
),

joined as (
    select
        p.slug,
        p.partner_name_raw          as partner_name,
        p.tier,
        p.tier_rank,
        p.profile_url,
        d.location,
        d.expertise,
        d.icps,
        d.industry,
        d.language,
        d.pricing,
        d.min_engagement,
        d.description_len,
        d.is_ex_clay_founder,
        d.mentions_hubspot,
        d.mentions_salesforce
    from partners p
    left join detail d on p.slug = d.slug
),

featured as (
    select
        *,
        -- derive a coarse region from the location string
        case
            when location ilike '%united states%' or location ilike '%usa%'
                 or location ilike '%, ca%' or location ilike '%new york%' then 'North America'
            when location ilike '%india%' then 'India'
            when location ilike '%uk%' or location ilike '%london%'
                 or location ilike '%germany%' or location ilike '%dach%'
                 or location ilike '%france%' or location ilike '%europe%' then 'Europe'
            when location ilike '%philippines%' or location ilike '%singapore%'
                 or location ilike '%asia%' then 'APAC'
            else 'Other / Unknown'
        end as region,

        -- count how many expertise tags the partner lists (richness proxy)
        case when expertise is null then 0
             else array_length(split(expertise, ','), 1)
        end as expertise_count,

        -- is this a top-tier partner? (the target variable for the analysis)
        case when tier_rank >= 4 then 1 else 0 end as is_elite
    from joined
)

select * from featured
