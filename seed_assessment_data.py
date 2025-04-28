# seed_assessment_data.py
from supabase import create_client
import json
import time
import sys
import os
import uuid

# Add the project root to the Python path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the settings from your app
from app.core.config import settings

# Initialize Supabase client using your application settings
try:
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    print("Successfully connected to Supabase.")
    print(f"Using URL: {settings.SUPABASE_URL}")
except Exception as e:
    print(f"Error connecting to Supabase: {e}")
    exit(1)

# Generate UUIDs for dimensions
dimension_uuids = {
    "personality": str(uuid.uuid4()),
    "values": str(uuid.uuid4()),
    "interests": str(uuid.uuid4()),
    "communication": str(uuid.uuid4()),
    "goals": str(uuid.uuid4()),
    "emotional": str(uuid.uuid4()),
    "lifestyle": str(uuid.uuid4())
}

# Define dimensions
dimensions = [
    {
        "id": dimension_uuids["personality"],
        "name": "Personality Traits",
        "description": "Assessment of core personality characteristics based on established psychological models",
        "weight": 20,
        "order_index": 1
    },
    {
        "id": dimension_uuids["values"],
        "name": "Values & Beliefs",
        "description": "Evaluation of core principles and beliefs that guide decision-making",
        "weight": 25,
        "order_index": 2
    },
    {
        "id": dimension_uuids["interests"],
        "name": "Interests & Activities",
        "description": "Analysis of hobbies and preferred activities",
        "weight": 15,
        "order_index": 3
    },
    {
        "id": dimension_uuids["communication"],
        "name": "Communication Styles",
        "description": "Assessment of how individuals express themselves and resolve conflicts",
        "weight": 15,
        "order_index": 4
    },
    {
        "id": dimension_uuids["goals"],
        "name": "Life Goals & Priorities",
        "description": "Evaluation of long-term aspirations and current priorities",
        "weight": 15,
        "order_index": 5
    },
    {
        "id": dimension_uuids["emotional"],
        "name": "Emotional Intelligence",
        "description": "Measurement of ability to understand and manage emotions",
        "weight": 5,
        "order_index": 6
    },
    {
        "id": dimension_uuids["lifestyle"],
        "name": "Lifestyle Preferences",
        "description": "Assessment of daily habits, routines, and living preferences",
        "weight": 5,
        "order_index": 7
    }
]

# Define questions for each dimension
questions = [
    # Personality Traits Questions
    {
        "dimension_id": dimension_uuids["personality"],
        "text": "I enjoy being the center of attention at social gatherings",
        "options": [
            {"value": "1", "label": "Strongly Disagree"},
            {"value": "2", "label": "Disagree"},
            {"value": "3", "label": "Neutral"},
            {"value": "4", "label": "Agree"},
            {"value": "5", "label": "Strongly Agree"}
        ],
        "weight": 1,
        "order_index": 1
    },
    {
        "dimension_id": dimension_uuids["personality"],
        "text": "I prefer having a few close friends rather than many acquaintances",
        "options": [
            {"value": "1", "label": "Strongly Disagree"},
            {"value": "2", "label": "Disagree"},
            {"value": "3", "label": "Neutral"},
            {"value": "4", "label": "Agree"},
            {"value": "5", "label": "Strongly Agree"}
        ],
        "weight": 1,
        "order_index": 2
    },
    {
        "dimension_id": dimension_uuids["personality"],
        "text": "I often worry about things that might go wrong",
        "options": [
            {"value": "1", "label": "Strongly Disagree"},
            {"value": "2", "label": "Disagree"},
            {"value": "3", "label": "Neutral"},
            {"value": "4", "label": "Agree"},
            {"value": "5", "label": "Strongly Agree"}
        ],
        "weight": 1,
        "order_index": 3
    },
    {
        "dimension_id": dimension_uuids["personality"],
        "text": "I stay calm under pressure",
        "options": [
            {"value": "1", "label": "Strongly Disagree"},
            {"value": "2", "label": "Disagree"},
            {"value": "3", "label": "Neutral"},
            {"value": "4", "label": "Agree"},
            {"value": "5", "label": "Strongly Agree"}
        ],
        "weight": 1,
        "order_index": 4
    },
    {
        "dimension_id": dimension_uuids["personality"],
        "text": "I enjoy trying new experiences and activities",
        "options": [
            {"value": "1", "label": "Strongly Disagree"},
            {"value": "2", "label": "Disagree"},
            {"value": "3", "label": "Neutral"},
            {"value": "4", "label": "Agree"},
            {"value": "5", "label": "Strongly Agree"}
        ],
        "weight": 1,
        "order_index": 5
    },
    
    # Values & Beliefs Questions
    {
        "dimension_id": dimension_uuids["values"],
        "text": "Which value is most important to you?",
        "options": [
            {"value": "honesty", "label": "Honesty"},
            {"value": "loyalty", "label": "Loyalty"},
            {"value": "compassion", "label": "Compassion"},
            {"value": "independence", "label": "Independence"},
            {"value": "achievement", "label": "Achievement"}
        ],
        "weight": 1,
        "order_index": 1
    },
    {
        "dimension_id": dimension_uuids["values"],
        "text": "How important is family in your life?",
        "options": [
            {"value": "1", "label": "Not Important"},
            {"value": "2", "label": "Slightly Important"},
            {"value": "3", "label": "Moderately Important"},
            {"value": "4", "label": "Very Important"},
            {"value": "5", "label": "Extremely Important"}
        ],
        "weight": 1,
        "order_index": 2
    },
    {
        "dimension_id": dimension_uuids["values"],
        "text": "How important is financial success to you?",
        "options": [
            {"value": "1", "label": "Not Important"},
            {"value": "2", "label": "Slightly Important"},
            {"value": "3", "label": "Moderately Important"},
            {"value": "4", "label": "Very Important"},
            {"value": "5", "label": "Extremely Important"}
        ],
        "weight": 1,
        "order_index": 3
    },
    {
        "dimension_id": dimension_uuids["values"],
        "text": "How important is spiritual or religious practice in your life?",
        "options": [
            {"value": "1", "label": "Not Important"},
            {"value": "2", "label": "Slightly Important"},
            {"value": "3", "label": "Moderately Important"},
            {"value": "4", "label": "Very Important"},
            {"value": "5", "label": "Extremely Important"}
        ],
        "weight": 1,
        "order_index": 4
    },
    {
        "dimension_id": dimension_uuids["values"],
        "text": "How important is environmental conservation to you?",
        "options": [
            {"value": "1", "label": "Not Important"},
            {"value": "2", "label": "Slightly Important"},
            {"value": "3", "label": "Moderately Important"},
            {"value": "4", "label": "Very Important"},
            {"value": "5", "label": "Extremely Important"}
        ],
        "weight": 1,
        "order_index": 5
    },
    
    # Interests & Activities Questions
    {
        "dimension_id": dimension_uuids["interests"],
        "text": "How often do you engage in creative activities (art, music, writing, etc.)?",
        "options": [
            {"value": "1", "label": "Never"},
            {"value": "2", "label": "Rarely"},
            {"value": "3", "label": "Sometimes"},
            {"value": "4", "label": "Often"},
            {"value": "5", "label": "Very Often"}
        ],
        "weight": 1,
        "order_index": 1
    },
    {
        "dimension_id": dimension_uuids["interests"],
        "text": "How often do you participate in physical activities or sports?",
        "options": [
            {"value": "1", "label": "Never"},
            {"value": "2", "label": "Rarely"},
            {"value": "3", "label": "Sometimes"},
            {"value": "4", "label": "Often"},
            {"value": "5", "label": "Very Often"}
        ],
        "weight": 1,
        "order_index": 2
    },
    {
        "dimension_id": dimension_uuids["interests"],
        "text": "How important is traveling to new places in your life?",
        "options": [
            {"value": "1", "label": "Not Important"},
            {"value": "2", "label": "Slightly Important"},
            {"value": "3", "label": "Moderately Important"},
            {"value": "4", "label": "Very Important"},
            {"value": "5", "label": "Extremely Important"}
        ],
        "weight": 1,
        "order_index": 3
    },
    {
        "dimension_id": dimension_uuids["interests"],
        "text": "Do you prefer indoor or outdoor activities?",
        "options": [
            {"value": "indoor", "label": "Strongly prefer indoor"},
            {"value": "mostly_indoor", "label": "Mostly prefer indoor"},
            {"value": "both", "label": "Enjoy both equally"},
            {"value": "mostly_outdoor", "label": "Mostly prefer outdoor"},
            {"value": "outdoor", "label": "Strongly prefer outdoor"}
        ],
        "weight": 1,
        "order_index": 4
    },
    {
        "dimension_id": dimension_uuids["interests"],
        "text": "How interested are you in learning about new technologies?",
        "options": [
            {"value": "1", "label": "Not Interested"},
            {"value": "2", "label": "Slightly Interested"},
            {"value": "3", "label": "Moderately Interested"},
            {"value": "4", "label": "Very Interested"},
            {"value": "5", "label": "Extremely Interested"}
        ],
        "weight": 1,
        "order_index": 5
    },
    
    # Communication Styles Questions
    {
        "dimension_id": dimension_uuids["communication"],
        "text": "When discussing sensitive topics, I prefer to:",
        "options": [
            {"value": "direct", "label": "Be direct and straightforward"},
            {"value": "somewhat_direct", "label": "Be mostly direct but tactful"},
            {"value": "balanced", "label": "Balance directness with sensitivity"},
            {"value": "somewhat_indirect", "label": "Be somewhat indirect to avoid conflict"},
            {"value": "indirect", "label": "Be indirect and very careful with words"}
        ],
        "weight": 1,
        "order_index": 1
    },
    {
        "dimension_id": dimension_uuids["communication"],
        "text": "When there is a disagreement, I typically:",
        "options": [
            {"value": "confront", "label": "Address it immediately"},
            {"value": "discuss_later", "label": "Wait for the right time to discuss it"},
            {"value": "reflect_first", "label": "Think about it thoroughly before discussing"},
            {"value": "avoid_minor", "label": "Let minor issues go"},
            {"value": "avoid_most", "label": "Avoid most confrontations"}
        ],
        "weight": 1,
        "order_index": 2
    },
    {
        "dimension_id": dimension_uuids["communication"],
        "text": "I express my emotions:",
        "options": [
            {"value": "very_openly", "label": "Very openly and intensely"},
            {"value": "openly", "label": "Openly"},
            {"value": "selectively", "label": "Selectively depending on the situation"},
            {"value": "carefully", "label": "Carefully and in a controlled way"},
            {"value": "rarely", "label": "Rarely or not at all"}
        ],
        "weight": 1,
        "order_index": 3
    },
    {
        "dimension_id": dimension_uuids["communication"],
        "text": "When listening to others, I tend to:",
        "options": [
            {"value": "interrupt", "label": "Interrupt with my thoughts and solutions"},
            {"value": "think_ahead", "label": "Think ahead to my response"},
            {"value": "actively_listen", "label": "Listen actively but offer my view"},
            {"value": "understand_first", "label": "Focus completely on understanding first"},
            {"value": "just_listen", "label": "Just listen without planning a response"}
        ],
        "weight": 1,
        "order_index": 4
    },
    {
        "dimension_id": dimension_uuids["communication"],
        "text": "When making decisions with others, I prefer to:",
        "options": [
            {"value": "lead", "label": "Take the lead and direct the process"},
            {"value": "contribute", "label": "Actively contribute ideas and opinions"},
            {"value": "collaborate", "label": "Collaborate equally with everyone"},
            {"value": "support", "label": "Support the process but follow others' lead"},
            {"value": "defer", "label": "Defer to others' expertise or preferences"}
        ],
        "weight": 1,
        "order_index": 5
    },
    
    # Life Goals & Priorities Questions
    {
        "dimension_id": dimension_uuids["goals"],
        "text": "What is your most important long-term goal?",
        "options": [
            {"value": "career", "label": "Career success and advancement"},
            {"value": "family", "label": "Building a family"},
            {"value": "financial", "label": "Financial independence"},
            {"value": "personal_growth", "label": "Personal growth and development"},
            {"value": "societal", "label": "Making a positive impact on society"}
        ],
        "weight": 1,
        "order_index": 1
    },
    {
        "dimension_id": dimension_uuids["goals"],
        "text": "How do you approach work-life balance?",
        "options": [
            {"value": "work_first", "label": "Work comes first most of the time"},
            {"value": "mostly_work", "label": "Primarily focused on work with some personal time"},
            {"value": "balanced", "label": "Strive for an equal balance"},
            {"value": "mostly_life", "label": "Prioritize personal life with work as necessary"},
            {"value": "life_first", "label": "Personal life always comes first"}
        ],
        "weight": 1,
        "order_index": 2
    },
    {
        "dimension_id": dimension_uuids["goals"],
        "text": "What is your approach to saving and spending money?",
        "options": [
            {"value": "very_frugal", "label": "Save as much as possible, spend minimally"},
            {"value": "mostly_save", "label": "Focus on saving but enjoy some spending"},
            {"value": "balanced", "label": "Balance between saving and spending"},
            {"value": "mostly_spend", "label": "Enjoy spending with some saving"},
            {"value": "live_now", "label": "Live in the moment, worry less about saving"}
        ],
        "weight": 1,
        "order_index": 3
    },
    {
        "dimension_id": dimension_uuids["goals"],
        "text": "How important is it for you to live near family?",
        "options": [
            {"value": "1", "label": "Not Important"},
            {"value": "2", "label": "Slightly Important"},
            {"value": "3", "label": "Moderately Important"},
            {"value": "4", "label": "Very Important"},
            {"value": "5", "label": "Extremely Important"}
        ],
        "weight": 1,
        "order_index": 4
    },
    {
        "dimension_id": dimension_uuids["goals"],
        "text": "How do you feel about having children?",
        "options": [
            {"value": "definitely_want", "label": "Definitely want children"},
            {"value": "probably_want", "label": "Probably want children"},
            {"value": "undecided", "label": "Undecided or could go either way"},
            {"value": "probably_not", "label": "Probably don't want children"},
            {"value": "definitely_not", "label": "Definitely don't want children"}
        ],
        "weight": 1,
        "order_index": 5
    },
    
    # Emotional Intelligence Questions
    {
        "dimension_id": dimension_uuids["emotional"],
        "text": "How well do you understand your own emotions?",
        "options": [
            {"value": "1", "label": "Not Well at All"},
            {"value": "2", "label": "Slightly Well"},
            {"value": "3", "label": "Moderately Well"},
            {"value": "4", "label": "Very Well"},
            {"value": "5", "label": "Extremely Well"}
        ],
        "weight": 1,
        "order_index": 1
    },
    {
        "dimension_id": dimension_uuids["emotional"],
        "text": "I can usually recognize when others are feeling stressed or upset",
        "options": [
            {"value": "1", "label": "Strongly Disagree"},
            {"value": "2", "label": "Disagree"},
            {"value": "3", "label": "Neutral"},
            {"value": "4", "label": "Agree"},
            {"value": "5", "label": "Strongly Agree"}
        ],
        "weight": 1,
        "order_index": 2
    },
    {
        "dimension_id": dimension_uuids["emotional"],
        "text": "When I'm upset, I can calm myself down effectively",
        "options": [
            {"value": "1", "label": "Strongly Disagree"},
            {"value": "2", "label": "Disagree"},
            {"value": "3", "label": "Neutral"},
            {"value": "4", "label": "Agree"},
            {"value": "5", "label": "Strongly Agree"}
        ],
        "weight": 1,
        "order_index": 3
    },
    {
        "dimension_id": dimension_uuids["emotional"],
        "text": "I can adapt my communication based on others' emotional states",
        "options": [
            {"value": "1", "label": "Strongly Disagree"},
            {"value": "2", "label": "Disagree"},
            {"value": "3", "label": "Neutral"},
            {"value": "4", "label": "Agree"},
            {"value": "5", "label": "Strongly Agree"}
        ],
        "weight": 1,
        "order_index": 4
    },
    {
        "dimension_id": dimension_uuids["emotional"],
        "text": "When someone shares their problems with me, I usually focus on:",
        "options": [
            {"value": "solutions", "label": "Offering solutions"},
            {"value": "mostly_solutions", "label": "Mostly solutions with some listening"},
            {"value": "balanced", "label": "Both listening and offering solutions"},
            {"value": "mostly_listening", "label": "Mostly listening with some suggestions"},
            {"value": "just_listening", "label": "Just listening and providing emotional support"}
        ],
        "weight": 1,
        "order_index": 5
    },
    
    # Lifestyle Preferences Questions
    {
        "dimension_id": dimension_uuids["lifestyle"],
        "text": "I prefer to live in a:",
        "options": [
            {"value": "urban", "label": "Urban city center"},
            {"value": "suburban", "label": "Suburban area"},
            {"value": "small_town", "label": "Small town"},
            {"value": "rural", "label": "Rural area"},
            {"value": "remote", "label": "Remote location"}
        ],
        "weight": 1,
        "order_index": 1
    },
    {
        "dimension_id": dimension_uuids["lifestyle"],
        "text": "My preferred sleep schedule is:",
        "options": [
            {"value": "early_riser", "label": "Early riser (before 6am)"},
            {"value": "morning", "label": "Morning person (6-8am)"},
            {"value": "average", "label": "Average (7-9am)"},
            {"value": "late_morning", "label": "Late morning (8-10am)"},
            {"value": "night_owl", "label": "Night owl (stay up late, wake up late)"}
        ],
        "weight": 1,
        "order_index": 2
    },
    {
        "dimension_id": dimension_uuids["lifestyle"],
        "text": "How important is cleanliness and organization in your living space?",
        "options": [
            {"value": "1", "label": "Not Important - I'm very relaxed about mess"},
            {"value": "2", "label": "Slightly Important - I prefer basic cleanliness"},
            {"value": "3", "label": "Moderately Important - I like things tidy"},
            {"value": "4", "label": "Very Important - I maintain a clean space"},
            {"value": "5", "label": "Extremely Important - I keep things pristine"}
        ],
        "weight": 1,
        "order_index": 3
    },
    {
        "dimension_id": dimension_uuids["lifestyle"],
        "text": "How often do you prefer to eat out vs. cook at home?",
        "options": [
            {"value": "always_out", "label": "Almost always eat out"},
            {"value": "mostly_out", "label": "Mostly eat out, occasionally cook"},
            {"value": "balanced", "label": "Equal mix of eating out and cooking"},
            {"value": "mostly_cook", "label": "Mostly cook, occasionally eat out"},
            {"value": "always_cook", "label": "Almost always cook at home"}
        ],
        "weight": 1,
        "order_index": 4
    },
    {
        "dimension_id": dimension_uuids["lifestyle"],
        "text": "How do you typically spend your weekends?",
        "options": [
            {"value": "very_social", "label": "Very socially active with many plans"},
            {"value": "somewhat_social", "label": "Somewhat social with some plans"},
            {"value": "balanced", "label": "Balance of social activities and alone time"},
            {"value": "somewhat_quiet", "label": "Mostly relaxing with occasional outings"},
            {"value": "very_quiet", "label": "Quiet, restful time at home"}
        ],
        "weight": 1,
        "order_index": 5
    }
]

# Update all questions to use UUID references
for question in questions:
    # The dimension_id key in each question is already set to use dimension_uuids in the definition above
    # But we need to update the print statements to show the dimension name for better logging
    original_dimension = next((key for key, value in dimension_uuids.items() if value == question["dimension_id"]), "unknown")
    question["original_dimension"] = original_dimension

# Function to insert data into Supabase
def seed_database():
    # Insert dimensions
    print("\nInserting dimensions:")
    for dimension in dimensions:
        try:
            # Find the original dimension key for better logging
            original_key = next((key for key, value in dimension_uuids.items() if value == dimension["id"]), "unknown")
            
            response = supabase.table('assessment_dimensions').insert(dimension).execute()
            print(f"✅ Added: {dimension['name']} (original key: {original_key})")
            time.sleep(0.2)
        except Exception as e:
            print(f"❌ Error adding dimension {dimension['name']}: {e}")
    
    # Insert questions
    print("\nInserting questions:")
    for question in questions:
        try:
            # Get the original dimension for better logging
            original_dimension = question.pop("original_dimension", "unknown")
            
            # Convert options to JSON string
            question_data = question.copy()
            question_data["options"] = json.dumps(question["options"])
            
            # Insert question
            response = supabase.table('assessment_questions').insert(question_data).execute()
            print(f"✅ Added: {original_dimension} question - {question['text'][:30]}...")
            time.sleep(0.2)
        except Exception as e:
            print(f"❌ Error adding question for {original_dimension}: {e}")

    # Count inserted records
    try:
        dimensions_count = supabase.table('assessment_dimensions').select('count', count='exact').execute()
        questions_count = supabase.table('assessment_questions').select('count', count='exact').execute()
        
        print(f"\nDatabase now contains:")
        print(f"- {dimensions_count.count} dimensions")
        print(f"- {questions_count.count} questions")
        
        print("\n✅ Database seeding completed!")
    except Exception as e:
        print(f"\n❓ Unable to count records: {e}")
        print("\n⚠️ Database seeding process finished with errors.")

if __name__ == "__main__":
    seed_database()