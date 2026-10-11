import React, { useEffect, useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material'
import axios from 'axios'
import { ContactCandidate, subscribeToJob } from '../services/jobApi'

interface Person {
  name: string
  status: 'queued' | 'researching' | 'finding_contacts' | 'pending_review' | 'no_candidates' | 'failed'
}

interface JobResultsDisplayProps {
  jobId: string
  isCompleted: boolean
}

export default function JobResultsDisplay({ jobId, isCompleted }: JobResultsDisplayProps) {
  const [people, setPeople] = useState<Person[]>([])
  const [candidates, setCandidates] = useState<ContactCandidate[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    const source = subscribeToJob(jobId, (snapshot) => {
      if (!active) return
      setPeople(snapshot.people || [])
      setCandidates(snapshot.candidates || [])
      setError(null)
      setLoading(false)

      if (['awaiting_approval', 'completed', 'failed'].includes(snapshot.status)) {
        source.close()
      }
    })

    source.onerror = async () => {
      try {
        const [peopleResponse, candidateResponse] = await Promise.all([
          axios.get<{ job_id: string; people: Person[] }>(
          `/jobs/${jobId}/people`
          ),
          axios.get<{ job_id: string; candidates: ContactCandidate[] }>(
            `/jobs/${jobId}/candidates`
          ),
        ])
        if (active) {
          setPeople(peopleResponse.data.people || [])
          setCandidates(candidateResponse.data.candidates || [])
          setError(null)
          setLoading(false)
        }
      } catch (err: any) {
        if (active) {
          setError(err.response?.data?.detail || err.message || 'Failed to fetch people')
          setLoading(false)
        }
      }
    }

    return () => {
      active = false
      source.close()
    }
  }, [jobId])

  if (loading && people.length === 0) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <CircularProgress size={24} />
        <Typography>Loading results...</Typography>
      </Box>
    )
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success'
      case 'failed':
        return 'error'
      case 'researching':
        return 'info'
      default:
        return 'default'
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'completed':
        return '✅ Processed'
      case 'pending_review':
        return 'Needs review'
      case 'no_candidates':
        return 'No candidates found'
      case 'finding_contacts':
        return 'Analyzing pages'
      case 'failed':
        return '❌ Failed'
      case 'researching':
        return '🔍 Researching'
      case 'queued':
        return '⏳ Queued'
      default:
        return status
    }
  }

  return (
    <Card sx={{ mt: 3 }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Artist Research
        </Typography>

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                <TableCell>Artist Name</TableCell>
                <TableCell align="right">Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {people.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={2} align="center">
                    <Typography color="text.secondary">No artists to process</Typography>
                  </TableCell>
                </TableRow>
              ) : (
                people.map((person, index) => (
                  <TableRow key={index}>
                    <TableCell>{person.name}</TableCell>
                    <TableCell align="right">
                      <Chip
                        label={getStatusLabel(person.status)}
                        color={getStatusColor(person.status) as any}
                        size="small"
                        variant="filled"
                      />
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
          {candidates.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" sx={{ mb: 1 }}>
                Contact candidates awaiting review
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Artist</TableCell>
                      <TableCell>Email</TableCell>
                      <TableCell>Confidence</TableCell>
                      <TableCell>Evidence</TableCell>
                      <TableCell>Source</TableCell>
                      <TableCell>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {candidates.map((candidate) => (
                      <TableRow key={candidate.id}>
                        <TableCell>{candidate.person_name}</TableCell>
                        <TableCell>{candidate.email}</TableCell>
                        <TableCell>{Math.round(candidate.confidence * 100)}%</TableCell>
                        <TableCell>{candidate.evidence}</TableCell>
                        <TableCell>
                          <a href={candidate.source_url} target="_blank" rel="noreferrer">
                            View source
                          </a>
                        </TableCell>
                        <TableCell>
                          <Chip label="Pending review" color="warning" size="small" />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              <Alert severity="info" sx={{ mt: 2 }}>
                No emails have been sent. Candidate approval and sending are not available yet.
              </Alert>
            </Box>
          )}
      </CardContent>
    </Card>
  )
}
