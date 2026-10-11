import React, { useState } from 'react'
import axios from 'axios'
import Box from '@mui/material/Box'
import TextField from '@mui/material/TextField'
import Button from '@mui/material/Button'
import LinearProgress from '@mui/material/LinearProgress'
import Alert from '@mui/material/Alert'
import Typography from '@mui/material/Typography'
import JobStatusDisplay from './JobStatusDisplay'
import JobResultsDisplay from './JobResultsDisplay'

// Upload form: file input, artists, message, and send button.
export default function UploadForm() {
  const [file, setFile] = useState<File | null>(null)
  const [artists, setArtists] = useState('')
  const [message, setMessage] = useState('')
  const [fromEmail, setFromEmail] = useState('')
  const [uploading, setUploading] = useState(false)  
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [jobId, setJobId] = useState<string | null>(null)
  const [jobStatus, setJobStatus] = useState<string | null>(null)

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
      setUploading(true)
      setUploadError(null)
      const res = await axios.post('/upload', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setJobId(res.data.job_id)
      setJobStatus(res.data.status)
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || err.message || String(err))
    } finally {
      setUploading(false)
    }
  }

  // If job is in progress or completed, show status displays
  if (jobId) {
    const isCompleted = ['awaiting_approval', 'completed', 'failed'].includes(jobStatus ?? '')

    return (
      <Box>
        <Box sx={{ mb: 3, p: 2, backgroundColor: '#f0f7ff', borderRadius: 1 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>
            Contact research is in progress
          </Typography>
          <Typography variant="body2" color="text.secondary">
            We are checking public artist pages for contact details. No emails will be sent in this step.
          </Typography>
        </Box>

        <JobStatusDisplay jobId={jobId} onStatusChange={setJobStatus} />
        <JobResultsDisplay jobId={jobId} isCompleted={isCompleted} />

        {isCompleted && (
          <Button
            variant="outlined"
            sx={{ mt: 2 }}
            onClick={() => {
              // Reset form
              setJobId(null)
              setJobStatus(null)
              setFile(null)
              setArtists('')
              setMessage('')
              setFromEmail('')
              setUploadError(null)
            }}
          >
            Start Another Search
          </Button>
        )}
      </Box>
    )
  }

  return (
    <Box component="form" onSubmit={onSubmit}>
      {uploadError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {uploadError}
        </Alert>
      )}

      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
          Step 1: Select ZIP File
        </Typography>
        <input
          id="zip"
          type="file"
          accept=".zip"
          onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
          style={{ display: 'block', marginBottom: 8 }}
          disabled={uploading}
        />
        {file && (
          <Typography variant="caption" color="success.main">
            ✓ {file.name} selected
          </Typography>
        )}
      </Box>

      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
          Step 2: Enter Artists
        </Typography>
        <TextField
          label="Artists (comma or newline separated)"
          fullWidth
          multiline
          minRows={3}
          value={artists}
          onChange={(e) => setArtists(e.target.value)}
          disabled={uploading}
          placeholder="Drake, The Weeknd, Kendrick Lamar"
        />
      </Box>

      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
          Step 3: Compose Message
        </Typography>
        <TextField
          label="Message"
          fullWidth
          multiline
          minRows={4}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          disabled={uploading}
          placeholder="Hi! I've produced some beats that I think would work great for your next project..."
        />
      </Box>

      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
          Step 4: Sender Email (optional)
        </Typography>
        <TextField
          label="From Email"
          fullWidth
          type="email"
          value={fromEmail}
          onChange={(e) => setFromEmail(e.target.value)}
          disabled={uploading}
          placeholder="your-email@example.com"
        />
      </Box>

      <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2 }}>
        <Button variant="contained" type="submit" disabled={uploading} size="large">
          {uploading ? 'Uploading...' : 'Upload & Send Beats'}
        </Button>
        {uploading && <LinearProgress sx={{ flex: 1, height: 4 }} />}
      </Box>
    </Box>
  )
}
