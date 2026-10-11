import React, { useEffect, useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Alert,
  Chip,
  CircularProgress,
} from '@mui/material'
import { getJobStatus, getStatusColor, getStatusLabel, JobStatus, subscribeToJob } from '../services/jobApi'

interface JobStatusDisplayProps {
  jobId: string
}

export default function JobStatusDisplay({ jobId }: JobStatusDisplayProps) {
  const [status, setStatus] = useState<JobStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isStreaming, setIsStreaming] = useState(true)

  useEffect(() => {
    let active = true
    const source = subscribeToJob(jobId, (snapshot) => {
      if (!active) return
      setStatus(snapshot)
      setError(null)
      setLoading(false)

      if (snapshot.status === 'completed' || snapshot.status === 'failed') {
        setIsStreaming(false)
        source.close()
      }
    })

    source.onerror = async () => {
      if (!active) return
      try {
        const data = await getJobStatus(jobId)
        if (active) {
          setStatus(data)
          setLoading(false)
          setError(null)
        }
      } catch (err: any) {
        if (active && !status) {
          setError(err.response?.data?.detail || err.message || 'Failed to fetch job status')
          setLoading(false)
        }
      }
    }

    return () => {
      active = false
      source.close()
    }
  }, [jobId])

  if (loading && !status) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 3 }}>
        <CircularProgress size={24} />
        <Typography>Loading job status...</Typography>
      </Box>
    )
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>
  }

  if (!status) {
    return <Alert severity="error">Could not fetch job status</Alert>
  }

  const progress = status.people_found
    ? (status.people_completed / status.people_found) * 100
    : 0

  return (
    <Card sx={{ mt: 3, mb: 3 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6">Job Status</Typography>
          <Chip
            label={getStatusLabel(status.status)}
            color={getStatusColor(status.status) as any}
            variant="filled"
          />
        </Box>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          Job ID: <code>{status.job_id}</code>
        </Typography>

        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2">Progress</Typography>
            <Typography variant="body2">
              {status.people_completed} / {status.people_found} artists
            </Typography>
          </Box>
          <LinearProgress variant="determinate" value={progress} sx={{ height: 8 }} />
        </Box>

        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Status
            </Typography>
            <Typography variant="body1">{status.status}</Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Created
            </Typography>
            <Typography variant="body2">{new Date(status.created_at).toLocaleString()}</Typography>
          </Box>
        </Box>

        {isStreaming && status.status !== 'completed' && status.status !== 'failed' && (
          <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
            🔄 Live updates connected
          </Typography>
        )}
      </CardContent>
    </Card>
  )
}
