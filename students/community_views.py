import os
import json
import base64
import threading
from groq import Groq
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.db import transaction  # NEW: For secure coin transfer
from .models import Course, Enrollment, CourseGroupMessage, MessageReaction, User

# .env file loaded 
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

#  AI BOT BACKGROUND WORKERS (VISION ENABLED) 

def generate_ai_reply(course_id, prompt, reply_to_id=None, image_path=None):
    """
    Calls Groq API in the background. Now supports Image Vision!
    """
    try:
        # 1. Safely Create or Get the AI User
        ai_user, created = User.objects.get_or_create(
            username="ai_commander", 
            defaults={
                'first_name': 'AI', 
                'last_name': 'Commander', 
                'email': 'ai@commander.com',
                'is_teacher': True
            }
        )
        
        # 2. Fetch API Key
        api_key = os.environ.get("GROQ_API_KEY") or getattr(settings, 'GROQ_API_KEY', None)
        
        if not api_key:
            CourseGroupMessage.objects.create(
                course_id=course_id, sender=ai_user, reply_to_id=reply_to_id,
                text="⚠️ System Error: `GROQ_API_KEY` is missing."
            )
            return

        client = Groq(api_key=api_key)
        
        # Base setup for AI
        system_prompt = "You are an expert AI teaching assistant for a tech community. Provide short, clear, and very helpful answers. DO NOT use markdown asterisks (**) or bold text. Instead, use relevant emojis 🚀💡💻 🤖 to highlight key points. Format code blocks using standard markdown."
        
        # 3. Check if an Image was provided to use the Vision Model
        # NOTE: Vision models are currently unavailable on Groq (llama-3.2-90b-vision-preview was decommissioned).
        # Falling back to text-only model for all requests.
        if image_path and os.path.exists(image_path):
            # Vision model unavailable - use text model with a note about the image
            image_note = " (Note: An image was attached but I cannot process images currently. Please describe what's in the image if you need help with it.)"
            api_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": (prompt if prompt else "An image was shared but I cannot process it.") + image_note}
            ]
        else:
            # Standard Text-Only Model
            api_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]

        # Call Groq API
        chat_completion = client.chat.completions.create(
            messages=api_messages,
            model="qwen/qwen3.8-27b",  # Updated: using qwen model since llama models were removed
        )
        ai_response = chat_completion.choices[0].message.content
        
        # 4. Save AI reply
        CourseGroupMessage.objects.create(
            course_id=course_id,
            sender=ai_user,
            text=ai_response,
            reply_to_id=reply_to_id
        )
    except Exception as e:
        print(f"Groq AI Error: {e}")
        try:
            CourseGroupMessage.objects.create(
                course_id=course_id,
                sender=ai_user,
                text=f"⚠️ AI Core Error: `{str(e)}`",
                reply_to_id=reply_to_id
            )
        except Exception as inner_e:
            pass

def check_and_auto_reply(course_id, message_id, prompt):
    """
    Checks if a question has been answered after 45 mins. If not, AI replies.
    """
    try:
        newer_messages_exist = CourseGroupMessage.objects.filter(course_id=course_id, id__gt=message_id).exists()
        if not newer_messages_exist:
            ai_prompt = f"A student asked this question and no one replied. Please provide a helpful answer: '{prompt}'"
            generate_ai_reply(course_id, ai_prompt, reply_to_id=message_id)
    except Exception as e:
        print(f"Auto Reply Error: {e}")

# 1. MAIN COMMUNITY CHAT VIEW 

@login_required
def course_community_chat(request, slug):
    course = get_object_or_404(Course, slug=slug)

    is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
    if not (is_enrolled or request.user.is_teacher or getattr(request.user, 'is_faculty', False) or request.user.is_superuser):
        messages.error(request, "You must be enrolled in this course to access the community chat.")
        return redirect('dashboard')

    search_query = request.GET.get('q', '')
    if search_query:
        chat_messages = CourseGroupMessage.objects.filter(
            Q(course=course) & 
            (Q(text__icontains=search_query) | Q(sender__first_name__icontains=search_query) | Q(sender__username__icontains=search_query))
        ).select_related('sender', 'reply_to')
    else:
        chat_messages = CourseGroupMessage.objects.filter(course=course).select_related('sender', 'reply_to')

    pinned_messages = CourseGroupMessage.objects.filter(course=course, is_pinned=True).order_by('-created_at')

    enrollments = Enrollment.objects.filter(course=course).select_related('student__profile')
    members = [enrollment.student for enrollment in enrollments]

    if request.method == 'POST':
        message_text = request.POST.get('message_text', '')
        attachment = request.FILES.get('attachment')
        reply_to_id = request.POST.get('reply_to_id')
        
        #  BOUNTY DEDUCTION LOGIC 

        bounty_amount_str = request.POST.get('bounty_amount', '0')
        try:
            bounty_amount = int(bounty_amount_str) if bounty_amount_str else 0
        except ValueError:
            bounty_amount = 0

        # Check if user has enough coins
        if bounty_amount > 0:
            if request.user.lms_coins < bounty_amount:
                messages.error(request, "Insufficient LMS Coins to set this bounty.")
                return redirect('course_community_chat', slug=course.slug)
            
            # Deduct coins safely
            request.user.lms_coins -= bounty_amount
            request.user.save(update_fields=['lms_coins'])

        if message_text or attachment:
            reply_msg = None
            if reply_to_id:
                reply_msg = CourseGroupMessage.objects.filter(id=reply_to_id).first()

            # Save the new message to DB with Bounty Amount
            msg = CourseGroupMessage.objects.create(
                course=course,
                sender=request.user,
                text=message_text,
                attachment=attachment,
                reply_to=reply_msg,
                bounty_amount=bounty_amount #  Added here
            )

            #  AI BOT TRIGGERS (VISION ENABLED) 
            text_lower = message_text.strip().lower()
            
            # Check if it's an AI Command
            if text_lower.startswith('/ai'):
                prompt = message_text[3:].strip()
                
                # Check if there is an image attached
                image_path = None
                if msg.attachment:
                    ext = os.path.splitext(msg.attachment.name)[1].lower()
                    # Only pass valid images to the Vision model
                    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                        image_path = msg.attachment.path
                
                # Start Thread with Image Path
                threading.Thread(target=generate_ai_reply, args=(course.id, prompt, msg.id, image_path)).start()
            
            # Auto Reply Logic (Only for text questions without /ai)
            elif '?' in text_lower and not attachment:
                timer_seconds = 2700 # 45 mins
                threading.Timer(timer_seconds, check_and_auto_reply, args=[course.id, msg.id, message_text]).start()

            return redirect('course_community_chat', slug=course.slug)

    for msg in chat_messages:
        reactions = msg.reactions.all()
        reaction_counts = {}
        for r in reactions:
            reaction_counts[r.reaction_type] = reaction_counts.get(r.reaction_type, 0) + 1
        msg.reaction_counts = reaction_counts

    context = {
        'course': course,
        'chat_messages': chat_messages,
        'pinned_messages': pinned_messages,
        'members': members,
        'member_count': len(members),
        'search_query': search_query,
    }
    
    return render(request, 'community_chat.html', context)

#  2. PIN MESSAGE API (AJAX) 

@login_required
def toggle_pin_message(request, message_id):
    if request.method == "POST":
        msg = get_object_or_404(CourseGroupMessage, id=message_id)
        msg.is_pinned = not msg.is_pinned
        msg.save()
        return JsonResponse({'status': 'success', 'is_pinned': msg.is_pinned})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

#  3. EMOJI REACTION API (AJAX) 

@login_required
def add_message_reaction(request, message_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            reaction_type = data.get('reaction_type')
            msg = get_object_or_404(CourseGroupMessage, id=message_id)
            
            existing_reaction = MessageReaction.objects.filter(message=msg, user=request.user, reaction_type=reaction_type).first()
            
            if existing_reaction:
                existing_reaction.delete()
                action = 'removed'
            else:
                MessageReaction.objects.create(message=msg, user=request.user, reaction_type=reaction_type)
                action = 'added'
            
            reactions_count = {}
            for r in MessageReaction.objects.filter(message=msg):
                reactions_count[r.reaction_type] = reactions_count.get(r.reaction_type, 0) + 1
                
            return JsonResponse({'status': 'success', 'action': action, 'reactions': reactions_count})
        
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error'}, status=400)

#  4. STUDENT PROFILE API (AJAX) 

@login_required
def get_student_info(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    image_url = None
    bio = "No bio provided."
    if hasattr(user, 'profile'):
        bio = user.profile.bio if user.profile.bio else "No bio provided."
        if user.profile.profile_pic:
            image_url = user.profile.profile_pic.url

    data = {
        'name': user.full_name,
        'username': user.username,
        'level': user.student_level,
        'stream': user.stream if user.stream else "Not specified",
        'bio': bio,
        'image_url': image_url,
        'is_teacher': user.is_teacher
    }
    
    return JsonResponse({'status': 'success', 'data': data})

#  5. DELETE MESSAGE API (AJAX) 

@login_required
def delete_message(request, message_id):
    if request.method == "POST":
        msg = get_object_or_404(CourseGroupMessage, id=message_id)
        
        # Security: Only the sender of the message or a teacher can delete the message.
        if msg.sender == request.user or request.user.is_teacher:
            msg.delete()
            return JsonResponse({'status': 'success'})
            
    return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)

#  6. EDIT MESSAGE API (AJAX) 

@login_required
def edit_message(request, message_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_text = data.get('text', '').strip()
            msg = get_object_or_404(CourseGroupMessage, id=message_id)
            
            # Security: Only the sender of the message can edit its message.
            if msg.sender == request.user and new_text:
                msg.text = new_text
                msg.is_edited = True 
                msg.save()
                return JsonResponse({'status': 'success', 'new_text': msg.text})
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

#  7. ACCEPT BOUNTY API (AJAX) 

@login_required
def accept_bounty(request, reply_id):
    if request.method == "POST":
        try:
            reply_msg = get_object_or_404(CourseGroupMessage, id=reply_id)
            parent_msg = reply_msg.reply_to
            
            # Security Checks
            if not parent_msg:
                return JsonResponse({'status': 'error', 'message': 'This is not a reply to a bounty.'})
            
            if parent_msg.sender != request.user:
                return JsonResponse({'status': 'error', 'message': 'Only the creator of the bounty can accept an answer.'})
                
            if parent_msg.is_bounty_resolved:
                return JsonResponse({'status': 'error', 'message': 'This bounty is already resolved.'})
                
            if parent_msg.bounty_amount <= 0:
                return JsonResponse({'status': 'error', 'message': 'There is no bounty on this message.'})

            if reply_msg.sender == request.user:
                return JsonResponse({'status': 'error', 'message': 'You cannot accept your own answer.'})

            # Execute Transaction Securely
            with transaction.atomic():
                # 1. Mark bounty as resolved
                parent_msg.is_bounty_resolved = True
                parent_msg.bounty_winner = reply_msg.sender
                parent_msg.save()
                
                # 2. Add coins to the winner
                winner = reply_msg.sender
                winner.lms_coins += parent_msg.bounty_amount
                winner.save(update_fields=['lms_coins'])
                
                # 3. Create the global notification that triggers our Golden Popup!
                # Note: The word 'Coin' must be in the message for the JS to trigger the golden style
                winner_name = winner.first_name if winner.first_name else winner.username
                messages.success(request, f"🎉 <b>Bounty Resolved!</b> {parent_msg.bounty_amount} LMS Coins awarded to {winner_name}!")
                
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)