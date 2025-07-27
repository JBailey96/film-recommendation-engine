#!/bin/bash

# Wait for database to be ready
echo "Waiting for database..."
while ! pg_isready -h postgres -U postgres; do
    sleep 1
done

echo "Database is ready!"

# Run database migrations
echo "Running database setup..."
cd /app/backend
python -c "
import sys
from app.database.models import Base, Movie, UserRating, CastMember, PosterAnalysis, UserPreferences, ScrapingStatus
from app.database.connection import engine
from sqlalchemy import inspect

print('Starting database table creation...')
print(f'Database engine: {engine.url}')

# Get existing tables before creation
inspector = inspect(engine)
existing_tables = inspector.get_table_names()
print(f'Existing tables: {existing_tables}')

# Create all tables
try:
    Base.metadata.create_all(bind=engine)
    
    # Get tables after creation
    inspector = inspect(engine)
    all_tables = inspector.get_table_names()
    
    print('Database tables created successfully!')
    print(f'Total tables: {len(all_tables)}')
    
    # List all created tables with their columns
    for table_name in sorted(all_tables):
        columns = inspector.get_columns(table_name)
        print(f'  - {table_name}: {len(columns)} columns')
        for col in columns:
            print(f'    * {col[\"name\"]} ({col[\"type\"]})')
    
    print('Database setup completed successfully!')
    
except Exception as e:
    print(f'Error creating database tables: {e}')
    sys.exit(1)
"

# Start the application
echo "Starting application..."
cd /app
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000