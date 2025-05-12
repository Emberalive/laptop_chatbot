// server/api/laptop-details.ts
import { defineEventHandler, readBody, createError } from 'h3'
import { usePostgres } from '../utils/postgres'

export default defineEventHandler(async (event) => {
    try {
        const body = await readBody(event)
        const { modelId } = body

        if (!modelId) {
            throw createError({
                statusCode: 400,
                message: 'Model ID is required'
            })
        }

        const sql = usePostgres()

        // Join laptop_models and laptop_configurations tables to get complete laptop details
        // Join multiple tables to get complete laptop details including storage and screen info
        const details = await sql`
            SELECT
                lm.model_id,
                lm.model_name,
                lm.brand,
                lm.image_url,
                lc.processor,
                lc.memory_installed as ram,
                CONCAT(cs.storage_type, cs.capacity) as storage,
                s.size as display_size,
                s.resolution as display_resolution,
                CONCAT(gc.brand,' ' ,lc.graphics_card) as graphics,
                lc.weight,
                lc.battery_life,
                lc.price
            FROM
                laptop_models lm
                    JOIN
                laptop_configurations lc ON lm.model_id = lc.model_id
                    LEFT JOIN
                configuration_storage cs ON lc.config_id = cs.config_id
                    LEFT JOIN
                screens s ON lc.config_id = s.config_id
                    left join 
                    graphics_cards gc on lc.graphics_card = gc.model
            WHERE
                lm.model_id = ${modelId}
        `

        if (details.length === 0) {
            throw createError({
                statusCode: 404,
                message: 'Laptop not found'
            })
        }

        return {
            details: details[0]
        }
    } catch (error) {
        console.error('Error retrieving laptop details:', error)
        throw createError({
            statusCode: 500,
            message: 'Error retrieving laptop details'
        })
    }
})