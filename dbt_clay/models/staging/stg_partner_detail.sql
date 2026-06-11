-- staging: clean the enriched per-partner detail rows.

with source as (
    select * from {{ ref('raw_partners_detail') }}
),

cleaned as (
    select
        slug,
        nullif(trim(location), '')        as location,
        nullif(trim(expertise), '')       as expertise,
        nullif(trim(icps), '')            as icps,
        nullif(trim(industry), '')        as industry,
        nullif(trim(language), '')        as language,
        nullif(trim(pricing), '')         as pricing,
        nullif(trim(min_engagement), '')  as min_engagement,
        cast(description_len as integer)  as description_len,
        cast(mentions_ex_clay as integer)     as is_ex_clay_founder,
        cast(mentions_hubspot as integer)     as mentions_hubspot,
        cast(mentions_salesforce as integer)  as mentions_salesforce
    from source
)

select * from cleaned
