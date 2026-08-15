// Simple stubbed email finder. Replace with real search / people-API integration.
async function findEmailsForArtists(artists) {
  const out = {};
  for (const a of artists) {
    const name = a.trim();
    if (!name) continue;
    const norm = name.toLowerCase().replace(/\s+/g, '.').replace(/[^a-z0-9.]/g, '');
    out[name] = [
      `${norm}@example.com`,
      `contact@${norm}music.com`
    ];
  }
  return out;
}

module.exports = { findEmailsForArtists };
