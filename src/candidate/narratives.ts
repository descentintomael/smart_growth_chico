/**
 * Per-venue speaker briefings.
 *
 * Hand-written audience-priorities paragraphs for the top-10 venues in each
 * council district (28 unique venues after overlap). Auto-generated paragraphs
 * for ranks 11-50 live in catchment-demographics.json (added by
 * scripts/generate-venue-narratives.py); these hand-written entries take
 * precedence in the panel.
 *
 * Style: 80-100 word paragraphs naming what the audience likely weights
 * when voting in a Chico city council race. Plain text, no markdown — the
 * panel renders these as plain <p>.
 *
 * Grounded in:
 *  - Audience-level polling regularities (PPIC Statewide Survey, Pew
 *    typology, AP-NORC issue tracking) for the demographic-level priorities.
 *  - Chico City Council agenda sample (6 meetings April 2025 – May 2026
 *    pulled from chico-ca.granicus.com) for what the council actually
 *    decides on. Recurring agenda categories observed: sewer assessments
 *    and street rehab, homelessness response (Warren v. Chico is the
 *    recurring frame), police labor + Police Department reports, downtown
 *    vitality (Park & Go, ground-floor uses), tenant protections + code
 *    enforcement on existing rentals, development impact fees, e-bike/
 *    micromobility, Bidwell Park stewardship, sanctuary policy.
 *
 * Things explicitly NOT council jurisdiction (avoided as council-vote
 * drivers even when the audience cares): K-12 schools (CUSD), recreation
 * programming (CARD), mental-health services (Butte County BH),
 * healthcare access, higher education (CSU/Butte College), federal
 * immigration enforcement (sanctuary policy is the local-decision proxy),
 * reproductive rights. Climate-Action-Plan items appear rarely in the
 * agenda sample so climate is downweighted as a vote-driver.
 *
 * `brief` is currently not rendered; kept on the interface in case the
 * briefing block returns.
 */
export interface VenueBriefing {
  brief: string
  leadWith: string
}

export const VENUE_BRIEFINGS: Record<string, VenueBriefing> = {
  // ============================================================
  // DISTRICT 6 — top 10
  // ============================================================

  // 1. Lakeside Pavilion
  "way/868413772": {
    brief: "",
    leadWith:
      "Bimodal audience — older homeowners (34% age 65+, 52% own) and cost-stressed renters (48% renter, 53% rent-burdened) in the same room. The homeowner half tends to weight public safety, sewer assessments and street maintenance, property taxes, and government competence (recent council items: Police Department annual report, sewer enterprise study, Warren v. Chico litigation). The renter half weights housing cost, tenant protections and code enforcement on existing rentals, and cost of living. Chico's homelessness response is the rare topic that bridges both halves. Less likely to move votes: anti-density absolutism, culture-war framing. 85% turnout — engaged, policy-detail audience.",
  },

  // 2. Chico's Elks Lodge 423
  "node/13565778876": {
    brief: "",
    leadWith:
      "Older single-family-homeowner audience (81% own, 89% SF stock, 41% in $125k+) with 84% turnout — a substance, civic-engagement crowd. Local-government priorities cluster around public safety (Police Department reports, Warren v. Chico framing), infrastructure reliability (sewer assessments, street rehabilitation, property acquisitions for road projects), government competence (City Manager and Attorney recruitment, budget rigor, labor MOUs), and Bidwell Park stewardship. Housing supply rarely drives votes here; climate-as-identity underperforms. Registration competitive (42 D / 32 R) but top-of-ticket vote shifted +5 points D between 2022 and 2024 — meaningful persuadable-moderate share. Bring fiscal arithmetic.",
  },

  // 3. Canyon Oaks Country Club
  "relation/19628096": {
    brief: "",
    leadWith:
      "Walking sample is small (122 residents); what's robust is who joins a private country club in northeast Chico — high-income, college-educated, 45+. Local-issue priorities cluster around government competence (City Manager / Attorney hiring, budget, labor MOUs), public safety, infrastructure reliability (sewer, streets), and fiscal stewardship. Housing supply is generally a low vote-driver; climate ranks higher than in other affluent clusters but typically below the competence-and-safety stack on local races. Registration competitive (39 D / 36 R) but +7-point D shift at top of ticket in 2024 — strong moderate-R crossover. They will check that you live in the neighborhood.",
  },

  // 4. Hotel Káterina
  "way/1391306494": {
    brief: "",
    leadWith:
      "Younger, more mixed audience than most D6 catchments: 24% Hispanic, 10% Spanish-at-home, 29% age 18-34, 40% of households under $50k. Local-government priorities for working-class mixed-Hispanic audiences typically center on cost of living (utility rates, low-income sewer rate program is a recent council item), tenant protections and code enforcement on rentals, public safety in concrete terms, and sanctuary policy / equitable enforcement. K-12 concerns sit with CUSD, not the council, but parents conflate them. Spanish-language access to city services materially affects engagement. 76% turnout — voter-engagement framing has leverage alongside persuasion.",
  },

  // 5. Butte College Skyway Center
  "way/1486726820": {
    brief: "",
    leadWith:
      "Younger, working-and-professional mixed audience (29% age 18-34, 27% Hispanic, 47% renter, 60% in management/business/science/arts) with Democratic-leaning registration (41 D / 28 R / 21 NPP). Local-government priorities track to cost of living and utility rates, housing cost (tenant protections, code enforcement on existing rentals), public safety (homelessness response in the Warren v. Chico framing, police-community relations), and sanctuary policy for the 10% Spanish-at-home subset. Top-of-ticket vote barely shifted between 2022 and 2024 — unusually stable local political identity. 74% turnout is moderate.",
  },

  // 6. Tbar
  "node/13137263368": {
    brief: "",
    leadWith:
      "Younger working/professional mixed audience (29% age 18-34, 28% Hispanic, 47% renter, 60% in management/business/science/arts) with Democratic-leaning registration (41 D / 28 R / 21 NPP) and 38% of households under $50k. Local priorities typically center on cost of living and utility rates, housing cost (tenant protections, code enforcement on rentals), public safety (homelessness response, police-community), and sanctuary policy for the 10% Spanish-at-home share. Schools matter to parents but sit with CUSD, not the council. 74% turnout — engagement framing has leverage alongside persuasion.",
  },

  // 7. Butte College (main campus)
  "way/85465037": {
    brief: "",
    leadWith:
      "Younger working-and-professional mixed audience (29% age 18-34, 28% Hispanic, 47% renter, 60% in management/business/science/arts) with Democratic-leaning registration (41 D / 28 R / 21 NPP). Local priorities typically center on cost of living and utility rates, housing cost (tenant protections, code enforcement on rentals), public safety, and sanctuary policy. Butte College funding and tuition are state-decided, not council, but a campus-event audience may foreground them anyway. Off-campus student housing supply (Greenfield-style bond issuances, Hubbard-style rezones) is the council-touch dimension. 74% turnout — engagement framing carries weight.",
  },

  // 8. Little Chico Creek Elementary School
  "way/1104515170": {
    brief: "",
    leadWith:
      "Heavily renter (74%), multifamily-dense (71%), working-class (42% of households under $50k) audience with Democratic-leaning registration (42 D / 30 R / 19 NPP) and 79% turnout. Local priorities for low-income renter audiences typically center on tenant protections and code enforcement on existing rentals, cost of living (utility rates and the low-income sewer rate program are recent council items), public safety (homelessness response, equitable policing), and sanctuary policy for the 10% Spanish-at-home share. Less likely to drive votes: fiscal-conservative framing, anti-density arguments. K-12 schools are highly salient but sit with CUSD, not council.",
  },

  // 9. Marigold Elementary School
  "way/84969479": {
    brief: "",
    leadWith:
      "Established single-family-homeowner audience (82% own, 94% SF stock) with a family skew (27% under 18, 35% age 35-54) and meaningful affluence (44% in $125k+). Registration competitive-D (42 D / 32 R / 18 NPP), 84% turnout. Local-government priorities for affluent parent-heavy owners typically center on public safety, infrastructure reliability (sewer assessments, road rehabilitation), government competence (City Manager / Attorney recruitment, budget rigor), and quality of new development (impact fees, zoning). Schools are highly salient given the venue but sit with CUSD, not council. Top-of-ticket +5 point D shift — moderate-R-leaning households persuadable on competence.",
  },

  // 10. Sierra Nevada Brewing Company Taproom
  "node/9796268718": {
    brief: "",
    leadWith:
      "Renter-majority (66%), multifamily-leaning (61%) audience skewing younger (28% age 18-34) with a moderately-low-income profile (41% under $50k) and Democratic-leaning registration (42 D / 29 R / 20 NPP). Local-government priorities typically center on housing cost (tenant protections, code enforcement on rentals), cost of living, public safety (homelessness response, police-community), and active-transportation infrastructure (shared micromobility program, e-bike regulation are recent council items). As a Sierra Nevada destination venue, actual forum attendees may skew older and more affluent than the walking catchment implies — civic-event-going professionals more than immediate-neighborhood residents.",
  },

  // ============================================================
  // DISTRICT 4 — top 10
  // ============================================================

  // 11. Butte County Library - Chico Branch (D4 + D2)
  "way/461041054": {
    brief: "",
    leadWith:
      "Heavily Democratic-leaning audience (51 D / 22 R / 19 NPP, Harris took 69%) with high college attainment (55% bachelor+), majority-renter housing (59% renter, 58% rent-burdened), and 23% Hispanic / 7% Spanish-at-home share. Local-government priorities for college-educated Democratic audiences in this profile typically center on housing cost (tenant protections, code enforcement on rentals, downtown infill), public safety (homelessness response in the Warren v. Chico framing, policing accountability), downtown vitality (Park & Go, ground-floor uses), active-transportation infrastructure, and sanctuary policy. Already partisan-aligned: persuasion happens on competence and specifics, not values.",
  },

  // 12. Enloe Conference Center
  "relation/18020131": {
    brief: "",
    leadWith:
      "Young (44% age 18-34), heavily renter (68%), Democratic-leaning audience (49 D / 20 R / 21 NPP, Harris took 68%) with severe rent burden (64% of renters at 30%+ of income). Local-government priorities for this demographic center on tenant protections and code enforcement on rentals (recurring council items), housing supply (Greenfield-style bond issuances, downtown infill), public safety (Warren v. Chico framing of homelessness response, policing accountability), and active-transportation infrastructure. Mental-health services are highly salient but sit with Butte County, not council. 76% turnout — already mobilized. National-grievance topics underperform.",
  },

  // 13. California State University, Chico
  "way/28551484": {
    brief: "",
    leadWith:
      "Overwhelmingly student audience (76% age 18-34, 93% renter, 74% under $50k, 74% rent-burdened) with Democratic-leaning registration (48 D / 17 R / 23 NPP) and 70% turnout. Local-government priorities for college students typically center on off-campus housing supply (Greenfield bonds, Hubbard-style rezones), tenant protections, downtown vitality and ground-floor uses (Park & Go), active-transportation infrastructure (e-bike regulation, micromobility), and police-student relations. Tuition and student-debt are state/federal, not council. For a pre-aligned student audience, mobilization — registration drives, ballot logistics — typically beats persuasion.",
  },

  // 14. Citrus Avenue Elementary School
  "way/28551317": {
    brief: "",
    leadWith:
      "Young (59% age 18-34), heavily renter (78%), college-educated (49%) audience with strong Democratic lean (49 D / 19 R / 22 NPP, Harris took 68%) and high rent burden (63%). Local priorities for young college-educated renters typically center on tenant protections and code enforcement on rentals, housing supply (Greenfield-style bonds, infill), public safety (homelessness response, policing accountability), and active-transportation infrastructure. K-12 schools are highly salient given the venue but sit with CUSD, not council. Already Democratic-aligned: differentiator is competence and policy specifics.",
  },

  // 15. CARD Community Center
  "way/1392880190": {
    brief: "",
    leadWith:
      "Racially diverse (35% Hispanic), highly educated (54% bachelor+), middle-class-to-affluent audience (30% in $125k+, 40% under $50k — bimodal) with strong Democratic lean (52 D / 22 R / 18 NPP, Harris took 69%) and 81% turnout. Local-government priorities typically center on cost of living, housing (tenant protections, downtown infill), public safety (homelessness, policing accountability), Bidwell Park stewardship, and sanctuary policy for the Hispanic and Spanish-speaking subset. CARD recreation programming is independent of the council. Already partisan-aligned; differentiator is competence and specifics.",
  },

  // 16. Gateway Science Museum
  "way/546953163": {
    brief: "",
    leadWith:
      "Young (49% age 18-34), college-educated (54% bachelor+), renter-majority (64%) Democratic-leaning audience (50 D / 21 R / 19 NPP, Harris took 68%) with high rent burden (60%). Local priorities typically center on tenant protections and code enforcement on rentals, housing supply (downtown infill, Hubbard-style rezones), public safety (homelessness response, policing accountability), active-transportation infrastructure, and downtown vitality. Already partisan-aligned: differentiator is competence and specifics. Less likely to drive votes: fiscal-conservative framing, anti-density arguments, national-grievance topics.",
  },

  // 17. Creekside Rose Garden
  "way/1416654666": {
    brief: "",
    leadWith:
      "Same neighborhood as CARD — racially diverse (35% Hispanic), highly educated (54% bachelor+), middle-class-to-affluent audience with strong Democratic lean (52 D / 22 R / 18 NPP, Harris took 69%) and 81% turnout. Local-government priorities typically center on cost of living, public safety (homelessness, policing accountability), tenant protections, Bidwell Park stewardship, and sanctuary policy for the Hispanic and Spanish-speaking subset. Already partisan-aligned: persuasion happens on competence and specifics. Less likely to drive votes: fiscal-conservative framing, anti-density arguments.",
  },

  // 18. Hooker Oak Elementary School (D4 + D2)
  "way/186727445": {
    brief: "",
    leadWith:
      "College-educated (55% bachelor+), professional (73% management/business/science/arts), Democratic-leaning audience (51 D / 22 R / 19 NPP, Harris took 69%) with mixed renter-owner split (58/42) and 57% rent-burdened renters. Local-government priorities typically center on tenant protections (for the renter share), housing supply (infill, downtown), public safety (homelessness response, policing accountability), active-transportation infrastructure, and Bidwell Park stewardship. The 14% active-commute share (well above Chico norm) signals an audience that thinks about transportation as lived friction. Already partisan-aligned: differentiator is competence.",
  },

  // 19. Chico Junior High School
  "way/460975283": {
    brief: "",
    leadWith:
      "Meaningfully younger (38% age 18-34), college-educated (57% bachelor+), majority-renter (57%) Democratic audience (51 D / 21 R / 19 NPP, Harris took 69%). Local priorities typically center on tenant protections, housing supply (downtown infill, Greenfield-style bonds), public safety (homelessness response, policing accountability), active-transportation infrastructure, and sanctuary policy for the 8% Spanish-at-home subset. K-12 schools are highly salient given the venue but sit with CUSD, not council. 79% turnout signals high engagement. Already partisan-aligned: differentiator is competence and specifics.",
  },

  // 20. Senator Theater
  "way/460976024": {
    brief: "",
    leadWith:
      "Younger (40% age 18-34), racially diverse (33% Hispanic), college-educated (50% bachelor+), Democratic-leaning audience (51 D / 22 R / 19 NPP, Harris took 69%). Local-government priorities typically center on downtown vitality (Park & Go, ground-floor uses, parking — all recurring council items), tenant protections, public safety (homelessness response, policing accountability), active-transportation infrastructure, and sanctuary policy for the Hispanic and 10% Spanish-at-home subset. Already partisan-aligned: differentiator is competence, specifics, and authentic Hispanic-community engagement. Spanish-language outreach is operationally useful.",
  },

  // ============================================================
  // DISTRICT 2 — top 10
  // ============================================================

  // 21. Butte College - Cosmetology & Barbering
  "node/12209917996": {
    brief: "",
    leadWith:
      "Younger-skewing (31% age 18-34), majority-renter (52%), mixed-income (42% under $50k, 22% in $125k+) audience with moderately-Democratic registration (42 D / 30 R / 19 NPP). Local-government priorities for mixed-income working-and-professional renters typically center on cost of living and utility rates, tenant protections and code enforcement on rentals, public safety (homelessness response, police-community), and sanctuary policy for the 8% Spanish-at-home subset. Top-of-ticket vote shifted +4 points D in 2024 — persuadable moderate-R share. 77% turnout is moderate-engaged.",
  },

  // 22. Neal Dow Elementary School
  "way/186727450": {
    brief: "",
    leadWith:
      "Young (43% age 18-34), heavily renter (70%), mostly-white (75%) Democratic-leaning audience (51 D / 23 R / 18 NPP) with 83% turnout and meaningful rent burden (59%). Local priorities typically center on tenant protections and code enforcement on rentals, housing supply (downtown infill), public safety (homelessness response, policing accountability), active-transportation infrastructure, and downtown vitality. K-12 sits with CUSD, not council. Top-of-ticket vote shifted +6 points D in 2024 — consistent with broader young-renter-Dem patterns. Already partisan-aligned: competence and specifics differentiate.",
  },

  // 23. John A. McManus Elementary School
  "way/85087700": {
    brief: "",
    leadWith:
      "Mixed-age (28% 18-34, 26% 35-54, 15% 65+), mixed-tenure (52% renter, 48% owner) audience with slightly-Democratic registration (43 D / 29 R / 19 NPP). Local-government priorities for mixed-income, mixed-tenure audiences typically center on cost of living, public safety (homelessness response, Police Department reports), tenant protections (renter share) and infrastructure (owner share), and sanctuary policy. The income mix is somewhat bimodal — renters and owners weight different concerns, but cost of living and public safety bridge both. Top-of-ticket vote shifted +4 points D in 2024 — persuadable moderates.",
  },

  // 24. Fairview High School
  "way/84968698": {
    brief: "",
    leadWith:
      "Mixed-age (33% 18-34, 18% 65+), majority-owner (56%) audience with competitive registration (41 D / 31 R / 20 NPP). Local-government priorities for mixed-age owner-leaning competitive suburban audiences typically center on public safety (Police Department reports, Warren v. Chico framing of homelessness), infrastructure reliability (sewer, street rehab), cost of living, and government competence. Housing cost matters less for the owner share but tenant protections matter for the 44% renter share. Top-of-ticket vote shifted +5 points D in 2024 — persuadable moderate-R-leaning households on competence. 77% turnout.",
  },

  // 25. Oak Bridge Academy
  "node/13608269862": {
    brief: "",
    leadWith:
      "Heavily renter (75%), multifamily-leaning (52%), working-class (49% under $50k) audience with competitive R-leaning registration (39 D / 32 R / 20 NPP) but D-voting at the top of the ticket (Harris took 53%). Local-government priorities for working-class renters regardless of partisan lean typically center on cost of living and utility rates (low-income sewer rate program is a recent council item), tenant protections and code enforcement on existing rentals, public safety, and jobs / local economy. Less likely to move this audience: anti-density framing (renters live in the housing supply being argued about), abstract fiscal-conservative arguments. Top-of-ticket +4 point D shift — moderate-R persuadable on local issues.",
  },

  // 26. Shasta Union School
  "way/186727461": {
    brief: "",
    leadWith:
      "Predominantly Hispanic (54%), heavily Spanish-speaking (22% at home) audience with low college attainment (16%), low income (38% under $50k), and competitive R-leaning registration (38 D / 31 R / 21 NPP). Top-of-ticket vote shifted +10 points D in 2024 — biggest 2022-2024 shift in the D2 top-10. Local-government priorities for working-class Hispanic voters typically center on cost of living and utility rates (low-income sewer rate program), tenant protections and code enforcement on rentals, public safety in concrete terms, sanctuary policy / equitable enforcement, and jobs / local economy. K-12 sits with CUSD. Hispanic voters are not a Democratic monolith — values-aligned framing (faith, family) cuts both ways. 70% turnout — voter-engagement framing has real ROI. Spanish-language outreach is operationally essential.",
  },

  // 27. Bidwell Junior High School
  "way/85629476": {
    brief: "",
    leadWith:
      "Older-skewing (19% age 65+, 27% age 35-54), majority-owner (61%) audience with meaningful affluence (36% in $125k+) and moderate Democratic lean (44 D / 29 R / 19 NPP). Local-government priorities for older settled owner-occupied Democrats typically center on public safety (Police Department reports, Warren v. Chico framing of homelessness), infrastructure reliability (sewer assessments, street rehab), government competence, and quality-of-development decisions (impact fees, zoning). Housing affordability matters as 'options for our kids when they grow up.' Top-of-ticket vote shifted +2 points D in 2024 — modest persuadable-moderate share. 76% turnout. Bring substance and detail.",
  },

  // 28. Mekkala Thai Cuisine
  "node/13608269857": {
    brief: "",
    leadWith:
      "Heavily renter (73%), multifamily-leaning (51%), working/lower-middle-income (49% under $50k) audience with competitive R-leaning registration (39 D / 32 R / 20 NPP) but D-voting at the top of the ticket — top shifted +4 points D in 2024. Local priorities for working-class renters regardless of partisan lean typically center on cost of living and utility rates, tenant protections and code enforcement on existing rentals, public safety, and jobs / local economy. Less likely to move this audience: anti-density framing (renters live in the housing supply being argued about), abstract fiscal-conservative arguments without concrete dollar impacts, culture-war wedges.",
  },
}
