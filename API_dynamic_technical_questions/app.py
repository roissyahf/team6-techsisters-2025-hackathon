from flask import Flask, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI
import os
import json
import traceback

app = Flask(__name__)
load_dotenv()

# Check for API key and initialize client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Warning: OPENAI_API_KEY environment variable not set.")
client = OpenAI(api_key=api_key)

# ============================================================
#  FIXED DEFINITIONS
# ============================================================

SKILL_MAP = {
    "T1_programming": "programming",
    "T2_problem_solving": "problem_solving",
    "T3_debugging": "debugging",
    "T4_system_understanding": "system_understanding",
    "T5_tools_familiarity": "tools_familiarity",
}

# Domain to Skill Category mapping with detailed context
DOMAIN_CONTEXT = {
    "software": {
        "category": "A. Logical & Structured Thinking",
        "field": "Software Engineering/Development",
        "roles": ["Software Engineer", "Full-stack Developer", "QA Engineer"],
        "focus": "building robust, maintainable code and applications",
        "skill_priority": ["T1_programming", "T3_debugging", "T2_problem_solving", "T4_system_understanding", "T5_tools_familiarity"]
    },
    "data": {
        "category": "B. Data & Analytical Insight",
        "field": "Data & Analytics",
        "roles": ["Data Scientist", "Data Analyst", "ML Engineer"],
        "focus": "extracting insights, building models, and data-driven decision making",
        "skill_priority": ["T2_problem_solving", "T1_programming", "T4_system_understanding", "T3_debugging", "T5_tools_familiarity"]
    },
    "design": {
        "category": "C. Creative & User-Centricity",
        "field": "Design/User Experience",
        "roles": ["UX Designer", "UI Designer", "Product Designer"],
        "focus": "creating intuitive, user-centered experiences and interfaces",
        "skill_priority": ["T4_system_understanding", "T2_problem_solving", "T5_tools_familiarity", "T1_programming", "T3_debugging"]
    },
    "security": {
        "category": "D. Systemic & Risk Management",
        "field": "Infrastructure & Security",
        "roles": ["Cybersecurity Analyst", "Cloud Architect", "DevOps Engineer"],
        "focus": "securing systems, managing risks, and ensuring reliability",
        "skill_priority": ["T4_system_understanding", "T3_debugging", "T2_problem_solving", "T1_programming", "T5_tools_familiarity"]
    },
    "management": {
        "category": "E. Communication & Stakeholder",
        "field": "Management/Strategy",
        "roles": ["Product Manager", "Project Manager", "Business Analyst"],
        "focus": "coordinating teams, aligning technical and business goals",
        "skill_priority": ["T4_system_understanding", "T2_problem_solving", "T5_tools_familiarity", "T1_programming", "T3_debugging"]
    },
    "content": {
        "category": "F. Content & Language Fluency",
        "field": "Technical Content & Digital",
        "roles": ["Technical Writer", "Content Strategist", "SEO Specialist"],
        "focus": "communicating technical concepts clearly and effectively",
        "skill_priority": ["T5_tools_familiarity", "T2_problem_solving", "T4_system_understanding", "T1_programming", "T3_debugging"]
    }
}

# Map Q4 answer to domain key
INTEREST_AREA_MAP = {
    "building and coding software or apps": "software",
    "working with data and insights": "data",
    "designing visuals or user experiences": "design",
    "managing systems or ensuring cybersecurity": "security",
    "coordinating teams or managing projects": "management",
    "creating content or writing documentation": "content",
}

# Skill level behavioral descriptors
SKILL_LEVEL_CONTEXT = {
    "beginner": {
        "description": "Has little or no practical experience",
        "behaviors": "basic understanding, willingness to learn, following guidance, simple tasks",
        "depth": "foundational concepts and basic familiarity"
    },
    "intermediate": {
        "description": "Has some hands-on experience or projects",
        "behaviors": "applying knowledge independently, handling moderate complexity, learning from experience",
        "depth": "practical application and growing autonomy"
    },
    "expert": {
        "description": "Has worked or studied deeply in a tech area",
        "behaviors": "architectural thinking, optimization, mentoring others, handling complex scenarios",
        "depth": "strategic thinking and advanced mastery"
    }
}

# Competency definitions for each skill
COMPETENCY_DEFINITIONS = {
    "T1_programming": {
        "competency": "Ability to write, understand, and work with code",
        "behaviors": ["writing code", "understanding syntax", "implementing algorithms", "using programming languages"]
    },
    "T2_problem_solving": {
        "competency": "Ability to analyze problems and design effective solutions",
        "behaviors": ["breaking down problems", "identifying patterns", "designing solutions", "thinking analytically"]
    },
    "T3_debugging": {
        "competency": "Ability to identify, diagnose, and fix technical issues",
        "behaviors": ["troubleshooting errors", "testing solutions", "root cause analysis", "fixing bugs"]
    },
    "T4_system_understanding": {
        "competency": "Ability to comprehend how components interact in larger systems",
        "behaviors": ["understanding architecture", "seeing connections", "grasping workflows", "system thinking"]
    },
    "T5_tools_familiarity": {
        "competency": "Ability to learn and use technical tools effectively",
        "behaviors": ["adopting new tools", "using software efficiently", "learning platforms", "applying technologies"]
    }
}

# Fallback questions (if LLM fails twice)
FALLBACK_QUESTIONS = {
    "T1_programming": {
        "question": "I can write basic code to solve simple problems.",
        "scale": {
            "1": "Never written code",
            "2": "Tried a few times with help",
            "3": "Can write simple scripts",
            "4": "Write code regularly",
            "5": "Write complex code confidently"
        }
    },
    "T2_problem_solving": {
        "question": "I can break down complex technical problems into smaller, manageable steps.",
        "scale": {
            "1": "Need complete guidance",
            "2": "Can do with significant help",
            "3": "Can break down simple problems",
            "4": "Handle moderate complexity",
            "5": "Solve complex problems independently"
        }
    },
    "T3_debugging": {
        "question": "I can identify and fix errors when something doesn't work as expected.",
        "scale": {
            "1": "Cannot debug at all",
            "2": "Need help to debug",
            "3": "Can fix simple errors",
            "4": "Debug moderate issues",
            "5": "Expert at troubleshooting"
        }
    },
    "T4_system_understanding": {
        "question": "I understand how different parts of a technical system work together.",
        "scale": {
            "1": "No understanding",
            "2": "Grasp very basic connections",
            "3": "Understand simple systems",
            "4": "Understand complex interactions",
            "5": "Design system architectures"
        }
    },
    "T5_tools_familiarity": {
        "question": "I can quickly learn and use new technical tools or software.",
        "scale": {
            "1": "Very difficult to learn new tools",
            "2": "Slow learner with guidance",
            "3": "Learn with moderate effort",
            "4": "Learn quickly",
            "5": "Master new tools rapidly"
        }
    }
}


# ============================================================
#  OPTIMIZED PROMPT BUILDER
# ============================================================

def build_optimized_prompt(domain, skill_level):
    domain_info = DOMAIN_CONTEXT[domain]
    skill_info = SKILL_LEVEL_CONTEXT[skill_level]
    
    # Build competency guidance
    competency_guide = ""
    for skill_id, details in COMPETENCY_DEFINITIONS.items():
        competency_guide += f"\n- {skill_id}: {details['competency']} (behaviors: {', '.join(details['behaviors'])})"
    
    prompt = f"""You are an expert assessment designer creating technical competency questions.

CONTEXT:
- User's interest area: {domain_info['category']} - {domain_info['field']}
- Target roles: {', '.join(domain_info['roles'])}
- Domain focus: {domain_info['focus']}
- Skill level: {skill_level.upper()} ({skill_info['description']})
- Behavioral depth: {skill_info['behaviors']}
- Question depth: {skill_info['depth']}

COMPETENCIES TO ASSESS:
{competency_guide}

YOUR TASK:
Generate 5 technical competency questions that:
1. Are specific to the {domain_info['field']} domain
2. Match {skill_level} level complexity
3. Use behavioral, observable language (avoid "I think", "I believe")
4. Can be answered on a 5-point scale from low to high capability
5. Each question must have a contextually relevant 5-point scale (NOT generic agree/disagree)

CRITICAL REQUIREMENTS:
- Questions must be domain-specific (reference {domain} concepts, not generic tech)
- Scales must describe actual capability levels relevant to each question
- Scale points should progress from "cannot do" → "beginner level" → "moderate capability" → "advanced capability" → "expert level"
- Each scale must be unique and tailored to its specific question

OUTPUT FORMAT (pure JSON, no markdown):
{{
  "T1_programming": {{
    "question": "Domain-specific question about coding/programming in {domain} context",
    "scale": {{
      "1": "Level 1 description",
      "2": "Level 2 description",
      "3": "Level 3 description",
      "4": "Level 4 description",
      "5": "Level 5 description"
    }}
  }},
  "T2_problem_solving": {{
    "question": "Domain-specific question about analytical thinking in {domain} context",
    "scale": {{
      "1": "Level 1 description",
      "2": "Level 2 description",
      "3": "Level 3 description",
      "4": "Level 4 description",
      "5": "Level 5 description"
    }}
  }},
  "T3_debugging": {{
    "question": "Domain-specific question about troubleshooting in {domain} context",
    "scale": {{
      "1": "Level 1 description",
      "2": "Level 2 description",
      "3": "Level 3 description",
      "4": "Level 4 description",
      "5": "Level 5 description"
    }}
  }},
  "T4_system_understanding": {{
    "question": "Domain-specific question about systems thinking in {domain} context",
    "scale": {{
      "1": "Level 1 description",
      "2": "Level 2 description",
      "3": "Level 3 description",
      "4": "Level 4 description",
      "5": "Level 5 description"
    }}
  }},
  "T5_tools_familiarity": {{
    "question": "Domain-specific question about tool usage in {domain} context",
    "scale": {{
      "1": "Level 1 description",
      "2": "Level 2 description",
      "3": "Level 3 description",
      "4": "Level 4 description",
      "5": "Level 5 description"
    }}
  }}
}}

EXAMPLE SCALE (for reference - create unique scales for each question):
- Bad: {{"1": "Strongly Disagree", "2": "Disagree", "3": "Neutral", "4": "Agree", "5": "Strongly Agree"}}
- Good: {{"1": "Never done this", "2": "Tried with heavy support", "3": "Can do with guidance", "4": "Can do independently", "5": "Can teach others"}}

Return ONLY the JSON object. No explanations, no markdown formatting."""

    return prompt


# ============================================================
#  LLM INTERACTION
# ============================================================

def ask_llm(domain, skill_level):
    prompt = build_optimized_prompt(domain, skill_level)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert technical assessment designer. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        text = response.choices[0].message.content
        parsed = json.loads(text)
        
        # Validate structure
        for skill_id in SKILL_MAP.keys():
            if skill_id not in parsed:
                print(f"⚠️ Missing key: {skill_id}")
                return None
            if "question" not in parsed[skill_id] or "scale" not in parsed[skill_id]:
                print(f"⚠️ Invalid structure for {skill_id}")
                return None
            
            # Validate scale is a dict with keys "1" through "5"
            scale = parsed[skill_id]["scale"]
            if not isinstance(scale, dict):
                print(f"⚠️ Scale is not a dict for {skill_id}")
                return None
            
            required_keys = {"1", "2", "3", "4", "5"}
            if set(scale.keys()) != required_keys:
                print(f"⚠️ Invalid scale keys for {skill_id}: {scale.keys()}")
                return None
        
        return parsed
        
    except Exception as e:
        print("❌ LLM error:", str(e))
        print(traceback.format_exc())
        return None


def sanitize_question(q):
    if not q:
        return ""
    q = q.strip().strip('"').strip("'")
    if not q.endswith("?"):
        q = q.rstrip(".") + "?"
    return q


def build_final_payload(domain, llm_obj):
    domain_info = DOMAIN_CONTEXT[domain]
    ordered_ids = domain_info["skill_priority"]
    
    payload = []
    for skill_id in ordered_ids:
        skill_name = SKILL_MAP[skill_id]
        
        if llm_obj and skill_id in llm_obj:
            # Use LLM-generated content
            q = sanitize_question(llm_obj[skill_id]["question"])
            scale = llm_obj[skill_id]["scale"]
        else:
            # Use fallback
            fallback = FALLBACK_QUESTIONS[skill_id]
            q = fallback["question"]
            scale = fallback["scale"]
        
        payload.append({
            "id": skill_id,
            "skill": skill_name,
            "question": q,
            "scale": scale
        })
    
    return payload


# ============================================================
#  ENDPOINT
# ============================================================

@app.post("/dynamic-technical-questions")
def generate_questions():
    try:
        data = request.get_json()
        
        # Extract Q4 & Q6
        q4 = data["user_profile"]["responses"]["Q4_interest_area"]["answer"]
        q6 = data["user_profile"]["responses"]["Q6_skill_level"]["answer"]
        
        domain = INTEREST_AREA_MAP.get(q4.lower(), "software")
        skill_level = q6.lower() if q6 in ["beginner", "intermediate", "expert"] else "beginner"
        
        print(f"Generating questions for: domain={domain}, skill_level={skill_level}")
        
        # LLM attempt 1
        llm_result = ask_llm(domain, skill_level)
        
        # Retry once if failed
        if llm_result is None:
            print("Retrying LLM...")
            llm_result = ask_llm(domain, skill_level)
        
        # Build final output
        output = build_final_payload(domain, llm_result)
        
        if llm_result:
            print("Using LLM-generated questions")
        else:
            print("Using fallback questions")
        
        return jsonify(output), 200
        
    except Exception as e:
        print("API failure:", e)
        print(traceback.format_exc())
        
        # Emergency fallback
        domain = "software"
        fallback_payload = build_final_payload(domain, None)
        return jsonify(fallback_payload), 500


# ============================================================
#  MAIN
# ============================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7075, debug=True)