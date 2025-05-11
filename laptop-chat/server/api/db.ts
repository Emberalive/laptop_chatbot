import { defineEventHandler, readBody, createError } from 'h3'
import { usePostgres } from '../utils/postgres'
import bcrypt from 'bcrypt'

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
            return await handleRegister(body, sql);
        }
        else if (action === 'login') {
            return await handleLogin(body, sql);
        }
        else if (action === 'updateProfile') {
            return await handleProfileUpdate(body, sql);
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

async function handleRegister(body, sql) {
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

    return {
        success: true,
        user: {
            username: result[0].username,
            email: result[0].email
        }
    }
}

async function handleLogin(body, sql) {
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
    SELECT username, email, primary_use, budget 
    FROM users 
    WHERE username = ${username}
  `;

    return {
        success: true,
        user: {
            username: updatedUser[0].username,
            email: updatedUser[0].email,
            primaryUse: updatedUser[0].primary_use,
            budget: updatedUser[0].budget
        }
    };
}
