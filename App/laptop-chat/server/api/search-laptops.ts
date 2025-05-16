// server/api/search-laptops.ts
import { defineEventHandler, readBody, createError } from 'h3'
import { usePostgres } from '../utils/postgres'

export default defineEventHandler(async (event) => {
    try {
        const body = await readBody(event)
        const { searchTerm } = body

        if (!searchTerm) {
            throw createError({
                statusCode: 400,
                message: 'Search term is required'
            })
        }

        const sql = usePostgres()

        // Search for laptops with names that contain the search term
        const results = await sql`
      SELECT model_id, model_name, brand 
      FROM laptop_models
      WHERE 
        LOWER(model_name) LIKE LOWER(${'%' + searchTerm + '%'})
        OR LOWER(brand) LIKE LOWER(${'%' + searchTerm + '%'})
      ORDER BY brand, model_name
    `

        return {
            results
        }
    } catch (error) {
        console.error('Error searching laptops:', error)
        throw createError({
            statusCode: 500,
            message: 'Error searching laptops'
        })
    }
});