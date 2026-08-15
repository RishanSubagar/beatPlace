// Mailer service: exposes a sendMail helper.
// For this demo we simulate sends and log when the method is called.
const nodemailer = require('nodemailer');

// Simulated send that logs the action instead of actually sending.
async function sendMail(mailOptions) {
  // Log the simulated send action
  console.log('send through smtp (simulated):', mailOptions.to, 'subject:', mailOptions.subject)
  // Return a simulated info object similar to nodemailer
  return { messageId: `sim-${Date.now()}` }
}

module.exports = { sendMail };
