import { defineEventHandler, readBody, createError, setCookie, deleteCookie, getCookie } from 'h3'
import { usePostgres } from '../utils/postgres'
import bcrypt from 'bcrypt'
import jwt from 'jsonwebtoken'

const JWT_SECRET = process.env.JWT_SECRET || 'your-default-secret-key-change-in-production'
export default defineEventHandler(async (event) => {
    const body = await readBody(event);
    const { action } = body;

    if (!action) {
        throw createError({
            statusCode: 400,
            message: 'Action is required'
        });
    }

    // Get PostgreSQL client
    const sql = usePostgres();

    try {
        if (action === 'register') {
            return await handleRegister(body, sql, event);
        }
        else if (action === 'login') {
            return await handleLogin(body, sql, event);
        }
        else if (action === 'updateProfile') {
            return await handleProfileUpdate(body, sql);
        }
        else if (action === 'logout') {
            deleteCookie(event, 'auth_token', { path: '/' });
            return { success: true };
        }
        else if (action === 'verify') {
            return await verifyAuth(event, sql);
        }
        else if (action === 'saveRecommendation') {
            return await handleSaveRecommendation(body, sql);
        }
        else if (action === 'getPastRecommendations') {
            return await handleGetPastRecommendations(body, sql);
        }
        else if (action === 'deleteRecommendation') {
            return await handleDeleteRecommendation(body, sql);
        }
        else {
            throw createError({
                statusCode: 400,
                message: `Invalid action: ${action}`
            });
        }
    } catch (error) {
        console.error('Database operation error:', error);
        throw createError({
            statusCode: 500,
            message: 'Server error during database operation'
        });
    }
});

async function handleRegister(body, sql, event) {
    const { username, password, email } = body

    if (!username || !password) {
        throw createError({
            statusCode: 400,
            message: 'Username and password are required'
        })
    }

    // Check if user already exists
    const existingUser = await sql`
        SELECT username FROM users WHERE username = ${username}
    `

    if (existingUser.length > 0) {
        return {
            success: false,
            message: 'Username already exists'
        }
    }

    // Hash the password
    const saltRounds = 10
    const hashedPassword = await bcrypt.hash(password, saltRounds)

    // Insert the new user
    const result = await sql`
        INSERT INTO users (username, password, email)
        VALUES (${username}, ${hashedPassword}, ${email || null})
        RETURNING username, email
    `
    const token = jwt.sign({ username: result[0].username }, JWT_SECRET, { expiresIn: '7d' })
    setCookie(event, 'auth_token', token, {
        httpOnly: true,
        maxAge: 60 * 60 * 24 * 7, // 7 days
        path: '/'
    })

    return {
        success: true,
        user: {
            username: result[0].username,
            email: result[0].email
        }
    }
}

async function handleLogin(body, sql, event) {
    const { username, password } = body

    if (!username || !password) {
        throw createError({
            statusCode: 400,
            message: 'Username and password are required'
        })
    }

    // Find user by username
    const users = await sql`
        SELECT username, email, password FROM users WHERE username = ${username}
    `

    if (users.length === 0) {
        return {
            success: false,
            message: 'Invalid username or password'
        }
    }

    const user = users[0]

    // Check password
    const passwordMatch = await bcrypt.compare(password, user.password)

    if (!passwordMatch) {
        return {
            success: false,
            message: 'Invalid username or password'
        }
    }

    const token = jwt.sign({ username: user.username }, JWT_SECRET, { expiresIn: '7d' })
    setCookie(event, 'auth_token', token, {
        httpOnly: true,
        maxAge: 60 * 60 * 24 * 7, // 7 days
        path: '/'
    })

    return {
        success: true,
        user: {
            username: user.username,
            email: user.email
        }
    }
}

async function handleProfileUpdate(body, sql) {
    const { username, email, primary_use, budget } = body;

    if (!username) {
        throw createError({
            statusCode: 400,
            message: 'Username is required'
        });
    }

    // Check if user exists
    const users = await sql`
        SELECT username FROM users WHERE username = ${username}
    `;

    if (users.length === 0) {
        return {
            success: false,
            message: 'User not found'
        };
    }

    // Update user information including preferences
    await sql`
        UPDATE users
        SET
            email = ${email || null},
            pref_laptop = ${primary_use || null},
            budget = ${budget || null}
        WHERE username = ${username}
    `;

    // Get updated user data
    const updatedUser = await sql`
        SELECT username, email, pref_laptop, budget
        FROM users
        WHERE username = ${username}
    `;

    return {
        success: true,
        user: {
            username: updatedUser[0].username,
            email: updatedUser[0].email,
            primaryUse: updatedUser[0].pref_laptop,
            budget: updatedUser[0].budget
        }
    };
}

async function verifyAuth(event, sql) {
    const token = getCookie(event, 'auth_token')

    if (!token) {
        return { success: false }
    }

    try {
        const decoded = jwt.verify(token, JWT_SECRET)
        const username = decoded.username

        // Get fresh user data from database
        const users = await sql`
            SELECT username, email, pref_laptop as primary_use, budget
            FROM users WHERE username = ${username}
        `

        if (users.length === 0) {
            return { success: false }
        }

        return {
            success: true,
            user: {
                username: users[0].username,
                email: users[0].email,
                primaryUse: users[0].primary_use,
                budget: users[0].budget
            }
        }
    } catch (err) {
        console.error('Auth verification error:', err)
        return { success: false }
    }
}

async function handleSaveRecommendation(body, sql) {
    const { username, model_id, model_name, model_brand } = body;

    if (!username || !model_id || !model_name || !model_brand) {
        throw createError({
            statusCode: 400,
            message: 'Missing required recommendation data'
        });
    }

    // Check if this recommendation already exists for this user
    const existing = await sql`
        SELECT rec_id FROM past_recommendations
        WHERE username = ${username} AND model_id = ${model_id}
    `;

    // If it exists, just return success (no duplicates)
    if (existing.length > 0) {
        return {
            success: true,
            message: 'Recommendation already saved'
        };
    }

    // Insert the recommendation
    await sql`
        INSERT INTO past_recommendations (username, model_id, model_name, model_brand, rec_date)
        VALUES (${username}, ${model_id}, ${model_name}, ${model_brand}, NOW())
    `;

    return { success: true };
}

async function handleGetPastRecommendations(body, sql) {
    const { username } = body;

    if (!username) {
        throw createError({
            statusCode: 400,
            message: 'Username is required'
        });
    }

    // Get recommendations for this user
    const recommendations = await sql`
        SELECT rec_id, model_id, model_name, model_brand, rec_date
        FROM past_recommendations
        WHERE username = ${username}
        ORDER BY rec_date DESC
    `;

    return {
        success: true,
        recommendations
    };
}

// Add this function to db.ts
async function handleDeleteRecommendation(body, sql) {
    const { username, rec_id } = body;

    if (!username || !rec_id) {
        throw createError({
            statusCode: 400,
            message: 'Missing required data for deletion'
        });
    }

    // Delete the recommendation
    await sql`
        DELETE FROM past_recommendations
        WHERE username = ${username} AND rec_id = ${rec_id}
    `;

    return { success: true };
}