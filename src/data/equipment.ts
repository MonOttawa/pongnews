// Equipment catalog for the science-backed equipment picks.
// Every product verified live on Amazon (ASIN resolves to the exact
// listing) on 2026-11-10. Price bands are conservative ranges observed
// at verification time; Amazon prices move, so we never print an exact
// number on the site.
//
// `evidence` links each pick to the pongnews.com research that makes
// the recommendation credible. Update `lastVerified` when re-checking
// ASINs (monthly is plenty).

export interface EquipmentItem {
  id: string;
  name: string;
  brand: string;
  category: string;
  asin: string;
  priceBand: string;
  bestFor: string;
  why: string;
  researchSlug?: string; // pongnews.com article backing the recommendation
}

export const EQUIPMENT: EquipmentItem[] = [
  {
    id: 'stiga-apex',
    name: 'STIGA Apex Table Tennis Racket',
    brand: 'STIGA',
    category: 'Paddle',
    asin: 'B003JJW5HA',
    priceBand: '$20-35',
    bestFor: 'Your first racket',
    why: 'A control-first beginner racket (ACS Technology) at a price that makes trying table tennis a no-brainer. Research keeps showing the health gains come from consistent play, not expensive gear -- control-oriented equipment keeps rallies alive, and longer rallies mean more of the movement and attention benefits studies measure.',
    researchSlug: 'largest-sport-longevity-study-racquet-sports-5-years',
  },
  {
    id: 'killerspin-jet200',
    name: 'Killerspin JET200 Paddle',
    brand: 'Killerspin',
    category: 'Paddle',
    asin: 'B002GJY338',
    priceBand: '$25-35',
    bestFor: 'Older adults and Parkinson\u2019s players',
    why: 'At roughly 165 g assembled, the JET200 sits at the light end of premade paddles, with a manufacturer control rating of 9/10. Light weight matters for players with reduced grip strength or tremor -- the NeuroPong program for Parkinson\u2019s showed benefits from regular play with manageable, forgiving equipment.',
    researchSlug: 'neuropong-table-tennis-parkinsons-rct',
  },
  {
    id: 'stiga-talon',
    name: 'STIGA Talon Performance Racket',
    brand: 'STIGA',
    category: 'Paddle',
    asin: 'B07ZGDQYS6',
    priceBand: '$30-60',
    bestFor: 'Stepping up your game',
    why: 'A mid-tier performance racket (Nano Composite and ACS technologies for speed and spin) for players whose rallies are getting serious. Faster, spinnier play raises the cognitive load -- exactly the open-skill challenge the research links to sharper attention and executive function.',
    researchSlug: 'open-skill-taxonomy-595-athletes-cognitive-test',
  },
  {
    id: 'prospin-starter-set',
    name: 'PRO-SPIN Portable Ping Pong Set',
    brand: 'PRO-SPIN',
    category: 'Starter set',
    asin: 'B078XKSQ41',
    priceBand: '$25-40',
    bestFor: 'Starting without a table',
    why: 'Retractable net, two paddles, three balls, and a case -- clamps onto any table up to 72 inches. The single biggest barrier to the health benefits is simply having a place to play; an any-table set removes it for the price of a takeout dinner.',
    researchSlug: 'table-tennis-brain-alzheimers-defense',
  },
  {
    id: 'prospin-net',
    name: 'PRO-SPIN Retractable Ping Pong Net (72")',
    brand: 'PRO-SPIN',
    category: 'Net',
    asin: 'B0F6QB5L9B',
    priceBand: '$15-19',
    bestFor: 'Turning any table into a court',
    why: 'Spring-loaded retractable net with clamps that fit tables up to 72 inches wide and 2 inches thick, plus a mesh storage bag. The cheapest possible upgrade to daily play at home -- no dedicated table, no assembly, no storage problem.',
  },
  {
    id: 'joola-training-balls',
    name: 'JOOLA Training 3-Star Balls (12/60/120 pack)',
    brand: 'JOOLA',
    category: 'Balls',
    asin: 'B0DHGH5F65',
    priceBand: '$15-30',
    bestFor: 'Never running out mid-drill',
    why: 'Regulation 40+ mm three-star training balls in white or orange, sold in 12, 60, or 120 packs. Drills and robot practice eat balls; a bulk pack is what makes the sustained, rhythmic practice sessions used in the intervention studies actually happen.',
  },
  {
    id: 'joola-inside-13',
    name: 'JOOLA Inside 13 Indoor Table',
    brand: 'JOOLA',
    category: 'Table',
    asin: 'B0DZN8RXCF',
    priceBand: 'around $330',
    bestFor: 'A real table at home',
    why: '9,000+ ratings, 10-minute assembly, folds for storage, and includes a single-player playback mode -- the feature that matters most for anyone building a solo daily habit. An at-home table is the difference between intending to play and actually playing three times a week.',
    researchSlug: 'table-tennis-walking-heart-combo-rct',
  },
  {
    id: 'stiga-xtr-outdoor',
    name: 'STIGA XTR All-Weather Outdoor Table',
    brand: 'STIGA',
    category: 'Table',
    asin: 'B01JKJ8OPE',
    priceBand: '$500-650',
    bestFor: 'Patios, garages, backyards',
    why: 'Waterproof aluminum composite surface built for outdoor play, so weather stops being an excuse. Outdoor tables also tend to attract neighbors and family -- and the social side of table tennis is one of the strongest drivers of the mental-health benefits in the research.',
    researchSlug: 'table-tennis-nature-medicine-adolescent-obesity-rct',
  },
  {
    id: 'ipong-v300',
    name: 'iPong V300 Training Robot',
    brand: 'JOOLA iPong',
    category: 'Robot',
    asin: 'B016A7UMV8',
    priceBand: '$135-190',
    bestFor: 'Practicing alone',
    why: 'Serves regulation 40 mm balls automatically so you can drill without a partner. Home-based rehab and training studies work because practice is available on demand -- a robot puts a serving machine on your own table for roughly the cost of two months of a gym membership.',
    researchSlug: 'table-tennis-boosts-brain-waves-stroke-rehabilitation',
  },
];

export const EQUIPMENT_BY_ID: Record<string, EquipmentItem> = Object.fromEntries(
  EQUIPMENT.map((item) => [item.id, item]),
);

export const EQUIPMENT_LAST_VERIFIED = '2026-11-10';
