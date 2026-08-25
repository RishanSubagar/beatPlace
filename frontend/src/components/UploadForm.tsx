import React, { useState } from 'react'
import axios from 'axios'
import Box from '@mui/material/Box'
import TextField from '@mui/material/TextField'
import Button from '@mui/material/Button'
import LinearProgress from '@mui/material/LinearProgress'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import Typography from '@mui/material/Typography'

// Upload form: file input, artists, message, and send button.
export default function UploadForm() {
  const [file, setFile] = useState<File | null>(null)
  const [artists, setArtists] = useState('')
  const [message, setMessage] = useState('')
  const [fromEmail, setFromEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any | null>(null)

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) return alert('Please choose a ZIP file')
    if (!artists.trim()) return alert('Please enter at least one artist')
    const fd = new FormData()
    fd.append('zip', file)
    fd.append('artists', artists)
    fd.append('message', message)
    fd.append('fromEmail', fromEmail)

    try {
      setLoading(true)
      const res = await axios.post('/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      setResult(res.data)
    } catch (err: any) {
      setResult({ error: err.response?.data?.detail || err.message || String(err) })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box component="form" onSubmit={onSubmit}>
      <input
        id="zip"
        type="file"
        accept=".zip"
        onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
        style={{ marginBottom: 12 }}
      />

      <TextField
        label="Artists (comma or newline separated)"
        fullWidth
        multiline
        minRows={3}
        value={artists}
        onChange={(e) => setArtists(e.target.value)}
        margin="normal"
      />

      <TextField
        label="Message"
        fullWidth
        multiline
        minRows={4}
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        margin="normal"
      />

      <TextField
        label="From (optional)"
        fullWidth
        value={fromEmail}
        onChange={(e) => setFromEmail(e.target.value)}
        margin="normal"
      />

      <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', marginTop: 2 }}>
        <Button variant="contained" type="submit" disabled={loading}>
          Upload & Send
        </Button>
        {loading && <LinearProgress style={{ flex: 1 }} />}
      </Box>

      <Box sx={{ marginTop: 3 }}>
        <Typography variant="h6">Result</Typography>
        {result ? (
          Array.isArray(result.results) ? (
            <List>
              {result.results.map((r: any, i: number) => (
                <ListItem key={i}>{`${r.artist} → ${r.email} (${r.previewUrl || r.messageId})`}</ListItem>
              ))}
            </List>
          ) : (
            <pre>{JSON.stringify(result, null, 2)}</pre>
          )
        ) : (
          <Typography color="text.secondary">No result yet.</Typography>
        )}
      </Box>
    </Box>
  )
}
