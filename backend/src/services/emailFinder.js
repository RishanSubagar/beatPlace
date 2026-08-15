// Lightweight email discovery stub.
// Replace with real search / people-API integration (SerpAPI, Hunter, Clearbit, etc.).

// Parse artist input (comma/newline separated) and log when called.
function parseArtists(artistsStr) {
  const list = (artistsStr || '')
    .split(/[\n,]+/)
    .map(s => s.trim())
    .filter(Boolean)

  console.log('artists done parsing:', list.length, list)
  return list
}

// Find emails for given artist names and log discovery counts when called.
async function findEmailsForArtists(artists) {
  const out = {}
  for (const a of artists) {
    const name = a.trim()
    if (!name) continue
    // create a naive normalized handle for demo purposes
    const norm = name.toLowerCase().replace(/\s+/g, '.').replace(/[^a-z0-9.]/g, '')
    out[name] = [
      `${norm}@example.com`,
      `contact@${norm}music.com`
    ]
  }

  // count discovered emails and log
  let total = 0
  for (const k of Object.keys(out)) total += (out[k] || []).length
  console.log('found', total, 'emails')

  // Log each discovered email per artist for visibility
  for (const artist of Object.keys(out)) {
    console.log('discovered for', artist + ':', out[artist])
  }

  return out
}

module.exports = { parseArtists, findEmailsForArtists };
