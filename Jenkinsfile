pipeline {
    agent any

    environment {
        IMAGE_NAME = 'saharshvashishtha/aceest-fitness'
        IMAGE_TAG = "${BUILD_NUMBER}"
        PYTHON_EXE = 'C:\\Users\\saharsh vashishtha\\AppData\\Local\\Programs\\Python\\Python312\\python.exe'
        KUBECONFIG = 'C:\\Users\\saharsh vashishtha\\.kube\\config'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup and Install') {
            steps {
                bat '''
                if exist venv rmdir /s /q venv

                "%PYTHON_EXE%" --version
                "%PYTHON_EXE%" -m venv venv

                venv\\Scripts\\python -m pip install --upgrade pip setuptools wheel
                venv\\Scripts\\python -m pip install -r requirements.txt
                venv\\Scripts\\python -m pip install pytest pytest-cov flake8
                '''
            }
        }

        stage('Lint') {
            steps {
                bat '''
                venv\\Scripts\\python -m flake8 .
                '''
            }
        }

        stage('Test') {
            steps {
                bat '''
                venv\\Scripts\\python -m pytest --cov=. --cov-report=xml --cov-report=term
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                bat '''
                docker build -t %IMAGE_NAME%:%IMAGE_TAG% .
                '''
            }
        }

        stage('Push Docker Image') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: '53dd520f-3072-4b33-807e-55518476daed',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    bat '''
                    echo %DOCKER_PASS% | docker login -u %DOCKER_USER% --password-stdin
                    docker push %IMAGE_NAME%:%IMAGE_TAG%
                    '''
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                bat '''
                kubectl config use-context minikube
                kubectl config current-context
                kubectl get ns
                kubectl get deployment -n aceest

                kubectl set image deployment/aceest-fitness aceest-fitness=%IMAGE_NAME%:%IMAGE_TAG% -n aceest
                kubectl rollout status deployment/aceest-fitness -n aceest
                '''
            }
        }
    }

    post {
        failure {
            bat '''
            kubectl config current-context >nul 2>&1
            if %ERRORLEVEL% NEQ 0 exit /b 0

            kubectl rollout undo deployment/aceest-fitness -n aceest
            if %ERRORLEVEL% NEQ 0 exit /b 0
            '''
        }
    }
}