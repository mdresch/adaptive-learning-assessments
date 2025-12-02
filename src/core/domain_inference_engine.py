"""
Domain Inference Engine

This module provides algorithms for automatically inferring the primary domain
of learning documents and content based on content analysis.
"""

import re
import logging
from typing import Dict, List, Tuple, Any, Optional
from collections import Counter
from datetime import datetime

from ..models.template_analytics import DomainCategory, DomainAssociation

logger = logging.getLogger(__name__)


class DomainInferenceEngine:
    """Engine for inferring document domains based on content analysis"""

    def __init__(self):
        self.domain_keywords = self._initialize_domain_keywords()
        self.domain_patterns = self._initialize_domain_patterns()
        self.feature_weights = self._initialize_feature_weights()

    def _initialize_domain_keywords(self) -> Dict[DomainCategory, List[str]]:
        """Initialize domain-specific keywords for classification"""
        return {
            DomainCategory.PROGRAMMING: [
                "python", "java", "javascript", "c++", "code", "function", "variable",
                "loop", "conditional", "syntax", "debugging", "programming", "script",
                "method", "class", "object", "inheritance", "polymorphism", "encapsulation",
                "api", "framework", "library", "module", "package", "import", "compile"
            ],
            DomainCategory.DATA_STRUCTURES: [
                "array", "list", "stack", "queue", "tree", "graph", "hash", "linked list",
                "binary tree", "heap", "priority queue", "set", "map", "dictionary",
                "vector", "matrix", "node", "pointer", "index", "sort", "search",
                "traversal", "insertion", "deletion", "data structure", "collection"
            ],
            DomainCategory.ALGORITHMS: [
                "algorithm", "complexity", "big o", "time complexity", "space complexity",
                "sorting", "searching", "recursion", "iteration", "dynamic programming",
                "greedy", "divide and conquer", "backtracking", "optimization",
                "efficiency", "performance", "analysis", "asymptotic", "logarithmic",
                "linear", "quadratic", "exponential", "polynomial", "np-complete"
            ],
            DomainCategory.MATHEMATICS: [
                "mathematics", "math", "algebra", "calculus", "geometry", "statistics",
                "probability", "linear algebra", "discrete math", "number theory",
                "equation", "formula", "theorem", "proof", "derivative", "integral",
                "matrix", "vector", "function", "graph", "set theory", "logic",
                "combinatorics", "optimization", "numerical", "mathematical"
            ],
            DomainCategory.COMPUTER_SCIENCE: [
                "computer science", "theoretical", "computational", "formal methods",
                "automata", "finite state", "turing machine", "complexity theory",
                "computability", "formal language", "grammar", "parsing", "compiler",
                "operating system", "computer architecture", "processor", "memory",
                "cache", "parallel", "distributed", "concurrent", "synchronization"
            ],
            DomainCategory.SOFTWARE_ENGINEERING: [
                "software engineering", "design patterns", "architecture", "requirements",
                "testing", "debugging", "version control", "git", "agile", "scrum",
                "waterfall", "lifecycle", "documentation", "maintenance", "deployment",
                "continuous integration", "devops", "quality assurance", "code review",
                "refactoring", "technical debt", "scalability", "reliability"
            ],
            DomainCategory.WEB_DEVELOPMENT: [
                "web development", "html", "css", "javascript", "react", "angular", "vue",
                "frontend", "backend", "fullstack", "responsive", "bootstrap", "jquery",
                "ajax", "rest", "api", "http", "https", "json", "xml", "dom",
                "browser", "client", "server", "database", "sql", "nosql", "mongodb"
            ],
            DomainCategory.DATABASE: [
                "database", "sql", "nosql", "mysql", "postgresql", "mongodb", "redis",
                "query", "table", "schema", "index", "primary key", "foreign key",
                "join", "transaction", "acid", "normalization", "denormalization",
                "backup", "recovery", "replication", "sharding", "data modeling",
                "entity relationship", "relational", "document", "key-value"
            ],
            DomainCategory.MACHINE_LEARNING: [
                "machine learning", "artificial intelligence", "neural network",
                "deep learning", "supervised", "unsupervised", "reinforcement",
                "classification", "regression", "clustering", "feature", "training",
                "model", "algorithm", "prediction", "accuracy", "precision", "recall",
                "cross validation", "overfitting", "underfitting", "gradient descent",
                "backpropagation", "tensorflow", "pytorch", "scikit-learn"
            ],
            DomainCategory.CYBERSECURITY: [
                "cybersecurity", "security", "encryption", "cryptography", "authentication",
                "authorization", "vulnerability", "threat", "attack", "malware",
                "firewall", "intrusion", "penetration testing", "ethical hacking",
                "ssl", "tls", "certificate", "hash", "digital signature", "privacy",
                "gdpr", "compliance", "risk assessment", "incident response"
            ]
        }

    def _initialize_domain_patterns(self) -> Dict[DomainCategory, List[str]]:
        """Initialize regex patterns for domain identification"""
        return {
            DomainCategory.PROGRAMMING: [
                r'\b(def|function|class|import|from|if|else|for|while|try|except)\b',
                r'\b\w+\(\)',  # Function calls
                r'[=]{1,2}|[!<>]=?',  # Operators
                r'[\[\]{}()]',  # Brackets and parentheses
            ],
            DomainCategory.DATA_STRUCTURES: [
                r'\b(array|list|stack|queue|tree|graph|node)\[.*?\]',
                r'\b(insert|delete|search|traverse|sort)\b',
                r'\bO\([^)]+\)',  # Big O notation
            ],
            DomainCategory.ALGORITHMS: [
                r'\bO\([^)]+\)',  # Big O notation
                r'\b(time|space)\s+complexity\b',
                r'\b(recursive|iterative)\s+(solution|approach)\b',
            ],
            DomainCategory.MATHEMATICS: [
                r'[∑∏∫∂∇]',  # Mathematical symbols
                r'\b(theorem|proof|lemma|corollary)\b',
                r'\b\d+\s*[+\-*/]\s*\d+\b',  # Mathematical expressions
            ],
            DomainCategory.WEB_DEVELOPMENT: [
                r'<[^>]+>',  # HTML tags
                r'\.(css|js|html|php)$',  # File extensions
                r'\b(GET|POST|PUT|DELETE)\b',  # HTTP methods
            ],
            DomainCategory.DATABASE: [
                r'\b(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)\b',
                r'\b(FROM|WHERE|JOIN|GROUP BY|ORDER BY)\b',
                r'\b(PRIMARY KEY|FOREIGN KEY|INDEX)\b',
            ]
        }

    def _initialize_feature_weights(self) -> Dict[str, float]:
        """Initialize weights for different content features"""
        return {
            "keyword_density": 0.4,
            "pattern_matches": 0.3,
            "content_structure": 0.2,
            "metadata_hints": 0.1
        }

    def analyze_content(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze content and extract features for domain inference"""
        try:
            # Clean and normalize content
            cleaned_content = self._clean_content(content)
            
            # Extract features
            features = {
                "keyword_scores": self._calculate_keyword_scores(cleaned_content),
                "pattern_scores": self._calculate_pattern_scores(cleaned_content),
                "content_length": len(cleaned_content),
                "word_count": len(cleaned_content.split()),
                "code_blocks": self._count_code_blocks(content),
                "technical_terms": self._count_technical_terms(cleaned_content),
                "complexity_indicators": self._analyze_complexity(cleaned_content)
            }
            
            # Add metadata features if available
            if metadata:
                features["metadata_hints"] = self._extract_metadata_hints(metadata)
            
            return features

        except Exception as e:
            logger.error(f"Error analyzing content: {e}")
            return {}

    def infer_domain(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[DomainCategory, float, List[DomainAssociation]]:
        """Infer the primary domain and confidence score for content"""
        try:
            # Analyze content features
            features = self.analyze_content(content, metadata)
            
            if not features:
                return DomainCategory.OTHER, 0.0, []
            
            # Calculate domain scores
            domain_scores = self._calculate_domain_scores(features)
            
            # Find primary domain
            primary_domain = max(domain_scores.keys(), key=lambda k: domain_scores[k])
            primary_confidence = domain_scores[primary_domain]
            
            # Create secondary domain associations
            secondary_domains = []
            for domain, score in sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)[1:4]:
                if score > 0.3:  # Minimum threshold for secondary domains
                    secondary_domains.append(DomainAssociation(
                        domain=domain,
                        confidence=score,
                        evidence_count=1
                    ))
            
            # Normalize confidence score
            normalized_confidence = min(primary_confidence, 1.0)
            
            logger.info(f"Inferred domain: {primary_domain.value} with confidence: {normalized_confidence:.3f}")
            
            return primary_domain, normalized_confidence, secondary_domains

        except Exception as e:
            logger.error(f"Error inferring domain: {e}")
            return DomainCategory.OTHER, 0.0, []

    def _clean_content(self, content: str) -> str:
        """Clean and normalize content for analysis"""
        # Convert to lowercase
        content = content.lower()
        
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove special characters but keep alphanumeric and basic punctuation
        content = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\{\}]', ' ', content)
        
        return content.strip()

    def _calculate_keyword_scores(self, content: str) -> Dict[DomainCategory, float]:
        """Calculate keyword-based scores for each domain"""
        scores = {}
        words = content.split()
        total_words = len(words)
        
        if total_words == 0:
            return {domain: 0.0 for domain in DomainCategory}
        
        for domain, keywords in self.domain_keywords.items():
            keyword_count = sum(1 for word in words if word in keywords)
            scores[domain] = keyword_count / total_words
        
        return scores

    def _calculate_pattern_scores(self, content: str) -> Dict[DomainCategory, float]:
        """Calculate pattern-based scores for each domain"""
        scores = {}
        
        for domain, patterns in self.domain_patterns.items():
            pattern_matches = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, content, re.IGNORECASE))
                pattern_matches += matches
            
            # Normalize by content length
            scores[domain] = min(pattern_matches / max(len(content), 1) * 1000, 1.0)
        
        # Set default scores for domains without patterns
        for domain in DomainCategory:
            if domain not in scores:
                scores[domain] = 0.0
        
        return scores

    def _count_code_blocks(self, content: str) -> int:
        """Count code blocks in content"""
        # Look for common code block indicators
        code_patterns = [
            r'```[\s\S]*?```',  # Markdown code blocks
            r'<code>[\s\S]*?</code>',  # HTML code tags
            r'<pre>[\s\S]*?</pre>',  # HTML pre tags
            r'^\s{4,}.*$',  # Indented code (markdown style)
        ]
        
        total_blocks = 0
        for pattern in code_patterns:
            total_blocks += len(re.findall(pattern, content, re.MULTILINE))
        
        return total_blocks

    def _count_technical_terms(self, content: str) -> int:
        """Count technical terms in content"""
        technical_patterns = [
            r'\b[A-Z]{2,}\b',  # Acronyms
            r'\b\w+\(\)',  # Function calls
            r'\b\w+\.\w+\b',  # Method calls or file extensions
            r'\b[a-z]+[A-Z]\w*\b',  # CamelCase
        ]
        
        total_terms = 0
        for pattern in technical_patterns:
            total_terms += len(re.findall(pattern, content))
        
        return total_terms

    def _analyze_complexity(self, content: str) -> Dict[str, float]:
        """Analyze content complexity indicators"""
        words = content.split()
        
        if not words:
            return {"avg_word_length": 0.0, "sentence_complexity": 0.0}
        
        # Average word length
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Sentence complexity (approximate)
        sentences = re.split(r'[.!?]+', content)
        avg_sentence_length = len(words) / max(len(sentences), 1)
        sentence_complexity = min(avg_sentence_length / 20, 1.0)  # Normalize
        
        return {
            "avg_word_length": avg_word_length,
            "sentence_complexity": sentence_complexity
        }

    def _extract_metadata_hints(self, metadata: Dict[str, Any]) -> Dict[DomainCategory, float]:
        """Extract domain hints from metadata"""
        hints = {domain: 0.0 for domain in DomainCategory}
        
        # Check file extensions
        if "file_extension" in metadata:
            ext = metadata["file_extension"].lower()
            if ext in [".py", ".java", ".js", ".cpp", ".c"]:
                hints[DomainCategory.PROGRAMMING] += 0.5
            elif ext in [".html", ".css", ".php"]:
                hints[DomainCategory.WEB_DEVELOPMENT] += 0.5
            elif ext in [".sql"]:
                hints[DomainCategory.DATABASE] += 0.5
        
        # Check tags or categories
        if "tags" in metadata:
            tags = [tag.lower() for tag in metadata["tags"]]
            for domain, keywords in self.domain_keywords.items():
                for tag in tags:
                    if tag in keywords:
                        hints[domain] += 0.3
        
        # Check title or subject
        if "title" in metadata:
            title_features = self.analyze_content(metadata["title"])
            if "keyword_scores" in title_features:
                for domain, score in title_features["keyword_scores"].items():
                    hints[domain] += score * 0.4
        
        return hints

    def _calculate_domain_scores(self, features: Dict[str, Any]) -> Dict[DomainCategory, float]:
        """Calculate final domain scores based on all features"""
        scores = {domain: 0.0 for domain in DomainCategory}
        
        # Keyword scores
        if "keyword_scores" in features:
            for domain, score in features["keyword_scores"].items():
                scores[domain] += score * self.feature_weights["keyword_density"]
        
        # Pattern scores
        if "pattern_scores" in features:
            for domain, score in features["pattern_scores"].items():
                scores[domain] += score * self.feature_weights["pattern_matches"]
        
        # Content structure scores
        structure_bonus = 0.0
        if features.get("code_blocks", 0) > 0:
            structure_bonus += 0.3
            scores[DomainCategory.PROGRAMMING] += structure_bonus * 0.5
            scores[DomainCategory.WEB_DEVELOPMENT] += structure_bonus * 0.3
        
        if features.get("technical_terms", 0) > 5:
            structure_bonus += 0.2
            # Distribute among technical domains
            for domain in [DomainCategory.COMPUTER_SCIENCE, DomainCategory.SOFTWARE_ENGINEERING]:
                scores[domain] += structure_bonus * 0.3
        
        # Apply structure bonus
        for domain in scores:
            scores[domain] += structure_bonus * self.feature_weights["content_structure"] / len(DomainCategory)
        
        # Metadata hints
        if "metadata_hints" in features:
            for domain, hint_score in features["metadata_hints"].items():
                scores[domain] += hint_score * self.feature_weights["metadata_hints"]
        
        return scores

    def batch_infer_domains(self, documents: List[Dict[str, Any]]) -> List[Tuple[str, DomainCategory, float, List[DomainAssociation]]]:
        """Batch process multiple documents for domain inference"""
        results = []
        
        for doc in documents:
            doc_id = doc.get("id", "unknown")
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            
            try:
                primary_domain, confidence, secondary_domains = self.infer_domain(content, metadata)
                results.append((doc_id, primary_domain, confidence, secondary_domains))
                
            except Exception as e:
                logger.error(f"Error processing document {doc_id}: {e}")
                results.append((doc_id, DomainCategory.OTHER, 0.0, []))
        
        return results