'use strict';
require('dotenv').config();
const express = require('express');
const multer = require('multer');
const path = require('path');
const emailFinder = require('./src/services/emailFinder');
const mailer = require('./src/services/mailer');

// store uploads under backend/uploads
const upload = multer({ dest: path.join(__dirname, 'uploads') });

const app = express();
app.use(express.json());

// POST /upload
// - accepts multipart form with fields: zip (file), artists (string), message (string), fromEmail (string)
app.post('/upload', upload.single('zip'), async (req, res) => {
  try {
    const file = req.file;
    const { artists = '', message = '', fromEmail } = req.body;
    if (!file) return res.status(400).json({ error: 'zip file required in "zip" field' });

    // parse artist list from comma/newline-separated input
    // process attachment and message using attachmentService (logs inside)
    const attachmentService = require('./src/services/attachmentService')
    const mailer = require('./src/services/mailer')

    const attached = attachmentService.processAttachment(file)
    const msg = attachmentService.processMessage(message)
    const from = attachmentService.processFrom(fromEmail)

    // parse artists using emailFinder.parseArtists (which logs)
    const artistsList = emailFinder.parseArtists(artists)

    // discover candidate emails (stubbed service) — this logs discovery counts
    const found = await emailFinder.findEmailsForArtists(artistsList)

    const results = []
    // call mailer.sendMail which logs the simulated send
    for (const artist of Object.keys(found)) {
      for (const email of found[artist]) {
        const mailOptions = {
          from: from,
          to: email,
          subject: `Beats for ${artist}`,
          text: msg.text,
          attachments: attached ? [{ filename: attached.filename, path: attached.path }] : []
        }
        const info = await mailer.sendMail(mailOptions)
        results.push({ artist, email, messageId: info.messageId, simulated: true })
      }
    }

    return res.json({ uploaded: file.originalname, artists: artistsList, found, results });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message });
  }
});

// serve demo frontend page
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'frontend', 'public', 'index.html'));
});

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`Server listening on ${port}`));
