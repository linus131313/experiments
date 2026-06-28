"""Toy knowledge base and query set for the memory backend comparison."""

CORPUS = {
    "python-gc": {
        "content": (
            "Python uses reference counting as its primary garbage collection mechanism,"
            " supplemented by a cyclic garbage collector to handle reference cycles."
        ),
        "tags": ["python", "garbage-collection", "memory-management", "reference-counting"],
    },
    "java-gc": {
        "content": (
            "Java's garbage collector is generational; the heap is split into young and old"
            " generations, and the JVM chooses from several GC algorithms such as G1 and ZGC."
        ),
        "tags": ["java", "garbage-collection", "memory-management", "jvm", "generational-gc"],
    },
    "rust-ownership": {
        "content": (
            "Rust enforces memory safety without a garbage collector through an ownership"
            " system with borrow checking at compile time."
        ),
        "tags": ["rust", "memory-management", "ownership", "borrow-checker", "compile-time"],
    },
    "python-gil": {
        "content": (
            "CPython's Global Interpreter Lock (GIL) prevents multiple threads from executing"
            " Python bytecodes simultaneously, limiting CPU-bound parallelism."
        ),
        "tags": ["python", "cpython", "gil", "threading", "concurrency"],
    },
    "java-threads": {
        "content": (
            "Java supports true native OS threads and the java.util.concurrent package provides"
            " high-level concurrency primitives like thread pools and locks."
        ),
        "tags": ["java", "threading", "concurrency", "jvm", "thread-pool"],
    },
    "rust-async": {
        "content": (
            "Rust's async/await syntax enables cooperative multitasking; futures are zero-cost"
            " abstractions that compile to efficient state machines."
        ),
        "tags": ["rust", "async", "concurrency", "futures", "zero-cost-abstraction"],
    },
    "python-typing": {
        "content": (
            "Python 3.5 introduced optional type hints via PEP 484; tools like mypy and pyright"
            " perform static type checking without affecting runtime behaviour."
        ),
        "tags": ["python", "type-hints", "static-analysis", "mypy", "pep484"],
    },
    "java-generics": {
        "content": (
            "Java generics use type erasure: generic type parameters are replaced by Object at"
            " runtime, which can cause unexpected behaviour with reflection."
        ),
        "tags": ["java", "generics", "type-system", "type-erasure", "reflection"],
    },
    "rust-traits": {
        "content": (
            "Rust traits define shared behaviour similar to interfaces; trait objects enable"
            " dynamic dispatch while generics enable static (monomorphised) dispatch."
        ),
        "tags": ["rust", "traits", "generics", "type-system", "dynamic-dispatch"],
    },
    "python-packages": {
        "content": (
            "Python packages are distributed via PyPI and installed with pip; virtual"
            " environments (venv, conda) isolate package dependencies per project."
        ),
        "tags": ["python", "packaging", "pypi", "pip", "virtual-environment"],
    },
    "java-maven": {
        "content": (
            "Maven and Gradle are the dominant Java build tools; they resolve transitive"
            " dependencies from Maven Central and support multi-module projects."
        ),
        "tags": ["java", "build-tool", "maven", "gradle", "dependency-management"],
    },
    "rust-cargo": {
        "content": (
            "Cargo is Rust's official package manager and build system; crates.io hosts the"
            " public registry and Cargo.toml declares dependencies with semantic versioning."
        ),
        "tags": ["rust", "packaging", "cargo", "crates-io", "semantic-versioning"],
    },
    "python-cpython": {
        "content": (
            "CPython is the reference implementation of Python written in C; alternative"
            " implementations include PyPy, Jython, and MicroPython."
        ),
        "tags": ["python", "cpython", "pypy", "implementation", "interpreter"],
    },
    "java-jvm": {
        "content": (
            "The Java Virtual Machine (JVM) compiles bytecode at runtime via JIT compilation,"
            " enabling platform independence and adaptive optimisation."
        ),
        "tags": ["java", "jvm", "jit", "bytecode", "platform-independence"],
    },
    "rust-compiler": {
        "content": (
            "The Rust compiler (rustc) performs extensive compile-time checks including"
            " lifetime analysis, preventing data races and null pointer dereferences before"
            " execution."
        ),
        "tags": ["rust", "compiler", "lifetime", "safety", "compile-time"],
    },
    "python-decorators": {
        "content": (
            "Python decorators are syntactic sugar for higher-order functions; @functools.wraps"
            " preserves the wrapped function's metadata for introspection."
        ),
        "tags": ["python", "decorators", "metaprogramming", "higher-order-functions"],
    },
    "java-annotations": {
        "content": (
            "Java annotations are metadata applied to code elements; frameworks like Spring and"
            " Hibernate use them for dependency injection and ORM mapping."
        ),
        "tags": ["java", "annotations", "metaprogramming", "spring", "hibernate"],
    },
    "rust-macros": {
        "content": (
            "Rust macros operate on the syntax tree at compile time; procedural macros allow"
            " arbitrary code generation from annotated Rust source."
        ),
        "tags": ["rust", "macros", "metaprogramming", "compile-time", "code-generation"],
    },
    "cross-memory": {
        "content": (
            "Memory management strategies differ across languages: Python uses reference"
            " counting plus a cyclic collector, Java uses a generational GC, and Rust enforces"
            " static ownership."
        ),
        "tags": [
            "python", "java", "rust", "memory-management", "garbage-collection", "ownership",
        ],
    },
    "cross-concurrency": {
        "content": (
            "Concurrency models vary: Python's GIL limits parallelism, Java uses OS threads"
            " with shared mutable state, and Rust's ownership rules prevent data races at"
            " compile time."
        ),
        "tags": [
            "python", "java", "rust", "concurrency", "threading", "data-race",
        ],
    },
}

QUERIES = [
    {
        "question": "How does Python manage memory and garbage collection?",
        "relevant": ["python-gc", "python-cpython", "cross-memory"],
    },
    {
        "question": "What are the concurrency limitations in CPython?",
        "relevant": ["python-gil", "cross-concurrency", "python-cpython"],
    },
    {
        "question": "How does Rust achieve memory safety without a garbage collector?",
        "relevant": ["rust-ownership", "rust-compiler", "cross-memory"],
    },
    {
        "question": "How do Java and Python differ in threading and parallelism?",
        "relevant": ["python-gil", "java-threads", "cross-concurrency"],
    },
    {
        "question": "What package managers do Python, Java and Rust use?",
        "relevant": ["python-packages", "java-maven", "rust-cargo"],
    },
    {
        "question": "How is compile-time metaprogramming done in Rust?",
        "relevant": ["rust-macros", "rust-compiler", "rust-traits"],
    },
    {
        "question": "What are the type system features of Java including generics?",
        "relevant": ["java-generics", "java-annotations", "rust-traits"],
    },
    {
        "question": "Explain JVM JIT compilation and platform independence.",
        "relevant": ["java-jvm", "java-gc", "java-threads"],
    },
]
