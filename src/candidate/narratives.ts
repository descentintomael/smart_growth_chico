/**
 * Per-venue speaker briefings.
 *
 * Hand-written audience-priorities paragraphs for the top-10 venues in each
 * council district (28 unique venues after overlap). Auto-generated paragraphs
 * for ranks 11-50 live in catchment-demographics.json (added by
 * scripts/generate-venue-narratives.py); these hand-written entries take
 * precedence in the panel.
 *
 * Style: describe what topics likely matter to the audience, anchored to
 * documented polling regularities (PPIC Statewide Survey, Pew political
 * typology, AP-NORC issue tracking, ANES "most important problem" series).
 * Avoid coaching the candidate on what to say or pushing any policy frame —
 * just intelligence on the room.
 *
 * `brief` is currently not rendered by the panel; kept on the interface for
 * future use if the briefing block comes back.
 */
export interface VenueBriefing {
  brief: string
  leadWith: string
}

export const VENUE_BRIEFINGS: Record<string, VenueBriefing> = {
  // ============================================================
  // DISTRICT 6 — top 10
  // ============================================================

  // 1. Lakeside Pavilion — bimodal income + senior + meaningful renter share
  "way/868413772": {
    brief: "",
    leadWith:
      "This catchment's audience is bimodal — older homeowners (34% are 65+, 52% own) sharing the room with a cost-stressed renter half (48% renter, 53% of those rent-burdened at 30%+ of income). Each brings a different top-issue mix. For the older homeowner half, polling on similar demographics (PPIC Statewide Survey, Pew typology) consistently puts **public safety, property-tax / cost-of-living, infrastructure reliability, and government competence** at the top — with **healthcare and Medicare-touching federal policy** rising for the 65+ subset. For the renter half, **housing cost and availability** has ranked at or near the top of California renters' concerns continuously since 2018 in PPIC tracking; **cost of living** sits adjacent. **Climate** polls high in stated importance for the younger Dem-leaning portion but historically under-performs as a vote driver in local elections — high importance, lower revealed salience. Topics less likely to drive votes here: traditional fiscal-conservative framing, anti-density arguments, property-rights appeals, culture-war wedges. The 85% turnout (vs Butte's 77%) signals an already-engaged audience where competence and specificity differentiate more than partisan framing.",
  },

  // 2. Chico's Elks Lodge 423 — older SF-owner audience, fraternal venue
  "node/13565778876": {
    brief: "",
    leadWith:
      "An older, single-family-homeowner audience (81% own, 89% SF housing stock, 41% in $125k+ income) with high college attainment (45% bachelor+) and an 84% turnout that signals deep civic engagement — the fraternal-order venue itself attracts people for whom local civic participation is a habit. Issue-salience patterns for older, settled California homeowners in PPIC tracking and Pew typology research consistently put **public safety, property taxes and cost of living, infrastructure reliability,** and **quality of local government** at the top; **healthcare and Medicare-touching federal policy** rises in salience for the older subset. **Housing supply** is rarely vote-driving for this cohort; **climate** polls as high stated importance but historically under-performs as a vote driver in local elections. Registration is competitive (42 D / 32 R / 18 NPP) but the catchment voted 5 points more Democratic at the top of the ticket in 2024 than in 2022 — meaningful moderate-R crossover suggests a persuadable share. The high turnout signals a substance audience: details, fiscal arithmetic, and concrete-example specificity matter more than framing.",
  },

  // 3. Canyon Oaks Country Club — affluent, college-educated, small-sample audience
  "relation/19628096": {
    brief: "",
    leadWith:
      "The walking sample is small (122 residents) so demographic noise is high — what's robust here is the kind of person who joins a private country club in northeast Chico. That audience is reliably high-income (55% in $125k+), college-educated (68% bachelor+), mostly white (88%), and 45+. Polling regularities for this demographic in Pew typology research and AP-NORC professional-suburban tracking typically put **government competence, infrastructure reliability, public safety, schools** (for the parent subset), and **fiscal stewardship** at the top of concerns; **healthcare** rises for the older subset. **Cost of living** matters as inflation/quality-of-life pressure but typically not as housing affordability per se. **Climate** has higher revealed-importance for affluent college-educated Democrats than other clusters but typically still ranks below the cost-and-competence stack locally. Registration is competitive (39 D / 36 R) but the catchment voted 7 points more Democratic at the top of the ticket in 2024 than in 2022 — strong moderate-R crossover signal. They will check that you live in the neighborhood; assume the audience is informed and substance-oriented.",
  },

  // 4. Hotel Káterina — younger, more Hispanic-meaningful, working-class mixed
  "way/1391306494": {
    brief: "",
    leadWith:
      "A younger, more racially and income-mixed audience than most D6 catchments: 24% Hispanic, 10% Spanish-at-home, 29% age 18-34, 40% of households under $50k. Registration is moderately Democratic (42 D / 28 R / 21 NPP). Issue-salience patterns for working-class, Hispanic-meaningful California voters in PPIC tracking and Pew Hispanic-voter research consistently put **cost of living and wages** at the top, followed by **public safety, housing cost, healthcare access,** and — particularly for the Spanish-speaking subset — **federal immigration enforcement** (a national issue that bleeds into local races via sanctuary-city framing). **K-12 education** ranks high for parents; **climate** polls high in stated importance but rarely vote-driving for working-class voters. Turnout here is 76% — moderate compared to the 80%+ in established-homeowner pockets — so voter-engagement framing has more leverage than pure persuasion. Republican-leaning fiscal frames rarely connect; culture-war wedges underperform. The catchment voted 4 points more Democratic at the top of the ticket in 2024 than 2022.",
  },

  // 5. Butte College Skyway Center — east 20th / Skyway working-professional mixed
  "way/1486726820": {
    brief: "",
    leadWith:
      "A younger, working/professional mixed audience: 29% age 18-34, 27% Hispanic, 47% renter, 37% of households under $50k, 60% in management/business/science/arts occupations. Registration is Democratic-leaning (41 D / 28 R / 21 NPP). Issue-salience patterns from PPIC tracking and AP-NORC research on mixed-income California renters in the 25-50 band consistently put **cost of living and wages, housing cost,** and **public safety** (typically framed around homelessness response and police-community relations rather than violent-crime statistics) at the top; **healthcare access** and **K-12 education** rank high for parents. **Climate** polls as high stated importance for younger Dem-leaning voters but historically under-performs as a vote driver in local elections. **Federal immigration enforcement** is a cross-pressure for the 10% Spanish-at-home subset. The top-of-ticket vote shifted only marginally between 2022 and 2024 (1 point), unusual for an otherwise-shifting demographic and suggesting a more settled local political identity than registration alone implies. 74% turnout is moderate — voter-engagement framing carries weight alongside persuasion.",
  },

  // 6. Tbar — same neighborhood as Skyway/Butte College
  "node/13137263368": {
    brief: "",
    leadWith:
      "Younger working/professional mixed audience (29% age 18-34, 28% Hispanic, 47% renter, 60% management/business/science/arts) with Democratic-leaning registration (41 D / 28 R / 21 NPP) and 38% of households under $50k. Issue-salience patterns from PPIC and AP-NORC tracking for mixed-income California renters in the 25-50 age band consistently put **cost of living and wages, housing cost,** and **public safety** (framed around homelessness response and policing accountability rather than violent-crime rates) at the top of concerns; **healthcare access** and **K-12 education** rank high for parents. **Climate** polls high in stated importance for the younger Dem-leaning portion but consistently under-performs as a vote driver in local elections. **Federal immigration enforcement** is a meaningful cross-pressure for the 10% Spanish-at-home share. The 2022-vs-2024 top-of-ticket shift was negligible (~1 point), unusual in this demographic and suggesting an unusually stable local political identity. Turnout is moderate (74%); registration and turnout framing has measurable bite alongside persuasion.",
  },

  // 7. Butte College (main campus) — same neighborhood again
  "way/85465037": {
    brief: "",
    leadWith:
      "A younger, working-and-professional mixed audience (29% age 18-34, 28% Hispanic, 47% renter, 60% management/business/science/arts roles) with Democratic-leaning registration (41 D / 28 R / 21 NPP). Issue-salience patterns from PPIC tracking and AP-NORC research on mixed-income California renters consistently put **cost of living and wages, housing cost, public safety** (framed around homelessness and police-community relations), **healthcare access,** and **K-12 education** (high for parents) at the top of concerns. **Climate** polls high in stated importance for younger Dem-leaning voters but historically under-performs as a vote driver locally. **Federal immigration enforcement** is a cross-pressure for the 10% Spanish-at-home subset. Note that as the Butte College main-campus venue, actual forum attendees may include a meaningful student-and-faculty share whose top concerns skew further toward **college affordability, student debt, climate, and reproductive rights** than the broader walking catchment suggests. 74% turnout is moderate; voter-engagement framing has leverage alongside persuasion.",
  },

  // 8. Little Chico Creek Elementary School — heavily renter, multifamily, working-class
  "way/1104515170": {
    brief: "",
    leadWith:
      "A heavily renter (74%), multifamily-dense (71% in 2-9+ unit buildings), working-class (42% of households under $50k) audience with Democratic-leaning registration (42 D / 30 R / 19 NPP) and 79% turnout. Issue-salience patterns for low-income renter audiences in PPIC tracking and AP-NORC research consistently put **housing cost and availability** (PPIC's Statewide Survey has shown housing in the top concerns for California renters almost every year since 2018), **wages and cost of living,** and **public safety** (typically framed around homelessness, police interactions, and equitable enforcement rather than violent-crime statistics) at the top; **healthcare access** and **K-12 education** rank high (especially given the school venue). **Federal immigration enforcement** is a real cross-pressure for the 10% Spanish-at-home subset. **Climate** polls high in stated importance but historically under-performs as a vote driver for working-class voters. Topics less likely to move this audience: traditional fiscal-conservative framing, anti-density arguments, culture-war wedges. The catchment voted 5 points more Democratic at the top of the ticket in 2024 than in 2022.",
  },

  // 9. Marigold Elementary School — established SF-owner, family, affluent
  "way/84969479": {
    brief: "",
    leadWith:
      "An established single-family-homeowner audience (82% own, 94% SF housing stock) with a family skew (27% under 18, 35% age 35-54) and meaningful affluence (44% of households in $125k+; 45% college-educated). Registration is competitive-Democratic (42 D / 32 R / 18 NPP) with high turnout (84%). Issue-salience patterns for affluent, parent-heavy, owner-occupied California audiences in PPIC tracking and Pew typology research consistently put **K-12 schools** at or near the top (especially relevant given the school venue), followed by **public safety, cost of living, infrastructure reliability,** and **government competence**. **Housing affordability** ranks lower than it does for renter audiences but matters as 'good housing options for our kids when they grow up' framing. **Climate** has higher revealed-importance for college-educated parents than for older homeowners and ranks meaningfully but typically below the schools-and-safety stack in local elections. The catchment voted 5 points more Democratic at the top of the ticket in 2024 than 2022 — moderate-R-leaning households are persuadable on local-government-competence questions. High turnout + high engagement: substance-and-specificity audience.",
  },

  // 10. Sierra Nevada Brewing Co Taproom — renter-majority, younger, destination venue
  "node/9796268718": {
    brief: "",
    leadWith:
      "A renter-majority (66%), multifamily-leaning (61%) audience skewing younger (28% age 18-34) with a moderately-low-income profile (41% of households under $50k) and Democratic-leaning registration (42 D / 29 R / 20 NPP). Issue-salience patterns for younger renter-majority California Democrats in PPIC tracking and Pew research consistently put **housing cost and availability** at the top — California renters have rated housing as a top concern almost continuously in PPIC's Statewide Survey since 2018 — with **cost of living** and **wages** adjacent. **Public safety** is reliably in the top 5 for this demographic but framed around homelessness response and police-community relations rather than violent-crime statistics. **Climate** polls high in stated importance for younger Dem voters but historically under-performs as a vote driver in local elections. **Federal immigration enforcement** is a cross-pressure for the 10% Spanish-at-home subset. As a Sierra Nevada destination venue, actual forum attendees may skew older and more affluent than the walking catchment suggests — the room may carry a more 'civic-event-going professional' demographic mix than the immediate neighborhood demographics imply.",
  },

  // ============================================================
  // DISTRICT 4 — top 10
  // ============================================================

  // 11. Butte County Library - Chico Branch (D4 + D2)
  "way/461041054": {
    brief: "",
    leadWith:
      "A heavily Democratic-leaning audience (51 D / 22 R / 19 NPP, Harris took 69% in 2024) with high college attainment (55% bachelor+), majority-renter housing (59% renter, 58% rent-burdened at 30%+ of income), and a meaningful 23% Hispanic / 7% Spanish-at-home share. Issue-salience patterns for college-educated California Democrats in PPIC tracking and Pew typology research (Establishment Liberal / Outsider Left clusters) consistently put **housing cost and availability** at the top — the singular issue for renter-Dem audiences statewide since 2018 — followed by **cost of living and wages, public safety** (framed around homelessness response and policing accountability), **climate** (one of the few demographics where climate registers as a vote driver and not just stated importance), and **reproductive rights** (persistently elevated post-Dobbs). **Federal immigration enforcement** is a salient federal-touch concern for the Hispanic and Spanish-speaking subset. The audience is already partisan-aligned with a Democratic candidate; persuasion happens on competence, specificity, and local-issue depth — values, partisan signaling, and broad framing land in friendly territory but won't differentiate among same-side rivals.",
  },

  // 12. Enloe Conference Center
  "relation/18020131": {
    brief: "",
    leadWith:
      "A young (44% age 18-34!), heavily renter (68%), Democratic-leaning audience (49 D / 20 R / 21 NPP, Harris took 68% in 2024) with severe rent burden (64% of renters paying 30%+ of income). Issue-salience patterns for young California renters in PPIC tracking are sharply weighted toward **housing cost** — the singular issue for this demographic since 2018 — followed by **wages and cost of living, mental health and healthcare access, public safety** (homelessness, police accountability), and **climate** (real revealed-importance for younger Dem voters, unlike for older voters where stated importance exceeds revealed). **Reproductive rights** persistently elevated post-Dobbs. **College affordability and student debt** rank high for the student-adjacent share. The audience is solidly aligned with a Democratic candidate; differentiation comes from specificity and local-issue depth rather than values or partisan framing. Turnout is 76% (high for this age demographic) — the audience is already mobilized; the 2024-vs-2022 shift was negligible (~1 point), suggesting a stable local political identity. Federal-political-grievance topics and culture-war wedges underperform.",
  },

  // 13. California State University, Chico
  "way/28551484": {
    brief: "",
    leadWith:
      "An overwhelmingly student audience (76% age 18-34, 93% renter, 74% of households under $50k, 74% rent-burdened) with Democratic-leaning registration (48 D / 17 R / 23 NPP) and 70% turnout. Issue-salience patterns for California college students in PPIC tracking and Pew college-attendee research cluster around **college affordability and student debt, housing cost, wages and job market, mental health,** and **climate** — this is one of the few demographics where climate ranks in the top 3 for vote-driving salience, not just stated importance. **Reproductive rights** persistently elevated post-Dobbs. **Public safety** ranks high but typically framed around mental-health crisis response, sexual assault on campus, and police-student interactions rather than property crime. The 2022-vs-2024 top-of-ticket shift was essentially flat (~1 point R drift), atypical for this demographic and worth noting — could reflect specifically how the local campus political climate has settled. For pre-aligned student audiences, registration drives and absentee-ballot logistics often carry more electoral impact than persuasion messaging. Federal-grievance and culture-war framing underperform; broad partisan signaling lands in friendly territory but doesn't differentiate.",
  },

  // 14. Citrus Avenue Elementary School — young, renter-heavy, CSU-adjacent
  "way/28551317": {
    brief: "",
    leadWith:
      "A young (59% age 18-34), heavily renter (78%), college-educated (49% bachelor+) audience with strong Democratic lean (49 D / 19 R / 22 NPP, Harris took 68%) and high rent burden (63% of renters at 30%+ of income). Issue-salience patterns for young, college-educated California renters in PPIC tracking and Pew research weight strongly toward **housing cost** (PPIC's Statewide Survey has shown this as the dominant issue for renters under 35 almost every year since 2018), followed by **cost of living and wages, climate** (this is one of the few demographics where climate registers as a vote driver, not just stated importance), **public safety** (homelessness, police-community), and **reproductive rights** (persistently elevated post-Dobbs). **Healthcare access** ranks high. **K-12 education** is salient given the school venue. The audience is solidly Democratic-aligned; differentiator is competence and policy specifics — values are aligned, broad framing won't differentiate. Federal-grievance and culture-war wedges underperform. The 2022-vs-2024 top-of-ticket shift was negligible — politically stable young-renter-Dem catchment.",
  },

  // 15. CARD Community Center
  "way/1392880190": {
    brief: "",
    leadWith:
      "A racially diverse (35% Hispanic), highly educated (54% bachelor+), middle-class-to-affluent audience (30% in $125k+) with strong Democratic lean (52 D / 22 R / 18 NPP, Harris took 69%) and high turnout (81%). Issue-salience patterns for diverse, college-educated California Democrats in PPIC tracking and Pew Hispanic/college-educated research consistently put **housing cost and availability, cost of living, public safety** (framed around homelessness and equitable enforcement), **education,** and **healthcare access** at the top of concerns. **Climate** has higher revealed-importance for college-educated Democrats than for other clusters but typically still ranks below the cost-and-services stack locally. **Federal immigration enforcement** is a real cross-pressure for the Hispanic and Spanish-speaking subset (8% Spanish-at-home), particularly when sanctuary-city debates surface. **Reproductive rights** persistently elevated post-Dobbs. The audience is already partisan-aligned with a Democratic candidate; competence, specificity, and local-issue depth differentiate more than framing. High turnout + high engagement: assume the audience is informed and reads policy detail.",
  },

  // 16. Gateway Science Museum
  "way/546953163": {
    brief: "",
    leadWith:
      "A young (49% age 18-34), college-educated (54% bachelor+), renter-majority (64%) Democratic-leaning audience (50 D / 21 R / 19 NPP, Harris took 68%) with high rent burden (60% of renters at 30%+ of income). Issue-salience patterns for college-educated young California Democrats in PPIC tracking weight strongly toward **housing cost, cost of living and wages, climate** (real revealed-importance for this demographic, unlike most others), **public safety** (homelessness response and policing accountability framings), **mental health and healthcare access,** and — persistently post-Dobbs — **reproductive rights**. **Education** ranks high for the parent and student-adjacent shares. The audience is solidly Democratic; differentiator is competence and specifics. Turnout is 78% (high for younger renters), suggesting an engaged and informed audience. Topics less likely to drive votes here: traditional fiscal-conservative framing, anti-density arguments, federal-political-grievance topics, culture-war wedges. The 2022-vs-2024 top-of-ticket shift was minimal, consistent with the broader downtown-Chico pattern of stable Dem identity.",
  },

  // 17. Creekside Rose Garden — same neighborhood as CARD
  "way/1416654666": {
    brief: "",
    leadWith:
      "A racially diverse (35% Hispanic), highly educated (54% bachelor+), middle-class-to-affluent audience (30% in $125k+, 40% under $50k — meaningfully bimodal) with strong Democratic lean (52 D / 22 R / 18 NPP, Harris took 69%) and high turnout (81%). Issue-salience patterns for college-educated California Democrats in PPIC tracking consistently put **cost of living, housing cost, public safety** (homelessness response, equitable enforcement), **education, healthcare access,** and **reproductive rights** (persistently elevated post-Dobbs) at the top. **Climate** has higher revealed-importance for college-educated Dems than other clusters but ranks below the cost-and-services stack locally. **Federal immigration enforcement** is a real cross-pressure for the Hispanic subset, particularly when sanctuary-city debates surface. The audience is solidly partisan-aligned; the persuasion challenge is competence and specificity, not values or framing. Topics less likely to drive votes here: traditional fiscal-conservative framing, anti-density framing, federal-grievance topics, culture-war wedges.",
  },

  // 18. Hooker Oak Elementary School (D4 + D2)
  "way/186727445": {
    brief: "",
    leadWith:
      "A college-educated (55% bachelor+), professional (73% management/business/science/arts), Democratic-leaning audience (51 D / 22 R / 19 NPP, Harris took 69%) with a mixed renter-owner split (58% renter, 42% owner) and meaningful rent burden (57% of renters at 30%+ of income). Issue-salience patterns for college-educated California Democrats in PPIC and Pew tracking consistently put **housing cost and availability, cost of living, public safety** (homelessness and police-community framing), **education** (highly salient given the school venue), **healthcare access,** and **climate** (real revealed-importance for this demographic) at the top of concerns. **Reproductive rights** persistently elevated post-Dobbs. The 14% active-commute share (transit/bike/walk — high for Chico) signals an audience that thinks about transportation infrastructure as a lived issue, not abstract policy. The audience is solidly Democratic-aligned; differentiator is competence and specificity. Federal-grievance and culture-war framing underperform; broad partisan signaling lands in friendly territory but won't differentiate.",
  },

  // 19. Chico Junior High School
  "way/460975283": {
    brief: "",
    leadWith:
      "A meaningfully younger (38% age 18-34), college-educated (57% bachelor+), majority-renter (57%) Democratic audience (51 D / 21 R / 19 NPP, Harris took 69%) with significant rent burden (52% of renters at 30%+ of income). Issue-salience patterns for younger college-educated California Democrats in PPIC tracking weight strongly toward **housing cost, cost of living and wages, public safety** (homelessness response and policing accountability), **education** (especially given the school venue context), **healthcare access, climate** (real revealed-importance for this demographic) and **reproductive rights** (persistently post-Dobbs) in the top concerns. **Federal immigration enforcement** is a meaningful cross-pressure for the 8% Spanish-at-home subset. The audience is solidly Democratic-aligned; persuasion happens on competence, specificity, and local-issue depth rather than values or framing. 79% turnout signals high engagement. Federal-grievance topics, traditional fiscal-conservative framing, and culture-war wedges underperform with this audience.",
  },

  // 20. Senator Theater
  "way/460976024": {
    brief: "",
    leadWith:
      "A younger (40% age 18-34), racially diverse (33% Hispanic, 10% Spanish-at-home), college-educated (50% bachelor+), Democratic-leaning audience (51 D / 22 R / 19 NPP, Harris took 69%). Issue-salience patterns for younger, Hispanic-meaningful, Democratic-leaning California voters in PPIC and Pew Hispanic-voter tracking consistently put **cost of living and wages, housing cost, public safety** (framed around homelessness response and police-community relations), **education,** and — particularly for the Hispanic subset — **federal immigration enforcement** (a national issue that spills into local races via sanctuary-city framing) at the top of concerns. **Healthcare access** ranks high. **Climate** has real revealed-importance for younger college-educated Democrats but typically ranks below the economic-cost stack in local elections. **Reproductive rights** persistently elevated post-Dobbs. The audience is solidly Democratic-aligned; differentiator is competence, specificity, and authentic engagement with Hispanic-community concerns. Culture-war wedges and federal-grievance framing underperform; Spanish-language outreach is operationally useful, not optional.",
  },

  // ============================================================
  // DISTRICT 2 — top 10
  // ============================================================

  // 21. Butte College - Cosmetology & Barbering
  "node/12209917996": {
    brief: "",
    leadWith:
      "A younger-skewing (31% age 18-34), majority-renter (52%), mixed-income audience (42% of households under $50k, 22% in $125k+) with moderately-Democratic registration (42 D / 30 R / 19 NPP). Issue-salience patterns for mixed-income, working-and-professional California renters in PPIC tracking consistently put **cost of living and wages, housing cost, public safety,** and **healthcare access** at the top of concerns; **K-12 education** ranks high for parents. **Climate** polls high in stated importance for the younger Dem-leaning portion but historically under-performs as a vote driver in local elections. **Federal immigration enforcement** is a cross-pressure for the 8% Spanish-at-home subset. The catchment voted 4 points more Democratic at the top of the ticket in 2024 than 2022 — moderate-R voters are persuadable on local issues. 77% turnout is moderate-engaged. Topics less likely to move this audience: anti-density framing, federal-political-grievance topics from either direction, culture-war wedges.",
  },

  // 22. Neal Dow Elementary School
  "way/186727450": {
    brief: "",
    leadWith:
      "A young (43% age 18-34!), heavily renter (70%), mostly-white (75%) Democratic-leaning audience (51 D / 23 R / 18 NPP) with high turnout (83%) and meaningful rent burden (59% of renters at 30%+ of income). Issue-salience patterns for younger college-educated California Democrats in PPIC tracking weight strongly toward **housing cost** (the dominant local issue for renter-Dem audiences statewide), followed by **cost of living, public safety** (framed around homelessness response and police-community relations), **climate** (real revealed-importance for this demographic), and **reproductive rights** (persistently elevated post-Dobbs). **Healthcare access and mental health services** rank high. The catchment shifted 6 points more Democratic at the top of the ticket in 2024 than 2022 — consistent with broader young-renter-Dem migration patterns statewide. High turnout + young + Dem-aligned: an informed, engaged audience where differentiation is competence and specifics, not values. Federal-grievance and culture-war wedges underperform.",
  },

  // 23. John A. McManus Elementary School
  "way/85087700": {
    brief: "",
    leadWith:
      "A mixed-age (28% 18-34, 26% 35-54, 15% 65+), mixed-tenure (52% renter, 48% owner) audience with slightly-Democratic registration (43 D / 29 R / 19 NPP). Issue-salience patterns for mixed-income, mixed-tenure California audiences in PPIC tracking and AP-NORC research consistently put **cost of living, public safety, housing cost, healthcare access,** and **education** (highly salient given the school venue) at the top of concerns. The income mix (40% under $50k, 24% in $125k+) means the audience is somewhat bimodal — renters and owners weight different issues, but cost-of-living and public safety bridge both. **Federal immigration enforcement** is a cross-pressure for the 9% Spanish-at-home subset. The catchment voted 4 points more Democratic at the top of the ticket in 2024 than 2022 — persuadable moderates are in the room. **Climate** polls high in stated importance but typically under-performs as a vote driver in local elections for mixed-income audiences.",
  },

  // 24. Fairview High School — mixed-age, slightly older, R-leaning competitive
  "way/84968698": {
    brief: "",
    leadWith:
      "A mixed-age (33% 18-34, 18% 65+), majority-owner (56%) audience with competitive registration (41 D / 31 R / 20 NPP). Issue-salience patterns for mixed-age, owner-leaning, competitive-registration California suburban audiences in PPIC and AP-NORC tracking consistently put **public safety, cost of living, infrastructure reliability, government competence,** and — particularly for parents — **K-12 schools** at the top of concerns. **Housing cost** ranks below for the owner share but matters for the 44% renter share. **Healthcare access and Medicare-touching federal policy** rises in salience for the older subset. **Climate** polls as moderate stated importance but rarely vote-driving locally for competitive audiences. The catchment voted 5 points more Democratic at the top of the ticket in 2024 than 2022 — moderate-R-leaning voters are persuadable on local-government-competence questions. 77% turnout signals decent engagement. Federal-political-grievance framing (from either side) typically under-performs in audiences where partisan registration is competitive.",
  },

  // 25. Oak Bridge Academy — renter-heavy but R-leaning
  "node/13608269862": {
    brief: "",
    leadWith:
      "A heavily renter (75%), multifamily-leaning (52%), working-class (49% under $50k) audience with competitive R-leaning registration (39 D / 32 R / 20 NPP) — but the catchment voted Democratic at the top of the ticket (Harris 53%, Newsom 49% in 2022). Issue-salience patterns for working-class, mixed-political California renters in AP-NORC tracking and Pew research consistently put **cost of living and wages, housing cost** (this ranks high for renter audiences regardless of partisan lean), **public safety, healthcare access,** and **K-12 education** at the top of concerns. **Federal immigration enforcement** is a real concern for some — including some R-leaning voters approaching it from a values frame rather than a worker-protection frame. **Climate** ranks low for vote-driving with working-class voters. The 4-point Democratic shift at the top of the ticket between cycles suggests moderate-R voters are persuadable on local issues. Less likely to move this audience: anti-density framing (renters here live in the housing supply being argued about), pure-fiscal-conservative framing without specific costs named, culture-war wedges from either direction.",
  },

  // 26. Shasta Union School — heavily Hispanic, working-class, R-leaning-trending-D
  "way/186727461": {
    brief: "",
    leadWith:
      "A predominantly Hispanic (54%), heavily Spanish-speaking (22% at home) audience with low college attainment (16%), low income (38% under $50k), and competitive R-leaning registration (38 D / 31 R / 21 NPP) — though the catchment voted 10 points more Democratic at the top of the ticket in 2024 than in 2022, the largest 2022-2024 shift in the D2 top-10. Issue-salience patterns for working-class Hispanic California voters in PPIC and Pew Hispanic-voter tracking consistently put **cost of living and wages, housing cost, public safety, healthcare access,** and — uniquely high here — **federal immigration enforcement** at the top of concerns. **K-12 education** ranks very high for parents (especially given the school venue context). **Jobs and economic opportunity** rank above climate or environmental framing. Hispanic working-class voters are not a monolithic Democratic bloc — values-aligned issues (faith, family, immigration framing) can move some toward Republicans, but cost-of-living and concrete-policy framing tend to favor Democrats. 70% turnout is below the catchment average — voter-engagement framing has real ROI here. Spanish-language outreach is operationally important, not optional.",
  },

  // 27. Bidwell Junior High School — older, settled, slightly affluent, D-leaning
  "way/85629476": {
    brief: "",
    leadWith:
      "An older-skewing (19% age 65+, 27% age 35-54), majority-owner (61%) audience with meaningful affluence (36% in $125k+, only 26% under $50k) and moderate Democratic lean (44 D / 29 R / 19 NPP). Issue-salience patterns for older, settled, owner-occupied California Democrats in PPIC and Pew tracking consistently put **public safety, cost of living, infrastructure reliability, government competence, healthcare** (especially Medicare-touching federal policy), and **K-12 schools** in the top concerns. **Housing affordability** ranks lower than for renter audiences but matters as 'good housing options for our kids when they grow up' framing. **Climate** polls as moderate-importance for owner-Dem audiences but typically ranks below the cost-and-competence stack in local elections. The catchment voted 2 points more Democratic at the top of the ticket in 2024 than 2022 — registration is meaningfully Democratic but moderate-R voters in the catchment are persuadable on local-government-competence questions. 76% turnout is solid; substance and detail differentiate.",
  },

  // 28. Mekkala Thai Cuisine — renter-heavy, R-leaning competitive
  "node/13608269857": {
    brief: "",
    leadWith:
      "A heavily renter (73%), multifamily-leaning (51%), working/lower-middle income (49% under $50k) audience with competitive R-leaning registration (39 D / 32 R / 20 NPP) — though the catchment voted 4 points more Democratic at the top of the ticket in 2024 than 2022. Issue-salience patterns for mixed-political working-class California renters in AP-NORC and Pew tracking consistently put **cost of living and wages, housing cost** (this ranks high for renter audiences regardless of partisan lean), **public safety, healthcare access,** and **K-12 education** at the top of concerns. **Federal immigration enforcement** is a salient cross-pressure for some — including some R-leaning voters approaching it from a values frame. **Climate** ranks low for vote-driving with working-class voters. Less likely to move this audience: anti-density framing (renters here live in the housing supply being targeted), abstract fiscal-conservative framing without specific costs named, culture-war wedges from either direction. Moderate-R voters in the catchment are persuadable on competence and specifics.",
  },
}
