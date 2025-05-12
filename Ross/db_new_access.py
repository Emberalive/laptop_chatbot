# Modified database connection test script
# This script checks the actual column names in the laptop_models table

import psycopg2
from psycopg2.extras import RealDictCursor

def check_table_structure():
    """Connect to the database and analyze table structure"""
    # Database connection parameters
    db_params = {
        "user": "samuel",
        "password": "QwErTy1243!",
        "host": "86.19.219.159",
        "port": "5432",
        "database": "laptopchatbot_new"  # Main database
    }
    
    conn = None
    cur = None
    
    try:
        print(f"Connecting to {db_params['database']}...")
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get current database
        cur.execute("SELECT current_database();")
        current_db = cur.fetchone()['current_database']
        print(f"Connected to database: {current_db}")
        
        # Check available tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        tables = [row['table_name'] for row in cur.fetchall()]
        print(f"\nAvailable tables ({len(tables)}):")
        for i, table in enumerate(tables, 1):
            print(f"  {i}. {table}")
        
        # First check the laptop_models table structure
        print("\n=== laptop_models table structure ===")
        try:
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = 'laptop_models' 
                ORDER BY ordinal_position
            """)
            
            columns = cur.fetchall()
            if columns:
                print("Column Name | Data Type")
                print("------------|----------")
                for col in columns:
                    print(f"{col['column_name']} | {col['data_type']}")
                
                # This is the key information we need to fix the error
                print("\nKey columns to use in our queries:")
                for col in columns:
                    if col['column_name'].lower() in ('model', 'model_id', 'name', 'id'):
                        print(f"Potential key column: {col['column_name']} ({col['data_type']})")
            else:
                print("No columns found for laptop_models table")
        
        except Exception as e:
            print(f"Error analyzing laptop_models: {str(e)}")
        
        # Check laptop_configurations structure next
        print("\n=== laptop_configurations table structure ===")
        try:
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = 'laptop_configurations' 
                ORDER BY ordinal_position
            """)
            
            columns = cur.fetchall()
            if columns:
                print("Column Name | Data Type")
                print("------------|----------")
                for col in columns:
                    print(f"{col['column_name']} | {col['data_type']}")
                
                # Check for foreign key relationships
                print("\nChecking foreign keys:")
                cur.execute("""
                    SELECT
                        kcu.column_name, 
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name 
                    FROM 
                        information_schema.table_constraints AS tc 
                        JOIN information_schema.key_column_usage AS kcu
                          ON tc.constraint_name = kcu.constraint_name
                          AND tc.table_schema = kcu.table_schema
                        JOIN information_schema.constraint_column_usage AS ccu 
                          ON ccu.constraint_name = tc.constraint_name
                          AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name='laptop_configurations'
                """)
                
                fks = cur.fetchall()
                for fk in fks:
                    print(f"Column {fk['column_name']} references {fk['foreign_table_name']}.{fk['foreign_column_name']}")
            else:
                print("No columns found for laptop_configurations table")
        
        except Exception as e:
            print(f"Error analyzing laptop_configurations: {str(e)}")
        
        # Check sample data
        print("\n=== Sample data from laptop_models ===")
        try:
            cur.execute("SELECT * FROM laptop_models LIMIT 1")
            sample = cur.fetchone()
            if sample:
                for col, val in sample.items():
                    print(f"{col}: {val}")
            else:
                print("No data found in laptop_models")
        except Exception as e:
            print(f"Error getting sample data: {str(e)}")
            
        return True
        
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    print("=" * 50)
    print("DATABASE STRUCTURE ANALYSIS")
    print("=" * 50)
    check_table_structure()
    print("=" * 50)