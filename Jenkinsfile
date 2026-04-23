pipeline {
    agent any

    environment {
        IMAGE_NAME = 'saharshvashishtha/aceest-fitness'
        IMAGE_TAG = "${BUILD_NUMBER}"
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
        python -m venv venv
        venv\\Scripts\\python -m pip install --upgrade pip
        venv\\Scripts\\python -m pip install -r requirements.txt
        venv\\Scripts\\python -m pip install pytest pytest-cov flake8
        '''
    }
}

        stage('Lint') {
    steps {
        bat 'venv\\Scripts\\python -m flake8 --exclude=venv,__pycache__,.git .'
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
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
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
                kubectl set image deployment/aceest-fitness aceest-fitness=%IMAGE_NAME%:%IMAGE_TAG% -n aceest
                kubectl rollout status deployment/aceest-fitness -n aceest
                '''
            }
        }
    }

    post {
        failure {
            bat '''
            kubectl rollout undo deployment/aceest-fitness -n aceest
            '''
        }
    }
}