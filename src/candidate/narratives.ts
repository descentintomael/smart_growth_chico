/**
 * Per-venue speaker briefings.
 *
 * Keyed by OSM ID (`way/...` or `node/...`). For the demo only Lakeside
 * Pavilion is hand-written; the full top-50-per-district pass is the next
 * step once the UI form is approved.
 */
export interface VenueBriefing {
  brief: string
  leadWith: string
}

export const VENUE_BRIEFINGS: Record<string, VenueBriefing> = {
  "way/868413772": {
    brief:
      "Lakeside Pavilion sits in a mixed-character residential neighborhood " +
      "in northeast D6. The walkable audience is sizable (1,341 voting-age " +
      "citizens) and unusually bimodal: 34% are 65+ — the highest of any D6 " +
      "venue — while 48% of households are renters, and 53% of those renters " +
      "are rent-burdened with 41% severely so (paying 50%+ of their income " +
      "on rent). It's a professional area (57% management/business roles) " +
      "that's 22% Spanish-speaking, 77% white, and overwhelmingly drives-" +
      "alone to work (73%) with a notable work-from-home share (13%). " +
      "Politically the neighborhood is competitive but trending Democratic " +
      "at the top of the ticket: thin D edge in registration (39 D / 36 R / " +
      "17 NPP), exceptional 85% turnout in 2024 (vs Butte's 77%), and a " +
      "clear partisan shift between cycles — Harris took 58% of the vote " +
      "here, up 6 points from Newsom's 52% in 2022.",
    leadWith:
      "Smart-growth and housing affordability framed for both sides of the " +
      "bimodal income split — property-value protection for the older " +
      "homeowner half, supply-side relief for the cost-burdened renter half. " +
      "Expect transit and walkability questions (the catchment has high " +
      "demand and near-zero supply for both). Senior services and " +
      "infrastructure as secondary topics. Avoid framing housing as " +
      "either-or between renters and owners — the bimodality means both " +
      "groups are in the same room.",
  },
}
