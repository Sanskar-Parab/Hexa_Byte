import app.models.user
import app.models.profile
import app.models.skill
import app.models.interest
import app.models.assessment
import app.models.career
import app.models.roadmap
import app.models.project
import app.models.progress
import app.models.skill_evidence
import app.models.skill_assessment
from app.database.config import SessionLocal
from app.models.skill import Skill
from app.models.interest import Interest
from app.models.career import Career
from app.models.project import Project


def add_new_skills():
    db = SessionLocal()
    try:
        existing = {s.name for s in db.query(Skill.name).all()}
        new_skills = [
            ("C#", "Programming", "Microsoft object-oriented language", "Variables, classes, basic syntax", "LINQ, async/await, generics", "IL optimization, source generators"),
            ("PHP", "Programming", "Server-side web language", "Variables, arrays, basic syntax", "Composer, Laravel, PSR standards", "Extension development, OPcache tuning"),
            ("Swift", "Programming", "Apple ecosystem language", "Optionals, basic syntax", "Protocol-oriented, concurrency", "Swift runtime, ABI stability"),
            ("Kotlin", "Programming", "Modern JVM language", "Null safety, basic syntax", "Coroutines, DSLs, extensions", "Compiler plugins, KMP"),
            ("Ruby", "Programming", "Dynamic scripting language", "Blocks, basic syntax", "Metaprogramming, Rails", "VM optimization, native extensions"),
            ("Scala", "Programming", "Functional JVM language", "Case classes, basic syntax", "Akka, Cats, implicits", "Macro system, ZIO"),
            ("Vue.js", "Web Development", "Progressive JavaScript framework", "Templates, directives, reactivity", "Composition API, Pinia, Nuxt", "Virtual DOM internals, custom renderers"),
            ("Angular", "Web Development", "Platform for web apps", "Components, modules, basic syntax", "RxJS, NgRx, lazy loading", "Zone.js, AOT compilation"),
            ("Svelte", "Web Development", "Compile-time web framework", "Reactive declarations, basic syntax", "Stores, transitions, SvelteKit", "Compiler output optimization"),
            ("Tailwind CSS", "Web Development", "Utility-first CSS framework", "Utility classes, basic styling", "Custom config, plugins, theming", "Purge optimization, design systems"),
            ("GraphQL", "Web Development", "Query language for APIs", "Queries, mutations, basic schema", "Subscriptions, resolvers, federation", "Schema stitching, performance optimization"),
            ("REST API Design", "Web Development", "RESTful API architecture", "HTTP methods, status codes", "Versioning, pagination, HATEOAS", "API gateway patterns, rate limiting"),
            ("Computer Vision", "Data Science", "Image and video analysis", "Image processing, basic CV", "Object detection, segmentation", "3D vision, video understanding"),
            ("Reinforcement Learning", "Data Science", "Learning from interactions", "Q-learning, basic RL", "Policy gradients, model-based RL", "Multi-agent RL, real-world deployment"),
            ("Data Engineering", "Data Science", "Building data pipelines", "ETL basics, SQL pipelines", "Spark, Airflow, data warehousing", "Stream processing, data mesh"),
            ("Generative AI", "Data Science", "AI content generation", "Prompt engineering, basic LLMs", "Fine-tuning, RAG, agents", "Custom training, alignment"),
            ("MLOps", "Data Science", "ML operations and deployment", "Model serving basics", "ML pipelines, monitoring", "Feature stores, A/B testing"),
            ("Azure", "Cloud", "Microsoft cloud platform", "Virtual machines, Blob storage", "Azure Functions, DevOps", "Arc, Synapse, Sentinel"),
            ("GCP", "Cloud", "Google Cloud Platform", "Compute Engine, Cloud Storage", "BigQuery, Cloud Functions", "Vertex AI, Anthos"),
            ("Terraform", "DevOps", "Infrastructure as Code", "Resources, providers, basic config", "Modules, workspaces, state management", "Custom providers, policy as code"),
            ("Ansible", "DevOps", "Configuration management", "Playbooks, basic modules", "Roles, AWX, galaxy", "Custom modules, collections"),
            ("Prometheus", "DevOps", "Monitoring and alerting", "Metrics, basic queries", "Alerting rules, Grafana dashboards", "Long-term storage, federation"),
            ("Grafana", "DevOps", "Observability platform", "Dashboards, basic panels", "Alerting, data sources, variables", "Provisioning, plugin development"),
            ("Teamwork", "Soft Skills", "Collaborating effectively with others", "Active participation, reliability", "Cross-functional collaboration, feedback", "Building high-performing teams"),
            ("Critical Thinking", "Soft Skills", "Objective analysis and evaluation", "Questioning assumptions", "Evidence-based reasoning, bias detection", "Complex system analysis"),
            ("Adaptability", "Soft Skills", "Adjusting to new conditions", "Learning from feedback", "Managing change, resilience", "Leading transformation"),
            ("Creativity", "Soft Skills", "Generating innovative ideas", "Brainstorming, curiosity", "Design thinking, innovation methods", "Creative leadership, fostering innovation"),
            ("MySQL", "Database", "Popular relational database", "Basic queries, table design", "Replication, optimization", "InnoDB internals, cluster"),
            ("Elasticsearch", "Database", "Search and analytics engine", "Basic queries, indexing", "Aggregations, analyzers", "Cluster management, performance tuning"),
            ("DynamoDB", "Database", "AWS NoSQL database", "Basic operations, capacity modes", "GSI, sparse indexes", "DynamoDB Streams, global tables"),
            ("Cassandra", "Database", "Distributed NoSQL database", "Basic queries, data modeling", "Tuning, compaction", "Multi-datacenter, repair"),
            ("Neo4j", "Database", "Graph database", "Cypher basics, node/edge creation", "Advanced queries, indexing", "Clustering, graph algorithms"),
            ("Figma", "Design", "Collaborative design tool", "Basic prototyping, frames", "Components, auto-layout, variants", "Design tokens, plugins"),
            ("Graphic Design", "Design", "Visual communication", "Typography, color theory", "Brand identity, layout", "Motion graphics, 3D design"),
            ("Motion Design", "Design", "Animation and visual effects", "Basic animation principles", "After Effects, Lottie", "Complex character animation"),
            ("Ethical Hacking", "Security", "Authorized security testing", "Reconnaissance, basic scanning", "Exploitation, post-exploitation", "Custom tools, advanced techniques"),
            ("Cloud Security", "Security", "Cloud-specific security practices", "IAM basics, security groups", "WAF, KMS, security auditing", "Zero trust architecture"),
            ("Application Security", "Security", "Securing software applications", "OWASP Top 10, basic hardening", "SAST/DAST, secure SDLC", "Security architecture, threat modeling"),
            ("Product Management", "Management", "Product strategy and execution", "User stories, basic roadmap", "Product discovery, metrics", "Product-led growth, pricing strategy"),
            ("Business Analysis", "Management", "Business requirements analysis", "Requirements gathering, basic modeling", "Process improvement, stakeholder management", "Enterprise architecture, digital transformation"),
            ("Networking", "DevOps", "Computer networking", "TCP/IP, DNS, basic protocols", "Load balancing, firewalls", "Software-defined networking"),
            ("VS Code", "Tools", "Code editor", "Basic usage, extensions", "Debugging, remote development", "Custom extensions, performance"),
            ("Jira", "Tools", "Project management tool", "Basic board setup, issues", "Workflows, automation, reporting", "Advanced configuration, integrations"),
            ("Statistics", "Academic", "Statistical methods and analysis", "Descriptive statistics, probability", "Inferential statistics, hypothesis testing", "Bayesian methods, causal inference"),
            ("Discrete Mathematics", "Academic", "Mathematics for computer science", "Logic, sets, basic proofs", "Graph theory, combinatorics", "Advanced algorithms, complexity theory"),
            ("Blockchain Development", "Blockchain", "Distributed ledger technology", "Basic transactions, smart contracts", "DeFi protocols, NFTs", "Layer 2, cross-chain"),
            ("Solidity", "Blockchain", "Smart contract language", "Basic contracts, variables", "Upgradable contracts, security", "Complex DeFi, gas optimization"),
            ("AR/VR Development", "AR/VR", "Augmented and virtual reality", "Unity basics, 3D objects", "Spatial computing, hand tracking", "Multi-user VR, haptics"),
            ("Software Testing", "Quality", "Testing methodologies", "Unit testing basics", "Integration testing, TDD", "Performance testing, chaos engineering"),
            ("Automation Testing", "Quality", "Automated test frameworks", "Selenium basics, test scripts", "CI integration, page object model", "Visual testing, performance testing"),
            ("IT Support", "Support", "Technical support and troubleshooting", "Hardware/software basics", "Network troubleshooting, ticketing systems", "System administration, scripting"),
        ]
        added = 0
        for name, cat, desc, beg, inter, adv in new_skills:
            if name not in existing:
                db.add(Skill(name=name, category=cat, description=desc,
                           beginner_definition=beg, intermediate_definition=inter,
                           advanced_definition=adv))
                added += 1
        db.commit()
        print(f"Added {added} new skills ({len(existing)} existed)")
    finally:
        db.close()


def add_new_interests():
    db = SessionLocal()
    try:
        existing = {i.name for i in db.query(Interest.name).all()}
        new_interests = [
            ("Blockchain", "Technology"), ("AR/VR", "Technology"), ("IoT", "Technology"),
            ("Gaming", "Creative"), ("Animation", "Creative"), ("Photography", "Creative"),
            ("Public Speaking", "Social"), ("Mentoring", "Social"), ("Volunteering", "Social"),
            ("Sustainability", "Academic"), ("Healthcare", "Academic"), ("Education", "Academic"),
            ("Robotics", "Technology"), ("Space", "Academic"), ("Biotechnology", "Academic"),
            ("E-commerce", "Business"), ("Consulting", "Business"), ("Real Estate", "Business"),
            ("Podcasting", "Creative"), ("Video Production", "Creative"), ("Graphic Design", "Creative"),
            ("Data Science", "Data"), ("Machine Learning", "Data"), ("Cloud Architecture", "Technology"),
        ]
        added = 0
        for name, cat in new_interests:
            if name not in existing:
                db.add(Interest(name=name, category=cat))
                added += 1
        db.commit()
        print(f"Added {added} new interests ({len(existing)} existed)")
    finally:
        db.close()


def add_new_careers():
    db = SessionLocal()
    try:
        existing = {c.name for c in db.query(Career.name).all()}
        new_careers = [
            {
                "name": "Data Engineer",
                "description": "Build and maintain data infrastructure. Design pipelines that transform raw data into usable formats for analysis and ML.",
                "category": "Data Science",
                "required_skills": ["Python", "SQL", "Data Engineering", "Docker"],
                "optional_skills": ["AWS", "Kubernetes", "Spark", "Airflow"],
                "skill_importance": {"Python": 0.9, "SQL": 0.95, "Data Engineering": 0.9, "Docker": 0.7},
                "recommended_projects": ["Real-time data pipeline", "Data warehouse design", "ETL automation system"],
                "learning_sequence": [
                    {"title": "Programming & SQL", "skills": ["Python", "SQL"], "project": "Build data transformation scripts", "objective": "Master programming and SQL"},
                    {"title": "Data Pipeline Tools", "skills": ["Data Engineering", "Docker"], "project": "Build an ETL pipeline with Docker", "objective": "Learn data engineering tools"},
                    {"title": "Cloud Data Services", "skills": ["AWS"], "project": "Deploy data pipelines on AWS", "objective": "Master cloud data services"},
                    {"title": "Advanced Data Engineering", "skills": ["Spark", "Airflow"], "project": "Build a real-time streaming pipeline", "objective": "Master advanced data engineering"},
                ],
                "related_careers": ["Data Scientist", "ML Engineer", "Backend Developer"],
            },
            {
                "name": "Solutions Architect",
                "description": "Design and oversee technology solutions for business problems. Bridge business requirements with technical implementation.",
                "category": "Architecture",
                "required_skills": ["AWS", "Docker", "SQL", "Communication", "Problem Solving"],
                "optional_skills": ["Kubernetes", "Terraform", "Python", "System Design"],
                "skill_importance": {"AWS": 0.9, "Docker": 0.8, "SQL": 0.7, "Communication": 0.9, "Problem Solving": 0.85},
                "recommended_projects": ["Architecture design document", "Technology evaluation report", "Migration plan"],
                "learning_sequence": [
                    {"title": "Cloud Foundations", "skills": ["AWS"], "project": "Design a cloud architecture", "objective": "Master cloud fundamentals"},
                    {"title": "Containerization & DevOps", "skills": ["Docker", "Kubernetes"], "project": "Design a microservices architecture", "objective": "Learn container orchestration"},
                    {"title": "Architecture Patterns", "skills": ["System Design", "SQL"], "project": "Design a scalable system", "objective": "Master architecture patterns"},
                    {"title": "Communication & Leadership", "skills": ["Communication", "Problem Solving"], "project": "Present architecture to stakeholders", "objective": "Master stakeholder communication"},
                ],
                "related_careers": ["Cloud Architect", "Engineering Manager", "Technical Lead"],
            },
            {
                "name": "Engineering Manager",
                "description": "Lead and grow engineering teams. Balance technical decisions with people management and team development.",
                "category": "Management",
                "required_skills": ["Leadership", "Communication", "Agile/Scrum", "Problem Solving"],
                "optional_skills": ["Git", "System Design", "Mentoring"],
                "skill_importance": {"Leadership": 0.95, "Communication": 0.95, "Agile/Scrum": 0.8, "Problem Solving": 0.85},
                "recommended_projects": ["Team process improvement", "Hiring pipeline design", "Technical roadmap"],
                "learning_sequence": [
                    {"title": "Leadership Fundamentals", "skills": ["Leadership", "Communication"], "project": "Lead a team through a project", "objective": "Master leadership basics"},
                    {"title": "Agile Management", "skills": ["Agile/Scrum"], "project": "Implement agile practices in a team", "objective": "Master agile methodologies"},
                    {"title": "Technical Leadership", "skills": ["System Design", "Git"], "project": "Make technical architecture decisions", "objective": "Build technical leadership skills"},
                    {"title": "People Management", "skills": ["Mentoring", "Problem Solving"], "project": "Mentor junior developers", "objective": "Master people management"},
                ],
                "related_careers": ["Technical Project Manager", "Product Manager", "CTO"],
            },
            {
                "name": "Cybersecurity Engineer",
                "description": "Design and implement security systems. Protect organizations from cyber threats through proactive security measures.",
                "category": "Security",
                "required_skills": ["Cybersecurity", "Python", "Linux", "Networking", "Cloud Security"],
                "optional_skills": ["Ethical Hacking", "Application Security", "AWS"],
                "skill_importance": {"Cybersecurity": 0.95, "Python": 0.8, "Linux": 0.85, "Networking": 0.9, "Cloud Security": 0.85},
                "recommended_projects": ["Security automation toolkit", "Cloud security audit", "Incident response system"],
                "learning_sequence": [
                    {"title": "Security Fundamentals", "skills": ["Cybersecurity", "Networking"], "project": "Set up a security monitoring lab", "objective": "Master security basics"},
                    {"title": "Scripting & Automation", "skills": ["Python", "Linux"], "project": "Build security automation tools", "objective": "Learn security scripting"},
                    {"title": "Cloud Security", "skills": ["Cloud Security", "AWS"], "project": "Secure a cloud deployment", "objective": "Master cloud security"},
                    {"title": "Advanced Security", "skills": ["Ethical Hacking", "Application Security"], "project": "Conduct a penetration test", "objective": "Master offensive security"},
                ],
                "related_careers": ["Security Architect", "Penetration Tester", "SOC Analyst"],
            },
            {
                "name": "Growth Hacker",
                "description": "Drive rapid business growth through innovative marketing and product strategies. Combine data analysis with creative experimentation.",
                "category": "Marketing",
                "required_skills": ["Data Analysis", "Python", "Communication", "Problem Solving"],
                "optional_skills": ["SQL", "A/B Testing", "Digital Marketing"],
                "skill_importance": {"Data Analysis": 0.9, "Python": 0.7, "Communication": 0.85, "Problem Solving": 0.8},
                "recommended_projects": ["Growth experiment dashboard", "Viral loop analysis", "Conversion optimization report"],
                "learning_sequence": [
                    {"title": "Data Analysis", "skills": ["Data Analysis", "Python"], "project": "Analyze user behavior data", "objective": "Master data analysis"},
                    {"title": "Growth Fundamentals", "skills": ["Communication", "Problem Solving"], "project": "Design a growth experiment", "objective": "Learn growth methodologies"},
                    {"title": "Experimentation", "skills": ["A/B Testing", "SQL"], "project": "Run A/B tests and analyze results", "objective": "Master experimentation"},
                    {"title": "Digital Marketing", "skills": ["Digital Marketing"], "project": "Execute a multi-channel campaign", "objective": "Learn digital marketing"},
                ],
                "related_careers": ["Product Manager", "Data Analyst", "Marketing Manager"],
            },
            {
                "name": "Embedded Systems Engineer",
                "description": "Design and program embedded systems for IoT devices, automotive, and consumer electronics. Work at the intersection of hardware and software.",
                "category": "Hardware",
                "required_skills": ["C++", "Linux", "Networking"],
                "optional_skills": ["Python", "Rust", "Kubernetes"],
                "skill_importance": {"C++": 0.95, "Linux": 0.9, "Networking": 0.8},
                "recommended_projects": ["IoT sensor network", "Real-time data logger", "Home automation system"],
                "learning_sequence": [
                    {"title": "C++ & Low-Level Programming", "skills": ["C++"], "project": "Build embedded firmware", "objective": "Master C++ for embedded"},
                    {"title": "Linux for Embedded", "skills": ["Linux"], "project": "Set up embedded Linux system", "objective": "Learn embedded Linux"},
                    {"title": "Networking & IoT", "skills": ["Networking"], "project": "Build an IoT communication system", "objective": "Master IoT networking"},
                    {"title": "Advanced Embedded", "skills": ["Python", "Rust"], "project": "Build a complete IoT product", "objective": "Master advanced embedded"},
                ],
                "related_careers": ["IoT Developer", "Firmware Engineer", "Hardware Engineer"],
            },
            {
                "name": "Blockchain Developer",
                "description": "Build decentralized applications and smart contracts. Work on Web3, DeFi, and distributed ledger technologies.",
                "category": "Blockchain",
                "required_skills": ["Blockchain Development", "Solidity", "JavaScript", "Git"],
                "optional_skills": ["Python", "Cryptography", "Docker"],
                "skill_importance": {"Blockchain Development": 0.95, "Solidity": 0.9, "JavaScript": 0.8, "Git": 0.6},
                "recommended_projects": ["DeFi protocol", "NFT marketplace", "DAO governance system"],
                "learning_sequence": [
                    {"title": "Blockchain Basics", "skills": ["Blockchain Development", "JavaScript"], "project": "Build a simple blockchain", "objective": "Understand blockchain fundamentals"},
                    {"title": "Smart Contracts", "skills": ["Solidity"], "project": "Deploy smart contracts on testnet", "objective": "Master Solidity development"},
                    {"title": "DApp Development", "skills": ["JavaScript", "Git"], "project": "Build a decentralized application", "objective": "Learn full-stack DApp development"},
                    {"title": "Advanced Web3", "skills": ["Python", "Cryptography"], "project": "Build a DeFi protocol", "objective": "Master advanced blockchain"},
                ],
                "related_careers": ["Web3 Developer", "Smart Contract Auditor", "Crypto Engineer"],
            },
            {
                "name": "VR/AR Developer",
                "description": "Create immersive virtual and augmented reality experiences. Build applications for gaming, training, and visualization.",
                "category": "AR/VR",
                "required_skills": ["C++", "AR/VR Development", "Problem Solving"],
                "optional_skills": ["Python", "Unity", "3D Modeling"],
                "skill_importance": {"C++": 0.9, "AR/VR Development": 0.95, "Problem Solving": 0.8},
                "recommended_projects": ["VR training simulation", "AR product visualization", "Interactive 3D experience"],
                "learning_sequence": [
                    {"title": "3D Programming Fundamentals", "skills": ["C++"], "project": "Build 3D rendering basics", "objective": "Master 3D programming"},
                    {"title": "VR/AR Frameworks", "skills": ["AR/VR Development"], "project": "Build a VR experience", "objective": "Learn VR/AR development"},
                    {"title": "Advanced Immersive Tech", "skills": ["Python", "Unity"], "project": "Build an AR application", "objective": "Master advanced VR/AR"},
                    {"title": "Production VR/AR", "skills": ["3D Modeling"], "project": "Build a complete VR game", "objective": "Master production VR/AR"},
                ],
                "related_careers": ["Game Developer", "Unity Developer", "3D Artist"],
            },
            {
                "name": "Quality Assurance Engineer",
                "description": "Ensure software quality through testing strategies, automation, and process improvement. Prevent bugs before they reach production.",
                "category": "Quality",
                "required_skills": ["Software Testing", "Git", "Problem Solving"],
                "optional_skills": ["Automation Testing", "Python", "CI/CD"],
                "skill_importance": {"Software Testing": 0.95, "Git": 0.7, "Problem Solving": 0.85},
                "recommended_projects": ["Test automation framework", "Performance testing suite", "Quality metrics dashboard"],
                "learning_sequence": [
                    {"title": "Testing Fundamentals", "skills": ["Software Testing"], "project": "Create test plans for a web app", "objective": "Master testing basics"},
                    {"title": "Automation Testing", "skills": ["Automation Testing", "Git"], "project": "Build an automation test suite", "objective": "Learn test automation"},
                    {"title": "CI/CD Integration", "skills": ["CI/CD", "Python"], "project": "Integrate tests into CI/CD pipeline", "objective": "Master CI/CD testing"},
                    {"title": "Advanced Testing", "skills": ["Problem Solving"], "project": "Design a testing strategy for microservices", "objective": "Master advanced testing"},
                ],
                "related_careers": ["SDET", "Test Lead", "DevOps Engineer"],
            },
            {
                "name": "Technical Support Engineer",
                "description": "Provide expert technical support to customers. Troubleshoot complex issues and improve support processes.",
                "category": "Support",
                "required_skills": ["IT Support", "Linux", "Networking", "Communication"],
                "optional_skills": ["Python", "SQL", "AWS"],
                "skill_importance": {"IT Support": 0.9, "Linux": 0.8, "Networking": 0.85, "Communication": 0.9},
                "recommended_projects": ["Knowledge base creation", "Support automation tool", "Customer satisfaction analysis"],
                "learning_sequence": [
                    {"title": "Support Fundamentals", "skills": ["IT Support", "Communication"], "project": "Document common support issues", "objective": "Master support basics"},
                    {"title": "System Troubleshooting", "skills": ["Linux", "Networking"], "project": "Build a troubleshooting guide", "objective": "Master system troubleshooting"},
                    {"title": "Scripting for Support", "skills": ["Python"], "project": "Automate common support tasks", "objective": "Learn support automation"},
                    {"title": "Advanced Support", "skills": ["SQL", "AWS"], "project": "Build a support analytics dashboard", "objective": "Master advanced support"},
                ],
                "related_careers": ["System Administrator", "Cloud Support", "DevOps Engineer"],
            },
        ]
        added = 0
        for data in new_careers:
            if data["name"] not in existing:
                db.add(Career(**data))
                added += 1
        db.commit()
        print(f"Added {added} new careers ({len(existing)} existed)")
    finally:
        db.close()


def add_new_projects():
    db = SessionLocal()
    try:
        existing = {p.title for p in db.query(Project.title).all()}
        new_projects = [
            {"title": "Social Media Dashboard", "description": "Build a dashboard that aggregates and visualizes social media metrics across multiple platforms with real-time updates.", "difficulty": "intermediate", "skills_developed": ["React", "Node.js", "Data Analysis", "SQL"], "expected_outcome": "A real-time social media analytics dashboard", "estimated_duration_weeks": 5, "portfolio_value": "High - demonstrates full-stack data visualization"},
            {"title": "AI-Powered Content Generator", "description": "Create an AI-powered tool that generates blog posts, social media content, or product descriptions using LLM APIs.", "difficulty": "advanced", "skills_developed": ["Python", "Generative AI", "React", "API Design"], "expected_outcome": "A working AI content generation tool", "estimated_duration_weeks": 6, "portfolio_value": "Very High - showcases AI integration skills"},
            {"title": "Real-time Collaboration Tool", "description": "Build a Google Docs-like collaboration tool with real-time editing, presence indicators, and version history.", "difficulty": "advanced", "skills_developed": ["React", "Node.js", "WebSocket", "SQL", "Redis"], "expected_outcome": "A functional real-time collaboration platform", "estimated_duration_weeks": 8, "portfolio_value": "Very High - demonstrates complex real-time systems"},
            {"title": "Personal Finance Tracker", "description": "Create a personal finance app with expense tracking, budgeting, investment portfolio tracking, and financial insights.", "difficulty": "intermediate", "skills_developed": ["React", "Node.js", "SQL", "Data Analysis"], "expected_outcome": "A comprehensive personal finance application", "estimated_duration_weeks": 5, "portfolio_value": "High - demonstrates practical full-stack development"},
            {"title": "DevOps Monitoring Dashboard", "description": "Build a monitoring dashboard that aggregates metrics from multiple services, alerts on anomalies, and shows system health.", "difficulty": "intermediate", "skills_developed": ["React", "Python", "Docker", "Prometheus", "Grafana"], "expected_outcome": "A real-time monitoring and alerting system", "estimated_duration_weeks": 4, "portfolio_value": "High - demonstrates DevOps and monitoring skills"},
            {"title": "ML Model Deployment Pipeline", "description": "Build an end-to-end ML pipeline that trains, evaluates, and deploys models with monitoring and automatic retraining.", "difficulty": "advanced", "skills_developed": ["Python", "Machine Learning", "Docker", "AWS", "CI/CD"], "expected_outcome": "A production-ready ML deployment system", "estimated_duration_weeks": 8, "portfolio_value": "Very High - demonstrates MLOps expertise"},
            {"title": "GraphQL API Gateway", "description": "Build a GraphQL API gateway that aggregates multiple REST APIs, handles authentication, and provides a unified interface.", "difficulty": "intermediate", "skills_developed": ["GraphQL", "Node.js", "Docker", "Redis"], "expected_outcome": "A working GraphQL gateway with documentation", "estimated_duration_weeks": 4, "portfolio_value": "High - demonstrates API architecture skills"},
            {"title": "Password Manager", "description": "Build a secure password manager with end-to-end encryption, browser extension, and cross-device sync.", "difficulty": "advanced", "skills_developed": ["JavaScript", "Python", "Cryptography", "Docker"], "expected_outcome": "A secure password management system", "estimated_duration_weeks": 6, "portfolio_value": "Very High - demonstrates security expertise"},
            {"title": "Kubernetes Cluster Manager", "description": "Build a web-based tool to manage Kubernetes clusters, deploy applications, and monitor resource usage.", "difficulty": "advanced", "skills_developed": ["Kubernetes", "React", "Python", "Docker"], "expected_outcome": "A Kubernetes management dashboard", "estimated_duration_weeks": 7, "portfolio_value": "Very High - demonstrates container orchestration skills"},
            {"title": "E-learning Platform", "description": "Create an e-learning platform with course management, progress tracking, quizzes, and video streaming.", "difficulty": "advanced", "skills_developed": ["React", "Node.js", "SQL", "Video Streaming", "AWS"], "expected_outcome": "A complete e-learning platform", "estimated_duration_weeks": 10, "portfolio_value": "Very High - demonstrates complex platform development"},
            {"title": "Inventory Management System", "description": "Build an inventory management system with barcode scanning, stock alerts, supplier management, and reporting.", "difficulty": "intermediate", "skills_developed": ["React", "Node.js", "SQL", "Data Analysis"], "expected_outcome": "A complete inventory management solution", "estimated_duration_weeks": 5, "portfolio_value": "High - demonstrates business application development"},
            {"title": "Code Review Tool", "description": "Create a code review tool with inline comments, approval workflows, and integration with Git repositories.", "difficulty": "intermediate", "skills_developed": ["React", "Python", "Git", "Docker"], "expected_outcome": "A working code review platform", "estimated_duration_weeks": 5, "portfolio_value": "High - demonstrates developer tool development"},
            {"title": "Weather Forecast App", "description": "Build a weather app with location-based forecasts, severe weather alerts, and historical weather data visualization.", "difficulty": "beginner", "skills_developed": ["JavaScript", "HTML/CSS", "React", "API Integration"], "expected_outcome": "A polished weather application", "estimated_duration_weeks": 2, "portfolio_value": "Medium - demonstrates API integration skills"},
            {"title": "URL Shortener with Analytics", "description": "Build a URL shortener service with click tracking, geographic analytics, and real-time dashboards.", "difficulty": "intermediate", "skills_developed": ["Node.js", "React", "Redis", "SQL", "Docker"], "expected_outcome": "A URL shortening service with analytics", "estimated_duration_weeks": 3, "portfolio_value": "High - demonstrates scalable backend development"},
            {"title": "Smart Home Dashboard", "description": "Create a smart home dashboard that controls IoT devices, automates routines, and displays sensor data.", "difficulty": "intermediate", "skills_developed": ["React", "Node.js", "MQTT", "Python", "Docker"], "expected_outcome": "A functional smart home control center", "estimated_duration_weeks": 6, "portfolio_value": "High - demonstrates IoT integration skills"},
            {"title": "Resume Builder", "description": "Build a resume builder with templates, PDF export, ATS optimization tips, and job matching.", "difficulty": "beginner", "skills_developed": ["React", "JavaScript", "HTML/CSS"], "expected_outcome": "A resume building application", "estimated_duration_weeks": 3, "portfolio_value": "Medium - demonstrates UI/UX skills"},
            {"title": "Collaborative Whiteboard", "description": "Build a collaborative whiteboard with drawing tools, sticky notes, real-time sync, and export capabilities.", "difficulty": "advanced", "skills_developed": ["React", "Node.js", "WebSocket", "Canvas API", "Redis"], "expected_outcome": "A real-time collaborative whiteboard", "estimated_duration_weeks": 7, "portfolio_value": "Very High - demonstrates complex real-time collaboration"},
            {"title": "API Rate Limiter", "description": "Build a distributed API rate limiter with multiple algorithms, Redis backend, and monitoring dashboard.", "difficulty": "intermediate", "skills_developed": ["Python", "Redis", "Docker", "Monitoring"], "expected_outcome": "A production-ready rate limiting service", "estimated_duration_weeks": 3, "portfolio_value": "High - demonstrates infrastructure component development"},
            {"title": "Job Board Platform", "description": "Create a job board with company profiles, job listings, application tracking, and matching algorithms.", "difficulty": "advanced", "skills_developed": ["React", "Node.js", "SQL", "Python", "Data Analysis"], "expected_outcome": "A complete job board platform", "estimated_duration_weeks": 8, "portfolio_value": "Very High - demonstrates platform development"},
        ]
        added = 0
        for data in new_projects:
            if data["title"] not in existing:
                db.add(Project(**data))
                added += 1
        db.commit()
        print(f"Added {added} new projects ({len(existing)} existed)")
    finally:
        db.close()


if __name__ == "__main__":
    add_new_skills()
    add_new_interests()
    add_new_careers()
    add_new_projects()
    print("Done! All new data added without affecting existing data.")
