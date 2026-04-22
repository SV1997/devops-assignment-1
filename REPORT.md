# CI/CD Report - ACEest Fitness & Gym

## 1. CI/CD Architecture Overview
The application is a Flask-based fitness and gym management API. GitHub stores the source code and Jenkins acts as the automation server. The pipeline checks out code, creates a Python environment, runs lint validation with flake8, executes Pytest, and generates coverage. SonarQube performs static code analysis and enforces a quality gate. Docker is used to build the application image, Docker Hub stores versioned images, and Kubernetes on Minikube deploys the application. Rollout checks and health probes improve release reliability.

## 2. Deployment and Release Design
The base release uses rolling update deployment. Blue-green deployment is represented through separate blue and green tracks with service switching. Canary release is represented using stable and canary deployments. Shadow deployment is represented using ingress mirroring so the shadow version receives mirrored traffic without serving users directly. A/B testing is represented using ingress rules based on a request header.

## 3. Challenges Faced
The original project supported application code, tests, Docker, and a simple Jenkins pipeline, but not a full delivery pipeline. The main challenge was extending it into a complete CI/CD workflow with quality gates, image publishing, Kubernetes deployment, rollback, and advanced release strategies. Another challenge was expressing shadow deployment and A/B testing in a local Minikube environment.

## 4. Mitigation Strategies
Cross-platform Jenkins steps were used to avoid a hardcoded local Python path. Readiness and liveness probes were added to reduce deployment failures. Rollback support was added using `kubectl rollout undo`. Docker image versioning was introduced so builds are traceable. Helper scripts simplify deployment and rollback for demonstration.

## 5. Key Automation Outcomes
The final solution automates validation, static analysis, image creation, registry publishing, deployment, and rollback. This improves delivery speed, consistency, and software quality while aligning with the assignment learning outcomes.
