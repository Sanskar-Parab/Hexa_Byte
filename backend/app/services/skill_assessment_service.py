import json
import logging
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models.skill import Skill, UserSkill
from app.models.skill_assessment import SkillAssessmentSession
from app.services.evidence_service import create_assessment_evidence
from app.ai.groq_client import groq_client, SkillAssessmentQuestion

logger = logging.getLogger(__name__)

DIFFICULTY_WEIGHTS = {
    "beginner": 0.20,
    "intermediate": 0.30,
    "advanced": 0.30,
    "practical": 0.20,
}

PROFICIENCY_THRESHOLDS = [
    (20, 1, "Beginner"),
    (40, 2, "Basic"),
    (60, 3, "Intermediate"),
    (80, 4, "Advanced"),
    (100, 5, "Expert"),
]

FALLBACK_QUESTIONS = {
    "JavaScript": [
        {"id": 1, "difficulty": "beginner", "type": "mcq", "question": "What is the output of typeof null in JavaScript?", "options": ["null", "undefined", "object", "boolean"], "correct_answer": "C", "explanation": "typeof null returns 'object' - this is a well-known JavaScript quirk."},
        {"id": 2, "difficulty": "beginner", "type": "mcq", "question": "Which keyword declares a block-scoped variable?", "options": ["var", "let", "function", "class"], "correct_answer": "B", "explanation": "let and const are block-scoped, while var is function-scoped."},
        {"id": 3, "difficulty": "beginner", "type": "mcq", "question": "How do you write a single-line comment in JavaScript?", "options": ["<!-- -->", "//", "#", "/* */"], "correct_answer": "B", "explanation": "// is the single-line comment syntax in JavaScript."},
        {"id": 4, "difficulty": "intermediate", "type": "mcq", "question": "What does the following code output?\nconst arr = [1, 2, 3]; arr.push([4, 5]); console.log(arr.length);", "options": ["3", "4", "5", "6"], "correct_answer": "C", "explanation": "push adds [4,5] as a single element, making the array length 5."},
        {"id": 5, "difficulty": "intermediate", "type": "mcq", "question": "What is a closure in JavaScript?", "options": ["A way to close browser windows", "A function that retains access to its lexical scope", "A method to end a loop", "A type of error handling"], "correct_answer": "B", "explanation": "A closure is a function that remembers the variables from its outer scope even after the outer function has returned."},
        {"id": 6, "difficulty": "intermediate", "type": "mcq", "question": "What is the result of: 0.1 + 0.2 === 0.3?", "options": ["true", "false", "undefined", "TypeError"], "correct_answer": "B", "explanation": "Due to floating-point precision, 0.1 + 0.2 equals 0.30000000000000004, not 0.3."},
        {"id": 7, "difficulty": "advanced", "type": "mcq", "question": "How would you prevent unnecessary memory retention in a long-running JavaScript application?", "options": ["Use global variables", "Nullify references to unused objects", "Always use var", "Avoid using closures"], "correct_answer": "B", "explanation": "Setting references to null allows garbage collection to free memory."},
        {"id": 8, "difficulty": "advanced", "type": "mcq", "question": "What is the event loop's role in JavaScript?", "options": ["It handles DOM events only", "It manages the call stack and callback queue for async operations", "It compiles JavaScript to machine code", "It manages memory allocation"], "correct_answer": "B", "explanation": "The event loop coordinates the call stack, task queue, and microtask queue for asynchronous execution."},
        {"id": 9, "difficulty": "practical", "type": "mcq", "question": "You are debugging an async function that sometimes returns undefined. What would you inspect first?", "options": ["The function's return statement", "The promise chain and await statements", "The variable declarations", "The function parameters"], "correct_answer": "B", "explanation": "Async issues usually stem from unhandled promises or incorrect await usage."},
        {"id": 10, "difficulty": "practical", "type": "mcq", "question": "A fetch() call works in browser but fails with CORS error. What is the most likely cause?", "options": ["JavaScript is disabled", "The API server lacks CORS headers", "The network is disconnected", "The browser is outdated"], "correct_answer": "B", "explanation": "CORS errors occur when the server doesn't include the appropriate Access-Control-Allow-Origin headers."},
    ],
    "Python": [
        {"id": 1, "difficulty": "beginner", "type": "mcq", "question": "What is the output of print(type([]))?", "options": ["<class 'array'>", "<class 'list'>", "<class 'tuple'>", "<class 'dict'>"], "correct_answer": "B", "explanation": "[] creates a list object in Python."},
        {"id": 2, "difficulty": "beginner", "type": "mcq", "question": "Which keyword is used to define a function in Python?", "options": ["function", "func", "def", "define"], "correct_answer": "C", "explanation": "Python uses 'def' to define functions."},
        {"id": 3, "difficulty": "beginner", "type": "mcq", "question": "What does 'pip' stand for?", "options": ["Python Installation Program", "Pip Installs Packages", "Python Interface Protocol", "Package Integration Process"], "correct_answer": "B", "explanation": "pip is Python's package installer."},
        {"id": 4, "difficulty": "intermediate", "type": "mcq", "question": "What is a decorator in Python?", "options": ["A comment style", "A function that modifies another function's behavior", "A type of loop", "A variable naming convention"], "correct_answer": "B", "explanation": "Decorators are higher-order functions that wrap other functions to extend their behavior."},
        {"id": 5, "difficulty": "intermediate", "type": "mcq", "question": "What is the difference between 'is' and '==' in Python?", "options": ["No difference", "'is' checks identity, '==' checks equality", "'is' checks value, '==' checks type", "'is' is faster than '=='"], "correct_answer": "B", "explanation": "'is' checks if two references point to the same object, while '==' checks if values are equal."},
        {"id": 6, "difficulty": "intermediate", "type": "mcq", "question": "What is a generator in Python?", "options": ["A type of variable", "A function that yields values lazily", "A class constructor", "A module importer"], "correct_answer": "B", "explanation": "Generators use yield to produce values one at a time, saving memory."},
        {"id": 7, "difficulty": "advanced", "type": "mcq", "question": "What is the Global Interpreter Lock (GIL)?", "options": ["A security feature", "A mutex that allows only one thread to execute Python bytecode", "A memory management tool", "A file locking mechanism"], "correct_answer": "B", "explanation": "The GIL prevents multiple threads from executing Python bytecode simultaneously."},
        {"id": 8, "difficulty": "advanced", "type": "mcq", "question": "What does __slots__ do in a Python class?", "options": ["Creates private variables", "Restricts instance attributes to reduce memory", "Defines class constants", "Enables multiple inheritance"], "correct_answer": "B", "explanation": "__slots__ restricts attributes to a fixed set, reducing per-instance memory overhead."},
        {"id": 9, "difficulty": "practical", "type": "mcq", "question": "You have a large CSV file that doesn't fit in memory. What's the best approach?", "options": ["Read the entire file at once", "Use chunked reading with pandas", "Compress the file first", "Split the file manually"], "correct_answer": "B", "explanation": "Pandas chunked reading processes the file in manageable pieces."},
        {"id": 10, "difficulty": "practical", "type": "mcq", "question": "A Python script runs slowly. Which tool should you use first to identify bottlenecks?", "options": ["print statements", "cProfile", "random testing", "rewriting in C"], "correct_answer": "B", "explanation": "cProfile is Python's built-in profiling tool for identifying performance bottlenecks."},
    ],
    "HTML/CSS": [
        {"id": 1, "difficulty": "beginner", "type": "mcq", "question": "Which HTML element is used to specify a header for a document or section?", "options": ["<head>", "<header>", "<top>", "<section>"], "correct_answer": "B", "explanation": "The <header> tag represents introductory content or navigational links for a page or section."},
        {"id": 2, "difficulty": "beginner", "type": "mcq", "question": "In CSS, which property is used to change the text color of an element?", "options": ["text-color", "fg-color", "color", "font-color"], "correct_answer": "C", "explanation": "The 'color' property specifies text color in CSS."},
        {"id": 3, "difficulty": "beginner", "type": "mcq", "question": "What is the correct HTML element for inserting a line break?", "options": ["<break>", "<lb>", "<br>", "<newline>"], "correct_answer": "C", "explanation": "The <br> tag inserts a single line break in HTML."},
        {"id": 4, "difficulty": "intermediate", "type": "mcq", "question": "Which CSS box model property adds space inside an element's border?", "options": ["margin", "padding", "border-spacing", "outline"], "correct_answer": "B", "explanation": "Padding is the space between an element's content and its border."},
        {"id": 5, "difficulty": "intermediate", "type": "mcq", "question": "In CSS Flexbox, which property controls alignment along the main axis?", "options": ["align-items", "justify-content", "align-content", "flex-direction"], "correct_answer": "B", "explanation": "justify-content aligns items along the flex container's main axis."},
        {"id": 6, "difficulty": "intermediate", "type": "mcq", "question": "Which CSS selector specificity ranking is correct from highest to lowest?", "options": ["Inline style > ID > Class > Element", "ID > Inline style > Class > Element", "Class > ID > Inline style > Element", "Element > Class > ID > Inline style"], "correct_answer": "A", "explanation": "Inline styles have weight (1,0,0,0), IDs (0,1,0,0), Classes (0,0,1,0), Elements (0,0,0,1)."},
        {"id": 7, "difficulty": "advanced", "type": "mcq", "question": "What does 'grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));' achieve in CSS Grid?", "options": ["Creates exactly 200 grid columns", "Creates a responsive grid layout that automatically adjusts column count based on available space", "Fixed-width layout", "Centers a single element in a grid"], "correct_answer": "B", "explanation": "auto-fit with minmax creates flexible auto-wrapping grid columns based on container width."},
        {"id": 8, "difficulty": "advanced", "type": "mcq", "question": "Which CSS property disables pointer events like clicks and hovers on an element?", "options": ["user-select: none", "pointer-events: none", "touch-action: none", "cursor: default"], "correct_answer": "B", "explanation": "pointer-events: none prevents an element from reacting to mouse or touch events."},
        {"id": 9, "difficulty": "practical", "type": "mcq", "question": "An image element on a mobile layout overflows its parent container width. What is the standard responsive CSS solution?", "options": ["width: 100vw", "max-width: 100%; height: auto;", "overflow: hidden on image", "min-width: 100%"], "correct_answer": "B", "explanation": "max-width: 100% with height: auto ensures images scale down proportionally inside their parent."},
        {"id": 10, "difficulty": "practical", "type": "mcq", "question": "You need to center a modal box horizontally and vertically on screen regardless of scroll position. Which CSS declaration is most suitable?", "options": ["position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);", "float: center", "display: inline-block; text-align: center;", "margin-top: 50%"], "correct_answer": "A", "explanation": "position: fixed with 50% offset and translate(-50%, -50%) centers an element relative to the viewport."},
    ],
    "React": [
        {"id": 1, "difficulty": "beginner", "type": "mcq", "question": "What is the primary mechanism to pass data down to child components in React?", "options": ["State", "Props", "Context", "Redux"], "correct_answer": "B", "explanation": "Props are passed from parent to child components."},
        {"id": 2, "difficulty": "beginner", "type": "mcq", "question": "Which React hook is used to handle side effects in functional components?", "options": ["useState", "useContext", "useEffect", "useReducer"], "correct_answer": "C", "explanation": "useEffect is used for side effects like data fetching, subscriptions, or DOM updates."},
        {"id": 3, "difficulty": "beginner", "type": "mcq", "question": "What syntax extension allows writing HTML-like markup inside JavaScript files in React?", "options": ["JSX", "TSX", "JSON", "XMLJS"], "correct_answer": "A", "explanation": "JSX is a syntax extension for JavaScript that looks like HTML."},
        {"id": 4, "difficulty": "intermediate", "type": "mcq", "question": "When does the cleanup function returned by useEffect execute?", "options": ["Before every render only", "On component unmount and before re-running the effect if dependencies change", "Only when an error occurs", "Never"], "correct_answer": "B", "explanation": "Effect cleanup runs on unmount and before re-running the effect on dependency change."},
        {"id": 5, "difficulty": "intermediate", "type": "mcq", "question": "Why should keys be provided for elements rendered in a list in React?", "options": ["Keys make elements look pretty", "Keys help React identify which items have changed, been added, or removed", "Keys are required for CSS styling", "Keys automatically sort the array"], "correct_answer": "B", "explanation": "Keys give elements a stable identity for efficient DOM diffing and reconciliation."},
        {"id": 6, "difficulty": "intermediate", "type": "mcq", "question": "What does useMemo return?", "options": ["A state setter function", "The memoized result of a calculation function", "A DOM ref", "A context object"], "correct_answer": "B", "explanation": "useMemo caches the result of a calculation between re-renders."},
        {"id": 7, "difficulty": "advanced", "type": "mcq", "question": "What causes an infinite loop in a component using useEffect?", "options": ["Passing an empty dependency array []", "Updating a state variable inside useEffect that is listed in its own dependency array", "Using React.memo on the component", "Using custom hooks"], "correct_answer": "B", "explanation": "Updating state inside useEffect triggers a re-render, which re-runs the effect if state is in dependencies."},
        {"id": 8, "difficulty": "advanced", "type": "mcq", "question": "How does React Fiber improve performance compared to the legacy stack reconciler?", "options": ["It converts JavaScript directly into C++ code", "It introduces incremental rendering, allowing work to be split into chunks and paused", "It bypasses the virtual DOM completely", "It replaces hooks with global state"], "correct_answer": "B", "explanation": "Fiber allows React to break rendering work into units and prioritize user interactions."},
        {"id": 9, "difficulty": "practical", "type": "mcq", "question": "A form component re-renders on every keystroke, causing lagging performance in child inputs. What hook helps optimize child callback references?", "options": ["useCallback", "useState", "useId", "useLayoutEffect"], "correct_answer": "A", "explanation": "useCallback caches function definitions between re-renders to prevent unnecessary child re-renders."},
        {"id": 10, "difficulty": "practical", "type": "mcq", "question": "You need to access an imperative DOM method (like focus() or scrollIntoView()) in a component. What hook should you use?", "options": ["useRef", "useMemo", "useState", "useTransition"], "correct_answer": "A", "explanation": "useRef provides a mutable ref object holding a direct reference to a DOM node."},
    ],
    "SQL": [
        {"id": 1, "difficulty": "beginner", "type": "mcq", "question": "Which SQL statement is used to fetch data from a database table?", "options": ["GET", "FETCH", "SELECT", "OPEN"], "correct_answer": "C", "explanation": "SELECT is used to query and extract data from database tables."},
        {"id": 2, "difficulty": "beginner", "type": "mcq", "question": "Which SQL clause is used to filter records?", "options": ["GROUP BY", "WHERE", "ORDER BY", "HAVING"], "correct_answer": "B", "explanation": "WHERE filters records based on specified conditions."},
        {"id": 3, "difficulty": "beginner", "type": "mcq", "question": "What does the COUNT() function do in SQL?", "options": ["Sums column values", "Returns the number of rows matching criteria", "Calculates average", "Finds maximum value"], "correct_answer": "B", "explanation": "COUNT() returns the number of rows matching query criteria."},
        {"id": 4, "difficulty": "intermediate", "type": "mcq", "question": "What is the difference between INNER JOIN and LEFT JOIN?", "options": ["No difference", "INNER JOIN returns matching rows; LEFT JOIN returns all left table rows plus matching right table rows", "LEFT JOIN only works on primary keys", "INNER JOIN returns all right table rows"], "correct_answer": "B", "explanation": "LEFT JOIN keeps all rows from the left table regardless of right table matches."},
        {"id": 5, "difficulty": "intermediate", "type": "mcq", "question": "What is the purpose of the GROUP BY clause?", "options": ["Sorts rows in ascending order", "Groups rows with identical values into summary rows", "Filters aggregated results", "Creates index on columns"], "correct_answer": "B", "explanation": "GROUP BY aggregates rows that share common values into summary rows."},
        {"id": 6, "difficulty": "intermediate", "type": "mcq", "question": "How does HAVING differ from WHERE in SQL?", "options": ["HAVING filters before grouping; WHERE filters after grouping", "HAVING filters aggregated groups; WHERE filters individual rows before grouping", "HAVING is faster than WHERE", "HAVING is only for text strings"], "correct_answer": "B", "explanation": "WHERE filters rows before aggregation; HAVING filters groups created by GROUP BY."},
        {"id": 7, "difficulty": "advanced", "type": "mcq", "question": "What type of database index improves search query performance at the cost of slower write performance?", "options": ["B-Tree Index", "Foreign Key", "Unique Constraint", "Primary Key only"], "correct_answer": "A", "explanation": "Indexes speed up read queries but add overhead on INSERT, UPDATE, and DELETE operations."},
        {"id": 8, "difficulty": "advanced", "type": "mcq", "question": "What ACID property ensures that all operations in a database transaction complete successfully or none are applied?", "options": ["Atomicity", "Consistency", "Isolation", "Durability"], "correct_answer": "A", "explanation": "Atomicity ensures 'all-or-nothing' execution of database transactions."},
        {"id": 9, "difficulty": "practical", "type": "mcq", "question": "A query selecting from a 10-million-row table takes 15 seconds. What is the first optimization to inspect?", "options": ["Rewrite in Python", "Check execution plan (EXPLAIN) for missing indexes on WHERE/JOIN columns", "Add more RAM to server", "Drop table and recreate"], "correct_answer": "B", "explanation": "Using EXPLAIN shows whether full table scans are occurring due to missing indexes."},
        {"id": 10, "difficulty": "practical", "type": "mcq", "question": "You need to find duplicate email addresses in a 'users' table. Which query structure is correct?", "options": ["SELECT email FROM users WHERE email IS DUP", "SELECT email, COUNT(*) FROM users GROUP BY email HAVING COUNT(*) > 1", "SELECT DISTINCT email FROM users", "SELECT email FROM users ORDER BY email"], "correct_answer": "B", "explanation": "GROUP BY email with HAVING COUNT(*) > 1 identifies emails appearing more than once."},
    ],
    "Java": [
        {"id": 1, "difficulty": "beginner", "type": "mcq", "question": "Which of the following is the correct entry point signature for a standard Java program?", "options": ["public void main(String[] args)", "public static void main(String[] args)", "static void main(String args)", "public static int main(String[] args)"], "correct_answer": "B", "explanation": "public static void main(String[] args) is the standard main entry point in Java."},
        {"id": 2, "difficulty": "beginner", "type": "mcq", "question": "Which primitive data type in Java is used to store double-precision floating-point numbers?", "options": ["float", "double", "decimal", "real"], "correct_answer": "B", "explanation": "double is 64-bit IEEE 754 floating-point in Java."},
        {"id": 3, "difficulty": "beginner", "type": "mcq", "question": "What is the output of System.out.println(10 % 3) in Java?", "options": ["3", "1", "0", "3.33"], "correct_answer": "B", "explanation": "10 % 3 evaluates to 1, which is the integer remainder."},
        {"id": 4, "difficulty": "intermediate", "type": "mcq", "question": "Which keyword is used to inherit a parent class in Java?", "options": ["implements", "extends", "inherits", "using"], "correct_answer": "B", "explanation": "The extends keyword is used for class inheritance in Java."},
        {"id": 5, "difficulty": "intermediate", "type": "mcq", "question": "What is a primary distinction between ArrayList and LinkedList in Java?", "options": ["ArrayList is thread-safe; LinkedList is not", "ArrayList is backed by a dynamic array (O(1) random access); LinkedList is a doubly-linked list", "LinkedList does not allow duplicate elements", "ArrayList cannot hold object references"], "correct_answer": "B", "explanation": "ArrayList provides fast O(1) indexed access via array; LinkedList provides O(1) node insertion/deletion."},
        {"id": 6, "difficulty": "intermediate", "type": "mcq", "question": "Which statement accurately describes checked vs unchecked exceptions in Java?", "options": ["Checked exceptions inherit from RuntimeException", "Checked exceptions must be caught or declared in throws clause; unchecked inherit from RuntimeException", "Unchecked exceptions are checked at compile time", "Errors are checked exceptions"], "correct_answer": "B", "explanation": "Checked exceptions are checked at compile time; RuntimeException and Error subclasses are unchecked."},
        {"id": 7, "difficulty": "advanced", "type": "mcq", "question": "How does Java's Garbage Collector determine if an object is eligible for memory reclamation?", "options": ["When reference count reaches zero", "When the object is no longer reachable from any active GC Root", "When System.gc() is called", "When the object scope ends"], "correct_answer": "B", "explanation": "Java GC uses reachability analysis from GC roots (thread stacks, static fields, JNI references)."},
        {"id": 8, "difficulty": "advanced", "type": "mcq", "question": "Which package in Java provides atomic variables like AtomicInteger for lock-free thread safety?", "options": ["java.util.concurrent.locks", "java.util.concurrent.atomic", "java.lang.reflect", "java.io"], "correct_answer": "B", "explanation": "java.util.concurrent.atomic provides lock-free atomic primitive classes using CAS (Compare-And-Swap)."},
        {"id": 9, "difficulty": "practical", "type": "mcq", "question": "A Java application throws a NullPointerException at runtime. What modern Java feature helps handle optional values safely?", "options": ["java.util.Optional", "java.util.Vector", "java.lang.System", "java.util.Hashtable"], "correct_answer": "A", "explanation": "Optional<T> explicitly represents present or absent values without using naked nulls."},
        {"id": 10, "difficulty": "practical", "type": "mcq", "question": "You need to process a large List of objects in parallel using Java 8 Streams. Which method call initiates parallel stream processing?", "options": ["list.stream().parallel()", "list.parallelStream()", "Both A and B", "Neither A nor B"], "correct_answer": "C", "explanation": "Both list.parallelStream() and list.stream().parallel() return a parallel Stream in Java."},
    ],
}

DEFAULT_SKILL_FALLBACK = {
    "id": 0,
    "difficulty": "intermediate",
    "type": "mcq",
    "question": "This is a placeholder question. AI assessment is temporarily unavailable.",
    "options": ["A", "B", "C", "D"],
    "correct_answer": "A",
    "explanation": "Fallback question.",
}


def _generate_fallback_questions(skill_name: str) -> list[dict]:
    normalized = skill_name.strip()
    norm_lower = normalized.lower()

    alias_map = {
        "html/css": "HTML/CSS",
        "html & css": "HTML/CSS",
        "html": "HTML/CSS",
        "css": "HTML/CSS",
        "html5": "HTML/CSS",
        "css3": "HTML/CSS",
        "javascript": "JavaScript",
        "js": "JavaScript",
        "python": "Python",
        "python3": "Python",
        "react": "React",
        "reactjs": "React",
        "react.js": "React",
        "sql": "SQL",
        "postgres": "SQL",
        "postgresql": "SQL",
        "mysql": "SQL",
        "java": "Java",
        "java 8": "Java",
        "java 11": "Java",
        "java 17": "Java",
        "java 21": "Java",
    }

    target_key = alias_map.get(norm_lower, normalized)
    if target_key in FALLBACK_QUESTIONS:
        return FALLBACK_QUESTIONS[target_key]

    generic_templates = [
        ("beginner", f"What is a primary core objective or purpose of {skill_name} in modern software development?",
         [f"Providing structured functionality and solution patterns for {skill_name} projects", "Replacing all network protocols with physical hardware", "Managing operating system kernel threads directly", "Compiling text directly to raw analog signals"], "A", f"{skill_name} provides specialized functionality and structures for development."),
        ("beginner", f"Which fundamental concept is essential when working with {skill_name}?",
         [f"Understanding core syntax, conventions, and standard workflows of {skill_name}", "Memorizing hardware CPU instruction opcodes", "Using only single-line command scripts", "Bypassing version control entirely"], "A", f"Mastering basic syntax and standard workflows is essential for {skill_name}."),
        ("beginner", f"In a standard project environment, how is {skill_name} typically integrated?",
         [f"As a core dependency, framework, tool, or runtime component for {skill_name}", "By manually editing binary executable files with a hex editor", "By running code only on local hardware without software tools", "As a BIOS-level firmware patch"], "A", f"{skill_name} is integrated as a dependency, library, tool, or language runtime."),
        ("intermediate", f"Which best practice should be followed when structuring components in {skill_name}?",
         ["Enforcing modularity, readable organization, and clear separation of concerns", "Placing all application logic inside a single monolithic block", "Ignoring error handling and logging", "Hardcoding secret keys directly in public source code"], "A", f"Modularity and separation of concerns ensure maintainable {skill_name} code."),
        ("intermediate", f"How are runtime errors or unexpected conditions properly handled in {skill_name}?",
         ["Using structured error handling mechanisms (e.g. exceptions or result types)", "Terminating the host operating system immediately", "Ignoring error returns and continuing execution blindly", "Suppressing all logs and console output"], "A", "Structured error handling ensures software stability."),
        ("intermediate", f"When optimizing a system built with {skill_name}, what approach is recommended?",
         ["Identifying performance bottlenecks using profiling tools and optimizing algorithms", "Increasing loop counts to force higher CPU usage", "Removing all comments and variable names", "Executing all operations sequentially without caching"], "A", f"Profiling and algorithmic optimization improve execution performance in {skill_name}."),
        ("advanced", f"What architectural consideration is vital when applying {skill_name} in large scalable systems?",
         ["Ensuring scalability, thread safety/concurrency, and low coupling between modules", "Forcing all microservices to share a single unindexed database table", "Using synchronous blocking network calls for all I/O", "Disabling automated testing"], "A", "Decoupling and concurrency management enable high-scalability systems."),
        ("advanced", f"How does memory management or resource handling function in robust {skill_name} implementations?",
         ["Managing resource lifecycles carefully to prevent memory leaks and thread starvation", "Allocating infinite heap memory on startup", "Disabling garbage collection or manual deallocation entirely", "Storing all state in temporary environment variables"], "A", "Proper resource lifecycle management avoids memory leaks and degradation."),
        ("practical", f"A component using {skill_name} exhibits unexpected degradation under load. What is the recommended diagnostic step?",
         ["Inspect system telemetry, application logs, and resource utilization (CPU/Memory/IO)", "Reboot the production server continuously", "Delete user database indices", "Increase client timeout values to infinity"], "A", "Analyzing telemetry, logs, and resource metrics pinpoints the root cause."),
        ("practical", f"You are setting up CI/CD for a project built with {skill_name}. What step ensures software quality before deployment?",
         ["Executing automated unit, integration, and static analysis tests", "Deploying directly to production without testing", "Committing compiled binary artifacts directly to git main branch", "Manually inspecting code on production servers"], "A", "Automated testing pipelines validate correctness prior to production release."),
    ]

    questions = []
    for qid, (diff, q_text, opts, correct, expl) in enumerate(generic_templates, start=1):
        questions.append({
            "id": qid,
            "difficulty": diff,
            "type": "mcq",
            "question": q_text,
            "options": opts,
            "correct_answer": correct,
            "explanation": expl,
        })
    return questions


def calculate_score(questions: list[dict], answers: dict[int, str]) -> float:
    total_weight = 0.0
    earned_weight = 0.0

    for q in questions:
        qid = q["id"]
        difficulty = q["difficulty"]
        weight = DIFFICULTY_WEIGHTS.get(difficulty, 0.1)
        total_weight += weight

        if qid in answers and answers[qid] == q["correct_answer"]:
            earned_weight += weight

    if total_weight == 0:
        return 0.0

    return (earned_weight / total_weight) * 100


def determine_proficiency(score_percentage: float) -> tuple[int, str]:
    for threshold, level, name in PROFICIENCY_THRESHOLDS:
        if score_percentage <= threshold:
            return level, name
    return 5, "Expert"


def check_ai_availability() -> dict:
    """Check if AI service is available and return status."""
    return {
        "available": groq_client.is_available,
        "error": groq_client.error_message,
    }


def start_assessment(db: Session, user_id: UUID, skill_id: UUID) -> dict:
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise ValueError("Skill not found")

    existing = db.query(SkillAssessmentSession).filter(
        SkillAssessmentSession.user_id == user_id,
        SkillAssessmentSession.skill_id == skill_id,
        SkillAssessmentSession.status == "in_progress",
    ).first()
    if existing:
        db.delete(existing)
        db.commit()

    ai_questions = None
    ai_error = None

    if groq_client.is_available:
        ai_questions, ai_error = groq_client.generate_questions(skill.name)

    if ai_questions:
        questions = [q.model_dump() for q in ai_questions.questions]
    else:
        logger.warning(f"Using fallback questions for '{skill.name}'. AI note: {ai_error or 'AI service unavailable'}")
        questions = _generate_fallback_questions(skill.name)

    session = SkillAssessmentSession(
        id=uuid4(),
        user_id=user_id,
        skill_id=skill_id,
        status="in_progress",
    )
    session.set_questions(questions)
    db.add(session)
    db.commit()
    db.refresh(session)

    sanitized = [
        {k: v for k, v in q.items() if k != "correct_answer" and k != "explanation"}
        for q in questions
    ]

    return {
        "assessment_id": session.id,
        "skill": {"id": skill.id, "name": skill.name},
        "questions": sanitized,
    }


def submit_assessment(db: Session, user_id: UUID, assessment_id: UUID, answers: list[dict]) -> dict:
    session = db.query(SkillAssessmentSession).filter(
        SkillAssessmentSession.id == assessment_id,
    ).first()

    if not session:
        raise ValueError("Assessment session not found")

    if session.user_id != user_id:
        raise ValueError("Unauthorized access to assessment")

    if session.status == "completed":
        raise ValueError("Assessment already completed")

    questions = session.get_questions()
    answers_dict = {a["question_id"]: a["answer"] for a in answers}

    score_percentage = calculate_score(questions, answers_dict)
    proficiency, level_name = determine_proficiency(score_percentage)

    skill = db.query(Skill).filter(Skill.id == session.skill_id).first()
    skill_name = skill.name if skill else "Unknown"

    question_details = []
    for q in questions:
        qid = q["id"]
        user_answer = answers_dict.get(qid, "No answer")
        is_correct = user_answer == q["correct_answer"]
        question_details.append(
            f"Q{qid} [{q['difficulty']}]: {q['question']}\n"
            f"  User answer: {user_answer} | Correct: {q['correct_answer']} | {'✓' if is_correct else '✗'}"
        )

    ai_analysis, analysis_error = groq_client.analyze_results(
        skill_name=skill_name,
        score_percentage=score_percentage,
        proficiency=proficiency,
        level_name=level_name,
        question_details="\n".join(question_details),
    )

    if ai_analysis:
        strengths = ai_analysis.strengths
        weaknesses = ai_analysis.weaknesses
        recommended_topics = ai_analysis.recommended_topics
        summary = ai_analysis.summary
    else:
        strengths = ["Completed the assessment"]
        weaknesses = ["AI analysis unavailable"]
        recommended_topics = ["Review core concepts"]
        summary = f"Scored {round(score_percentage)}% on {skill_name} assessment."

    session.set_answers(answers_dict)
    session.score_percentage = round(score_percentage)
    session.proficiency = proficiency
    session.level_name = level_name
    session.status = "completed"
    session.completed_at = datetime.utcnow()
    db.commit()

    user_skill = db.query(UserSkill).filter(
        UserSkill.user_id == user_id,
        UserSkill.skill_id == session.skill_id,
    ).first()

    if user_skill:
        user_skill.proficiency = proficiency
        user_skill.level_name = level_name
    else:
        user_skill = UserSkill(
            user_id=user_id,
            skill_id=session.skill_id,
            proficiency=proficiency,
            level_name=level_name,
        )
        db.add(user_skill)

    db.flush()

    create_assessment_evidence(
        db=db,
        user_id=user_id,
        skill_id=session.skill_id,
        session_id=session.id,
        score_percentage=score_percentage,
        level_name=level_name,
        proficiency=proficiency,
    )

    db.commit()
    db.refresh(user_skill)

    # Trigger adaptive intelligence loop
    adaptive_updates = {}
    try:
        from app.services.adaptive_events import on_skill_assessment_completed
        adaptive_updates = on_skill_assessment_completed(
            db=db,
            user_id=user_id,
            skill_id=session.skill_id,
            proficiency=proficiency,
            score_percentage=score_percentage,
        )
        db.commit()
    except Exception as e:
        logger.warning(f"Adaptive event failed after skill assessment: {e}")
        db.rollback()

    return {
        "assessment_id": session.id,
        "skill": {"id": skill.id, "name": skill_name},
        "proficiency": proficiency,
        "level_name": level_name,
        "score_percentage": round(score_percentage),
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommended_topics": recommended_topics,
        "summary": summary,
        "confidence": user_skill.confidence or "LOW",
        "adaptive_updates": adaptive_updates,
    }
