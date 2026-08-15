import React from 'react'
import Container from '@mui/material/Container'
import Typography from '@mui/material/Typography'
import Box from '@mui/material/Box'
import Paper from '@mui/material/Paper'
import UploadForm from './components/UploadForm'

// Top-level app shell using MUI components
export default function App() {
  return (
    <Container maxWidth="md" style={{ marginTop: 24 }}>
      <Paper elevation={3} style={{ padding: 20 }}>
        <Typography variant="h4" gutterBottom>
          BeatPlace — Send Beats
        </Typography>
        <Box>
          <UploadForm />
        </Box>
      </Paper>
    </Container>
  )
}
