/**
 * Per-venue speaker briefings.
 *
 * Hand-written audience-priorities paragraphs for the top-10 venues in each
 * council district (28 unique venues after overlap). Auto-generated paragraphs
 * for ranks 11-50 live in catchment-demographics.json (added by
 * scripts/generate-venue-narratives.py); these hand-written entries take
 * precedence in the panel.
 *
 * Style: 60-100 word paragraphs naming the LOCAL-government concerns each
 * audience likely weights when voting for city council — grounded in
 * polling regularities (PPIC Statewide Survey, Pew typology, AP-NORC issue
 * tracking) but kept tightly local. Plain text, no markdown — the panel
 * renders these as plain `<p>`. State/federal politics referenced only when
 * they spill into a local-government decision (e.g. sanctuary policy).
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
      "Bimodal audience — older homeowners (34% age 65+, 52% own) and cost-stressed renters (48% renter, 53% rent-burdened) in the same room. The homeowner half tends to weight public safety, property taxes, and infrastructure reliability on local races; the renter half weights housing cost and cost of living. Public safety — particularly Chico's homelessness response — is one of the few topics that bridges both. Less likely to move votes: anti-density absolutism, culture-war framing. 85% turnout (vs Butte's 77%) signals an engaged, policy-detail audience.",
  },

  // 2. Chico's Elks Lodge 423
  "node/13565778876": {
    brief: "",
    leadWith:
      "Older single-family-homeowner audience (81% own, 89% SF stock, 41% in $125k+) with 84% turnout — a substance, civic-engagement crowd. Local-government priorities for this demographic in PPIC tracking cluster around public safety, infrastructure reliability, property taxes and fiscal stewardship, and government competence. Housing supply is rarely vote-driving here; climate-as-identity underperforms. Registration is competitive (42 D / 32 R) but the top-of-ticket vote shifted +5 points more Democratic between 2022 and 2024 — meaningful persuadable-moderate share. Bring fiscal arithmetic and concrete examples.",
  },

  // 3. Canyon Oaks Country Club
  "relation/19628096": {
    brief: "",
    leadWith:
      "Walking sample is small (122 residents); what's robust is who joins a private country club in northeast Chico — high-income, college-educated, 45+. Local-issue priorities for this demographic cluster around government competence, public safety, infrastructure reliability, schools (for parents), and fiscal stewardship. Housing supply is generally a low vote-driver; climate ranks higher than in other affluent clusters but typically below the competence-and-safety stack on local races. Registration competitive (39 D / 36 R) but +7-point D shift at the top of the ticket in 2024 — strong moderate-R crossover. They will check that you live in the neighborhood.",
  },

  // 4. Hotel Káterina
  "way/1391306494": {
    brief: "",
    leadWith:
      "Younger, more mixed audience than most D6 catchments: 24% Hispanic, 10% Spanish-at-home, 29% age 18-34, 40% of households under $50k. Local-government priorities for working-class mixed-Hispanic audiences typically center on cost of living and wages, public safety (concrete and locally framed), schools (highly salient for parents), and housing affordability. Spanish-language access to city services materially affects engagement here. 76% turnout is moderate — voter-engagement framing has leverage alongside persuasion. Fiscal-conservative messaging rarely connects; culture-war wedges underperform.",
  },

  // 5. Butte College Skyway Center
  "way/1486726820": {
    brief: "",
    leadWith:
      "Younger, working-and-professional mixed audience (29% age 18-34, 27% Hispanic, 47% renter, 60% in management/business/science/arts roles) with Democratic-leaning registration (41 D / 28 R / 21 NPP). Local-government priorities track to cost of living, housing cost, public safety (homelessness response and police-community relations), healthcare access, and schools for parents. Sanctuary-policy and equitable-enforcement decisions matter for the 10% Spanish-at-home subset. Top-of-ticket vote barely shifted between 2022 and 2024 — unusually stable local political identity. 74% turnout is moderate.",
  },

  // 6. Tbar
  "node/13137263368": {
    brief: "",
    leadWith:
      "Younger working/professional mixed audience (29% age 18-34, 28% Hispanic, 47% renter, 60% in management/business/science/arts) with Democratic-leaning registration (41 D / 28 R / 21 NPP) and 38% of households under $50k. Local priorities for mixed-income California renters in this band typically center on cost of living and wages, housing cost, public safety, healthcare access, and schools for parents. Sanctuary-policy and equitable-enforcement matter for the 10% Spanish-at-home share. 74% turnout — engagement framing has leverage alongside persuasion.",
  },

  // 7. Butte College (main campus)
  "way/85465037": {
    brief: "",
    leadWith:
      "Younger working-and-professional mixed audience (29% age 18-34, 28% Hispanic, 47% renter, 60% in management/business/science/arts) with Democratic-leaning registration (41 D / 28 R / 21 NPP). Local priorities typically center on cost of living, housing cost, public safety, healthcare access, and schools (for parents) — plus Butte College funding and tuition for the student-and-faculty share that may turn out for a campus event. Sanctuary-policy matters for the 10% Spanish-at-home subset. 74% turnout — engagement framing carries weight.",
  },

  // 8. Little Chico Creek Elementary School
  "way/1104515170": {
    brief: "",
    leadWith:
      "Heavily renter (74%), multifamily-dense (71%), working-class (42% of households under $50k) audience with Democratic-leaning registration (42 D / 30 R / 19 NPP) and 79% turnout. Local priorities for low-income renter audiences typically center on housing cost (rent stabilization, code enforcement on existing rentals, supply), cost of living, public safety (homelessness response, equitable policing), healthcare access, and K-12 schools (highly relevant given the venue). Sanctuary-policy matters for the 10% Spanish-at-home share. Less likely to drive votes: fiscal-conservative framing, anti-density arguments.",
  },

  // 9. Marigold Elementary School
  "way/84969479": {
    brief: "",
    leadWith:
      "Established single-family-homeowner audience (82% own, 94% SF stock) with a family skew (27% under 18, 35% age 35-54) and meaningful affluence (44% in $125k+). Registration competitive-D (42 D / 32 R / 18 NPP), 84% turnout. Local-government priorities for affluent parent-heavy owner-occupied audiences typically center on K-12 schools (highly relevant given the venue), public safety, infrastructure reliability, government competence, and quality of new development. Housing affordability matters as 'options for our kids when they grow up.' Top-of-ticket +5 point D shift — moderate-R-leaning households persuadable on competence.",
  },

  // 10. Sierra Nevada Brewing Company Taproom
  "node/9796268718": {
    brief: "",
    leadWith:
      "Renter-majority (66%), multifamily-leaning (61%) audience skewing younger (28% age 18-34) with a moderately-low-income profile (41% under $50k) and Democratic-leaning registration (42 D / 29 R / 20 NPP). Local-government priorities for this demographic typically center on housing cost, cost of living, public safety (homelessness, police-community), and active-transportation infrastructure. As a Sierra Nevada destination venue, actual forum attendees may skew older and more affluent than the walking catchment implies — the room may carry a 'civic-event-going professional' demographic mix more than the immediate neighborhood does.",
  },

  // ============================================================
  // DISTRICT 4 — top 10
  // ============================================================

  // 11. Butte County Library - Chico Branch (D4 + D2)
  "way/461041054": {
    brief: "",
    leadWith:
      "Heavily Democratic-leaning audience (51 D / 22 R / 19 NPP, Harris took 69%) with high college attainment (55% bachelor+), majority-renter housing (59% renter, 58% rent-burdened), and 23% Hispanic / 7% Spanish-at-home share. Local-government priorities for college-educated Democratic California audiences typically center on housing cost (dominant for renter-Dem voters), cost of living, public safety (homelessness response and policing accountability), parks-and-libraries funding, and active-transportation infrastructure. Sanctuary-policy matters for the Spanish-speaking share. Already partisan-aligned: persuasion happens on competence and specifics, not values.",
  },

  // 12. Enloe Conference Center
  "relation/18020131": {
    brief: "",
    leadWith:
      "Young (44% age 18-34), heavily renter (68%), Democratic-leaning audience (49 D / 20 R / 21 NPP, Harris took 68%) with severe rent burden (64% of renters at 30%+ of income). Local-government priorities for young California renters in PPIC tracking center sharply on housing cost (the dominant local-renter issue), wages and cost of living, public safety (homelessness response and policing accountability), and mental-health and harm-reduction services. Active-transportation infrastructure is a lived issue. 76% turnout — already mobilized. National-grievance topics underperform; broad partisan signaling lands but doesn't differentiate.",
  },

  // 13. California State University, Chico
  "way/28551484": {
    brief: "",
    leadWith:
      "Overwhelmingly student audience (76% age 18-34, 93% renter, 74% under $50k, 74% rent-burdened) with Democratic-leaning registration (48 D / 17 R / 23 NPP) and 70% turnout. Local-government priorities for college students typically center on housing cost (off-campus housing availability), cost of living, public safety (mental-health crisis response, sexual-assault response, police-student relations), and active-transportation infrastructure. Town-gown friction is a real local issue here. For a pre-aligned student audience, mobilization — registration drives, ballot logistics — typically beats persuasion.",
  },

  // 14. Citrus Avenue Elementary School
  "way/28551317": {
    brief: "",
    leadWith:
      "Young (59% age 18-34), heavily renter (78%), college-educated (49%) audience with strong Democratic lean (49 D / 19 R / 22 NPP, Harris took 68%) and high rent burden (63%). Local priorities for young college-educated renters typically center on housing cost (the dominant local-renter issue), cost of living, public safety (homelessness response, policing accountability), schools (highly relevant given the venue), and active-transportation infrastructure. Already Democratic-aligned: differentiator is competence and policy specifics. Less likely to drive votes: anti-density framing, fiscal-conservative messaging.",
  },

  // 15. CARD Community Center
  "way/1392880190": {
    brief: "",
    leadWith:
      "Racially diverse (35% Hispanic), highly educated (54% bachelor+), middle-class-to-affluent audience (30% in $125k+, 40% under $50k — bimodal) with strong Democratic lean (52 D / 22 R / 18 NPP, Harris took 69%) and 81% turnout. Local-government priorities typically center on cost of living, housing cost, public safety (homelessness, equitable enforcement), parks-and-recreation funding (relevant given the CARD venue), and schools. Sanctuary-policy matters for the Hispanic and Spanish-speaking subset. Already partisan-aligned; differentiator is competence and specifics.",
  },

  // 16. Gateway Science Museum
  "way/546953163": {
    brief: "",
    leadWith:
      "Young (49% age 18-34), college-educated (54% bachelor+), renter-majority (64%) Democratic-leaning audience (50 D / 21 R / 19 NPP, Harris took 68%) with high rent burden (60%). Local priorities for college-educated young Democrats typically center on housing cost, cost of living, public safety (homelessness response, policing accountability), parks-and-museums-and-libraries funding, mental-health services, and active-transportation infrastructure. Already partisan-aligned: differentiator is competence and specifics. Less likely to drive votes: fiscal-conservative framing, anti-density arguments, national-grievance topics.",
  },

  // 17. Creekside Rose Garden
  "way/1416654666": {
    brief: "",
    leadWith:
      "Same neighborhood as CARD — racially diverse (35% Hispanic), highly educated (54% bachelor+), middle-class-to-affluent audience with strong Democratic lean (52 D / 22 R / 18 NPP, Harris took 69%) and 81% turnout. Local-government priorities typically center on cost of living, public safety (homelessness, equitable enforcement), housing cost, parks-and-recreation, and schools. Sanctuary-policy matters for the Hispanic and Spanish-speaking subset. Already partisan-aligned: persuasion happens on competence and specifics. Less likely to drive votes: fiscal-conservative framing, anti-density arguments.",
  },

  // 18. Hooker Oak Elementary School (D4 + D2)
  "way/186727445": {
    brief: "",
    leadWith:
      "College-educated (55% bachelor+), professional (73% management/business/science/arts), Democratic-leaning audience (51 D / 22 R / 19 NPP, Harris took 69%) with mixed renter-owner split (58/42) and 57% rent-burdened renters. Local-government priorities typically center on cost of living, housing cost, public safety, schools (highly relevant given the venue), parks, and active-transportation infrastructure. The 14% active-commute share (well above Chico norm) signals an audience that thinks about transportation as lived friction. Already partisan-aligned: differentiator is competence and specifics.",
  },

  // 19. Chico Junior High School
  "way/460975283": {
    brief: "",
    leadWith:
      "Meaningfully younger (38% age 18-34), college-educated (57% bachelor+), majority-renter (57%) Democratic audience (51 D / 21 R / 19 NPP, Harris took 69%). Local priorities typically center on housing cost, cost of living, public safety (homelessness, policing accountability), schools (highly relevant given the venue), mental-health services, and active-transportation infrastructure. Sanctuary-policy matters for the 8% Spanish-at-home subset. 79% turnout signals high engagement. Already partisan-aligned: differentiator is competence and specifics. Less likely to drive votes: fiscal-conservative framing, national-grievance topics.",
  },

  // 20. Senator Theater
  "way/460976024": {
    brief: "",
    leadWith:
      "Younger (40% age 18-34), racially diverse (33% Hispanic), college-educated (50% bachelor+), Democratic-leaning audience (51 D / 22 R / 19 NPP, Harris took 69%). Local-government priorities typically center on cost of living, housing cost, public safety (homelessness response, policing accountability and community relations), downtown vitality, schools, and active-transportation infrastructure. Sanctuary-policy matters for the Hispanic and 10% Spanish-at-home subset. Already partisan-aligned: differentiator is competence, specifics, and authentic Hispanic-community engagement. Spanish-language outreach is operationally useful.",
  },

  // ============================================================
  // DISTRICT 2 — top 10
  // ============================================================

  // 21. Butte College - Cosmetology & Barbering
  "node/12209917996": {
    brief: "",
    leadWith:
      "Younger-skewing (31% age 18-34), majority-renter (52%), mixed-income (42% under $50k, 22% in $125k+) audience with moderately-Democratic registration (42 D / 30 R / 19 NPP). Local-government priorities for mixed-income working-and-professional renters typically center on cost of living, housing cost, public safety, healthcare access, and schools for parents. Sanctuary-policy matters for the 8% Spanish-at-home subset. Top-of-ticket vote shifted +4 points D in 2024 — persuadable moderate-R share. 77% turnout is moderate-engaged.",
  },

  // 22. Neal Dow Elementary School
  "way/186727450": {
    brief: "",
    leadWith:
      "Young (43% age 18-34), heavily renter (70%), mostly-white (75%) Democratic-leaning audience (51 D / 23 R / 18 NPP) with 83% turnout and meaningful rent burden (59%). Local priorities for younger college-educated Democrats typically center on housing cost (dominant for renter-Dem voters), cost of living, public safety (homelessness, policing accountability), schools (highly relevant given the venue), mental-health services, and active-transportation infrastructure. Top-of-ticket vote shifted +6 points D in 2024 — consistent with broader young-renter-Dem patterns. Already partisan-aligned: competence and specifics differentiate.",
  },

  // 23. John A. McManus Elementary School
  "way/85087700": {
    brief: "",
    leadWith:
      "Mixed-age (28% 18-34, 26% 35-54, 15% 65+), mixed-tenure (52% renter, 48% owner) audience with slightly-Democratic registration (43 D / 29 R / 19 NPP). Local-government priorities for mixed-income, mixed-tenure California audiences typically center on cost of living, public safety, housing cost, healthcare access, schools (highly relevant given the venue), and infrastructure reliability. The income mix is somewhat bimodal — renters and owners weight different concerns, but cost of living and public safety bridge both. Top-of-ticket vote shifted +4 points D in 2024 — persuadable moderates.",
  },

  // 24. Fairview High School
  "way/84968698": {
    brief: "",
    leadWith:
      "Mixed-age (33% 18-34, 18% 65+), majority-owner (56%) audience with competitive registration (41 D / 31 R / 20 NPP). Local-government priorities for mixed-age owner-leaning competitive California suburban audiences typically center on public safety, cost of living, infrastructure reliability, government competence, and schools (for parents — highly relevant given the venue). Housing cost ranks below for the owner share but matters for the 44% renter share. Top-of-ticket vote shifted +5 points D in 2024 — persuadable moderate-R-leaning households on competence questions. 77% turnout.",
  },

  // 25. Oak Bridge Academy
  "node/13608269862": {
    brief: "",
    leadWith:
      "Heavily renter (75%), multifamily-leaning (52%), working-class (49% under $50k) audience with competitive R-leaning registration (39 D / 32 R / 20 NPP) but D-voting at the top of the ticket (Harris took 53%). Local-government priorities for working-class California renters regardless of partisan lean typically center on cost of living and wages, housing cost, public safety, healthcare access, and schools for parents. Less likely to move this audience: anti-density framing (renters live in the housing supply being argued about), abstract fiscal-conservative arguments. Top-of-ticket +4 point D shift — moderate-R persuadable on local issues.",
  },

  // 26. Shasta Union School
  "way/186727461": {
    brief: "",
    leadWith:
      "Predominantly Hispanic (54%), heavily Spanish-speaking (22% at home) audience with low college attainment (16%), low income (38% under $50k), and competitive R-leaning registration (38 D / 31 R / 21 NPP). Top-of-ticket vote shifted +10 points D in 2024 — biggest 2022-2024 shift in the D2 top-10. Local-government priorities for working-class Hispanic California voters typically center on cost of living and wages, housing cost, public safety, schools (highly relevant given the venue), jobs, and sanctuary-policy / equitable-enforcement. Hispanic voters are not a Democratic monolith — values-aligned framing (faith, family) cuts both ways. 70% turnout is below average — voter-engagement framing has real ROI. Spanish-language outreach is operationally essential.",
  },

  // 27. Bidwell Junior High School
  "way/85629476": {
    brief: "",
    leadWith:
      "Older-skewing (19% age 65+, 27% age 35-54), majority-owner (61%) audience with meaningful affluence (36% in $125k+) and moderate Democratic lean (44 D / 29 R / 19 NPP). Local-government priorities for older settled owner-occupied California Democrats typically center on public safety, cost of living, infrastructure reliability, government competence, schools (relevant given the venue), and quality-of-development decisions. Housing affordability matters as 'options for our kids when they grow up.' Top-of-ticket vote shifted +2 points D in 2024 — modest persuadable-moderate share. 76% turnout. Bring substance and detail.",
  },

  // 28. Mekkala Thai Cuisine
  "node/13608269857": {
    brief: "",
    leadWith:
      "Heavily renter (73%), multifamily-leaning (51%), working/lower-middle-income (49% under $50k) audience with competitive R-leaning registration (39 D / 32 R / 20 NPP) but D-voting at the top of the ticket — top shifted +4 points D in 2024. Local priorities for working-class California renters regardless of partisan lean typically center on cost of living and wages, housing cost, public safety, healthcare access, and schools for parents. Less likely to move this audience: anti-density framing (renters live in the housing supply being argued about), abstract fiscal-conservative arguments without concrete dollar impacts, culture-war wedges.",
  },
}
