"""Research-grounded demographic-profile cards for venue Lead-with paragraphs.

Each card represents a recognizable audience pattern (e.g. young renter
Democrats, working-class Hispanic households, senior owner-occupied
neighborhoods) and carries:

  - `triggers`: function over a metrics dict that decides whether the card
    fires for a given catchment, and how strongly.
  - `roles`: which paragraph slots the card can fill — ANCHOR (opening
    demographic anchor), BODY (top-concern statements), POLITICAL (partisan
    context), ENGAGEMENT (turnout / trend note), CAVEAT (less-likely-to-drive
    framing).
  - `anchor_variants` / `body_variants` / etc.: 3-5 prose snippets per card
    so paragraphs don't all open the same way. The generator picks one
    deterministically per venue (hash of venue id) so the output is stable
    across re-runs but varied across venues.

Two-layer grounding:
  - Demographic-level priorities come from publicly documented polling
    regularities — PPIC Statewide Survey, Pew political typology, AP-NORC
    issue-importance tracking, ANES "most important problem" series,
    Gallup MoMP. We lean on directional patterns, not fabricated numbers.
  - Local-government items referenced (sewer assessments, Warren v.
    Chico homelessness litigation, Park & Go downtown parking, low-income
    sewer rate program, tenant-protections ordinances, e-bike regulation,
    Greenfield/Hubbard housing approvals, Bidwell Park stewardship) come
    from a 6-meeting sample of Chico city council agendas pulled from
    chico-ca.granicus.com (April 2025 – May 2026). What we surface as a
    "council priority" is what the council has actually recently decided
    on or scheduled for decision.

Things NOT in council jurisdiction (referenced only as cross-pressures or
explicitly disclaimed in the prose): K-12 schools (CUSD), recreation
programming (CARD), mental-health services (Butte County Behavioral
Health), healthcare access, higher education (CSU/Butte College), federal
immigration enforcement (sanctuary policy is the local-decision proxy).

Design intent: the generator picks ~2-3 firing cards per catchment, weaves
their variants together, and produces ~120-180-word paragraphs that don't
read as templated. Hand-written Lead-with for the top-10 venues per district
live in src/candidate/narratives.ts and override these for the very best
venues.
"""
from __future__ import annotations

import hashlib
from typing import Callable

# ============================================================
# Card roles — which paragraph slot a card can fill.
# A single card may fill multiple roles (e.g. an anchor card also
# contributes body concerns).
# ============================================================

ROLE_ANCHOR = "anchor"
ROLE_BODY = "body"
ROLE_POLITICAL = "political"
ROLE_ENGAGEMENT = "engagement"
ROLE_CAVEAT = "caveat"

# body_kind values — controls how multiple BODY cards combine.
# "comprehensive" cards list the full top-concerns stack for an audience pattern.
# Only ONE comprehensive body lands per paragraph (the anchor's), even if
# multiple comprehensive cards trigger, because their issue lists overlap.
# "supplemental" cards add a single nuance (bimodal income mix, active-commute
# share) on top — up to 2 supplemental bodies may stack.
BODY_COMPREHENSIVE = "comprehensive"
BODY_SUPPLEMENTAL = "supplemental"


def pct(x: float) -> str:
    return f"{round(x * 100)}%"


def _pick(variants: list[str], seed: str) -> str:
    """Pick a variant deterministically based on `seed`."""
    if not variants:
        return ""
    idx = int(hashlib.sha256(seed.encode()).hexdigest(), 16) % len(variants)
    return variants[idx]


# ============================================================
# CARDS
# ============================================================
# Each card is a dict. The generator scores all cards against a catchment's
# metrics, picks the best-fitting ones per role, and renders.
#
# Anchor variants use {placeholders} that get filled from the metrics dict.
# Body variants are pre-formatted prose; pick the one whose tone fits.
# ============================================================

CARDS: list[dict] = [
    # --------------------------------------------------------
    # YOUNG_DEM_RENTER — young, heavily renter, Democratic-leaning
    # The dominant urban-Dem pattern in PPIC tracking
    # --------------------------------------------------------
    {
        "id": "young_dem_renter",
        "name": "Young Democratic-leaning renters",
        "triggers": lambda m: (
            m["young_share"] >= 0.35
            and m["renter_share"] >= 0.60
            and m["d_share_24"] >= 0.45
        ),
        "score": lambda m: m["young_share"] + m["renter_share"] / 2 + m["d_share_24"] / 2,
        "roles": [ROLE_ANCHOR, ROLE_BODY, ROLE_CAVEAT],
        "anchor_variants": [
            "A young ({young_share} age 18-34), heavily renter ({renter_share}), Democratic-leaning audience ({d_share_24} D / {r_share_24} R / {npp_share_24} NPP)",
            "Younger renter-majority audience: {young_share} of residents are 18-34, {renter_share} rent, and registration leans Democratic ({d_share_24} D / {r_share_24} R)",
            "The audience here skews young ({young_share} age 18-34) and heavily renter ({renter_share}), with strong Democratic registration ({d_share_24} D / {r_share_24} R)",
        ],
        "body_variants": [
            "Local-government priorities for this demographic typically center on tenant protections and code enforcement on existing rentals, housing supply (downtown infill, Greenfield-style bond issuances), public safety (homelessness response in the Warren v. Chico framing, policing accountability), and active-transportation infrastructure (e-bike regulation, micromobility). Mental-health services sit with Butte County, not council.",
            "Council-jurisdiction priorities for younger Democratic renters cluster around tenant protections, housing supply (council-approved bond issuances, downtown infill, rezones), public safety framed as homelessness response and policing accountability, downtown vitality (Park & Go, ground-floor uses), and active-transportation infrastructure.",
            "On items the council actually decides, this audience typically weights tenant protections, housing supply (downtown infill, Greenfield-style affordable-housing bonds), public safety in the homelessness-response framing, active-transportation infrastructure, and sanctuary policy where relevant.",
        ],
        "caveat_variants": [
            "Topics less likely to move this audience: traditional fiscal-conservative framing, anti-density arguments, national-grievance topics, culture-war wedges.",
            "Less likely to drive votes here: anti-density framing, abstract fiscal arguments, national-grievance topics from either direction, culture-war wedges.",
            "Framing that typically underperforms with this demographic: anti-density arguments, traditional fiscal-conservative messaging, national-grievance topics, culture-war wedges.",
        ],
    },

    # --------------------------------------------------------
    # AFFLUENT_DEM_OWNER — affluent, college-educated, owner-occupied D-leaning
    # --------------------------------------------------------
    {
        "id": "affluent_dem_owner",
        "name": "Affluent college-educated Democratic owners",
        "triggers": lambda m: (
            m["d_share_24"] >= 0.42
            and m["owner_share"] >= 0.60
            and m["high_income_share"] >= 0.30
            and m["college_share"] >= 0.45
        ),
        "score": lambda m: m["high_income_share"] + m["owner_share"] / 2 + m["d_share_24"] / 2,
        "roles": [ROLE_ANCHOR, ROLE_BODY, ROLE_CAVEAT],
        "anchor_variants": [
            "An affluent, college-educated, owner-occupied Democratic-leaning audience ({high_income_share} in $125k+, {college_share} bachelor+, {owner_share} own)",
            "College-educated affluent homeowner audience ({owner_share} own, {college_share} bachelor+, {high_income_share} in $125k+) with Democratic registration ({d_share_24} D / {r_share_24} R)",
            "Settled affluent professional Democratic audience: {owner_share} own their homes, {high_income_share} earn $125k+, and {college_share} hold a bachelor's or higher",
        ],
        "body_variants": [
            "Local-government priorities for this demographic typically center on government competence (City Manager / Attorney recruitment, budget rigor, labor MOUs), public safety (Police Department reports, Warren v. Chico framing of homelessness), infrastructure reliability (sewer assessments, street rehabilitation, property acquisitions), and Bidwell Park stewardship. K-12 schools sit with CUSD, not council.",
            "Council-jurisdiction priorities cluster around government competence and administrative quality, public safety (Police annual reports, homelessness response), infrastructure (sewer enterprise study, street rehab, capital projects), and quality of new development (impact fees, zoning). Healthcare is not council-decided; schools sit with CUSD.",
            "On items the council actually decides, this audience typically weights government competence, public safety, infrastructure reliability, Bidwell Park stewardship, and quality-of-development decisions (impact fees, zoning). Climate has higher stated importance here than in other affluent clusters but rarely surfaces on council agendas.",
        ],
        "caveat_variants": [
            "Less likely to drive votes here: housing supply arguments (rarely vote-driving for owners), national-grievance framing, anti-tax appeals.",
            "Topics that typically don't move this audience: housing supply framing (owners aren't economically squeezed by it), national-grievance topics from either direction, abstract anti-tax framing.",
            "Less likely to move votes: housing-supply framing (low salience for owners), national-grievance topics, abstract anti-tax messaging.",
        ],
    },

    # --------------------------------------------------------
    # SENIOR_OWNER_TRADITIONAL — older, established homeowners
    # --------------------------------------------------------
    {
        "id": "senior_owner_traditional",
        "name": "Senior owner-occupied audience",
        "triggers": lambda m: (
            m["senior_share"] >= 0.22 and m["owner_share"] >= 0.60
        ),
        "score": lambda m: m["senior_share"] * 1.5 + m["owner_share"] / 2,
        "roles": [ROLE_ANCHOR, ROLE_BODY, ROLE_CAVEAT],
        "anchor_variants": [
            "An older, established homeowner audience ({senior_share} age 65+, {owner_share} own)",
            "Senior-skewing homeowner cluster: {senior_share} of residents are 65+, {owner_share} own their homes",
            "Settled, older homeowner audience ({senior_share} age 65+, {owner_share} own)",
        ],
        "body_variants": [
            "Local-government priorities for this demographic typically center on public safety (Police Department reports, Warren v. Chico framing of homelessness response), infrastructure reliability (sewer assessments, street rehabilitation), property taxes and Prop 218 assessments, and government competence. Healthcare is not council-decided.",
            "Council-jurisdiction priorities cluster around public safety, infrastructure (sewer enterprise, street rehab, property acquisitions for road projects), government competence (City Manager and Attorney recruitment, budget rigor), and property-tax / assessment-district decisions.",
            "On items the council actually decides, this audience typically weights public safety, sewer and street infrastructure, property taxes and Prop 218 procedures, government competence, and Bidwell Park stewardship.",
        ],
        "caveat_variants": [
            "Less likely to drive votes here: housing supply framing, climate (high stated importance but historically low vote-driving salience for this cohort).",
            "Topics that typically don't move this audience locally: housing supply arguments, climate (stated importance exceeds revealed for older cohorts).",
            "Framing less likely to drive votes: housing supply, climate (high stated, low revealed salience for older voters).",
        ],
    },

    # --------------------------------------------------------
    # WORKING_CLASS_HISPANIC — Hispanic-majority or Spanish-meaningful working-class
    # --------------------------------------------------------
    {
        "id": "working_class_hispanic",
        "name": "Working-class Hispanic audience",
        "triggers": lambda m: (
            (m["hispanic_share"] >= 0.25 or m["spanish_share"] >= 0.12)
            and m["low_income_share"] >= 0.30
        ),
        "score": lambda m: m["hispanic_share"] + m["spanish_share"] + m["low_income_share"] / 2,
        "roles": [ROLE_ANCHOR, ROLE_BODY, ROLE_CAVEAT],
        "anchor_variants": [
            "A working-class audience with significant Hispanic share ({hispanic_share} Hispanic, {spanish_share} Spanish-at-home) and a low-income skew ({low_income_share} of households under $50k)",
            "Working-class, Hispanic-meaningful audience: {hispanic_share} Hispanic, {spanish_share} Spanish-at-home, {low_income_share} under $50k income",
            "{hispanic_share}-Hispanic working-class audience with {spanish_share} speaking Spanish at home and {low_income_share} of households under $50k",
        ],
        "body_variants": [
            "Local-government priorities for this demographic typically center on cost of living and utility rates (low-income sewer rate program is a recent council item), tenant protections and code enforcement on existing rentals, public safety in concrete terms (not abstract crime statistics), sanctuary policy / equitable enforcement, and jobs / local-economy decisions. K-12 sits with CUSD, not council, though parents conflate them.",
            "Council-jurisdiction priorities cluster around utility rates and fees (the low-income sewer rate program addresses this directly), tenant protections, public safety framed concretely, sanctuary-policy decisions, and local business / development climate. Healthcare and federal immigration enforcement are not council-decided.",
            "On items the council actually decides, this audience typically weights cost of living and utility rates, tenant protections, code enforcement on rentals, public safety, sanctuary policy / equitable enforcement, and jobs / local economic development.",
        ],
        "caveat_variants": [
            "Hispanic working-class voters are not a monolithic Democratic bloc — values-aligned issues (faith, family, immigration framing) can move some voters toward Republicans, but cost-of-living and concrete-policy framing tend to favor Democrats. Spanish-language outreach is operationally important.",
            "Cross-pressure note: this demographic splits more than registration suggests on values issues (faith, family, immigration framing from a values lens). Cost-of-living and concrete-policy framing favors D; abstract progressive framing and climate underperform. Spanish-language outreach is operationally important.",
            "Cross-pressures here: Hispanic voters are not a Democratic monolith — economic and family/values framings cut both ways. Climate ranks low for vote-driving with working-class Hispanic voters. Spanish-language outreach is operationally important, not optional.",
        ],
    },

    # --------------------------------------------------------
    # WORKING_CLASS_RENTER — non-Hispanic, renter, working-class
    # --------------------------------------------------------
    {
        "id": "working_class_renter",
        "name": "Working-class renter audience",
        "triggers": lambda m: (
            m["renter_share"] >= 0.55
            and m["low_income_share"] >= 0.30
            and m["college_share"] < 0.40
            and m["hispanic_share"] < 0.30
        ),
        "score": lambda m: m["renter_share"] + m["low_income_share"],
        "roles": [ROLE_ANCHOR, ROLE_BODY, ROLE_CAVEAT],
        "anchor_variants": [
            "A working-class, heavily renter ({renter_share} renter, {low_income_share} of households under $50k) audience",
            "Renter-majority working/lower-middle income audience ({renter_share} rent, {low_income_share} under $50k)",
            "Working-class renter audience: {renter_share} of housing is rental, {low_income_share} of households earn under $50k",
        ],
        "body_variants": [
            "Local-government priorities for this demographic typically center on cost of living and utility rates (the low-income sewer rate program is a recent council item), tenant protections and code enforcement on existing rentals (recurring council theme), public safety, and jobs / local-economy decisions. K-12 sits with CUSD, not council.",
            "Council-jurisdiction priorities cluster around tenant protections, code enforcement on existing rentals, utility rates and fees, public safety, and local-economy / development decisions. Healthcare is not council-decided.",
            "On items the council actually decides, this audience typically weights tenant protections (recurring council attention), code enforcement on rentals, cost of living via utility rates and fees, public safety, and local economic development.",
        ],
        "caveat_variants": [
            "Less likely to move this audience: anti-density framing (renters here live in the housing supply being argued about), abstract fiscal-conservative messaging without specific costs named, climate (low vote-driving salience for working-class voters), national-grievance from either direction, culture-war wedges.",
            "Topics that typically don't drive votes here: anti-density arguments (housing supply IS where these voters live), abstract fiscal framing, climate, national-grievance topics, culture-war wedges from either side.",
            "Less likely to drive votes: anti-density framing, abstract fiscal-conservative arguments, climate (low revealed-importance for working-class voters), national-grievance topics, culture-war wedges.",
        ],
    },

    # --------------------------------------------------------
    # SF_OWNER_FAMILY — established single-family homeowner family audience
    # --------------------------------------------------------
    {
        "id": "sf_owner_family",
        "name": "Single-family homeowner family audience",
        "triggers": lambda m: (
            m["kids_share"] >= 0.20
            and m["owner_share"] >= 0.55
            and m["single_family_share"] >= 0.75
        ),
        "score": lambda m: m["kids_share"] + m["owner_share"] / 2 + m["single_family_share"] / 2,
        "roles": [ROLE_ANCHOR, ROLE_BODY],
        "anchor_variants": [
            "An established single-family-homeowner audience with a family skew ({kids_share} under 18, {owner_share} own, {single_family_share} single-family housing stock)",
            "Settled SF homeowner family audience ({owner_share} own, {single_family_share} single-family, {kids_share} of residents under 18)",
            "Single-family homeowner family-skewed audience: {owner_share} own, {single_family_share} SF housing stock, {kids_share} of residents are under 18",
        ],
        "body_variants": [
            "Local-government priorities for parent-heavy owners typically center on public safety (Police Department reports, Warren v. Chico framing of homelessness), infrastructure reliability (sewer assessments, street rehab), government competence, and quality of new development (impact fees, zoning). Housing affordability matters as 'options for our kids when they grow up.' K-12 schools sit with CUSD, not council, though parents conflate them.",
            "Council-jurisdiction priorities cluster around public safety, infrastructure (sewer and street capital projects), quality-of-development decisions (impact fees, zoning), and government competence. Schools sit with CUSD, not council, but salience is high for the parent share.",
            "On items the council actually decides, this audience typically weights public safety, infrastructure reliability, quality of new development (impact fees), and government competence. Housing affordability frames as 'good options for our kids when they grow up.'",
        ],
    },

    # --------------------------------------------------------
    # HEAVILY_DEM_PROFESSIONAL — heavily-D, college-educated, mixed-tenure
    # --------------------------------------------------------
    {
        "id": "heavily_dem_professional",
        "name": "Heavily Democratic professional audience",
        "triggers": lambda m: (
            m["d_share_24"] >= 0.50 and m["college_share"] >= 0.45
        ),
        "score": lambda m: m["d_share_24"] + m["college_share"] / 2,
        "roles": [ROLE_ANCHOR, ROLE_BODY, ROLE_CAVEAT],
        "anchor_variants": [
            "A heavily Democratic-leaning ({d_share_24} D / {r_share_24} R / {npp_share_24} NPP, Harris took {top_d_24}), college-educated ({college_share} bachelor+) audience",
            "Strongly Democratic college-educated audience ({d_share_24} D, {college_share} bachelor+, Harris took {top_d_24} in 2024)",
            "Heavily Democratic professional audience: {d_share_24} D registration, {college_share} bachelor+, Harris won {top_d_24} of the 2024 top-of-ticket vote",
        ],
        "body_variants": [
            "Local-government priorities for this demographic typically center on tenant protections and housing supply (downtown infill, Greenfield-style bonds, Hubbard-style rezones), public safety (homelessness response in the Warren v. Chico framing, policing accountability), downtown vitality (Park & Go, ground-floor uses), active-transportation infrastructure, and sanctuary policy where relevant.",
            "Council-jurisdiction priorities cluster around tenant protections, housing supply (council-approved bond issuances, downtown infill), public safety framed as homelessness response and policing accountability, downtown vitality, and active-transportation infrastructure. Climate has high stated importance here but rarely surfaces on council agendas.",
            "On items the council actually decides, this audience typically weights tenant protections, housing supply (infill, council-approved affordable-housing bonds), public safety (Warren v. Chico framing), downtown vitality and ground-floor-use decisions, and active-transportation infrastructure.",
        ],
        "caveat_variants": [
            "This audience is already partisan-aligned with a Democratic candidate; persuasion happens on competence and specificity rather than values. National-grievance and culture-war framing underperform; broad partisan signaling lands in friendly territory but won't differentiate.",
            "Cross-pressures here are low — the audience is solidly Democratic-aligned. Differentiator is competence and policy specifics, not values or framing. National-grievance topics and culture-war wedges underperform.",
            "The audience is solidly partisan-aligned; the persuasion challenge is competence and specificity, not values or framing. National-grievance topics, culture-war wedges, and broad partisan signaling underperform.",
        ],
    },

    # --------------------------------------------------------
    # STUDENT_DOMINANT — overwhelmingly student
    # --------------------------------------------------------
    {
        "id": "student_dominant",
        "name": "Student-dominant audience",
        "triggers": lambda m: m["young_share"] >= 0.60 and m["renter_share"] >= 0.80,
        "score": lambda m: m["young_share"] * 2 + m["renter_share"],
        "roles": [ROLE_ANCHOR, ROLE_BODY, ROLE_CAVEAT],
        "anchor_variants": [
            "An overwhelmingly student audience ({young_share} age 18-34, {renter_share} renter)",
            "Student-dominant audience: {young_share} of residents are 18-34, {renter_share} rent, {low_income_share} of households under $50k",
            "Predominantly student audience ({young_share} age 18-34, {renter_share} rental housing)",
        ],
        "body_variants": [
            "Local-government priorities for college students typically center on off-campus housing supply (council-approved bond issuances like Greenfield, Hubbard-style rezones), tenant protections, downtown vitality and ground-floor uses (Park & Go), active-transportation infrastructure (e-bike regulation, micromobility program), and police-student relations. Tuition and student debt are state/federal, not council. Mental-health services sit with Butte County.",
            "Council-jurisdiction priorities cluster around off-campus housing (council-approved bonds, infill, rezones), tenant protections, downtown vitality, active-transportation infrastructure, and police practices. College affordability and mental-health services are not council-decided.",
            "On items the council actually decides, this audience typically weights off-campus housing supply, tenant protections, downtown vitality and parking, active-transportation infrastructure (e-bike, micromobility), and police-student relations.",
        ],
        "caveat_variants": [
            "For pre-aligned student audiences, registration drives and absentee-ballot logistics often carry more electoral impact than persuasion messaging. National-grievance topics and culture-war framing underperform; broad partisan signaling lands in friendly territory but doesn't differentiate.",
            "Mobilization (registration drives, ballot logistics) typically has more ROI than persuasion for student audiences. National-grievance topics and culture-war wedges underperform.",
            "Mobilization beats persuasion for student audiences with high baseline alignment. National-grievance topics, culture-war wedges, and abstract fiscal framing underperform.",
        ],
    },

    # --------------------------------------------------------
    # MIXED_PARTISAN_RENTER — younger, mixed-D, renter
    # --------------------------------------------------------
    {
        "id": "mixed_partisan_renter",
        "name": "Mixed-partisan renter audience",
        "triggers": lambda m: (
            m["renter_share"] >= 0.45
            and 0.35 <= m["d_share_24"] < 0.50
            and m["young_share"] >= 0.20
        ),
        "score": lambda m: m["renter_share"] / 2 + m["young_share"],
        "roles": [ROLE_ANCHOR, ROLE_BODY, ROLE_CAVEAT],
        "anchor_variants": [
            "A younger renter-majority ({renter_share} renter, {young_share} age 18-34) audience with mixed-Democratic registration ({d_share_24} D / {r_share_24} R / {npp_share_24} NPP)",
            "Renter-majority younger audience ({renter_share} rent, {young_share} age 18-34) with moderate-Democratic registration ({d_share_24} D / {r_share_24} R)",
            "Younger, renter-leaning audience with mixed partisan composition ({renter_share} renter, {young_share} age 18-34, {d_share_24} D / {r_share_24} R)",
        ],
        "body_variants": [
            "Local-government priorities for this demographic typically center on cost of living and utility rates (low-income sewer rate program is a recent council item), tenant protections and code enforcement on existing rentals, public safety (homelessness response, police-community relations), and active-transportation infrastructure. K-12 sits with CUSD, not council.",
            "Council-jurisdiction priorities cluster around tenant protections, utility rates and fees, public safety framed concretely, and active-transportation infrastructure. Healthcare is not council-decided.",
            "On items the council actually decides, this audience typically weights tenant protections, cost of living via utility rates and fees, public safety (homelessness response), and active-transportation infrastructure.",
        ],
        "caveat_variants": [
            "Less likely to move this audience: anti-density framing (renters here live in the housing supply), national-grievance topics from either direction, culture-war wedges, climate (high stated importance but historically lower vote-driving salience for mixed-income voters).",
            "Topics that typically don't drive votes here: anti-density arguments, national-grievance framing, culture-war wedges, climate (stated importance exceeds vote-driving salience for mixed-income voters).",
            "Framing less likely to drive votes: anti-density, abstract fiscal arguments, national-grievance topics from either direction, culture-war wedges.",
        ],
    },

    # --------------------------------------------------------
    # MIXED_MODERATE_SUBURBAN — catch-all for mixed-demographic
    # moderately-Democratic neighborhoods that don't fit cleaner patterns.
    # Low score so more specific cards win when they apply.
    # --------------------------------------------------------
    {
        "id": "mixed_moderate_suburban",
        "name": "Mixed moderate-Democratic suburban audience",
        "triggers": lambda m: (
            m["reg24"] >= 100
            and m["d_share_24"] >= 0.35
            and m["pop"] >= 100
        ),
        "score": lambda m: 0.3,  # below the more specific cards
        "roles": [ROLE_ANCHOR, ROLE_BODY, ROLE_CAVEAT],
        "anchor_variants": [
            "A mixed-demographic neighborhood — {young_share} age 18-34, {renter_share} renter, {college_share} bachelor+, with moderately-Democratic registration ({d_share_24} D / {r_share_24} R / {npp_share_24} NPP)",
            "Mixed Chico-suburban audience with moderate-Democratic lean ({d_share_24} D / {r_share_24} R / {npp_share_24} NPP), {renter_share} renter, {young_share} age 18-34",
            "Mixed-demographic moderate-Democratic audience ({d_share_24} D / {r_share_24} R), neither distinctly young nor senior, neither heavily renter nor owner",
        ],
        "body_variants": [
            "Local-government priorities for this mixed audience typically center on cost of living and utility rates, public safety (Police Department reports, Warren v. Chico framing of homelessness), tenant protections (for the renter share) and infrastructure reliability (for the owner share), and government competence (City Manager / Attorney recruitment, budget rigor). K-12 sits with CUSD, not council.",
            "Council-jurisdiction priorities cluster around cost of living via fees and utility rates, public safety, tenant protections (renter share) and infrastructure (owner share), and government competence. Healthcare is not council-decided.",
            "On items the council actually decides, this audience typically weights cost of living and utility rates, public safety, housing-related concerns (tenant protections for renters, infrastructure for owners), and government competence.",
        ],
        "caveat_variants": [
            "Less likely to drive votes here: heavy partisan signaling, national-grievance topics from either direction, anti-density absolutism, culture-war wedges.",
            "Topics that typically don't move mixed-demographic audiences: national-grievance framing, heavy partisan signaling, anti-density-as-identity arguments, culture-war wedges.",
            "Framing less likely to drive votes: heavy partisan signaling, national-grievance framing, abstract ideological appeals.",
        ],
    },

    # --------------------------------------------------------
    # COMPETITIVE_REGISTRATION — close partisan split
    # Political slot only; doesn't anchor demographic-wise
    # --------------------------------------------------------
    {
        "id": "competitive_registration",
        "name": "Competitive partisan registration",
        "triggers": lambda m: (
            abs(m["d_share_24"] - m["r_share_24"]) <= 0.05 and m["reg24"] >= 100
        ),
        "score": lambda m: 1.0,  # constant — fires when triggered
        "roles": [ROLE_POLITICAL, ROLE_CAVEAT],
        "political_variants": [
            "Registration is competitive ({d_share_24} D / {r_share_24} R / {npp_share_24} NPP), with the catchment voting {top_d_24} D / {top_r_24} R at the top of the 2024 ticket.",
            "Partisan registration here is closely balanced ({d_share_24} D vs {r_share_24} R) — the top-of-ticket vote split {top_d_24} / {top_r_24} in 2024.",
            "Competitive registration ({d_share_24} D / {r_share_24} R), with 2024 top-of-ticket vote split {top_d_24} D / {top_r_24} R.",
        ],
        "caveat_variants": [
            "National-grievance framing (from either direction) typically under-performs in audiences where partisan registration is competitive.",
            "Heavy partisan signaling and national-grievance framing from either direction typically don't move competitive-registration audiences.",
            "In competitive-registration rooms, national-grievance topics from either side typically underperform.",
        ],
    },

    # --------------------------------------------------------
    # R_LEANING_COMPETITIVE — R registers > D, but recent vote D-leaning
    # --------------------------------------------------------
    {
        "id": "r_leaning_competitive",
        "name": "Republican-registered, top-of-ticket-Dem voting",
        "triggers": lambda m: (
            m["r_share_24"] > m["d_share_24"]
            and m["top_d_24"] > m["top_r_24"]
            and m["reg24"] >= 100
        ),
        "score": lambda m: 0.9,
        "roles": [ROLE_POLITICAL],
        "political_variants": [
            "Registration tilts Republican ({d_share_24} D / {r_share_24} R) but the catchment voted Democratic at the top of the ticket ({top_d_24} D / {top_r_24} R in 2024) — meaningful split-ticket / persuadable-R signal.",
            "Although Republicans hold a registration edge ({d_share_24} D / {r_share_24} R), the 2024 top-of-ticket vote favored Democrats ({top_d_24} D / {top_r_24} R) — moderate-R voters are persuadable.",
            "R-leaning registration ({d_share_24} D / {r_share_24} R) but D-leaning top-of-ticket vote ({top_d_24} D / {top_r_24} R in 2024) — substantial persuadable-moderate share.",
        ],
    },

    # --------------------------------------------------------
    # D_TRENDING — significant D shift between cycles
    # --------------------------------------------------------
    {
        "id": "d_trending",
        "name": "Democratic-trending catchment",
        "triggers": lambda m: (
            m["top_d_24"] - m["top_d_22"] >= 0.04
            and m["top_d_24"] > 0
            and m["top_d_22"] > 0
        ),
        "score": lambda m: m["top_d_24"] - m["top_d_22"],
        "roles": [ROLE_ENGAGEMENT],
        "engagement_variants": [
            "The catchment voted {trend_pts} points more Democratic at the top of the ticket in 2024 than in 2022 — consistent with broader young-renter or college-educated migration patterns; moderate-R voters in the catchment are persuadable on local issues.",
            "Top-of-ticket vote shifted {trend_pts} points more Democratic between 2022 and 2024 — a meaningful local trend consistent with statewide patterns. Moderate-R voters are persuadable.",
            "The 2022-to-2024 top-of-ticket shift was {trend_pts} points more Democratic — persuadable-moderate-R signal in the room.",
        ],
    },

    # --------------------------------------------------------
    # R_TRENDING — significant R shift between cycles
    # --------------------------------------------------------
    {
        "id": "r_trending",
        "name": "Republican-trending catchment",
        "triggers": lambda m: (
            m["top_d_22"] - m["top_d_24"] >= 0.04
            and m["top_d_24"] > 0
            and m["top_d_22"] > 0
        ),
        "score": lambda m: m["top_d_22"] - m["top_d_24"],
        "roles": [ROLE_ENGAGEMENT],
        "engagement_variants": [
            "The catchment voted {trend_pts} points more Republican at the top of the ticket in 2024 than in 2022 — consistent with the broader working-class realignment pattern observed in California in 2024.",
            "2022-to-2024 top-of-ticket shift was {trend_pts} points more Republican — meaningful local rightward movement.",
            "The catchment shifted {trend_pts} points toward Republicans at the top of the ticket between 2022 and 2024 — worth noting given the otherwise-stable local political identity.",
        ],
    },

    # --------------------------------------------------------
    # POLITICALLY_STABLE — minimal cycle-to-cycle shift
    # --------------------------------------------------------
    {
        "id": "politically_stable",
        "name": "Politically stable catchment",
        "triggers": lambda m: (
            abs(m["top_d_24"] - m["top_d_22"]) < 0.02
            and m["top_d_24"] > 0
            and m["top_d_22"] > 0
            and m["reg24"] >= 100
        ),
        "score": lambda m: 0.5,
        "roles": [ROLE_ENGAGEMENT],
        "engagement_variants": [
            "The 2022-vs-2024 top-of-ticket shift was negligible (~{trend_pts_abs} point), suggesting a stable local political identity.",
            "Cycle-to-cycle vote shift was minimal (~{trend_pts_abs} point), indicating an unusually stable local political identity.",
            "Top-of-ticket vote barely shifted between 2022 and 2024 (~{trend_pts_abs} point) — stable local political identity.",
        ],
    },

    # --------------------------------------------------------
    # HIGH_TURNOUT_ENGAGED — substance audience
    # --------------------------------------------------------
    {
        "id": "high_turnout_engaged",
        "name": "High-turnout engaged audience",
        "triggers": lambda m: m["turnout_24"] >= 0.80,
        "score": lambda m: m["turnout_24"],
        "roles": [ROLE_ENGAGEMENT],
        "engagement_variants": [
            "Turnout is high ({turnout_24} in 2024 vs Butte's 77%) — substance audience where specifics and policy depth differentiate more than framing.",
            "High turnout ({turnout_24} in 2024) signals deep civic engagement — assume the audience reads policy detail and weights it.",
            "{turnout_24} turnout in 2024 (well above Butte's 77%) — substance-and-specificity audience.",
        ],
    },

    # --------------------------------------------------------
    # LOW_TURNOUT_MOBILIZATION
    # --------------------------------------------------------
    {
        "id": "low_turnout_mobilization",
        "name": "Lower-turnout audience",
        "triggers": lambda m: 0 < m["turnout_24"] < 0.70,
        "score": lambda m: 1.0 - m["turnout_24"],
        "roles": [ROLE_ENGAGEMENT],
        "engagement_variants": [
            "Turnout is below the catchment average ({turnout_24}) — voter-engagement framing has real ROI alongside persuasion.",
            "Lower-than-average turnout ({turnout_24}) — mobilization framing carries weight alongside persuasion.",
            "{turnout_24} turnout signals room for voter-engagement work, not just persuasion.",
        ],
    },

    # --------------------------------------------------------
    # BIMODAL_INCOME — two distinct audiences in same room
    # --------------------------------------------------------
    {
        "id": "bimodal_income",
        "name": "Bimodal income distribution",
        "triggers": lambda m: (
            m["high_income_share"] >= 0.22 and m["low_income_share"] >= 0.30
        ),
        "score": lambda m: m["high_income_share"] + m["low_income_share"],
        "roles": [ROLE_BODY],
        "body_variants": [
            "Income is meaningfully bimodal ({low_income_share} under $50k, {high_income_share} in $125k+) — two distinct audiences in the same room. The affluent subset weights government competence and infrastructure; the lower-income subset weights cost of living, utility rates, and tenant protections. Public safety (Chico's homelessness response) bridges both.",
            "The income distribution here is bimodal ({low_income_share} under $50k vs {high_income_share} in $125k+) — affluent attendees and cost-stressed attendees weight different council items, but public safety (homelessness response) and cost of living are common ground.",
            "Bimodal income mix ({low_income_share} under $50k / {high_income_share} in $125k+) splits attendees into different top-issue lists, but Chico's homelessness response and cost of living bridge both subgroups.",
        ],
    },

    # --------------------------------------------------------
    # ACTIVE_COMMUTE — meaningful transit/bike/walk share
    # --------------------------------------------------------
    {
        "id": "active_commute",
        "name": "Active-commute audience",
        "triggers": lambda m: m["active_share"] >= 0.12,
        "score": lambda m: m["active_share"],
        "roles": [ROLE_BODY],
        "body_variants": [
            "The {active_share} active-commute share (transit/bike/walk — high for Chico) signals an audience for whom council items like e-bike regulation, the shared-micromobility program, and street-corridor design (South Park Drive, Park Avenue) are lived friction, not abstract policy.",
            "Meaningful active-commute share ({active_share} commute by bike/walk/transit) — council items like e-bike regulation, the micromobility program, and active-corridor design are lived issues here, not theoretical.",
            "{active_share} of workers commute actively (bike/walk/transit) — well above Chico norm — so council items on e-bike regulation, micromobility, and street-corridor design carry weight as concrete daily friction.",
        ],
    },
]


# ============================================================
# Card matching + paragraph composition
# ============================================================


def _trend_pts(m: dict) -> str:
    """Format absolute shift in top-of-ticket vote between 2022 and 2024."""
    if m.get("top_d_22", 0) > 0 and m.get("top_d_24", 0) > 0:
        return str(round(abs(m["top_d_24"] - m["top_d_22"]) * 100))
    return "0"


def _format(template: str, m: dict) -> str:
    """Fill {placeholder} tokens from metrics."""
    fields = {
        "young_share": pct(m.get("young_share", 0)),
        "senior_share": pct(m.get("senior_share", 0)),
        "kids_share": pct(m.get("kids_share", 0)),
        "renter_share": pct(m.get("renter_share", 0)),
        "owner_share": pct(m.get("owner_share", 0)),
        "single_family_share": pct(m.get("single_family_share", 0)),
        "multifamily_share": pct(m.get("multifamily_share", 0)),
        "college_share": pct(m.get("college_share", 0)),
        "high_income_share": pct(m.get("high_income_share", 0)),
        "low_income_share": pct(m.get("low_income_share", 0)),
        "hispanic_share": pct(m.get("hispanic_share", 0)),
        "spanish_share": pct(m.get("spanish_share", 0)),
        "white_share": pct(m.get("white_share", 0)),
        "active_share": pct(m.get("active_share", 0)),
        "rent_burdened_share": pct(m.get("rent_burdened_share", 0)),
        "d_share_24": pct(m.get("d_share_24", 0)),
        "r_share_24": pct(m.get("r_share_24", 0)),
        "npp_share_24": pct(m.get("npp_share_24", 0)),
        "top_d_24": pct(m.get("top_d_24", 0)),
        "top_r_24": pct(m.get("top_r_24", 0)),
        "turnout_24": pct(m.get("turnout_24", 0)),
        "trend_pts": _trend_pts(m),
        "trend_pts_abs": _trend_pts(m),
    }
    return template.format(**fields)


def match_cards(m: dict) -> list[tuple[dict, float]]:
    """Return all cards that fire for `m`, sorted by score descending."""
    matched = []
    for card in CARDS:
        try:
            if card["triggers"](m):
                matched.append((card, card["score"](m)))
        except (KeyError, ZeroDivisionError):
            continue
    matched.sort(key=lambda t: t[1], reverse=True)
    return matched


# Cards whose BODY contributions are *supplemental* (a single nuance) rather
# than *comprehensive* (a full top-concerns enumeration). Only one comprehensive
# body lands per paragraph (the anchor's), but up to 2 supplemental bodies may
# stack on top.
SUPPLEMENTAL_BODY_CARDS = {"bimodal_income", "active_commute"}


def _generic_anchor(m: dict) -> str:
    """Fallback opener when no demographic-pattern card fires.

    Used for catchments whose mix doesn't match any of the audience templates
    strongly — produces a still-useful paragraph from registration and
    turnout data.
    """
    bits = []
    if m.get("reg24", 0) >= 100:
        bits.append(
            f"registration is {pct(m['d_share_24'])} D / {pct(m['r_share_24'])} R / {pct(m['npp_share_24'])} NPP"
        )
    if m.get("turnout_24", 0) > 0:
        bits.append(f"turnout was {pct(m['turnout_24'])} in 2024")
    if bits:
        return f"This catchment doesn't fit a single audience template — {', and '.join(bits)}."
    return "This catchment doesn't fit a single audience template."


def compose_lead_with(m: dict, venue_id: str) -> str:
    """Compose a research-grounded Lead-with paragraph for `m`.

    Strategy:
      1. Match all firing cards, sorted by score.
      2. Pick best ANCHOR card → opening sentence + comprehensive issue body.
      3. Stack up to 2 supplemental BODY cards (e.g. bimodal income, active
         commute) — never two comprehensive bodies, because they overlap.
      4. Pick best POLITICAL card → partisan-context sentence.
      5. Pick best ENGAGEMENT card → turnout/trend sentence.
      6. Pick best CAVEAT card → "less-likely-to-drive" sentence.

    Always returns a non-empty paragraph (falls back to generic anchor +
    political/engagement when no demographic card fires).
    """
    matched = match_cards(m)

    anchors = [c for c, _ in matched if ROLE_ANCHOR in c["roles"]]
    politicals = [c for c, _ in matched if ROLE_POLITICAL in c["roles"]]
    engagements = [c for c, _ in matched if ROLE_ENGAGEMENT in c["roles"]]
    caveats = [c for c, _ in matched if ROLE_CAVEAT in c["roles"]]

    # Supplemental body cards only — comprehensive bodies are skipped to avoid
    # stacking redundant issue lists.
    supplementals = [
        c
        for c, _ in matched
        if ROLE_BODY in c["roles"] and c["id"] in SUPPLEMENTAL_BODY_CARDS
    ]

    parts: list[str] = []

    # --- Anchor ---
    if anchors:
        a = anchors[0]
        parts.append(
            _format(_pick(a["anchor_variants"], f"{venue_id}|anchor"), m) + "."
        )
        # Anchor card's own body (the comprehensive issue list).
        if ROLE_BODY in a["roles"] and a.get("body_variants"):
            parts.append(_format(_pick(a["body_variants"], f"{venue_id}|body"), m))
    else:
        parts.append(_generic_anchor(m))

    # --- Up to 2 supplemental bodies ---
    for i, s in enumerate(supplementals[:2]):
        if s.get("body_variants"):
            parts.append(_format(_pick(s["body_variants"], f"{venue_id}|sup{i}"), m))

    # --- Political ---
    if politicals and politicals[0].get("political_variants"):
        parts.append(
            _format(_pick(politicals[0]["political_variants"], f"{venue_id}|pol"), m)
        )

    # --- Engagement ---
    if engagements and engagements[0].get("engagement_variants"):
        parts.append(
            _format(_pick(engagements[0]["engagement_variants"], f"{venue_id}|eng"), m)
        )

    # --- Caveat (prefer anchor's caveat, fall back to any matched caveat) ---
    caveat_source = None
    if anchors and ROLE_CAVEAT in anchors[0]["roles"] and anchors[0].get("caveat_variants"):
        caveat_source = anchors[0]
    elif caveats:
        caveat_source = caveats[0]
    if caveat_source:
        parts.append(
            _format(_pick(caveat_source["caveat_variants"], f"{venue_id}|caveat"), m)
        )

    return " ".join(parts)
