from database import get_db

def execute(query, params=(), fetchone=False, fetchall=False, commit=False):
    db = get_db()

    if fetchone and fetchall:
        raise ValueError("Cannot Use Fetchone and Fetchall at the same time!")
    
    cursor = db.execute(query,params)

    try:
        result = None

        if fetchone:
            row = cursor.fetchone()
            result = dict(row) if row else None
        
        elif fetchall:
            rows = cursor.fetchall()
            result = [dict(r) for r in rows]
        
        if commit:
            db.commit()
            return cursor.rowcount
        
        return result
    
    except Exception:
        db.rollback()
        raise

    finally:
        cursor.close()