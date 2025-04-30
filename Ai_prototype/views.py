from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import random
import json

# Mock feedback templates
MOCK_FEEDBACK = {
    'assignment': [
        "Your submission shows good understanding of the core concepts. Consider exploring the relationship between {concept1} and {concept2} more deeply in future assignments.",
        "Well-structured submission! To improve, try to include more practical examples demonstrating {concept1} in real-world scenarios.",
        "Your analysis of {concept1} is thorough, but your conclusion could be strengthened by connecting it back to the initial hypothesis."
    ],
    'quiz': [
        "Based on your quiz performance, you seem to have a strong grasp of {concept1}. However, you might want to review the topics related to {concept2}.",
        "Your quiz results indicate you're excelling at theoretical concepts but might benefit from more practice with applied problems.",
        "Good quiz attempt! To improve your score next time, focus on understanding the relationship between {concept1} and its practical applications."
    ],
    'general': [
        "Your recent activities show consistent engagement. To enhance your learning, consider exploring additional resources on {concept1}.",
        "You're making good progress! Based on your interaction patterns, you might find topics related to {concept2} particularly interesting.",
        "Your learning pattern suggests you grasp concepts quickly. Consider challenging yourself with advanced material on {concept1} and {concept2}."
    ]
}

# Placeholder concepts for personalization
CONCEPTS = [
    "data structures", "algorithmic efficiency", "object-oriented programming",
    "functional programming", "web architecture", "database optimization",
    "user experience design", "security principles", "API design",
    "machine learning fundamentals", "statistical analysis"
]

@login_required
def ai_assistant_page(request):
    """View for the AI Assistant page."""
    context = {
        'active_page': 'ai_assistant',
    }
    return render(request, 'ai_prototype/ai_assistant.html', context)

@login_required
def generate_mock_feedback_view(request, submission_id=None):
    """Generate mock AI feedback based on submission ID."""
    if submission_id is None:
        # If no submission ID is provided, use a random one for demo purposes
        submission_id = f"mock-{random.randint(1000, 9999)}"
    
    # Randomly select feedback type
    feedback_type = request.GET.get('type', random.choice(['assignment', 'quiz', 'general']))
    
    # Select random concepts for personalization
    concept1 = random.choice(CONCEPTS)
    concept2 = random.choice([c for c in CONCEPTS if c != concept1])
    
    # Select and personalize a random feedback template
    templates = MOCK_FEEDBACK.get(feedback_type, MOCK_FEEDBACK['general'])
    template = random.choice(templates)
    feedback = template.format(concept1=concept1, concept2=concept2)
    
    # Return JSON response
    return JsonResponse({
        'status': 'success',
        'submission_id': submission_id,
        'feedback_type': feedback_type,
        'feedback': feedback
    })

@login_required
@require_POST
def feedback_request_view(request):
    """Handle submission form requests for feedback."""
    try:
        data = json.loads(request.body)
        submission_id = data.get('submission_id', f"req-{random.randint(1000, 9999)}")
        feedback_type = data.get('type', 'general')
        
        # Generate mock feedback
        concept1 = random.choice(CONCEPTS)
        concept2 = random.choice([c for c in CONCEPTS if c != concept1])
        
        templates = MOCK_FEEDBACK.get(feedback_type, MOCK_FEEDBACK['general'])
        template = random.choice(templates)
        feedback = template.format(concept1=concept1, concept2=concept2)
        
        # Return JSON response with a slight delay to simulate processing
        return JsonResponse({
            'status': 'success',
            'submission_id': submission_id,
            'feedback_type': feedback_type,
            'feedback': feedback
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f"An error occurred: {str(e)}"
        }, status=400)
