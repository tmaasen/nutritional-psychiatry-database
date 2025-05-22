import * as functions from 'firebase-functions'
import * as admin from 'firebase-admin'
import * as nodemailer from 'nodemailer'

admin.initializeApp()

interface ContactFormData {
  name: string
  email: string
  expertise: string
  message: string
}

export const contactForm = functions.https.onRequest(async (req, res) => {
  // Enable CORS
  res.set('Access-Control-Allow-Origin', '*')
  res.set('Access-Control-Allow-Methods', 'POST')
  res.set('Access-Control-Allow-Headers', 'Content-Type')

  // Handle preflight requests
  if (req.method === 'OPTIONS') {
    res.status(204).send('')
    return
  }

  // Only allow POST requests
  if (req.method !== 'POST') {
    res.status(405).send('Method Not Allowed')
    return
  }

  try {
    const { name, email, expertise, message } = req.body as ContactFormData

    // Validate required fields
    if (!name || !email || !expertise || !message) {
      res.status(400).send('Missing required fields')
      return
    }

    // Create a transporter using SMTP
    const transporter = nodemailer.createTransport({
      service: 'gmail',
      auth: {
        user: process.env.EMAIL_USER,
        pass: process.env.EMAIL_PASS,
      },
    })

    // Email content
    const mailOptions = {
      from: process.env.EMAIL_USER,
      to: 'contact@swellapp.co',
      subject: `New Expert Collaboration Request from ${name}`,
      html: `
        <h2>New Expert Collaboration Request</h2>
        <p><strong>Name:</strong> ${name}</p>
        <p><strong>Email:</strong> ${email}</p>
        <p><strong>Area of Expertise:</strong> ${expertise}</p>
        <h3>Message:</h3>
        <p>${message}</p>
      `,
    }

    // Send email
    await transporter.sendMail(mailOptions)

    // Send confirmation email to the user
    const confirmationMailOptions = {
      from: process.env.EMAIL_USER,
      to: email,
      subject: 'Thank you for your interest in collaborating',
      html: `
        <h2>Thank you for your interest in collaborating!</h2>
        <p>Dear ${name},</p>
        <p>We have received your collaboration request and will review it within 48 hours.</p>
        <p>Best regards,<br>The Nutritional Psychiatry Database Team</p>
      `,
    }

    await transporter.sendMail(confirmationMailOptions)

    res.status(200).send('Email sent successfully')
  } catch (error) {
    console.error('Error sending email:', error)
    res.status(500).send('Error sending email')
  }
}) 