from django.shortcuts import render
from django.http import HttpResponse
import PyPDF2
import re
from collections import defaultdict
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required

# Define skills database
SKILLS = {
    'Technical': ['Python', 'Java', 'SQL', 'HTML', 'CSS', 'JavaScript', 'Excel', 'Machine Learning', 'Data Analysis', 'Git', 'Django'],
    'Soft': ['Communication', 'Problem Solving']
}

# Job roles with required skills
JOBS = {
    'Software Developer': ['Python', 'Java', 'HTML', 'CSS', 'Git'],
    'Data Analyst': ['Python', 'SQL', 'Excel', 'Data Analysis'],
    'Machine Learning Engineer': ['Python', 'Machine Learning']
}

# Interview questions and learning recommendations
INTERVIEW_QUESTIONS = {
    'Software Developer': [
        "Explain the difference between == and === in JavaScript.",
        "How do you handle asynchronous operations in Python?",
        "What is version control and why is it important?",
        "Describe the MVC architecture pattern.",
        "How do you optimize database queries?",
        "Explain the concept of RESTful APIs."
    ],
    'Data Analyst': [
        "How would you clean and prepare a dataset for analysis?",
        "Explain the difference between SQL JOIN types.",
        "What metrics would you use to evaluate a model's performance?",
        "How do you handle missing data in a dataset?",
        "Describe the steps in the data analysis process.",
        "What is the difference between supervised and unsupervised learning?"
    ],
    'Machine Learning Engineer': [
        "Explain overfitting and how to prevent it.",
        "What is the difference between supervised and unsupervised learning?",
        "How do you handle imbalanced datasets?",
        "Describe the bias-variance tradeoff.",
        "How do you evaluate the performance of a machine learning model?",
        "What are some common feature selection techniques?"
    ]
}

LEARNING_RECOMMENDATIONS = {
    'Python': "Codecademy Python course or Automate the Boring Stuff with Python book",
    'Java': "Oracle Java tutorials or Head First Java book",
    'SQL': "SQLZoo interactive tutorials or SQL for Data Science course",
    'HTML': "freeCodeCamp HTML/CSS course",
    'CSS': "CSS-Tricks website or freeCodeCamp responsive design course",
    'JavaScript': "Eloquent JavaScript book or MDN JavaScript guide",
    'Excel': "Microsoft Excel tutorials or Excel for Data Analysis course",
    'Machine Learning': "Coursera Machine Learning by Andrew Ng",
    'Data Analysis': "DataCamp Data Analyst track",
    'Git': "Git documentation or Learn Git Branching interactive tool",
    'Django': "Django official tutorial or Django for Beginners book",
    'Communication': "Toastmasters or online public speaking courses",
    'Problem Solving': "LeetCode practice or algorithmic thinking courses"
}

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def extract_skills(text):
    extracted = defaultdict(list)
    text_lower = text.lower()
    for category, skills in SKILLS.items():
        for skill in skills:
            if re.search(r'\b' + re.escape(skill.lower()) + r'\b', text_lower):
                extracted[category].append(skill)
    return dict(extracted)

def calculate_match(user_skills, job_skills):
    matched = set(user_skills) & set(job_skills)
    missing = set(job_skills) - set(user_skills)
    match_percentage = (len(matched) / len(job_skills)) * 100 if job_skills else 0
    return match_percentage, list(matched), list(missing)

def recommend_role(matches):
    best_role = max(matches, key=lambda x: x['percentage'])
    return best_role

def calculate_resume_strength(extracted_skills):
    total_skills = sum(len(skills) for skills in SKILLS.values())
    found_skills = sum(len(skills) for skills in extracted_skills.values())
    return (found_skills / total_skills) * 100

def home(request):
    context = {}
    if request.method == 'POST':
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        resume_file = request.FILES.get('resume')
        pasted_resume = request.POST.get('pasted_resume', '').strip()
        
        if not name:
            context['error'] = 'Please provide your name.'
            return render(request, 'matcher/home.html', context)
        
        if not resume_file and not pasted_resume:
            context['error'] = 'Please upload a resume PDF or paste your resume text.'
            return render(request, 'matcher/home.html', context)
        
        try:
            if resume_file:
                text = extract_text_from_pdf(resume_file)
            else:
                text = pasted_resume
            
            extracted_skills = extract_skills(text)
            
            # Flatten skills for matching
            all_user_skills = [skill for cat in extracted_skills.values() for skill in cat]
            
            matches = []
            for job, req_skills in JOBS.items():
                percentage, matched, missing = calculate_match(all_user_skills, req_skills)
                matches.append({
                    'role': job,
                    'percentage': percentage,
                    'matched': matched,
                    'missing': missing
                })
            
            recommended = recommend_role(matches)
            resume_strength = calculate_resume_strength(extracted_skills)
            
            context.update({
                'name': name,
                'email': email,
                'extracted_skills': extracted_skills,
                'matches': matches,
                'recommended': recommended,
                'resume_strength': resume_strength,
                'interview_questions': INTERVIEW_QUESTIONS.get(recommended['role'], []),
                'learning_recs': {skill: LEARNING_RECOMMENDATIONS.get(skill, 'General online courses') for skill in recommended['missing']},
                'show_results': True
            })
        except Exception as e:
            context['error'] = f'Error processing resume: {str(e)}'
    
    return render(request, 'matcher/home.html', context)

def about(request):
    return render(request, 'matcher/about.html')

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email', '')
            user.save()
            login(request, user)
            messages.success(request, 'Successfully signed up!')
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'matcher/signup.html', {'form': form})

class CustomLoginView(LoginView):
    template_name = 'matcher/login.html'

    def get_success_url(self):
        from django.urls import reverse
        return reverse('home')

    def form_valid(self, form):
        # Call parent's form_valid to handle authentication
        response = super().form_valid(form)
        return response

    def form_invalid(self, form):
        # JavaScript handles the redirect, so just return the invalid form
        return super().form_invalid(form)