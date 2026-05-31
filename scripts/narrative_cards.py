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

Polling references throughout are to publicly documented patterns from
PPIC's Statewide Survey, Pew Research's political typology, AP-NORC's
issue-importance tracking, ANES "most important problem" series, and
Gallup's Most Important Problem tracking. We don't fabricate specific
year-by-year numbers; we lean on the directional regularities those
sources have shown repeatedly.

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
            "Issue-salience patterns for young California renters in PPIC tracking weight strongly toward **housing cost** — the dominant issue for renters under 35 in PPIC's Statewide Survey almost every year since 2018 — followed by **cost of living and wages, public safety** (framed around homelessness response and policing accountability rather than violent-crime statistics), **climate** (real revealed-importance for this demographic, unlike most others), and **reproductive rights** (persistently elevated post-Dobbs). **Mental health and healthcare access** rank high.",
            "Polling regularities for younger Democratic renters in PPIC and Pew typology research consistently put **housing cost and availability** at the top, with **cost of living and wages, public safety** (homelessness and police-community framing), **climate** (one of the few demographics where climate registers in vote-driving salience, not just stated importance), and **reproductive rights** (post-Dobbs) rounding out the top concerns.",
            "Top-issue tracking for this demographic across PPIC, AP-NORC, and Pew research consistently surfaces **housing cost** as singular, with **cost of living and wages, climate, public safety** (in homelessness/policing framing), and **reproductive rights** also in the top tier. **Healthcare access** ranks high.",
        ],
        "caveat_variants": [
            "Topics less likely to move this audience: traditional fiscal-conservative framing, anti-density arguments, federal-political-grievance topics, culture-war wedges.",
            "Less likely to drive votes here: anti-density framing, abstract fiscal arguments, federal-grievance topics from either direction, culture-war wedges.",
            "Framing that typically underperforms with this demographic: anti-density arguments, traditional fiscal-conservative messaging, federal-grievance topics, culture-war wedges.",
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
            "Issue-salience patterns for affluent, college-educated Democratic homeowners in PPIC tracking and Pew typology research consistently put **government competence, public safety, infrastructure reliability,** and — for the parent subset — **K-12 schools** at the top of concerns. **Healthcare** rises in salience for the older subset. **Climate** has higher revealed-importance for college-educated Democrats than for other clusters but typically ranks below the cost-and-services stack in local elections.",
            "Polling regularities for this demographic — Pew's Establishment Liberal cluster, AP-NORC affluent-suburban tracking — consistently rank **government competence and quality of local administration, public safety, infrastructure,** and **healthcare access** in the top concerns; **K-12 schools** is highly salient for the parent share. **Cost of living** matters as inflation/quality-of-life pressure rather than as housing affordability.",
            "Top concerns for affluent owner-Dems track tightly with Pew's Establishment Liberal typology and PPIC's professional-Dem tracking: **government competence, public safety, infrastructure reliability,** **healthcare** (rising with the older subset), and **schools** for parents. **Climate** has real but typically secondary salience locally.",
        ],
        "caveat_variants": [
            "Less likely to drive votes here: housing supply arguments (rarely vote-driving for owners), federal-political-grievance framing, anti-tax appeals.",
            "Topics that typically don't move this audience: housing supply framing (owners aren't economically squeezed by it), federal-grievance topics from either direction, abstract anti-tax framing.",
            "Less likely to move votes: housing-supply framing (low salience for owners), federal-political-grievance topics, abstract anti-tax messaging.",
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
            "Issue-salience patterns for older, settled homeowners in PPIC tracking and Pew typology research consistently put **public safety, property taxes and cost of living, infrastructure reliability,** and **government competence** at the top of concerns; **healthcare and Medicare-touching federal policy** rises in salience for the 65+ subset.",
            "Polling regularities for senior owner-occupied California audiences in PPIC's Statewide Survey and AP-NORC senior-voter tracking consistently rank **public safety, infrastructure reliability, government competence, property taxes,** and **healthcare** (especially Medicare) in the top concerns.",
            "Top-concern tracking for this demographic across PPIC, Pew, and AP-NORC research consistently weights **public safety, cost of living and property taxes, infrastructure,** and **government competence** at the top, with **healthcare and Medicare** rising for the 65+ portion.",
        ],
        "caveat_variants": [
            "Less likely to drive votes here: housing supply framing, climate (high stated importance but historically low vote-driving salience for this cohort), reproductive rights.",
            "Topics that typically don't move this audience locally: housing supply arguments, climate (stated importance exceeds revealed for older cohorts), reproductive rights.",
            "Framing less likely to drive votes: housing supply, climate (high stated, low revealed salience for older voters), reproductive rights.",
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
            "Issue-salience patterns for working-class Hispanic California voters in PPIC and Pew Hispanic-voter tracking consistently put **cost of living and wages, housing cost, public safety, healthcare access,** and — uniquely high here — **federal immigration enforcement** at the top of concerns. **K-12 education** ranks very high for parents. **Jobs and economic opportunity** rank above climate or environmental framing.",
            "Polling regularities for Hispanic working-class voters in California across PPIC, Pew, and Equis Research tracking consistently rank **cost of living and wages, jobs and economic opportunity, housing cost, public safety, healthcare,** and **federal immigration enforcement** as top concerns. **K-12 schools** is highly salient for parents.",
            "Top-issue tracking for this demographic in PPIC's Statewide Survey and Pew's Hispanic-voter research consistently weights **cost of living, wages and jobs, housing cost, public safety, healthcare access,** and — distinctively — **federal immigration enforcement** at the top. **Education** ranks high for parents.",
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
            "Issue-salience patterns for working-class California renters in PPIC and AP-NORC tracking consistently put **cost of living and wages, housing cost** (this ranks high for renter audiences regardless of partisan lean), **public safety, healthcare access,** and **K-12 education** (high for parents) at the top of concerns.",
            "Polling regularities for working-class renter audiences across PPIC, AP-NORC, and Pew research consistently rank **cost of living, housing cost, public safety, jobs and wages,** and **healthcare access** at the top of concerns. **K-12 schools** is highly salient for parents.",
            "Top-issue tracking for working-class California renters in PPIC's Statewide Survey consistently weights **cost of living and wages, housing cost** (a top concern for renters regardless of partisan lean), **public safety, healthcare access,** and **education** at the top.",
        ],
        "caveat_variants": [
            "Less likely to move this audience: anti-density framing (renters here live in the housing supply being argued about), abstract fiscal-conservative messaging without specific costs named, climate (low vote-driving salience for working-class voters), federal-grievance from either direction, culture-war wedges.",
            "Topics that typically don't drive votes here: anti-density arguments (housing supply IS where these voters live), abstract fiscal framing, climate, federal-political-grievance topics, culture-war wedges from either side.",
            "Less likely to drive votes: anti-density framing, abstract fiscal-conservative arguments, climate (low revealed-importance for working-class voters), federal-grievance topics, culture-war wedges.",
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
            "Issue-salience patterns for parent-heavy, owner-occupied California audiences in PPIC tracking and Pew typology research consistently put **K-12 schools** at or near the top of concerns, followed by **public safety, cost of living, infrastructure reliability,** and **government competence**. **Housing affordability** ranks lower than for renter audiences but matters as 'good options for our kids when they grow up' framing.",
            "Polling regularities for owner-occupied family audiences across PPIC, AP-NORC, and Pew research consistently rank **K-12 schools, public safety, cost of living,** and **infrastructure** at the top of concerns, with **government competence** also weighted heavily.",
            "Top-concern tracking for this demographic consistently weights **schools** (especially given school-venue contexts), **public safety, cost of living, infrastructure reliability,** and **government competence** at the top.",
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
            "Issue-salience patterns for heavily-Democratic, college-educated California audiences in PPIC tracking and Pew Establishment Liberal typology research consistently put **housing cost and availability** at or near the top (the dominant issue for renter-Dem audiences statewide since 2018), followed by **cost of living, public safety** (framed around homelessness response and policing accountability), **climate** (real revealed-importance for this demographic), and **reproductive rights** (persistently elevated post-Dobbs). **Education and healthcare access** rank high.",
            "Polling regularities for college-educated heavily-Democratic California voters in PPIC and Pew research consistently rank **housing cost, cost of living, public safety** (homelessness and police-community framing), **climate, reproductive rights,** and **education** at the top of concerns. **Healthcare access** ranks high.",
            "Top-concern tracking for this demographic across PPIC, Pew, and AP-NORC research weights **housing cost** (singular for renters), **cost of living, climate** (real revealed-importance, unlike most other clusters), **public safety, reproductive rights,** and **healthcare access** at the top.",
        ],
        "caveat_variants": [
            "This audience is already partisan-aligned with a Democratic candidate; persuasion happens on competence and specificity rather than values. Federal-grievance and culture-war framing underperform; broad partisan signaling lands in friendly territory but won't differentiate.",
            "Cross-pressures here are low — the audience is solidly Democratic-aligned. Differentiator is competence and policy specifics, not values or framing. Federal-grievance topics and culture-war wedges underperform.",
            "The audience is solidly partisan-aligned; the persuasion challenge is competence and specificity, not values or framing. Federal-grievance topics, culture-war wedges, and broad partisan signaling underperform.",
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
            "Issue-salience for California college students in PPIC tracking and Pew college-attendee research clusters around **college affordability and student debt, housing cost, wages and job market, mental health,** and **climate** — this is one of the few demographics where climate ranks in the top 3 for vote-driving salience, not just stated importance. **Reproductive rights** persistently elevated post-Dobbs. **Public safety** ranks high but typically framed around mental-health crisis response, sexual assault on campus, and police-student interactions rather than property crime.",
            "Polling regularities for college students in PPIC, Pew, and Harvard IOP youth-poll tracking consistently rank **college affordability and student debt, housing cost, mental health, climate, reproductive rights,** and **wages and job-market access** at the top of concerns.",
            "Top-concern tracking for college students across PPIC, Pew, and Harvard IOP research consistently weights **college affordability, student debt, housing cost, mental health, climate** (real vote-driving salience here, unlike most demographics), and **reproductive rights** at the top.",
        ],
        "caveat_variants": [
            "For pre-aligned student audiences, registration drives and absentee-ballot logistics often carry more electoral impact than persuasion messaging. Federal-grievance topics and culture-war framing underperform; broad partisan signaling lands in friendly territory but doesn't differentiate.",
            "Mobilization (registration drives, ballot logistics) typically has more ROI than persuasion for student audiences. Federal-grievance topics and culture-war wedges underperform.",
            "Mobilization beats persuasion for student audiences with high baseline alignment. Federal-grievance topics, culture-war wedges, and abstract fiscal framing underperform.",
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
            "Issue-salience patterns for mixed-income, mixed-partisan California renters in PPIC tracking and AP-NORC research consistently put **cost of living and wages, housing cost, public safety** (framed around homelessness response and police-community relations), **healthcare access,** and **K-12 education** at the top of concerns.",
            "Polling regularities for mixed-partisan younger renter audiences across PPIC and AP-NORC research consistently rank **cost of living, housing cost, public safety, healthcare access,** and **education** in the top tier.",
            "Top-issue tracking for this demographic in PPIC and AP-NORC research weights **cost of living and wages, housing cost, public safety, healthcare access,** and **K-12 education** (especially for parents) at the top.",
        ],
        "caveat_variants": [
            "Less likely to move this audience: anti-density framing (renters here live in the housing supply), federal-political-grievance topics from either direction, culture-war wedges, climate (high stated importance but historically lower vote-driving salience for mixed-income voters).",
            "Topics that typically don't drive votes here: anti-density arguments, federal-grievance framing, culture-war wedges, climate (stated importance exceeds vote-driving salience for mixed-income voters).",
            "Framing less likely to drive votes: anti-density, abstract fiscal arguments, federal-grievance topics from either direction, culture-war wedges.",
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
            "Issue-salience patterns for mixed-demographic California suburban Democratic audiences in PPIC tracking and AP-NORC research consistently put **cost of living and quality of life, public safety** (typically framed around homelessness response and equitable enforcement), **housing cost** (relevant for the renter share), **K-12 education** (for parents), and **healthcare access** at the top of concerns. **Government competence and local-administration quality** rank meaningfully across the board.",
            "Polling regularities for mixed-suburban California audiences across PPIC, AP-NORC, and Pew research consistently rank **cost of living, public safety, housing cost** (for renter share), **K-12 schools, healthcare access,** and **government competence** at the top.",
            "Top-issue tracking for mixed-demographic suburban California voters in PPIC's Statewide Survey consistently weights **cost of living and wages, public safety, housing cost** (more salient for the renter share), **K-12 education,** and **healthcare access** at the top. **Government competence** matters across the spectrum.",
        ],
        "caveat_variants": [
            "Less likely to drive votes here: heavy partisan signaling, federal-political-grievance topics from either direction, anti-density absolutism, culture-war wedges.",
            "Topics that typically don't move mixed-demographic audiences: federal-grievance framing, heavy partisan signaling, anti-density-as-identity arguments, culture-war wedges.",
            "Framing less likely to drive votes: heavy partisan signaling, federal-political-grievance framing, abstract ideological appeals.",
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
            "Federal-political-grievance framing (from either direction) typically under-performs in audiences where partisan registration is competitive.",
            "Heavy partisan signaling and federal-grievance framing from either direction typically don't move competitive-registration audiences.",
            "In competitive-registration rooms, federal-political-grievance topics from either side typically underperform.",
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
            "Income is meaningfully bimodal ({low_income_share} under $50k, {high_income_share} in $125k+) — two distinct audiences in the same room. The affluent subset weights government competence, infrastructure, and public safety; the lower-income subset weights cost of living, housing cost, and healthcare. **Cost of living and public safety** bridge both.",
            "The income distribution here is bimodal ({low_income_share} under $50k vs {high_income_share} in $125k+) — affluent attendees and cost-stressed attendees may weight different issues, but **cost of living** and **public safety** are common ground for both.",
            "Bimodal income mix ({low_income_share} under $50k / {high_income_share} in $125k+) means renter and owner halves bring different top-issue lists. **Cost of living, public safety,** and **schools** for parents bridge both subgroups.",
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
            "The {active_share} active-commute share (transit/bike/walk — high for Chico) signals an audience that thinks about transportation infrastructure as a lived issue, not abstract policy.",
            "Meaningful active-commute share ({active_share} commute by bike/walk/transit) — transportation infrastructure is a lived issue here, not theoretical.",
            "{active_share} of workers commute actively (bike/walk/transit) — well above Chico norm — implying transportation-infrastructure concerns land as concrete daily friction.",
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
