"""Toy corpus of programming-topic documents with labeled queries."""

DOCUMENTS = {
    "doc_python_basics": (
        "Python is a high-level interpreted programming language. "
        "It uses indentation to define code blocks rather than braces. "
        "Variables are dynamically typed so no explicit declaration is needed. "
        "Python supports procedural, object-oriented, and functional paradigms. "
        "The standard library ships batteries-included for most common tasks."
    ),
    "doc_python_classes": (
        "Python classes are defined with the class keyword. "
        "The __init__ method initializes new instances and receives self as first argument. "
        "Instance methods all take self as their first parameter. "
        "Inheritance is declared by listing base classes in parentheses after the class name. "
        "Python supports multiple inheritance and method resolution order via C3 linearisation."
    ),
    "doc_js_functions": (
        "JavaScript functions are first-class objects that can be assigned to variables. "
        "They can be declared with the function keyword or written as arrow functions. "
        "Functions can be passed as arguments to other functions. "
        "Closures allow inner functions to capture variables from their enclosing scope. "
        "Immediately invoked function expressions run as soon as they are defined."
    ),
    "doc_js_async": (
        "JavaScript async functions implicitly return a Promise. "
        "The await keyword pauses execution inside an async function until a Promise resolves. "
        "Error handling uses try/catch blocks around awaited expressions. "
        "Async/await is syntactic sugar built on top of Promise chains. "
        "The event loop processes asynchronous callbacks after synchronous code completes."
    ),
    "doc_sql_queries": (
        "SQL SELECT statements retrieve rows from one or more tables. "
        "WHERE clauses filter rows based on boolean conditions. "
        "JOIN operations combine rows from multiple tables on a matching column. "
        "GROUP BY aggregates rows that share the same value in a column. "
        "ORDER BY sorts the result set by one or more columns ascending or descending."
    ),
    "doc_sql_indexing": (
        "Database indexes speed up data retrieval at the cost of extra storage. "
        "A B-tree index stores keys in sorted order enabling binary search. "
        "Covering indexes include all columns referenced by a query to avoid table lookups. "
        "Index scans outperform full table scans for highly selective predicates. "
        "Over-indexing degrades write performance because every insert updates all indexes."
    ),
    "doc_git_basics": (
        "Git is a distributed version control system where every clone is a full repository. "
        "Commits record immutable snapshots of the entire working tree. "
        "The staging area accumulates changes before they are recorded in a commit. "
        "Git stores history as a directed acyclic graph of commit objects. "
        "Each commit is identified by a SHA-1 hash of its contents and metadata."
    ),
    "doc_git_branching": (
        "Git branches are lightweight pointers that move forward with each new commit. "
        "Creating a branch copies only a 40-byte reference not the file contents. "
        "Merging integrates the history of one branch into another. "
        "Rebasing replays commits onto a different base to produce a linear history. "
        "Feature branches keep work-in-progress isolated from the main line."
    ),
    "doc_docker_containers": (
        "Docker containers package an application together with all its runtime dependencies. "
        "A Dockerfile lists the steps used to build an image layer by layer. "
        "Containers share the host operating system kernel unlike full virtual machines. "
        "Images are stored as read-only layers that are shared across containers. "
        "The docker run command creates and starts a container from an image."
    ),
    "doc_docker_networking": (
        "Docker networks let containers communicate with each other. "
        "The bridge network is the default mode for containers on a single host. "
        "Containers on the same user-defined network can resolve each other by name. "
        "Host mode networking removes the network namespace isolation entirely. "
        "Port mapping with -p exposes container ports on the host machine."
    ),
    "doc_rest_api": (
        "REST APIs model resources as URLs and use HTTP methods to act on them. "
        "Responses are typically formatted as JSON or XML. "
        "Stateless design means every request carries all the information the server needs. "
        "REST is an architectural style not a formal protocol or standard. "
        "Hypermedia links in responses can guide clients to related resources."
    ),
    "doc_http_methods": (
        "HTTP GET retrieves a resource and must not have side effects. "
        "POST submits data to create a new resource or trigger a server-side action. "
        "PUT replaces an existing resource with the supplied representation. "
        "PATCH applies a partial update to an existing resource. "
        "DELETE removes the specified resource from the server."
    ),
    "doc_json_format": (
        "JSON is a lightweight text format for exchanging structured data. "
        "It supports strings, numbers, booleans, null, arrays, and nested objects. "
        "Object keys must be quoted strings unlike JavaScript object literals. "
        "JSON is language-independent and has parsers in virtually every language. "
        "Python's json module converts between JSON strings and native dicts and lists."
    ),
    "doc_csv_parsing": (
        "CSV files store tabular data as rows of comma-separated values. "
        "The first row conventionally contains column header names. "
        "Fields containing commas or newlines are wrapped in double quotes. "
        "Python's built-in csv module handles quoting and escape sequences correctly. "
        "Pandas read_csv offers convenient options for large-scale data analysis."
    ),
    "doc_regex": (
        "Regular expressions describe text patterns using a compact notation. "
        "Python's re module provides compile, match, search, findall, and sub. "
        "Metacharacters such as dot, star, plus, and question-mark have special meaning. "
        "Character classes enclosed in square brackets match any listed character. "
        "Anchors like caret and dollar match positions rather than characters."
    ),
    "doc_unit_testing": (
        "Unit tests verify that individual functions or classes behave correctly in isolation. "
        "Python's unittest module provides TestCase as a base class for test suites. "
        "Assertions such as assertEqual and assertRaises check expected versus actual outcomes. "
        "setUp and tearDown methods run before and after every test method. "
        "Mocking replaces real dependencies with controllable test doubles."
    ),
    "doc_cicd": (
        "CI/CD automates the build, test, and deployment lifecycle on every code change. "
        "A pipeline defines ordered stages that run when commits are pushed. "
        "Continuous integration merges branches frequently and runs the full test suite. "
        "Continuous delivery automatically promotes passing builds to a staging environment. "
        "GitHub Actions defines pipelines as YAML workflow files stored in the repository."
    ),
    "doc_db_normalization": (
        "Database normalization organises tables to minimise redundancy and anomalies. "
        "First normal form requires that every column holds atomic indivisible values. "
        "Second normal form removes partial dependencies on a composite primary key. "
        "Third normal form eliminates transitive dependencies between non-key columns. "
        "Higher normal forms improve consistency but often require additional joins at query time."
    ),
    "doc_ml_basics": (
        "Machine learning algorithms discover patterns in data without explicit programming. "
        "Supervised learning trains on labelled examples of input-output pairs. "
        "Features are the measurable properties used as model inputs. "
        "A loss function quantifies the gap between predictions and ground truth labels. "
        "Gradient descent iteratively adjusts weights to minimise the loss function."
    ),
    "doc_neural_networks": (
        "Neural networks arrange artificial neurons into layers that transform inputs. "
        "Activation functions introduce non-linearity enabling complex pattern learning. "
        "Backpropagation computes gradients of the loss with respect to each weight. "
        "Deep networks stack many hidden layers to learn hierarchical representations. "
        "Dropout randomly zeroes neuron outputs during training to reduce overfitting."
    ),
}

QUERIES = [
    {
        "id": "q1",
        "text": "How do Python classes and inheritance work?",
        "relevant": ["doc_python_classes"],
    },
    {
        "id": "q2",
        "text": "What is async await and Promises in JavaScript?",
        "relevant": ["doc_js_async"],
    },
    {
        "id": "q3",
        "text": "How do SQL joins and GROUP BY aggregate rows?",
        "relevant": ["doc_sql_queries"],
    },
    {
        "id": "q4",
        "text": "How to create branches and rebase commits in Git?",
        "relevant": ["doc_git_branching"],
    },
    {
        "id": "q5",
        "text": "How to expose Docker container ports to the host machine?",
        "relevant": ["doc_docker_networking"],
    },
    {
        "id": "q6",
        "text": "What HTTP methods does a REST API use?",
        "relevant": ["doc_rest_api", "doc_http_methods"],
    },
    {
        "id": "q7",
        "text": "How to write unit tests with assertions and mocking?",
        "relevant": ["doc_unit_testing"],
    },
    {
        "id": "q8",
        "text": "What is gradient descent and loss functions in machine learning?",
        "relevant": ["doc_ml_basics"],
    },
    {
        "id": "q9",
        "text": "How does CI/CD pipeline automation work with GitHub Actions?",
        "relevant": ["doc_cicd"],
    },
    {
        "id": "q10",
        "text": "How to parse JSON format in Python?",
        "relevant": ["doc_json_format"],
    },
]
