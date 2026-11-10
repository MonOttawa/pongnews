// Amazon Associates configuration.
//
// The tag is EMPTY by default: links point to Amazon but earn nothing.
// To activate monetization after Amazon Associates approval:
//   1. Add PUBLIC_AMAZON_TAG=yourtag-20 to ~/Projects/pongnews/.env
//      (or hardcode it below)
//   2. Rebuild + redeploy. Every equipment link site-wide starts
//      carrying the tag immediately.
//
// Amazon Operating Agreement requires rel="sponsored" (or nofollow) on
// affiliate links and the FTC disclosure -- both handled in
// EquipmentPick.astro. Do not remove them when the tag is active.

export const AMAZON_TAG: string = import.meta.env.PUBLIC_AMAZON_TAG ?? '';

export function amazonUrl(asin: string): string {
  const base = `https://www.amazon.com/dp/${asin}`;
  return AMAZON_TAG ? `${base}/?tag=${AMAZON_TAG}` : base;
}

export const AMAZON_TAG_ACTIVE = AMAZON_TAG.length > 0;
