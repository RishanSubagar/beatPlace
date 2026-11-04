import axios from 'axios'

export interface JobStatus {
  job_id: string
  status: 'queued' | 'researching' | 'interpreting' | 'awaiting_approval' | 'completed' | 'failed'
  people_found: number
  people_completed: number
  created_at: string
}

export interface JobSnapshot extends JobStatus {
  people: Array<{
    name: string
    status: 'queued' | 'researching' | 'finding_contacts' | 'pending_review' | 'no_candidates' | 'failed'
  }>
  candidates: ContactCandidate[]
}

export interface ContactCandidate {
  id: number
  person_name: string
  email: string
  confidence: number
  source_url: string
  evidence: string
  status: 'pending' | 'approved' | 'rejected'
  created_at: string
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const response = await axios.get<JobStatus>(`/jobs/${jobId}`)
  return response.data
}

export function subscribeToJob(jobId: string, onUpdate: (snapshot: JobSnapshot) => void): EventSource {
  const source = new EventSource(`/jobs/${jobId}/events`)
  source.onmessage = (event) => onUpdate(JSON.parse(event.data) as JobSnapshot)
  return source
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'queued':
      return 'warning'
    case 'researching':
      return 'info'
    case 'interpreting':
      return 'info'
    case 'finding_contacts':
      return 'info'
    case 'completed':
      return 'success'
    case 'failed':
      return 'error'
    case 'awaiting_approval':
      return 'warning'
    default:
      return 'default'
  }
}

export function getStatusLabel(status: string): string {
  switch (status) {
    case 'queued':
      return '⏳ Queued'
    case 'researching':
      return '🔍 Researching Artists'
    case 'interpreting':
      return 'Extracting contact candidates'
    case 'finding_contacts':
      return 'Analyzing artist pages'
    case 'completed':
      return '✅ Completed'
    case 'failed':
      return '❌ Failed'
    case 'awaiting_approval':
      return 'Review candidates'
    default:
      return status
  }
}
