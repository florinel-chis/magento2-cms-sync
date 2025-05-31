from fastapi import APIRouter

router = APIRouter()

@router.get("/test-logging")
async def test_logging():
    """Test endpoint to verify logging"""
    print("\n=== TEST LOGGING ===")
    print("This is a test message")
    print("If you see this, logging is working!")
    return {"message": "Check console for logs"}