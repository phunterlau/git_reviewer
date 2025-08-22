"""
Technical Proficiency Analyzer

Implements Category 1 analysis: Core AI/ML Technical Proficiency
Analyzes dependency sophistication, framework usage, and code complexity.
"""

import re
import os
from typing import Dict, List, Tuple, Set
from collections import defaultdict, Counter

from ..models.metrics import TechnicalProficiencyMetrics, ActivityData


class TechnicalProficiencyAnalyzer:
    """Analyzer for Category 1: Core AI/ML Technical Proficiency."""
    
    def __init__(self):
        """Initialize analyzer with technology detection patterns."""
        self._init_tech_patterns()
    
    def _init_tech_patterns(self):
        """Initialize technology detection patterns."""
        
        # AI/ML frameworks (comprehensive list)
        self.ai_ml_frameworks = {
            # Deep Learning Frameworks
            'torch', 'pytorch', 'tensorflow', 'tf', 'jax', 'flax', 'keras',
            'mxnet', 'paddle', 'oneflow', 'mindspore',
            
            # NLP/LLM Libraries  
            'transformers', 'langchain', 'llama', 'openai', 'anthropic',
            'spacy', 'nltk', 'gensim', 'sentence-transformers',
            
            # Traditional ML
            'scikit-learn', 'sklearn', 'xgboost', 'lightgbm', 'catboost',
            'pandas', 'numpy', 'scipy', 'statsmodels',
            
            # MLOps and Experiment Tracking
            'mlflow', 'dvc', 'wandb', 'neptune', 'tensorboard', 'optuna',
            'hyperopt', 'ray', 'tune', 'kubeflow',
            
            # Performance Optimization
            'triton', 'tensorrt', 'onnx', 'openvino', 'cuda', 'cupy',
            'numba', 'cython', 'tvm', 'tensorlite',
            
            # Computer Vision
            'opencv', 'cv2', 'pillow', 'imageio', 'albumentations',
            'torchvision', 'detectron2', 'mmdetection',
            
            # Audio/Speech
            'librosa', 'torchaudio', 'soundfile', 'whisper', 'espnet'
        }
        
        # Performance languages by file extension
        self.performance_languages = {
            '.rs': 'rust',
            '.cpp': 'cpp', 
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.zig': 'zig',
            '.jl': 'julia',
            '.cu': 'cuda'
        }
        
        # API and web frameworks
        self.api_frameworks = {
            'fastapi', 'flask', 'django', 'starlette', 'aiohttp',
            'tornado', 'bottle', 'falcon', 'sanic',
            'grpc', 'graphql', 'rest', 'restful'
        }
        
        # Infrastructure and deployment keywords
        self.infra_keywords = {
            'docker', 'kubernetes', 'k8s', 'terraform', 'helm',
            'aws', 'gcp', 'azure', 'cloud', 'serverless',
            'lambda', 'ec2', 's3', 'rds', 'redis',
            'postgres', 'mongodb', 'elasticsearch',
            'nginx', 'apache', 'gunicorn', 'uvicorn',
            'celery', 'airflow', 'kafka', 'rabbitmq'
        }
        
        # Advanced code complexity indicators
        self.complexity_indicators = {
            'async', 'await', 'asyncio', 'threading', 'multiprocessing',
            'concurrent', 'parallel', 'distributed', 'queue',
            'decorator', 'metaclass', 'generator', 'yield',
            'context manager', '__enter__', '__exit__',
            'property', 'classmethod', 'staticmethod',
            'inheritance', 'polymorphism', 'abstraction'
        }
    
    def analyze_dependency_files(self, commits: List[Dict]) -> Tuple[Dict[str, int], float]:
        """
        Analyze dependency files for framework sophistication.
        
        Args:
            commits: List of commit data
            
        Returns:
            Tuple of (framework_usage_counts, sophistication_score)
        """
        framework_usage = defaultdict(int)
        dependency_files = [
            'requirements.txt', 'pyproject.toml', 'setup.py', 'environment.yml',
            'Pipfile', 'poetry.lock', 'package.json', 'Cargo.toml', 'go.mod'
        ]
        
        dependency_changes = 0
        advanced_frameworks = 0
        
        for commit in commits:
            if 'files' in commit:
                for file_info in commit['files']:
                    filename = os.path.basename(file_info['filename']).lower()
                    
                    if filename in dependency_files:
                        dependency_changes += 1
                        
                        # Analyze patch content for framework additions
                        if 'patch' in file_info:
                            patch_content = file_info['patch'].lower()
                            
                            for framework in self.ai_ml_frameworks:
                                if framework in patch_content:
                                    framework_usage[framework] += 1
                                    
                                    # Count advanced frameworks for sophistication score
                                    if framework in ['triton', 'tensorrt', 'mlflow', 'dvc', 
                                                   'wandb', 'ray', 'kubeflow', 'optuna']:
                                        advanced_frameworks += 1
        
        # Calculate sophistication score (0-1)
        if dependency_changes == 0:
            sophistication_score = 0.0
        else:
            # Score based on ratio of advanced frameworks and diversity
            diversity_score = min(len(framework_usage) / 10.0, 1.0)  # Max 10 different frameworks
            advanced_ratio = min(advanced_frameworks / dependency_changes, 1.0)
            sophistication_score = (diversity_score + advanced_ratio) / 2.0
        
        return dict(framework_usage), sophistication_score
    
    def analyze_language_distribution(self, commits: List[Dict]) -> Dict[str, int]:
        """
        Analyze distribution of performance languages.
        
        Args:
            commits: List of commit data
            
        Returns:
            Dict mapping language to line count
        """
        language_stats = defaultdict(int)
        
        for commit in commits:
            if 'files' in commit:
                for file_info in commit['files']:
                    filename = file_info['filename']
                    _, ext = os.path.splitext(filename.lower())
                    
                    if ext in self.performance_languages:
                        language = self.performance_languages[ext]
                        # Use additions as proxy for lines written
                        language_stats[language] += file_info.get('additions', 0)
        
        return dict(language_stats)
    
    def analyze_full_stack_evidence(self, commits: List[Dict]) -> List[str]:
        """
        Find evidence of full-stack development capabilities.
        
        Args:
            commits: List of commit data
            
        Returns:
            List of full-stack evidence strings
        """
        evidence = set()
        
        # Track different types of files and frameworks
        file_types_seen = set()
        frameworks_found = set()
        infra_found = set()
        
        for commit in commits:
            commit_message = commit.get('message', '').lower()
            
            # Check commit message for API/infra keywords
            for keyword in self.api_frameworks:
                if keyword in commit_message:
                    frameworks_found.add(keyword)
            
            for keyword in self.infra_keywords:
                if keyword in commit_message:
                    infra_found.add(keyword)
            
            if 'files' in commit:
                for file_info in commit['files']:
                    filename = file_info['filename'].lower()
                    
                    # Categorize file types
                    if any(ext in filename for ext in ['.py', '.js', '.ts', '.go', '.rs']):
                        file_types_seen.add('backend')
                    elif any(ext in filename for ext in ['.html', '.css', '.jsx', '.tsx', '.vue']):
                        file_types_seen.add('frontend')
                    elif any(name in filename for name in ['dockerfile', 'docker-compose', '.yml', '.yaml']):
                        file_types_seen.add('infrastructure')
                    elif any(ext in filename for ext in ['.sql', '.db']):
                        file_types_seen.add('database')
        
        # Generate evidence based on findings
        if len(file_types_seen) >= 3:
            evidence.add(f"Multi-layer development: {', '.join(sorted(file_types_seen))}")
        
        if frameworks_found:
            evidence.add(f"API frameworks: {', '.join(sorted(frameworks_found))}")
        
        if infra_found:
            evidence.add(f"Infrastructure tools: {', '.join(sorted(infra_found))}")
        
        if 'backend' in file_types_seen and 'frontend' in file_types_seen:
            evidence.add("Full-stack web development")
        
        if 'infrastructure' in file_types_seen:
            evidence.add("DevOps and deployment experience")
        
        return list(evidence)
    
    def analyze_code_complexity(self, commits: List[Dict]) -> List[str]:
        """
        Analyze code complexity indicators from patches.
        
        Args:
            commits: List of commit data
            
        Returns:
            List of complexity indicators found
        """
        complexity_found = set()
        
        for commit in commits:
            if 'files' in commit:
                for file_info in commit['files']:
                    if 'patch' in file_info:
                        patch_content = file_info['patch'].lower()
                        
                        # Look for complexity indicators
                        for indicator in self.complexity_indicators:
                            if indicator in patch_content:
                                complexity_found.add(indicator)
                        
                        # Additional pattern-based detection
                        if re.search(r'class.*\(.*\):', patch_content):
                            complexity_found.add('inheritance')
                        
                        if re.search(r'@\w+', patch_content):
                            complexity_found.add('decorators')
                        
                        if re.search(r'def.*yield', patch_content):
                            complexity_found.add('generators')
                        
                        if re.search(r'with.*as', patch_content):
                            complexity_found.add('context_managers')
        
        return list(complexity_found)
    
    def analyze_production_readiness(self, commits: List[Dict]) -> List[str]:
        """
        Analyze signals of production-ready code.
        
        Args:
            commits: List of commit data
            
        Returns:
            List of production readiness signals
        """
        signals = set()
        
        production_patterns = {
            'logging': ['logging', 'logger', 'log.', 'debug', 'info', 'warning', 'error'],
            'error_handling': ['try:', 'except:', 'raise', 'exception', 'error'],
            'testing': ['test_', 'unittest', 'pytest', 'mock', 'assert'],
            'configuration': ['config', 'settings', 'env', 'environment'],
            'monitoring': ['metrics', 'prometheus', 'grafana', 'alert', 'monitor'],
            'security': ['auth', 'token', 'jwt', 'ssl', 'encrypt', 'secure'],
            'performance': ['cache', 'redis', 'memcache', 'optimize', 'performance']
        }
        
        pattern_counts = defaultdict(int)
        
        for commit in commits:
            commit_message = commit.get('message', '').lower()
            
            if 'files' in commit:
                for file_info in commit['files']:
                    content = f"{file_info['filename']} {file_info.get('patch', '')}".lower()
                    
                    for category, patterns in production_patterns.items():
                        for pattern in patterns:
                            if pattern in content:
                                pattern_counts[category] += 1
        
        # Generate signals based on evidence
        for category, count in pattern_counts.items():
            if count >= 3:  # Threshold for meaningful evidence
                signals.add(f"{category.replace('_', ' ').title()}: {count} instances")
        
        return list(signals)
    
    def analyze(self, activity_data: ActivityData) -> TechnicalProficiencyMetrics:
        """
        Perform comprehensive technical proficiency analysis.
        
        Args:
            activity_data: Raw GitHub activity data
            
        Returns:
            TechnicalProficiencyMetrics with analysis results
        """
        print("🔬 Analyzing Technical Proficiency...")
        
        commits = activity_data.commits
        
        # Analyze different aspects
        framework_usage, sophistication_score = self.analyze_dependency_files(commits)
        language_distribution = self.analyze_language_distribution(commits)
        full_stack_evidence = self.analyze_full_stack_evidence(commits)
        complexity_indicators = self.analyze_code_complexity(commits)
        production_signals = self.analyze_production_readiness(commits)
        
        # Extract AI/ML frameworks from usage
        ai_ml_frameworks = [fw for fw in framework_usage.keys() if fw in self.ai_ml_frameworks]
        
        # Create metrics object
        metrics = TechnicalProficiencyMetrics(
            ai_ml_frameworks=ai_ml_frameworks,
            performance_languages=language_distribution,
            full_stack_evidence=full_stack_evidence,
            dependency_sophistication_score=sophistication_score,
            code_complexity_indicators=complexity_indicators,
            advanced_library_usage=framework_usage,
            production_readiness_signals=production_signals
        )
        
        print(f"✅ Technical Analysis Complete:")
        print(f"  - AI/ML Frameworks: {len(ai_ml_frameworks)}")
        print(f"  - Performance Languages: {len(language_distribution)}")
        print(f"  - Sophistication Score: {sophistication_score:.2f}")
        print(f"  - Complexity Indicators: {len(complexity_indicators)}")
        
        return metrics
