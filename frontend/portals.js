const COUNCIL_PORTALS = {
  "hertfordshire": (ref) => `https://planning.hertfordshire.gov.uk/Search/Results?query=${encodeURIComponent(ref)}`,
  "cheshire east": (ref) => `https://planning.cheshireeast.gov.uk/applicationdetails.aspx?search=${encodeURIComponent(ref)}`
};
export function portalLink(council, ref){
  const k = (council||"").toLowerCase().trim();
  if (COUNCIL_PORTALS[k]) return COUNCIL_PORTALS[k](ref);
  return `https://www.google.com/search?q=${encodeURIComponent(council+" "+ref)}`;
}
