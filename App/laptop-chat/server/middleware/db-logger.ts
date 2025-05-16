// server/middleware/db-logger.ts
import { defineEventHandler } from 'h3'

export default defineEventHandler(async (event) => {
    // Only run once
    if (event.path === '/api/search-laptops' && !global.__dbChecked) {
        try {
            const client = event.context.postgres
            const result = await client.query('SELECT COUNT(*) FROM laptops')
            console.log(`Connected to database with ${result.rows[0].count} laptops`)
            global.__dbChecked = true
        } catch (error) {
            console.error('Database connection error:', error)
        }
    }
})