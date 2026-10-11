import axios from 'axios'

export interface JobStatus {
  job_id: string
  status: 'queued' | 'researching' | 'interpreting' | 'completed' | 'failed'
  people_found: number
  people_completed: number
  created_at: string
}

export interface JobSnapshot extends JobStatus {
  people: Array<{
    name: string
    status: 'queued' | 'researching' | 'completed' | 'failed'
  }>
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
    case 'completed':
      return 'success'
    case 'failed':
      return 'error'
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
      return '✉️ Finding Emails & Sending'
    case 'completed':
      return '✅ Completed'
    case 'failed':
      return '❌ Failed'
    default:
      return status
  }
}
