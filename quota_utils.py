# backend/quota_utils.py

"""
Quota management utilities for feature access control.
Each user has a limited number of attempts per feature.
"""

from db import get_db_connection, return_db_connection
from fastapi import HTTPException

# Feature quota limits
FEATURE_QUOTAS = {
    "Avatar Sync Studio": 5,  # Feature 1
    "Text-to-Avatar Studio": 5,  # Feature 2
    "Personalized Wishes Generator": 2,  # Feature 3
    "IntelliTutor": 2,  # Feature 4
}


def get_feature_quota_limit(feature: str) -> int:
    """Get the quota limit for a feature"""
    return FEATURE_QUOTAS.get(feature, 0)


def check_quota(user_id: int, feature: str) -> tuple[bool, int, int]:
    """
    Check if user has quota remaining for a feature.
    
    Returns:
        (has_quota: bool, current_attempts: int, max_attempts: int)
    """
    max_attempts = get_feature_quota_limit(feature)
    if max_attempts == 0:
        # Feature not found or no quota set
        return False, 0, 0
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get current attempts for this user and feature
        cursor.execute("""
            SELECT attempts_count 
            FROM quotas 
            WHERE user_id = %s AND feature = %s
        """, (user_id, feature))
        
        row = cursor.fetchone()
        current_attempts = row[0] if row else 0
        
        has_quota = current_attempts < max_attempts
        
        return has_quota, current_attempts, max_attempts
    finally:
        return_db_connection(conn)


def increment_quota(user_id: int, feature: str) -> None:
    """
    Increment the quota count for a user and feature.
    Creates a new record if it doesn't exist.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Use UPSERT (INSERT ... ON CONFLICT)
        cursor.execute("""
            INSERT INTO quotas (user_id, feature, attempts_count)
            VALUES (%s, %s, 1)
            ON CONFLICT (user_id, feature)
            DO UPDATE SET attempts_count = quotas.attempts_count + 1
        """, (user_id, feature))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update quota: {str(e)}")
    finally:
        return_db_connection(conn)


def validate_and_increment_quota(user_id: int, feature: str) -> None:
    """
    Validate quota and increment if allowed.
    Raises HTTPException if quota limit is reached.
    """
    has_quota, current_attempts, max_attempts = check_quota(user_id, feature)
    
    if not has_quota:
        raise HTTPException(
            status_code=403,
            detail=f"Maximum limit reached for {feature}. You have used {current_attempts}/{max_attempts} attempts."
        )
    
    # Increment quota
    increment_quota(user_id, feature)
