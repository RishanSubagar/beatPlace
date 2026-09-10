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

interface Person {
  name: string
  status: 'queued' | 'researching' | 'completed' | 'failed'
}

interface JobResultsDisplayProps {
  jobId: string
  isCompleted: boolean
}

export default function JobResultsDisplay({ jobId, isCompleted }: JobResultsDisplayProps) {
  const [people, setPeople] = useState<Person[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchPeople = async () => {
      try {
        const response = await axios.get<{ job_id: string; people: Person[] }>(
          `/jobs/${jobId}/people`
        )
        setPeople(response.data.people)
        setError(null)
      } catch (err: any) {
        setError(err.response?.data?.detail || err.message || 'Failed to fetch people')
      } finally {
        setLoading(false)
      }
    }

    // Fetch immediately and then every 2 seconds
    fetchPeople()
    const interval = setInterval(fetchPeople, 2000)

    return () => clearInterval(interval)
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
        return '✅ Sent'
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
          Artists Status
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
      </CardContent>
    </Card>
  )
}
