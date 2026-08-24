from app.database.config import SessionLocal, engine, Base
from app.models.user import User
from app.models.profile import Profile
from app.models.skill import Skill
from app.models.interest import Interest
from app.models.career import Career
from app.models.assessment import AssessmentQuestion
from app.models.project import Project
from app.utils.auth import get_password_hash


def seed_if_empty():
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return

        _seed_skills(db)
        _seed_interests(db)
        _seed_careers(db)
        _seed_assessment_questions(db)
        _seed_projects(db)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Seed error: {e}")
    finally:
        db.close()


def _seed_skills(db):
    skills_data = [
        # Programming Languages
        ("Python", "Programming", "General-purpose programming language", "Basic syntax, variables, loops", "OOP, decorators, generators, async", "Meta-programming, C extensions, performance optimization"),
        ("JavaScript", "Programming", "Web programming language", "DOM manipulation, basic syntax", "ES6+, async/await, closures", "V8 internals, AST manipulation, transpilers"),
        ("TypeScript", "Programming", "Typed superset of JavaScript", "Basic types, interfaces", "Generics, utility types, declaration files", "Advanced type system, conditional types"),
        ("Java", "Programming", "Object-oriented programming language", "Classes, inheritance, basic syntax", "Streams, concurrency, design patterns", "JVM internals, performance tuning"),
        ("C++", "Programming", "High-performance programming language", "Variables, loops, functions", "Templates, STL, memory management", "Template metaprogramming, SIMD optimization"),
        ("Go", "Programming", "Simple, fast programming language", "Variables, functions, structs", "Goroutines, channels, interfaces", "Runtime internals, CGo, assembly"),
        ("Rust", "Programming", "Systems programming language", "Ownership, borrowing, basic syntax", "Lifetimes, traits, async", "Unsafe Rust, FFI, compiler internals"),
        ("SQL", "Programming", "Database query language", "SELECT, INSERT, JOIN", "Window functions, CTEs, optimization", "Query planning, indexing strategies"),

        # Web Development
        ("HTML/CSS", "Web Development", "Web markup and styling", "Tags, basic CSS properties", "Flexbox, Grid, animations", "Accessibility, performance optimization"),
        ("React", "Web Development", "JavaScript UI library", "Components, JSX, props", "Hooks, context, performance patterns", "Fiber architecture, SSR, concurrent features"),
        ("Node.js", "Web Development", "JavaScript runtime", "Basic server setup, Express", "Middleware, streams, clustering", "V8 internals, native modules"),
        ("Next.js", "Web Development", "React framework", "Pages, routing, basic SSR", "API routes, ISR, middleware", "Turbopack, advanced caching"),

        # Data Science & AI
        ("Machine Learning", "Data Science", "AI/ML algorithms", "Linear regression, decision trees", "Neural networks, NLP, computer vision", "Custom architectures, distributed training"),
        ("Data Analysis", "Data Science", "Data processing and insights", "Pandas basics, data cleaning", "Statistical analysis, visualization", "Big data pipelines, real-time analytics"),
        ("Deep Learning", "Data Science", "Neural network models", "Feedforward networks, CNNs", "Transformers, GANs, reinforcement learning", "Model optimization, edge deployment"),
        ("Natural Language Processing", "Data Science", "Text processing and understanding", "Tokenization, basic NLP", "Transformers, sentiment analysis", "Fine-tuning LLMs, prompt engineering"),
        ("NLP", "Data Science", "Natural Language Processing techniques", "Tokenization, basic NLP", "Transformers, sentiment analysis", "Fine-tuning LLMs, prompt engineering"),

        # DevOps & Cloud
        ("Docker", "DevOps", "Containerization platform", "Dockerfile, basic commands", "Multi-stage builds, compose", "Container security, orchestration"),
        ("AWS", "Cloud", "Amazon Web Services", "EC2, S3 basics", "Lambda, RDS, VPC", "Multi-region, cost optimization"),
        ("Kubernetes", "DevOps", "Container orchestration", "Pods, services, deployments", "Helm, operators, RBAC", "Cluster autoscaling, service mesh"),
        ("CI/CD", "DevOps", "Continuous integration and deployment", "GitHub Actions basics", "Pipeline optimization, rollback strategies", "GitOps, progressive delivery"),

        # Soft Skills
        ("Communication", "Soft Skills", "Effective information exchange", "Active listening, clear writing", "Presentation, negotiation", "Cross-cultural communication"),
        ("Problem Solving", "Soft Skills", "Analytical thinking and solution design", "Breaking down problems", "Algorithmic thinking, pattern recognition", "Systems thinking, creative solutions"),
        ("Leadership", "Soft Skills", "Guiding and motivating teams", "Team coordination", "Conflict resolution, mentoring", "Strategic thinking, organizational change"),
        ("Time Management", "Soft Skills", "Efficient time utilization", "Task prioritization", "Project planning, delegation", "Strategic planning, optimization"),

        # Database
        ("PostgreSQL", "Database", "Relational database", "Basic queries, table design", "Indexing, query optimization", "Partitioning, replication"),
        ("MongoDB", "Database", "NoSQL document database", "CRUD operations, basic queries", "Aggregation pipeline, indexing", "Sharding, change streams"),
        ("Redis", "Database", "In-memory data store", "Basic operations, data types", "Pub/sub, Lua scripting", "Cluster mode, memory optimization"),

        # Design
        ("UI/UX Design", "Design", "User interface and experience design", "Wireframing, basic design principles", "User research, prototyping", "Design systems, accessibility"),

        # Security
        ("Cybersecurity", "Security", "Information security practices", "Basic security concepts", "Penetration testing, secure coding", "Threat modeling, incident response"),

        # Project Management
        ("Agile/Scrum", "Management", "Project management methodology", "Sprints, basic ceremonies", "Scrum master, backlog management", "Scaling agile, Kanban"),

        # DevOps & Infrastructure
        ("Linux", "DevOps", "Linux operating system administration", "Basic commands, file system", "Shell scripting, system administration", "Kernel tuning, performance optimization"),

        # Tools
        ("Git", "Tools", "Version control system", "Basic commits, branches", "Rebasing, cherry-picking, hooks", "Advanced workflows, monorepo strategies"),

        # Mathematics
        ("Mathematics", "Academic", "Mathematical foundations for tech", "Basic algebra, statistics", "Linear algebra, calculus, probability", "Abstract algebra, real analysis"),
    ]

    for name, category, desc, beginner, intermediate, advanced in skills_data:
        skill = Skill(
            name=name, category=category, description=desc,
            beginner_definition=beginner, intermediate_definition=intermediate,
            advanced_definition=advanced,
        )
        db.add(skill)


def _seed_interests(db):
    interests_data = [
        ("Technology", "Technology"), ("AI/ML", "Technology"), ("Web Development", "Technology"),
        ("Mobile Development", "Technology"), ("Cloud Computing", "Technology"), ("Cybersecurity", "Technology"),
        ("Data Analysis", "Data"), ("Data Visualization", "Data"), ("Big Data", "Data"),
        ("Problem Solving", "Academic"), ("Research", "Academic"), ("Innovation", "Academic"),
        ("Business Strategy", "Business"), ("Entrepreneurship", "Business"), ("Marketing", "Business"),
        ("Finance", "Business"), ("Product Management", "Business"),
        ("Design", "Creative"), ("Writing", "Creative"), ("Music", "Creative"),
        ("Teaching", "Social"), ("Community Building", "Social"),
    ]
    for name, category in interests_data:
        db.add(Interest(name=name, category=category))


def _seed_careers(db):
    careers_data = [
        {
            "name": "Full Stack Developer",
            "description": "Build end-to-end web applications using frontend and backend technologies. Work on everything from database design to user interfaces.",
            "category": "Software Development",
            "required_skills": ["JavaScript", "React", "Node.js", "SQL", "HTML/CSS", "Git"],
            "optional_skills": ["TypeScript", "Docker", "AWS", "Next.js", "MongoDB"],
            "skill_importance": {"JavaScript": 1.0, "React": 0.9, "Node.js": 0.9, "SQL": 0.8, "HTML/CSS": 0.7, "Git": 0.6},
            "recommended_projects": ["E-commerce platform", "Social media dashboard", "Real-time chat app"],
            "learning_sequence": [
                {"title": "Web Fundamentals", "skills": ["HTML/CSS", "JavaScript"], "project": "Build a personal portfolio website", "objective": "Master web fundamentals"},
                {"title": "Frontend Development", "skills": ["React", "TypeScript"], "project": "Build a task management app with React", "objective": "Learn modern frontend development"},
                {"title": "Backend Development", "skills": ["Node.js", "SQL"], "project": "Build a REST API with authentication", "objective": "Master backend development"},
                {"title": "Full Stack Integration", "skills": ["Docker", "AWS"], "project": "Deploy a full-stack application", "objective": "Learn deployment and DevOps basics"},
            ],
            "related_careers": ["Frontend Developer", "Backend Developer", "DevOps Engineer"],
        },
        {
            "name": "Frontend Developer",
            "description": "Specialize in building user interfaces and experiences for web applications. Focus on design, interactivity, and performance.",
            "category": "Software Development",
            "required_skills": ["JavaScript", "React", "HTML/CSS", "Git"],
            "optional_skills": ["TypeScript", "Next.js", "CSS Frameworks"],
            "skill_importance": {"JavaScript": 1.0, "React": 0.95, "HTML/CSS": 0.9, "Git": 0.6},
            "recommended_projects": ["Interactive data dashboard", "Design system", "Progressive Web App"],
            "learning_sequence": [
                {"title": "HTML & CSS Mastery", "skills": ["HTML/CSS"], "project": "Build responsive landing pages", "objective": "Master HTML/CSS"},
                {"title": "JavaScript Proficiency", "skills": ["JavaScript"], "project": "Build interactive web components", "objective": "Master JavaScript"},
                {"title": "React Development", "skills": ["React", "TypeScript"], "project": "Build a component library", "objective": "Master React"},
                {"title": "Advanced Frontend", "skills": ["Next.js"], "project": "Build and deploy a Next.js application", "objective": "Learn advanced frontend patterns"},
            ],
            "related_careers": ["Full Stack Developer", "UI/UX Designer", "Mobile Developer"],
        },
        {
            "name": "Backend Developer",
            "description": "Build server-side logic, databases, and APIs. Focus on scalability, security, and system architecture.",
            "category": "Software Development",
            "required_skills": ["Python", "SQL", "Node.js", "Git", "Docker"],
            "optional_skills": ["AWS", "Kubernetes", "Redis", "MongoDB"],
            "skill_importance": {"Python": 0.9, "SQL": 0.95, "Node.js": 0.8, "Git": 0.7, "Docker": 0.7},
            "recommended_projects": ["Microservices architecture", "Real-time notification system", "API gateway"],
            "learning_sequence": [
                {"title": "Programming Foundations", "skills": ["Python", "SQL"], "project": "Build a CLI database tool", "objective": "Master programming and databases"},
                {"title": "Web Frameworks", "skills": ["Node.js"], "project": "Build a REST API with auth", "objective": "Learn web frameworks"},
                {"title": "DevOps Basics", "skills": ["Docker", "AWS"], "project": "Containerize and deploy an application", "objective": "Learn deployment"},
                {"title": "Advanced Backend", "skills": ["Redis", "Kubernetes"], "project": "Build a scalable microservices system", "objective": "Master advanced backend concepts"},
            ],
            "related_careers": ["Full Stack Developer", "DevOps Engineer", "Cloud Architect"],
        },
        {
            "name": "Data Scientist",
            "description": "Analyze complex data sets to extract insights and build predictive models. Combine statistics, programming, and domain expertise.",
            "category": "Data Science",
            "required_skills": ["Python", "Machine Learning", "Data Analysis", "SQL"],
            "optional_skills": ["Deep Learning", "NLP", "R", "Tableau"],
            "skill_importance": {"Python": 0.95, "Machine Learning": 0.9, "Data Analysis": 0.9, "SQL": 0.8},
            "recommended_projects": ["Predictive analytics dashboard", "Customer segmentation analysis", "Time series forecasting model"],
            "learning_sequence": [
                {"title": "Data Fundamentals", "skills": ["Python", "SQL", "Data Analysis"], "project": "Exploratory data analysis on real dataset", "objective": "Master data fundamentals"},
                {"title": "Machine Learning Basics", "skills": ["Machine Learning"], "project": "Build a classification model", "objective": "Learn ML algorithms"},
                {"title": "Advanced ML", "skills": ["Deep Learning", "NLP"], "project": "Build a sentiment analysis system", "objective": "Master advanced ML"},
                {"title": "Production ML", "skills": ["Docker"], "project": "Deploy an ML model as a web service", "objective": "Learn MLOps basics"},
            ],
            "related_careers": ["ML Engineer", "Data Analyst", "Business Intelligence Analyst"],
        },
        {
            "name": "Machine Learning Engineer",
            "description": "Design and implement ML systems that can learn from data. Bridge the gap between data science and production systems.",
            "category": "Data Science",
            "required_skills": ["Python", "Machine Learning", "Deep Learning", "Docker", "SQL"],
            "optional_skills": ["Kubernetes", "AWS", "NLP", "Computer Vision"],
            "skill_importance": {"Python": 0.95, "Machine Learning": 0.95, "Deep Learning": 0.85, "Docker": 0.7, "SQL": 0.6},
            "recommended_projects": ["End-to-end ML pipeline", "Real-time recommendation engine", "Computer vision application"],
            "learning_sequence": [
                {"title": "ML Foundations", "skills": ["Python", "Machine Learning"], "project": "Implement ML algorithms from scratch", "objective": "Deep understanding of ML"},
                {"title": "Deep Learning", "skills": ["Deep Learning", "NLP"], "project": "Build a transformer model", "objective": "Master deep learning"},
                {"title": "MLOps", "skills": ["Docker", "Kubernetes"], "project": "Build an ML pipeline with monitoring", "objective": "Learn MLOps"},
                {"title": "Production Systems", "skills": ["AWS"], "project": "Deploy a scalable ML service", "objective": "Master production ML"},
            ],
            "related_careers": ["Data Scientist", "AI Research Scientist", "Data Engineer"],
        },
        {
            "name": "Data Analyst",
            "description": "Transform raw data into actionable insights. Create reports, dashboards, and analyses that drive business decisions.",
            "category": "Data Science",
            "required_skills": ["SQL", "Data Analysis", "Python"],
            "optional_skills": ["Tableau", "Power BI", "R", "Data Visualization"],
            "skill_importance": {"SQL": 0.95, "Data Analysis": 0.95, "Python": 0.8},
            "recommended_projects": ["Sales performance dashboard", "Customer behavior analysis", "A/B test analysis report"],
            "learning_sequence": [
                {"title": "Data Fundamentals", "skills": ["SQL", "Data Analysis"], "project": "Analyze a real business dataset", "objective": "Master data querying and analysis"},
                {"title": "Python for Data", "skills": ["Python"], "project": "Automate data pipelines", "objective": "Learn Python for data work"},
                {"title": "Visualization", "skills": ["Tableau", "Data Visualization"], "project": "Build an interactive dashboard", "objective": "Master data visualization"},
                {"title": "Business Analytics", "skills": ["Data Analysis"], "project": "Complete end-to-end business analysis", "objective": "Apply analytics to business problems"},
            ],
            "related_careers": ["Data Scientist", "Business Intelligence Analyst", "Product Analyst"],
        },
        {
            "name": "DevOps Engineer",
            "description": "Bridge development and operations. Automate deployments, manage infrastructure, and ensure system reliability.",
            "category": "DevOps",
            "required_skills": ["Docker", "AWS", "CI/CD", "Git", "Linux"],
            "optional_skills": ["Kubernetes", "Terraform", "Ansible", "Monitoring"],
            "skill_importance": {"Docker": 0.95, "AWS": 0.9, "CI/CD": 0.9, "Git": 0.7, "Linux": 0.8},
            "recommended_projects": ["CI/CD pipeline setup", "Infrastructure as Code", "Monitoring dashboard"],
            "learning_sequence": [
                {"title": "Linux & Scripting", "skills": ["Linux", "Git"], "project": "Set up a Linux server and automate tasks", "objective": "Master Linux fundamentals"},
                {"title": "Containerization", "skills": ["Docker"], "project": "Containerize a multi-service application", "objective": "Master Docker"},
                {"title": "Cloud & CI/CD", "skills": ["AWS", "CI/CD"], "project": "Build a complete CI/CD pipeline", "objective": "Learn cloud and automation"},
                {"title": "Orchestration", "skills": ["Kubernetes"], "project": "Deploy applications on Kubernetes", "objective": "Master container orchestration"},
            ],
            "related_careers": ["Cloud Architect", "SRE", "Backend Developer"],
        },
        {
            "name": "Mobile App Developer",
            "description": "Build applications for iOS and Android platforms. Create engaging mobile experiences for millions of users.",
            "category": "Software Development",
            "required_skills": ["JavaScript", "React", "HTML/CSS"],
            "optional_skills": ["React Native", "Flutter", "Swift", "Kotlin"],
            "skill_importance": {"JavaScript": 0.9, "React": 0.85, "HTML/CSS": 0.6},
            "recommended_projects": ["Social media clone", "Fitness tracking app", "Food delivery app"],
            "learning_sequence": [
                {"title": "Programming Basics", "skills": ["JavaScript", "HTML/CSS"], "project": "Build a web calculator", "objective": "Master programming fundamentals"},
                {"title": "React & React Native", "skills": ["React", "React Native"], "project": "Build a cross-platform mobile app", "objective": "Learn mobile development"},
                {"title": "Native Development", "skills": ["Swift", "Kotlin"], "project": "Build native iOS and Android apps", "objective": "Learn native development"},
                {"title": "App Publishing", "skills": ["React Native"], "project": "Publish an app to both stores", "objective": "Master app deployment"},
            ],
            "related_careers": ["Full Stack Developer", "UI/UX Designer", "Product Manager"],
        },
        {
            "name": "Cloud Architect",
            "description": "Design and implement cloud-based solutions. Lead cloud migration strategies and optimize cloud infrastructure.",
            "category": "Cloud",
            "required_skills": ["AWS", "Docker", "Kubernetes", "SQL"],
            "optional_skills": ["Terraform", "Azure", "GCP", "Security"],
            "skill_importance": {"AWS": 0.95, "Docker": 0.85, "Kubernetes": 0.9, "SQL": 0.6},
            "recommended_projects": ["Multi-region deployment", "Cost optimization analysis", "Disaster recovery plan"],
            "learning_sequence": [
                {"title": "Cloud Foundations", "skills": ["AWS"], "project": "Set up a basic AWS infrastructure", "objective": "Master cloud fundamentals"},
                {"title": "Containerization", "skills": ["Docker", "Kubernetes"], "project": "Deploy microservices on Kubernetes", "objective": "Master container orchestration"},
                {"title": "Infrastructure as Code", "skills": ["Terraform"], "project": "Automate infrastructure provisioning", "objective": "Learn IaC"},
                {"title": "Cloud Architecture", "skills": ["AWS", "Security"], "project": "Design a production-ready architecture", "objective": "Master cloud architecture"},
            ],
            "related_careers": ["DevOps Engineer", "SRE", "Backend Developer"],
        },
        {
            "name": "Cybersecurity Analyst",
            "description": "Protect organizations from cyber threats. Monitor security systems, investigate incidents, and implement security measures.",
            "category": "Security",
            "required_skills": ["Cybersecurity", "Python", "Networking"],
            "optional_skills": ["Penetration Testing", "SIEM", "Forensics"],
            "skill_importance": {"Cybersecurity": 0.95, "Python": 0.8, "Networking": 0.85},
            "recommended_projects": ["Security audit report", "Vulnerability scanning tool", "Incident response simulation"],
            "learning_sequence": [
                {"title": "Security Fundamentals", "skills": ["Cybersecurity"], "project": "Complete a security fundamentals course", "objective": "Master security basics"},
                {"title": "Networking Security", "skills": ["Networking"], "project": "Set up a secure network lab", "objective": "Learn network security"},
                {"title": "Scripting for Security", "skills": ["Python"], "project": "Build a vulnerability scanner", "objective": "Learn security scripting"},
                {"title": "Advanced Security", "skills": ["Penetration Testing"], "project": "Conduct a penetration test", "objective": "Master offensive security"},
            ],
            "related_careers": ["Security Engineer", "SOC Analyst", "Penetration Tester"],
        },
        {
            "name": "Product Manager",
            "description": "Lead product strategy and development. Define product vision, prioritize features, and work with cross-functional teams.",
            "category": "Business",
            "required_skills": ["Communication", "Leadership", "Problem Solving"],
            "optional_skills": ["SQL", "Data Analysis", "Agile/Scrum"],
            "skill_importance": {"Communication": 0.95, "Leadership": 0.9, "Problem Solving": 0.85},
            "recommended_projects": ["Product requirements document", "User story mapping", "Product roadmap"],
            "learning_sequence": [
                {"title": "Product Fundamentals", "skills": ["Communication", "Problem Solving"], "project": "Write a PRD for a product", "objective": "Learn product thinking"},
                {"title": "User Research", "skills": ["Communication"], "project": "Conduct user interviews and analysis", "objective": "Master user research"},
                {"title": "Data-Driven PM", "skills": ["SQL", "Data Analysis"], "project": "Build a product metrics dashboard", "objective": "Learn data-driven PM"},
                {"title": "Agile Management", "skills": ["Agile/Scrum", "Leadership"], "project": "Manage a sprint cycle", "objective": "Master agile methodologies"},
            ],
            "related_careers": ["Business Analyst", "Project Manager", "UX Researcher"],
        },
        {
            "name": "UX/UI Designer",
            "description": "Design intuitive and beautiful user experiences. Combine research, wireframing, and visual design to create delightful products.",
            "category": "Design",
            "required_skills": ["UI/UX Design", "HTML/CSS", "Communication"],
            "optional_skills": ["Figma", "Prototyping", "User Research"],
            "skill_importance": {"UI/UX Design": 0.95, "HTML/CSS": 0.7, "Communication": 0.8},
            "recommended_projects": ["Design system", "Mobile app redesign", "UX case study"],
            "learning_sequence": [
                {"title": "Design Fundamentals", "skills": ["UI/UX Design"], "project": "Redesign an existing app's onboarding", "objective": "Master design principles"},
                {"title": "User Research", "skills": ["Communication"], "project": "Conduct user research and create personas", "objective": "Learn user research"},
                {"title": "Prototyping", "skills": ["Figma", "Prototyping"], "project": "Build an interactive prototype", "objective": "Master prototyping"},
                {"title": "Design Systems", "skills": ["UI/UX Design"], "project": "Create a design system", "objective": "Build scalable design systems"},
            ],
            "related_careers": ["Product Manager", "Frontend Developer", "UX Researcher"],
        },
        {
            "name": "AI Research Scientist",
            "description": "Push the boundaries of artificial intelligence. Publish research, develop new algorithms, and advance the state of the art.",
            "category": "Data Science",
            "required_skills": ["Python", "Machine Learning", "Deep Learning", "Mathematics"],
            "optional_skills": ["NLP", "Computer Vision", "Reinforcement Learning"],
            "skill_importance": {"Python": 0.9, "Machine Learning": 0.95, "Deep Learning": 0.95, "Mathematics": 0.9},
            "recommended_projects": ["Research paper implementation", "Novel model architecture", "Benchmark evaluation"],
            "learning_sequence": [
                {"title": "Mathematical Foundations", "skills": ["Mathematics", "Python"], "project": "Implement math algorithms in Python", "objective": "Master mathematical foundations"},
                {"title": "ML Research", "skills": ["Machine Learning"], "project": "Reproduce a research paper", "objective": "Learn ML research methods"},
                {"title": "Deep Learning Research", "skills": ["Deep Learning", "NLP"], "project": "Develop a novel model architecture", "objective": "Master deep learning research"},
                {"title": "Publishing & Communication", "skills": ["Communication"], "project": "Write and present a research paper", "objective": "Learn to communicate research"},
            ],
            "related_careers": ["ML Engineer", "Data Scientist", "Professor"],
        },
        {
            "name": "Technical Writer",
            "description": "Create clear, comprehensive documentation for software products. Make complex technical concepts accessible to all audiences.",
            "category": "Content",
            "required_skills": ["Communication", "HTML/CSS"],
            "optional_skills": ["Markdown", "Git", "API Documentation"],
            "skill_importance": {"Communication": 0.95, "HTML/CSS": 0.6},
            "recommended_projects": ["API documentation", "Tutorial series", "Knowledge base"],
            "learning_sequence": [
                {"title": "Writing Fundamentals", "skills": ["Communication"], "project": "Write technical tutorials", "objective": "Master technical writing"},
                {"title": "Documentation Tools", "skills": ["Markdown", "Git"], "project": "Set up a documentation site", "objective": "Learn documentation tools"},
                {"title": "API Documentation", "skills": ["API Documentation"], "project": "Document a REST API", "objective": "Master API documentation"},
                {"title": "Advanced Documentation", "skills": ["HTML/CSS"], "project": "Build an interactive documentation portal", "objective": "Create advanced documentation"},
            ],
            "related_careers": ["Content Strategist", "Developer Advocate", "Product Manager"],
        },
        {
            "name": "Business Intelligence Analyst",
            "description": "Transform data into business insights. Build dashboards, reports, and analyses that drive strategic decisions.",
            "category": "Business",
            "required_skills": ["SQL", "Data Analysis", "Communication"],
            "optional_skills": ["Tableau", "Power BI", "Python", "Excel"],
            "skill_importance": {"SQL": 0.9, "Data Analysis": 0.9, "Communication": 0.85},
            "recommended_projects": ["Executive dashboard", "KPI tracking system", "Sales forecasting model"],
            "learning_sequence": [
                {"title": "SQL & Data", "skills": ["SQL", "Data Analysis"], "project": "Build a sales analysis report", "objective": "Master SQL and data analysis"},
                {"title": "Visualization", "skills": ["Tableau", "Power BI"], "project": "Create an executive dashboard", "objective": "Master data visualization"},
                {"title": "Business Acumen", "skills": ["Communication"], "project": "Present findings to stakeholders", "objective": "Learn business communication"},
                {"title": "Advanced Analytics", "skills": ["Python"], "project": "Build a predictive model for business", "objective": "Learn advanced analytics"},
            ],
            "related_careers": ["Data Analyst", "Data Scientist", "Product Analyst"],
        },
        {
            "name": "Site Reliability Engineer",
            "description": "Ensure system reliability and performance at scale. Build monitoring, alerting, and incident response systems.",
            "category": "DevOps",
            "required_skills": ["Linux", "Docker", "AWS", "Python", "CI/CD"],
            "optional_skills": ["Kubernetes", "Terraform", "Monitoring", "Incident Response"],
            "skill_importance": {"Linux": 0.9, "Docker": 0.85, "AWS": 0.85, "Python": 0.8, "CI/CD": 0.8},
            "recommended_projects": ["Monitoring dashboard", "Incident response playbook", "Chaos engineering experiment"],
            "learning_sequence": [
                {"title": "Linux & Scripting", "skills": ["Linux", "Python"], "project": "Build monitoring scripts", "objective": "Master Linux and scripting"},
                {"title": "Cloud Infrastructure", "skills": ["AWS", "Docker"], "project": "Set up cloud infrastructure with monitoring", "objective": "Master cloud infrastructure"},
                {"title": "Reliability Practices", "skills": ["CI/CD", "Monitoring"], "project": "Implement a CI/CD pipeline with rollback", "objective": "Learn reliability practices"},
                {"title": "Advanced SRE", "skills": ["Kubernetes", "Incident Response"], "project": "Run a chaos engineering experiment", "objective": "Master SRE practices"},
            ],
            "related_careers": ["DevOps Engineer", "Cloud Architect", "Backend Developer"],
        },
        {
            "name": "Digital Marketing Specialist",
            "description": "Drive online marketing strategies across channels. Optimize campaigns, analyze performance, and grow digital presence.",
            "category": "Marketing",
            "required_skills": ["Data Analysis", "Communication", "SEO"],
            "optional_skills": ["Google Analytics", "Social Media Marketing", "Content Marketing"],
            "skill_importance": {"Data Analysis": 0.8, "Communication": 0.9, "SEO": 0.85},
            "recommended_projects": ["Marketing campaign analysis", "SEO audit report", "Social media strategy"],
            "learning_sequence": [
                {"title": "Marketing Fundamentals", "skills": ["Communication"], "project": "Create a marketing strategy document", "objective": "Learn marketing basics"},
                {"title": "SEO & Analytics", "skills": ["SEO", "Data Analysis"], "project": "Conduct an SEO audit", "objective": "Master SEO and analytics"},
                {"title": "Campaign Management", "skills": ["Google Analytics"], "project": "Run and analyze a marketing campaign", "objective": "Learn campaign management"},
                {"title": "Content Strategy", "skills": ["Content Marketing"], "project": "Develop a content marketing plan", "objective": "Master content marketing"},
            ],
            "related_careers": ["Content Strategist", "Social Media Manager", "Growth Hacker"],
        },
        {
            "name": "Database Administrator",
            "description": "Manage and optimize database systems. Ensure data integrity, performance, and security across database infrastructure.",
            "category": "Database",
            "required_skills": ["SQL", "PostgreSQL", "Linux"],
            "optional_skills": ["MongoDB", "Redis", "Python"],
            "skill_importance": {"SQL": 0.95, "PostgreSQL": 0.9, "Linux": 0.8},
            "recommended_projects": ["Database optimization project", "Backup and recovery system", "Performance monitoring"],
            "learning_sequence": [
                {"title": "Database Fundamentals", "skills": ["SQL", "PostgreSQL"], "project": "Design and optimize a database schema", "objective": "Master SQL and database design"},
                {"title": "Database Administration", "skills": ["Linux"], "project": "Set up a production database server", "objective": "Learn database administration"},
                {"title": "NoSQL & Caching", "skills": ["MongoDB", "Redis"], "project": "Implement a multi-database architecture", "objective": "Learn NoSQL databases"},
                {"title": "Performance Tuning", "skills": ["SQL", "Python"], "project": "Build a database monitoring tool", "objective": "Master performance optimization"},
            ],
            "related_careers": ["Data Engineer", "Backend Developer", "Cloud Architect"],
        },
        {
            "name": "Technical Project Manager",
            "description": "Lead technical projects from conception to delivery. Coordinate between engineering teams and stakeholders.",
            "category": "Management",
            "required_skills": ["Agile/Scrum", "Communication", "Leadership", "Problem Solving"],
            "optional_skills": ["SQL", "Git", "Risk Management"],
            "skill_importance": {"Agile/Scrum": 0.9, "Communication": 0.95, "Leadership": 0.9, "Problem Solving": 0.85},
            "recommended_projects": ["Project retrospective", "Risk assessment matrix", "Process improvement plan"],
            "learning_sequence": [
                {"title": "Project Management Basics", "skills": ["Agile/Scrum", "Communication"], "project": "Manage a small project end-to-end", "objective": "Learn PM fundamentals"},
                {"title": "Technical Understanding", "skills": ["Git", "SQL"], "project": "Review and manage technical requirements", "objective": "Build technical understanding"},
                {"title": "Leadership", "skills": ["Leadership"], "project": "Lead a team through a project lifecycle", "objective": "Develop leadership skills"},
                {"title": "Advanced PM", "skills": ["Problem Solving", "Risk Management"], "project": "Handle a project crisis and recover", "objective": "Master advanced PM skills"},
            ],
            "related_careers": ["Product Manager", "Scrum Master", "Engineering Manager"],
        },
    ]

    for data in careers_data:
        db.add(Career(**data))


def _seed_assessment_questions(db):
    questions = [
        {
            "question_text": "When you encounter a new technology, what do you do first?",
            "category": "technical_interest",
            "options": [
                "Read the documentation thoroughly",
                "Try a quick tutorial",
                "Watch someone else use it first",
                "Skip it unless I need it for a project",
            ],
            "scoring": {"0": 0.9, "1": 0.7, "2": 0.4, "3": 0.2},
        },
        {
            "question_text": "How do you approach a complex problem?",
            "category": "problem_solving",
            "options": [
                "Break it into smaller parts and solve each",
                "Try different approaches until something works",
                "Ask someone who has solved it before",
                "Feel overwhelmed and delay starting",
            ],
            "scoring": {"0": 0.9, "1": 0.7, "2": 0.5, "3": 0.2},
        },
        {
            "question_text": "Which activity sounds most interesting to you?",
            "category": "technology_interest",
            "options": [
                "Building a mobile app",
                "Analyzing large datasets",
                "Designing a website",
                "Managing a team project",
            ],
            "scoring": {"0": 0.8, "1": 0.6, "2": 0.6, "3": 0.4},
        },
        {
            "question_text": "When working on a group project, you prefer to:",
            "category": "communication",
            "options": [
                "Present the final result to the group",
                "Handle the technical implementation",
                "Organize tasks and coordinate the team",
                "Research and gather information",
            ],
            "scoring": {"0": 0.8, "1": 0.7, "2": 0.6, "3": 0.5},
        },
        {
            "question_text": "How do you feel about working with numbers and data?",
            "category": "analytical_ability",
            "options": [
                "I enjoy finding patterns in data",
                "I can work with numbers when needed",
                "I prefer creative tasks over analytical ones",
                "Numbers and data feel overwhelming",
            ],
            "scoring": {"0": 0.9, "1": 0.6, "2": 0.3, "3": 0.1},
        },
        {
            "question_text": "Which type of project would you most enjoy?",
            "category": "creativity",
            "options": [
                "Creating an interactive game",
                "Designing a beautiful interface",
                "Solving a real-world problem with code",
                "Building something that helps people",
            ],
            "scoring": {"0": 0.8, "1": 0.7, "2": 0.6, "3": 0.6},
        },
        {
            "question_text": "What interests you most about business?",
            "category": "business_interest",
            "options": [
                "Building and launching new products",
                "Analyzing market trends and opportunities",
                "Managing teams and resources",
                "Creating marketing strategies",
            ],
            "scoring": {"0": 0.8, "1": 0.7, "2": 0.6, "3": 0.5},
        },
        {
            "question_text": "How do you approach learning something new?",
            "category": "research_interest",
            "options": [
                "I dive deep into the theory first",
                "I prefer hands-on practice immediately",
                "I look for real-world applications",
                "I learn best by teaching others",
            ],
            "scoring": {"0": 0.8, "1": 0.7, "2": 0.6, "3": 0.5},
        },
        {
            "question_text": "When debugging code, you:",
            "category": "problem_solving",
            "options": [
                "Systematically trace through the logic",
                "Use print statements to find the issue",
                "Search Stack Overflow for similar problems",
                "Ask a colleague for help",
            ],
            "scoring": {"0": 0.9, "1": 0.6, "2": 0.5, "3": 0.4},
        },
        {
            "question_text": "Which skill development area excites you most?",
            "category": "technical_interest",
            "options": [
                "Learning a new programming language",
                "Understanding cloud infrastructure",
                "Building AI/ML models",
                "Designing user experiences",
            ],
            "scoring": {"0": 0.9, "1": 0.7, "2": 0.8, "3": 0.6},
        },
        {
            "question_text": "In your free time, you're most likely to:",
            "category": "technology_interest",
            "options": [
                "Work on a personal coding project",
                "Read tech news and articles",
                "Play video games",
                "Socialize with friends",
            ],
            "scoring": {"0": 0.9, "1": 0.7, "2": 0.3, "3": 0.2},
        },
        {
            "question_text": "How do you handle tight deadlines?",
            "category": "problem_solving",
            "options": [
                "Prioritize tasks and work systematically",
                "Work overtime to get everything done",
                "Negotiate the deadline with stakeholders",
                "Feel stressed and struggle to focus",
            ],
            "scoring": {"0": 0.9, "1": 0.6, "2": 0.7, "3": 0.2},
        },
        {
            "question_text": "Which communication style do you prefer?",
            "category": "communication",
            "options": [
                "Writing detailed documentation",
                "Giving presentations",
                "One-on-one conversations",
                "Visual diagrams and charts",
            ],
            "scoring": {"0": 0.8, "1": 0.7, "2": 0.6, "3": 0.5},
        },
        {
            "question_text": "How do you feel about repetitive tasks?",
            "category": "creativity",
            "options": [
                "I automate them with scripts",
                "I do them efficiently and move on",
                "I delegate or avoid them",
                "I find them meditative",
            ],
            "scoring": {"0": 0.9, "1": 0.7, "2": 0.3, "3": 0.4},
        },
        {
            "question_text": "What's your approach to analyzing a dataset?",
            "category": "analytical_ability",
            "options": [
                "Start with descriptive statistics and visualizations",
                "Look for specific patterns I expect",
                "Use pre-built tools and dashboards",
                "Avoid data analysis when possible",
            ],
            "scoring": {"0": 0.9, "1": 0.7, "2": 0.5, "3": 0.1},
        },
        {
            "question_text": "How interested are you in starting your own company someday?",
            "category": "business_interest",
            "options": [
                "Very interested - it's my dream",
                "Somewhat interested - if the right idea comes",
                "Not sure - depends on opportunities",
                "Not interested - prefer stability",
            ],
            "scoring": {"0": 0.9, "1": 0.6, "2": 0.4, "3": 0.2},
        },
        {
            "question_text": "When reading a research paper, you:",
            "category": "research_interest",
            "options": [
                "Read it thoroughly and take notes",
                "Skim the abstract and conclusion",
                "Look for practical applications",
                "Prefer video explanations instead",
            ],
            "scoring": {"0": 0.9, "1": 0.5, "2": 0.6, "3": 0.3},
        },
        {
            "question_text": "Which project type appeals to you most?",
            "category": "creativity",
            "options": [
                "Building something from scratch",
                "Improving an existing system",
                "Researching new possibilities",
                "Teaching others what I know",
            ],
            "scoring": {"0": 0.8, "1": 0.6, "2": 0.7, "3": 0.5},
        },
        {
            "question_text": "How do you prefer to receive feedback?",
            "category": "communication",
            "options": [
                "Written, detailed feedback",
                "Verbal discussion",
                "Visual examples",
                "Anonymous surveys",
            ],
            "scoring": {"0": 0.7, "1": 0.8, "2": 0.5, "3": 0.3},
        },
        {
            "question_text": "What motivates you most in your career?",
            "category": "problem_solving",
            "options": [
                "Solving challenging technical problems",
                "Creating products people love",
                "Leading teams to success",
                "Making a positive impact on society",
            ],
            "scoring": {"0": 0.8, "1": 0.7, "2": 0.6, "3": 0.7},
        },
    ]

    for q in questions:
        db.add(AssessmentQuestion(**q))


def _seed_projects(db):
    projects_data = [
        {
            "title": "Personal Portfolio Website",
            "description": "Build a responsive portfolio website showcasing your projects, skills, and experience. Include a contact form and project gallery.",
            "difficulty": "beginner",
            "skills_developed": ["HTML/CSS", "JavaScript", "React"],
            "expected_outcome": "A deployed website you can share with employers",
            "estimated_duration_weeks": 2,
            "portfolio_value": "High - demonstrates web development fundamentals",
        },
        {
            "title": "Task Management App",
            "description": "Create a full-featured task management application with user authentication, CRUD operations, and real-time updates.",
            "difficulty": "intermediate",
            "skills_developed": ["React", "Node.js", "SQL", "JavaScript"],
            "expected_outcome": "A production-ready web application",
            "estimated_duration_weeks": 4,
            "portfolio_value": "High - shows full-stack capabilities",
        },
        {
            "title": "REST API with Authentication",
            "description": "Build a secure REST API with JWT authentication, rate limiting, input validation, and comprehensive documentation.",
            "difficulty": "intermediate",
            "skills_developed": ["Node.js", "SQL", "Docker", "Git"],
            "expected_outcome": "A well-documented API with security best practices",
            "estimated_duration_weeks": 3,
            "portfolio_value": "High - demonstrates backend expertise",
        },
        {
            "title": "E-commerce Platform",
            "description": "Develop a complete e-commerce solution with product listings, shopping cart, payment integration, and admin dashboard.",
            "difficulty": "advanced",
            "skills_developed": ["React", "Node.js", "SQL", "TypeScript", "AWS"],
            "expected_outcome": "A scalable e-commerce platform",
            "estimated_duration_weeks": 8,
            "portfolio_value": "Very High - complex full-stack project",
        },
        {
            "title": "Machine Learning Classification Model",
            "description": "Build a model that classifies data using various ML algorithms. Include data preprocessing, model evaluation, and visualization.",
            "difficulty": "intermediate",
            "skills_developed": ["Python", "Machine Learning", "Data Analysis"],
            "expected_outcome": "A working ML model with evaluation metrics",
            "estimated_duration_weeks": 4,
            "portfolio_value": "High - demonstrates ML skills",
        },
        {
            "title": "Real-time Chat Application",
            "description": "Create a real-time messaging app with WebSocket support, user presence indicators, and message history.",
            "difficulty": "intermediate",
            "skills_developed": ["JavaScript", "Node.js", "React", "Docker"],
            "expected_outcome": "A functional real-time chat application",
            "estimated_duration_weeks": 3,
            "portfolio_value": "High - shows real-time programming skills",
        },
        {
            "title": "Data Dashboard",
            "description": "Build an interactive data dashboard that visualizes metrics from multiple data sources with filters and drill-down capabilities.",
            "difficulty": "intermediate",
            "skills_developed": ["React", "Data Analysis", "SQL", "JavaScript"],
            "expected_outcome": "An interactive dashboard with multiple visualizations",
            "estimated_duration_weeks": 4,
            "portfolio_value": "High - demonstrates data visualization skills",
        },
        {
            "title": "CI/CD Pipeline Setup",
            "description": "Set up a complete CI/CD pipeline with automated testing, building, and deployment to cloud infrastructure.",
            "difficulty": "intermediate",
            "skills_developed": ["CI/CD", "Docker", "AWS", "Git"],
            "expected_outcome": "A working CI/CD pipeline for a sample project",
            "estimated_duration_weeks": 2,
            "portfolio_value": "High - shows DevOps competency",
        },
        {
            "title": "Cloud Infrastructure as Code",
            "description": "Design and implement cloud infrastructure using Terraform or CloudFormation. Include networking, security, and monitoring.",
            "difficulty": "advanced",
            "skills_developed": ["AWS", "Docker", "Kubernetes", "CI/CD"],
            "expected_outcome": "Production-ready infrastructure code",
            "estimated_duration_weeks": 5,
            "portfolio_value": "Very High - demonstrates cloud architecture",
        },
        {
            "title": "Sentiment Analysis Tool",
            "description": "Build a tool that analyzes text sentiment using NLP techniques. Include a web interface and API for integration.",
            "difficulty": "advanced",
            "skills_developed": ["Python", "Machine Learning", "NLP", "Docker"],
            "expected_outcome": "A working sentiment analysis application",
            "estimated_duration_weeks": 5,
            "portfolio_value": "Very High - showcases NLP and ML skills",
        },
        {
            "title": "Mobile Expense Tracker",
            "description": "Create a cross-platform mobile app for tracking expenses with categories, charts, and export functionality.",
            "difficulty": "intermediate",
            "skills_developed": ["React", "JavaScript", "Node.js", "SQL"],
            "expected_outcome": "A published mobile app on app stores",
            "estimated_duration_weeks": 6,
            "portfolio_value": "High - demonstrates mobile development",
        },
        {
            "title": "Security Audit Report",
            "description": "Conduct a comprehensive security audit of a web application. Document vulnerabilities, provide remediation steps, and create a security policy.",
            "difficulty": "advanced",
            "skills_developed": ["Cybersecurity", "Python", "SQL"],
            "expected_outcome": "A professional security audit report",
            "estimated_duration_weeks": 3,
            "portfolio_value": "High - demonstrates security expertise",
        },
        {
            "title": "Open Source Contribution",
            "description": "Contribute meaningful features or bug fixes to established open source projects. Document your contributions and impact.",
            "difficulty": "intermediate",
            "skills_developed": ["Git", "Communication", "Problem Solving"],
            "expected_outcome": "Merged pull requests in open source repositories",
            "estimated_duration_weeks": 4,
            "portfolio_value": "Very High - shows collaboration and code quality",
        },
        {
            "title": "Technical Blog Series",
            "description": "Write a series of 5 technical blog posts explaining complex concepts clearly. Include code examples and diagrams.",
            "difficulty": "beginner",
            "skills_developed": ["Communication", "HTML/CSS"],
            "expected_outcome": "Published technical articles with reader engagement",
            "estimated_duration_weeks": 3,
            "portfolio_value": "Medium - demonstrates communication skills",
        },
    ]

    for data in projects_data:
        db.add(Project(**data))
