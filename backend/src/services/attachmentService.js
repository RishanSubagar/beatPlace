// Attachment and message helpers that log when called.

function processAttachment(file) {
  if (!file) return null
  console.log('file attached:', file.originalname)
  return { filename: file.originalname, path: file.path }
}

function processMessage(message) {
  console.log('message included:', !!message)
  return { text: message }
}

function processFrom(fromEmail) {
  const from = fromEmail || process.env.DEFAULT_FROM || 'no-reply@example.com'
  console.log('from included:', from)
  return from
}

module.exports = { processAttachment, processMessage, processFrom }
