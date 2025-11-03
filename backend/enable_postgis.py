"""
Script to enable PostGIS extension in the database.
Run this once after database is created.
"""
import os
from sqlalchemy import create_engine, text

def enable_postgis():
    """Enable PostGIS extension"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return
    
    # Fix Railway's postgres:// to postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    print(f"🔌 Connecting to database...")
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            # Enable PostGIS extension
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            conn.commit()
            print("✅ PostGIS extension enabled successfully!")
            
            # Verify PostGIS version
            result = conn.execute(text("SELECT PostGIS_version();"))
            version = result.fetchone()[0]
            print(f"✅ PostGIS version: {version}")
            
    except Exception as e:
        print(f"❌ Error enabling PostGIS: {e}")
        return
    
    print("\n🎉 PostGIS is now ready to use!")

if __name__ == '__main__':
    enable_postgis()
