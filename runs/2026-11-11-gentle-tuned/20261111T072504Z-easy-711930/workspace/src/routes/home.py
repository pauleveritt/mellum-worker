from fastapi import APIRouter

router = APIRouter()

@router.get('/')
def home():
    return {
        'message': 'Come in. Sit down. Tell us about your human.'
    }