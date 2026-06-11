-- staging: clean and standardize the raw partner list.
-- One row per partner. Light typing and trimming only -- no business logic here.

with source as (
    select * from {{ ref('raw_partners_list') }}
),

cleaned as (
    select
        slug,
        profile_url,
        nullif(trim(tier), '')                       as tier,
        cast(tier_rank as integer)                   as tier_rank,
        -- pull a clean display name out of the noisy card text
        trim(split_part(card_text, '  ', 1))         as partner_name_raw
    from source
)

select * from cleaned
